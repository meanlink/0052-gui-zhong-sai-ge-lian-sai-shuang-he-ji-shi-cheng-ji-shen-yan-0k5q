from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from core import db, require
from meet_records import taxonomy
from score_archive import publish, history

router = APIRouter(prefix="/standings")

class Review(BaseModel):
    notes: str = Field(min_length=6, max_length=180)

@router.get("")
def results(_=Depends(require())):
    with db() as cx:
        info = taxonomy(cx)
        info["books"] = cx.execute('''
            SELECT id,meet,group_code,version,calibration_epoch,status,standings,evidence,
                   source_audit,notes,approved_by,created_at,superseded_at
            FROM score_books WHERE status<>'superseded'
            ORDER BY meet,group_code
        ''').fetchall()
        info["audit_epochs"] = cx.execute(
            "SELECT meet,calibration_epoch,blocked,analyzed_at FROM clock_audits ORDER BY meet"
        ).fetchall()
        info["current_epoch"] = cx.execute(
            "SELECT code,calibration_epoch FROM meets ORDER BY code").fetchall()
        return info

@router.post("/{meet}/publish")
def close(meet: str, data: Review, user=Depends(require("reviewer"))):
    with db() as cx:
        return publish(cx, meet, data.notes, user["email"])

@router.get("/{meet}/history")
def ledger(meet: str, _=Depends(require())):
    with db() as cx:
        return history(cx, meet)
