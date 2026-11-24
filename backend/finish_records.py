from datetime import datetime
from fastapi import HTTPException
from pydantic import BaseModel,Field,field_validator
from meet_records import active,invalidate

class Timestamps(BaseModel):
    primary_at:datetime
    witness_at:datetime

    @field_validator("primary_at","witness_at")
    @classmethod
    def timezone_required(cls,value):
        if value.utcoffset() is None:
            raise ValueError("击钟记录需明确时区")
        return value

class Finish(Timestamps):
    group_code:str
    bird:str=Field(pattern=r"^[0-9]{4,8}$")
    remark:str=Field(min_length=4,max_length=150)

class Correction(Timestamps):
    reason:str=Field(min_length=6,max_length=150)

def ingest(cx,key,data):
    active(cx,key)
    if not cx.execute("SELECT 1 FROM release_groups WHERE meet=%s AND code=%s",(key,data.group_code)).fetchone():
        raise HTTPException(409,"成绩必须属于本场已登记的放飞组")
    cx.execute('''
        INSERT INTO finish_clicks(meet,group_code,bird,primary_at,witness_at,remark)
        VALUES(%(meet)s,%(group_code)s,%(bird)s,%(primary_at)s,%(witness_at)s,%(remark)s)
    ''',data.model_dump()|{"meet":key})
    invalidate(cx,key)
    return {"bird":data.bird,"revision":1}

def correct(cx,key,bird,data,actor):
    active(cx,key)
    audit=cx.execute("SELECT results FROM clock_audits WHERE meet=%s",(key,)).fetchone()
    if not audit or not any(row["bird"]==bird and row["flag"] for row in audit["results"]):
        raise HTTPException(409,"只有已审验且标记双盒异常的击钟可退回复录")
    row=cx.execute("SELECT * FROM finish_clicks WHERE meet=%s AND bird=%s",(key,bird)).fetchone()
    rev=row["revision"]+1
    cx.execute('''INSERT INTO finish_corrections(meet,bird,revision,prior_primary,prior_witness,reason,corrected_by)
        VALUES(%s,%s,%s,%s,%s,%s,%s)''',(key,bird,rev,row["primary_at"],row["witness_at"],data.reason,actor))
    cx.execute("UPDATE finish_clicks SET primary_at=%s,witness_at=%s,revision=%s WHERE meet=%s AND bird=%s",
               (data.primary_at,data.witness_at,rev,key,bird))
    invalidate(cx,key)
    return {"bird":bird,"revision":rev}
