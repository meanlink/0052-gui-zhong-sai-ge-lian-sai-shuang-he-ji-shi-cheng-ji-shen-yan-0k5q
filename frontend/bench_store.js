import {api,waitJob} from './base.js'
import {fixedZone} from './case_labels.js'
export const bench=()=>api('/api/bench')
export const capture=({meet,reference_at,recorded_at,...fields})=>api('/api/bench/'+encodeURIComponent(meet)+'/anchor','POST',{
 ...fields,reference_at:fixedZone(reference_at),recorded_at:fixedZone(recorded_at)
})
export async function synchronize(meet){
 const {job_id}=await api('/api/bench/'+encodeURIComponent(meet)+'/audit','POST',{})
 return waitJob(job_id)
}
