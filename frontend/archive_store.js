import {api} from './base.js'
export const ledgers=()=>api('/api/standings')
export const archive=({meet,notes})=>api('/api/standings/'+encodeURIComponent(meet)+'/archive','POST',{notes})
