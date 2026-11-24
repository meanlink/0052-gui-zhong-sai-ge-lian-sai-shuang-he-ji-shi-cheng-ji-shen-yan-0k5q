import {api} from './base.js'
export const stops=()=>api('/api/handoffs')
export const note=({tag,clock_at,...data})=>api('/api/handoffs/'+encodeURIComponent(tag),'POST',{...data,clock_at:clock_at+':00+08:00'})
