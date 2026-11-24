from datetime import datetime
from fastapi import HTTPException
from pydantic import BaseModel, Field, field_validator

from meet_records import invalidate

class Timestamps(BaseModel):
    primary_at: datetime
    witness_at: datetime

    @field_validator("primary_at", "witness_at")
    @classmethod
    def timezone_required(cls, value):
        if value.utcoffset() is None:
            raise ValueError("击钟记录需明确时区")
        return value

class Finish(Timestamps):
    group_code: str
    bird: str = Field(pattern=r"^[0-9]{4,8}$")
    remark: str = Field(min_length=4, max_length=150)

class Correction(Timestamps):
    reason: str = Field(min_length=6, max_length=150)

def reopen_group(cx, meet, group_code):
    """成绩簿签发后的证据变化只重开所属放飞组；其他组的榜照常可查。

    校点更正撤下的榜（withdrawn）保持 withdrawn，直到新校点审验通过。
    返回被重开的在榜成绩簿数量。
    """
    return cx.execute('''
        UPDATE score_books SET status='reviewing'
        WHERE meet=%s AND group_code=%s AND status='published'
    ''', (meet, group_code)).rowcount

def require_open_meet(cx, key):
    row = cx.execute("SELECT * FROM meets WHERE code=%s FOR UPDATE", (key,)).fetchone()
    if not row:
        raise HTTPException(404, "没有这个比赛场次")
    if row["status"] == "archived":
        raise HTTPException(409, "整场比赛已封存，不再接受击钟")
    return row

def ingest(cx, key, data):
    require_open_meet(cx, key)
    if not cx.execute(
        "SELECT 1 FROM release_groups WHERE meet=%s AND code=%s", (key, data.group_code)
    ).fetchone():
        raise HTTPException(409, "成绩必须属于本场已登记的放飞组")
    cx.execute('''
        INSERT INTO finish_clicks(meet,group_code,bird,primary_at,witness_at,remark)
        VALUES(%(meet)s,%(group_code)s,%(bird)s,%(primary_at)s,%(witness_at)s,%(remark)s)
    ''', data.model_dump() | {"meet": key})
    invalidate(cx, key)
    reopened = reopen_group(cx, key, data.group_code)
    return {"bird": data.bird, "revision": 1, "group_reopened": reopened}

def correct(cx, key, bird, data, actor):
    require_open_meet(cx, key)
    row = cx.execute(
        "SELECT * FROM finish_clicks WHERE meet=%s AND bird=%s FOR UPDATE", (key, bird)
    ).fetchone()
    if not row:
        raise HTTPException(404, "没有这条击钟记录")
    audit = cx.execute("SELECT results FROM clock_audits WHERE meet=%s", (key,)).fetchone()
    # 已发榜后的复录允许直接进行：只重开所属组，不再要求先重跑审验。
    if not audit or not any(r["bird"] == bird and r["flag"] for r in audit["results"]):
        if not cx.execute(
            "SELECT 1 FROM score_books WHERE meet=%s AND group_code=%s AND status<>'superseded'",
            (key, row["group_code"]),
        ).fetchone():
            raise HTTPException(409, "只有已审验且标记双盒异常的击钟可退回复录")
    rev = row["revision"] + 1
    cx.execute('''INSERT INTO finish_corrections(meet,bird,revision,prior_primary,prior_witness,reason,corrected_by)
        VALUES(%s,%s,%s,%s,%s,%s,%s)''',
        (key, bird, rev, row["primary_at"], row["witness_at"], data.reason, actor))
    cx.execute(
        "UPDATE finish_clicks SET primary_at=%s,witness_at=%s,revision=%s WHERE meet=%s AND bird=%s",
        (data.primary_at, data.witness_at, rev, key, bird))
    invalidate(cx, key)
    reopened = reopen_group(cx, key, row["group_code"])
    return {"bird": bird, "revision": rev, "group_reopened": reopened}
