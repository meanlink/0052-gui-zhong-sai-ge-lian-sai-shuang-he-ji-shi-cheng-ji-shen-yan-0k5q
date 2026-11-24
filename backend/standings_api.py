from fastapi import APIRouter,Depends
from core import db,require
from pydantic import BaseModel,Field
from meet_records import taxonomy
from score_archive import archive
router=APIRouter(prefix="/standings")

class Review(BaseModel):
    notes:str=Field(min_length=6,max_length=180)

@router.get("")
def results(_=Depends(require())):
    with db() as cx:
        info=taxonomy(cx)
        info["ledgers"]=cx.execute("SELECT * FROM score_ledgers ORDER BY meet").fetchall()
        return info

@router.post("/{meet}/archive")
def close(meet:str,data:Review,user=Depends(require("reviewer"))):
    with db() as cx:
        return archive(cx,meet,data.notes,user["email"])
