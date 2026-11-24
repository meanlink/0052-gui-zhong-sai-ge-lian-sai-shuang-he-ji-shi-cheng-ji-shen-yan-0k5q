import {api} from './base.js'
import {fixedZone} from './case_labels.js'
export const finishes=()=>api('/api/finishes')
function normalize({primary_at,witness_at,...fields}){
 return {...fields,primary_at:fixedZone(primary_at),witness_at:fixedZone(witness_at)}
}
export const record=({meet,...data})=>api('/api/finishes/'+encodeURIComponent(meet),'POST',normalize(data))
export const correction=({meet,bird,...data})=>api('/api/finishes/'+encodeURIComponent(meet)+'/'+encodeURIComponent(bird)+'/correct','POST',normalize(data))
