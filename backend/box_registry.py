from fastapi import HTTPException
from pydantic import BaseModel,Field

POINTS=("禾湾库","河桥渠口","渡河库","河桥厅")

class Box(BaseModel):
    tag:str=Field(pattern=r"^BX-[0-9]{2,7}$")
    serial:str=Field(pattern=r"^HH-[0-9]{4,7}$")
    seal:str=Field(pattern=r"^ZC-[0-9]{5,9}$")
    owner_club:str=Field(min_length=3,max_length=40)
    origin:str
    target:str

def register(cx,body):
    if body.origin==body.target or any(p not in POINTS for p in (body.origin,body.target)):
        raise HTTPException(409,"始发与目的库点需不同且在交接簿名录内")
    cx.execute("INSERT INTO timing_cases VALUES(%(tag)s,%(serial)s,%(seal)s,%(owner_club)s,%(origin)s,%(target)s,'registered')",body.model_dump())
    return {"tag":body.tag,"phase":"registered"}
