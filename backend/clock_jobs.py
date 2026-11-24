from datetime import timedelta
from fastapi import HTTPException
from psycopg.types.json import Jsonb
from meet_records import active
from robust_offset import offset_for
from handoff_ledger import recent

MAX_DISAGREEMENT_MS=500

def project(click, primary, witness, meet):
    left=click["primary_at"]-timedelta(milliseconds=primary)
    right=click["witness_at"]-timedelta(milliseconds=witness)
    disagreement=abs((left-right).total_seconds()*1000)
    center=left+(right-left)/2
    flag=""
    if any(not meet["finish_from"]<=instant<=meet["finish_to"] for instant in (left,right)):
        flag="超出本场计时窗"
    elif disagreement>MAX_DISAGREEMENT_MS:
        flag="双盒时差超 500 ms"
    elif center<=click["released_at"]:
        flag="计时早于所属组放飞"
    return {"bird":click["bird"],"group":click["group_code"],"club":click["club"],
        "corrected_at":center.isoformat(),"elapsed_ms":round((center-click["released_at"]).total_seconds()*1000),
        "disagreement_ms":round(disagreement,3),"revision":click["revision"],"flag":flag}

def run_job(cx,kind,payload):
    if kind!="twin-clock-audit":
        raise ValueError(kind)
    key=payload["meet"]
    meet=active(cx,key)
    kits=(meet["primary_box"],meet["witness_box"])
    for box in sorted(kits):
        cx.execute("SELECT tag FROM timing_cases WHERE tag=%s FOR UPDATE",(box,))
        custody=recent(cx,box)
        if not custody or custody["location"]!=meet["desk"] or custody["clock_at"]>meet["calibration_to"]:
            raise HTTPException(409,"两只计时盒均须在校点有效期内进同一赛台")
    anchors=cx.execute("SELECT * FROM clock_anchors WHERE meet=%s ORDER BY reference_at",(key,)).fetchall()
    offsets={box:offset_for(box,[r for r in anchors if r["box"]==box]) for box in kits}
    clicks=cx.execute('''
        SELECT f.*,g.club,g.released_at FROM finish_clicks f JOIN release_groups g
        ON f.meet=g.meet AND f.group_code=g.code WHERE f.meet=%s ORDER BY f.bird
    ''',(key,)).fetchall()
    if not clicks:
        raise HTTPException(409,"需先导入至少一条归巢击钟")
    results=[project(click,*(offsets[kit]["offset_ms"] for kit in kits),meet) for click in clicks]
    blocked=sum(bool(row["flag"]) for row in results)
    cx.execute('''
        INSERT INTO clock_audits(meet,offsets,results,blocked) VALUES(%s,%s,%s,%s)
        ON CONFLICT(meet) DO UPDATE SET offsets=excluded.offsets,results=excluded.results,
            blocked=excluded.blocked,analyzed_at=now()
    ''',(key,Jsonb(offsets),Jsonb(results),blocked))
    return {"meet":key,"offsets":offsets,"results":results,"blocked":blocked}
