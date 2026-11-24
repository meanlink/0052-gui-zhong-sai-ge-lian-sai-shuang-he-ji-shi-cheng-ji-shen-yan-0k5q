from fastapi import HTTPException

def active(cx,meet):
    row=cx.execute("SELECT * FROM meets WHERE code=%s FOR UPDATE",(meet,)).fetchone()
    if not row:
        raise HTTPException(404,"没有这个比赛场次")
    if row["status"]=="archived":
        raise HTTPException(409,"成绩已经归档，证据冻结")
    return row

def taxonomy(cx):
    meets=cx.execute("SELECT * FROM meets ORDER BY code").fetchall()
    return {"meets":meets,"groups":cx.execute("SELECT * FROM release_groups ORDER BY meet,code").fetchall()}

def invalidate(cx,meet):
    cx.execute("DELETE FROM clock_audits WHERE meet=%s",(meet,))
