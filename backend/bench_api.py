from fastapi import APIRouter, Depends, HTTPException
from core import db, require, enqueue
from calibration_input import Anchor, add_anchor
from meet_records import taxonomy, group_status
router=APIRouter(prefix="/bench")

@router.get("")
def bench(_=Depends(require())):
    with db() as cx:
        result = taxonomy(cx)
        result["anchors"] = cx.execute(
            "SELECT * FROM clock_anchors ORDER BY box,reference_at").fetchall()
        result["audits"] = cx.execute("SELECT * FROM clock_audits ORDER BY meet").fetchall()
        result["books"] = list(group_status(cx).values())
        return result

@router.post("/{meet}/anchor")
def anchor(meet:str,data:Anchor,_=Depends(require("operator","reviewer"))):
    with db() as cx:
        return add_anchor(cx,meet,data)

@router.post("/{meet}/audit")
def audit(meet: str, _=Depends(require("operator", "reviewer"))):
    with db() as cx:
        row = cx.execute("SELECT calibration_epoch FROM meets WHERE code=%s", (meet,)).fetchone()
        if not row:
            raise HTTPException(404, "没有这个比赛场次")
        return {"job_id": enqueue(cx, "twin-clock-audit",
                                  {"meet": meet, "calibration_epoch": row["calibration_epoch"]})}
