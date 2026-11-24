from fastapi import APIRouter,Depends
from box_registry import Box,register,POINTS
from core import db,require
router=APIRouter(prefix="/boxes")
@router.get("")
def boxes(_=Depends(require())):
    with db() as cx:
        return {"points":POINTS,"cases":cx.execute("SELECT * FROM timing_cases ORDER BY tag").fetchall()}
@router.post("")
def add(data:Box,_=Depends(require("operator","reviewer"))):
    with db() as cx:
        return register(cx,data)
