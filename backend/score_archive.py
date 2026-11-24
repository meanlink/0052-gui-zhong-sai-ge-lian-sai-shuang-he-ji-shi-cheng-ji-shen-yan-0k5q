"""组级成绩簿签发、撤榜与历史版本。

规则（对应业务约定）：
- 迟到击钟/复录只把所属组的当前榜置为 reviewing，其他组的榜照常可查、
  重新签发时保持不动，不产生新版本。
- 共用校点更正会把所有组的当前榜置为 withdrawn；只有全部受影响组
  基于同一代校点审验通过后，才在同一次操作中一次性切换到新榜。
- 同一次审验对同一组的重复签发不产生新版本（按 source_audit 幂等）：
  复核中的簿直接恢复为在榜，在榜中的簿原样保留。
- 更正前排队的旧审验即使晚完成也因代次不符而失败，旧榜不会恢复。
"""
from fastapi import HTTPException
from psycopg.types.json import Jsonb

from meet_records import active

ACTIVE_STATES = ("reviewing", "withdrawn")

def order_results(rows):
    result = []
    counters = {}
    keys = sorted({r["group"] for r in rows})
    for key in keys:
        order = sorted((r for r in rows if r["group"] == key),
                       key=lambda r: (r["elapsed_ms"], r["bird"]))
        last = None
        for position, row in enumerate(order, 1):
            if last != row["elapsed_ms"]:
                counters[key] = position
            result.append(row | {"rank": counters[key]})
            last = row["elapsed_ms"]
    return result

def _next_version(cx, meet, group):
    return (cx.execute(
        "SELECT max(version) AS v FROM score_books WHERE meet=%s AND group_code=%s",
        (meet, group)).fetchone()["v"] or 0) + 1

def _insert_book(cx, meet, group, version, epoch, rows, audit, notes, actor):
    cx.execute('''
        INSERT INTO score_books(meet,group_code,version,calibration_epoch,status,
            standings,evidence,source_audit,notes,approved_by)
        VALUES(%s,%s,%s,%s,'published',%s,%s,%s,%s,%s)
    ''', (meet, group, version, epoch, Jsonb(rows), Jsonb(audit["offsets"]),
          audit["analyzed_at"], notes, actor))

def publish(cx, key, notes, actor):
    meet = active(cx, key)
    audit = cx.execute(
        "SELECT * FROM clock_audits WHERE meet=%s FOR UPDATE", (key,)).fetchone()
    if not audit:
        raise HTTPException(409, "请先运行双盒审验，审验通过后才能签发成绩簿")
    if audit["calibration_epoch"] != meet["calibration_epoch"]:
        raise HTTPException(409, "校点已有更正，旧审验已失效，请按新校点重新审验后再签发")
    if audit["blocked"]:
        raise HTTPException(409, "仍有击钟未通过双盒审验，不能签发任何组的成绩簿")

    groups = [r["code"] for r in cx.execute(
        "SELECT code FROM release_groups WHERE meet=%s ORDER BY code", (key,)).fetchall()]
    scored = order_results(audit["results"])
    by_group = {g: [row for row in scored if row["group"] == g] for g in groups}

    current = {r["group_code"]: r for r in cx.execute('''
        SELECT * FROM score_books WHERE meet=%s AND status<>'superseded' FOR UPDATE
    ''', (key,)).fetchall()}

    # 校点更正撤下的组必须全部基于同一代审验一次性回榜；
    # 审验代次与当前代次一致（上面已校验），本次操作覆盖全场各组，结构上保证同批切换。
    withdrawn = [g for g, b in current.items() if b["status"] == "withdrawn"]

    new_versions, reopened, unchanged = [], [], []
    for g in groups:
        book = current.get(g)
        rows = by_group[g]
        if book is None:
            _insert_book(cx, key, g, _next_version(cx, key, g), meet["calibration_epoch"],
                         rows, audit, notes, actor)
            new_versions.append(g)
            continue

        if book["source_audit"] == audit["analyzed_at"]:
            # 同一次审验：重试签发不新增成绩簿。复核中的簿恢复在榜，在榜中的保持原样。
            if book["status"] in ACTIVE_STATES:
                cx.execute("UPDATE score_books SET status='published' WHERE id=%s", (book["id"],))
                reopened.append(g)
            else:
                unchanged.append(g)
            continue

        if book["status"] == "published":
            # 该组证据未变化（变化只发生在别的放飞组）：旧榜照常可查，保持不动。
            unchanged.append(g)
            continue

        # reviewing（迟到击钟/复录）或 withdrawn（校点更正）：旧当前簿归入历史，
        # 按本次审验出新版并一次性切换为在榜。
        cx.execute(
            "UPDATE score_books SET status='superseded', superseded_at=now() WHERE id=%s",
            (book["id"],))
        _insert_book(cx, key, g, _next_version(cx, key, g), meet["calibration_epoch"],
                     rows, audit, notes, actor)
        new_versions.append(g)

    leftover = cx.execute('''
        SELECT group_code FROM score_books
        WHERE meet=%s AND status IN ('reviewing','withdrawn')
    ''', (key,)).fetchall()
    if leftover:
        raise HTTPException(409, "仍有小组停留在复核/撤榜状态，本次切换未生效")

    return {"meet": key, "calibration_epoch": meet["calibration_epoch"],
            "withdrawn_recovered": withdrawn, "new_versions": new_versions,
            "reopened": reopened, "unchanged": unchanged, "state": "published"}

def history(cx, key):
    meet = cx.execute("SELECT * FROM meets WHERE code=%s", (key,)).fetchone()
    if not meet:
        raise HTTPException(404, "没有这个比赛场次")
    books = cx.execute('''
        SELECT id,meet,group_code,version,calibration_epoch,status,standings,evidence,
               source_audit,notes,approved_by,created_at,superseded_at
        FROM score_books WHERE meet=%s ORDER BY group_code,version
    ''', (key,)).fetchall()
    return {"meet": meet, "books": books}
