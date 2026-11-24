from fastapi import APIRouter,Depends
from core import db,require
from handoff_ledger import Stop,capture
router=APIRouter(prefix="/handoffs")
@router.get("")
def all_stops(_=Depends(require())):
    with db() as cx:
        return cx.execute("SELECT * FROM box_handoffs ORDER BY tag,seq").fetchall()
@router.post("/{tag}")
def add(tag:str,data:Stop,_=Depends(require("operator","reviewer"))):
    with db() as cx:
        return capture(cx,tag,data)
