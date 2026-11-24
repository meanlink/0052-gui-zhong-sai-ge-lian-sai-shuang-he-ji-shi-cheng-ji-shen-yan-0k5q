from fastapi import HTTPException
from psycopg.types.json import Jsonb
from meet_records import active

def order_results(rows):
    result=[]
    counters={}
    keys=sorted({r["group"] for r in rows})
    for key in keys:
        order=sorted((r for r in rows if r["group"]==key),key=lambda r:(r["elapsed_ms"],r["bird"]))
        last=None
        for position,row in enumerate(order,1):
            if last!=row["elapsed_ms"]:
                counters[key]=position
            result.append(row|{"rank":counters[key]})
            last=row["elapsed_ms"]
    return result

def archive(cx,key,notes,actor):
    active(cx,key)
    audit=cx.execute("SELECT * FROM clock_audits WHERE meet=%s",(key,)).fetchone()
    if not audit or audit["blocked"]:
        raise HTTPException(409,"待复录击钟或缺失的新审验拦截成绩归档")
    scored=order_results(audit["results"])
    cx.execute('''
      INSERT INTO score_ledgers(meet,standings,evidence,source_audit,notes,approved_by)
      VALUES(%s,%s,%s,%s,%s,%s)
    ''',(key,Jsonb(scored),Jsonb(audit["offsets"]),audit["analyzed_at"],notes,actor))
    cx.execute("UPDATE meets SET status='archived' WHERE code=%s",(key,))
    return {"meet":key,"scored":len(scored),"state":"archived"}
