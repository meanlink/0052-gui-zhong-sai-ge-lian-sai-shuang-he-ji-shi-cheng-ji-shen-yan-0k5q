import {api} from './base.js'
export const boxes=()=>api('/api/boxes')
export const register=data=>api('/api/boxes','POST',data)
