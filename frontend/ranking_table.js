import {table} from './view.js'
import {shortTime} from './finish_times.js'
export function ranking(group){
 return table(['位次','足环','校正后归巢','用时（秒）','双盒时差（ms）','修订'],group.map(r=>[
   r.rank,r.bird,shortTime(r.corrected_at),(r.elapsed_ms/1000).toFixed(3),r.disagreement_ms,'v'+r.revision
 ]))
}
