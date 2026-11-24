from fastapi import APIRouter, Depends
from core import db, require
from meet_records import taxonomy, group_status
from finish_records import Finish, Correction, ingest, correct
router = APIRouter(prefix="/finishes")

@router.get("")
def clicks(_=Depends(require())):
    with db() as cx:
        info = taxonomy(cx)
        info["clicks"] = cx.execute(
            "SELECT * FROM finish_clicks ORDER BY meet,group_code,bird").fetchall()
        info["corrections"] = cx.execute(
            "SELECT * FROM finish_corrections ORDER BY meet,bird,revision").fetchall()
        info["audits"] = cx.execute(
            "SELECT meet,results,calibration_epoch FROM clock_audits ORDER BY meet").fetchall()
        info["books"] = list(group_status(cx).values())
        return info

@router.post("/{meet}")
def record(meet: str, data: Finish, _=Depends(require("operator", "reviewer"))):
    with db() as cx:
        return ingest(cx, meet, data)

@router.post("/{meet}/{bird}/correct")
def redo(meet: str, bird: str, data: Correction, user=Depends(require("reviewer"))):
    with db() as cx:
        return correct(cx, meet, bird, data, user["email"])
