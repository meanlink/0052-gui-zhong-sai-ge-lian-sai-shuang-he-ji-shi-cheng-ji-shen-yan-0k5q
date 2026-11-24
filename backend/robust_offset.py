from statistics import median
from fastapi import HTTPException

def offset_for(box, observations):
    deltas=[round((row["recorded_at"]-row["reference_at"]).total_seconds()*1000,3)
            for row in observations]
    if len(deltas)<3:
        raise HTTPException(409,f"{box} 至少需要三个独立校点")
    middle=median(deltas)
    mad=median(abs(d-middle) for d in deltas)
    guard=max(100,3*1.4826*mad)
    reliable=[d for d in deltas if abs(d-middle)<=guard]
    if len(reliable)<3 or max(reliable)-min(reliable)>250:
        raise HTTPException(409,f"{box} 检点漂移过大，须重新校点")
    return {"offset_ms":median(reliable),"mad_ms":mad,"window_ms":round(guard,3),
         "kept":len(reliable),"rejected":len(deltas)-len(reliable)}
