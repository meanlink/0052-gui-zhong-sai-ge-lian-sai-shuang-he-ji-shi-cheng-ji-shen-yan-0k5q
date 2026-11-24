from fastapi import APIRouter,Depends
from core import db,require,enqueue
from calibration_input import Anchor,add_anchor
from meet_records import taxonomy
router=APIRouter(prefix="/bench")

@router.get("")
def bench(_=Depends(require())):
    with db() as cx:
        result=taxonomy(cx)
        result["anchors"]=cx.execute("SELECT * FROM clock_anchors ORDER BY box,reference_at").fetchall()
        result["audits"]=cx.execute("SELECT * FROM clock_audits ORDER BY meet").fetchall()
        return result

@router.post("/{meet}/anchor")
def anchor(meet:str,data:Anchor,_=Depends(require("operator","reviewer"))):
    with db() as cx:
        return add_anchor(cx,meet,data)

@router.post("/{meet}/audit")
def audit(meet:str,_=Depends(require("operator","reviewer"))):
    with db() as cx:
        return {"job_id":enqueue(cx,"twin-clock-audit",{"meet":meet})}
