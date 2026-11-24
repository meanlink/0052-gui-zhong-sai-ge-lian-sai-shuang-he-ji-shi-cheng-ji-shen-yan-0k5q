from fastapi import HTTPException

def active(cx, meet):
    row = cx.execute("SELECT * FROM meets WHERE code=%s FOR UPDATE", (meet,)).fetchone()
    if not row:
        raise HTTPException(404, "没有这个比赛场次")
    if row["status"] == "archived":
        raise HTTPException(409, "成绩已经归档，证据冻结")
    return row

def taxonomy(cx):
    meets = cx.execute("SELECT * FROM meets ORDER BY code").fetchall()
    return {"meets": meets,
            "groups": cx.execute("SELECT * FROM release_groups ORDER BY meet,code").fetchall()}

def invalidate(cx, meet):
    """击钟/复录变化后撤销本场审验；已发榜的组不受影响，仍可照常查榜。"""
    cx.execute("DELETE FROM clock_audits WHERE meet=%s", (meet,))

def bump_calibration_epoch(cx, meet):
    """共用校点更正：推进校点代次并立即撤下所有受影响组的当前榜。"""
    row = cx.execute(
        "UPDATE meets SET calibration_epoch=calibration_epoch+1 WHERE code=%s RETURNING calibration_epoch",
        (meet,),
    ).fetchone()
    if not row:
        raise HTTPException(404, "没有这个比赛场次")
    cx.execute('''
        UPDATE score_books SET status='withdrawn', superseded_at=now()
        WHERE meet=%s AND status IN ('published','reviewing')
    ''', (meet,))
    # 旧代次审验即刻失效；即使排队中的旧审验晚完成也无法恢复旧榜。
    cx.execute("DELETE FROM clock_audits WHERE meet=%s", (meet,))
    return row["calibration_epoch"]

def group_status(cx):
    """每个放飞组当前的成绩簿状态与版本。"""
    rows = cx.execute('''
        SELECT meet, group_code, version, status, calibration_epoch, approved_by, created_at, source_audit
        FROM score_books WHERE status <> 'superseded'
        ORDER BY meet, group_code
    ''').fetchall()
    return {(r["meet"], r["group_code"]): r for r in rows}
