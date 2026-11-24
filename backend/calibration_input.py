from datetime import datetime
from fastapi import HTTPException
from pydantic import BaseModel, Field, field_validator
from handoff_ledger import recent
from meet_records import active, bump_calibration_epoch
class Anchor(BaseModel):
    box: str
    reference_at: datetime
    recorded_at: datetime
    inspector: str = Field(min_length=3, max_length=50)

    @field_validator("reference_at", "recorded_at")
    @classmethod
    def timezone_required(cls, value):
        if value.utcoffset() is None:
            raise ValueError("校点时间需明确时区")
        return value

def add_anchor(cx, key, data):
    meet = active(cx, key)
    if data.box not in (meet["primary_box"], meet["witness_box"]):
        raise HTTPException(409, "校点仅适用本场两只独立计时盒")
    # A certificate is tied to the checked-in box and its physical timing desk.
    cx.execute("SELECT tag FROM timing_cases WHERE tag=%s FOR UPDATE", (data.box,))
    custody = recent(cx, data.box)
    if not custody or custody["location"] != meet["desk"] or custody["clock_at"] > data.reference_at:
        raise HTTPException(409, "计时盒尚未在本场赛台完成验封交接")
    if not meet["calibration_from"] <= data.reference_at <= meet["calibration_to"]:
        raise HTTPException(409, "校点读数超出赛前有效时窗")
    if abs((data.recorded_at - data.reference_at).total_seconds()) > 60:
        raise HTTPException(409, "偏移超出分钟表量程，请重读校点")
    cx.execute(
        "INSERT INTO clock_anchors VALUES(%s,%s,%s,%s,%s)",
        (key, data.box, data.reference_at, data.recorded_at, data.inspector),
    )
    # 赛前首次组装校点不构成更正；一旦已经形成审验快照（或已发榜），
    # 再动共用校点即产生新一代校点：立即撤下受影响组的榜，
    # 全部组按同一代次审验通过后才会一次性重新发榜。
    already_audited = cx.execute(
        "SELECT 1 FROM clock_audits WHERE meet=%s", (key,)).fetchone()
    published = cx.execute(
        "SELECT 1 FROM score_books WHERE meet=%s AND status<>'superseded' LIMIT 1",
        (key,)).fetchone()
    if already_audited or published:
        epoch = bump_calibration_epoch(cx, key)
    else:
        epoch = meet["calibration_epoch"]
    return {"box": data.box, "reference_at": data.reference_at, "calibration_epoch": epoch}
