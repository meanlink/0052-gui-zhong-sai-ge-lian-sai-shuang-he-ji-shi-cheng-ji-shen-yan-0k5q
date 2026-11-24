from datetime import datetime
from fastapi import HTTPException
from pydantic import BaseModel,Field,field_validator
from box_registry import POINTS

class Stop(BaseModel):
    location:str
    clock_at:datetime
    witness:str=Field(min_length=2,max_length=50)
    seal:str
    @field_validator("clock_at")
    @classmethod
    def zone(cls,value):
        if value.utcoffset() is None:
            raise ValueError("发生时间必须包含时区")
        return value

def recent(cx,tag):
    return cx.execute("SELECT * FROM box_handoffs WHERE tag=%s ORDER BY seq DESC LIMIT 1",(tag,)).fetchone()

def capture(cx,tag,data):
    case=cx.execute("SELECT * FROM timing_cases WHERE tag=%s FOR UPDATE",(tag,)).fetchone()
    if not case:
        raise HTTPException(404,"计时盒尚未登记")
    if cx.execute("SELECT 1 FROM clock_anchors WHERE box=%s",(tag,)).fetchone():
        raise HTTPException(409,"计时盒已校点，赛台交接证据冻结")
    if data.seal!=case["seal"]:
        raise HTTPException(409,"封条号与登记不匹配")
    last=recent(cx,tag)
    if data.location not in POINTS or (last and (data.clock_at<=last["clock_at"] or data.location==last["location"])):
        raise HTTPException(409,"交接地点应相异且发生时间须递增")
    if not last and data.location!=case["origin"]:
        raise HTTPException(409,"首次交接必须由登记始发点确认")
    seq=last["seq"]+1 if last else 1
    cx.execute("INSERT INTO box_handoffs VALUES(%s,%s,%s,%s,%s)",(tag,seq,data.location,data.clock_at,data.witness))
    return {"seq":seq}
