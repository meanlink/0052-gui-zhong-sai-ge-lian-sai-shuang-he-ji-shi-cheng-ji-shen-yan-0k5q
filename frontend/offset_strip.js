import {h} from './base.js'
export function offsets(data){
 return `<dl class="offset-strip">${Object.entries(data).map(([key,row])=>`<div><dt>${h(key)}</dt>
 <dd><strong>${row.offset_ms>0?'+':''}${row.offset_ms}</strong> ms</dd>
 <dd>MAD ${row.mad_ms} ms · ${row.kept} 有效 · ${row.rejected} 排除</dd></div>`).join('')}</dl>`
}
