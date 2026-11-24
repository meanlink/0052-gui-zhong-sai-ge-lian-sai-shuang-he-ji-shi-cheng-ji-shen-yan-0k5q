import {h,badge} from './base.js'
import {heading,choices,feedback} from './view.js'
import {wire,canEdit} from './forms.js'
import {boxes,register} from './box_store.js'
import {phases} from './case_labels.js'
export async function render(root,session){
 const {cases,points}=await boxes()
 const select=choices(points,k=>k,k=>k)
 root.innerHTML=heading('封条登记','每只计时盒的封条号对应实物交接。所属俱乐部和收件点均保留原始登记。')+`<div class="stamp-layout"><section>
 ${cases.map(c=>`<article class="seal-entry"><div><strong>${h(c.seal)}</strong><small>${h(c.serial)}</small></div><div><h2>${h(c.tag)} · ${h(c.owner_club)}</h2><p>${h(c.origin)} → ${h(c.target)}</p></div>${badge(phases[c.phase])}</article>`).join('')}</section>
 ${canEdit(session)?`<form class="panel compact-form"><h2>登记器材盒</h2><label>标签<input name="tag" pattern="BX-[0-9]{2,7}" placeholder="BX-35" required></label><label>机身号<input name="serial" pattern="HH-[0-9]{4,7}" required></label><label>封条号<input name="seal" pattern="ZC-[0-9]{5,9}" required></label>
 <label>所属俱乐部<input name="owner_club" required></label><label>始发点<select name="origin">${select}</select></label><label>目的点<select name="target">${select}</select></label><button>登记封条</button>${feedback}</form>`:''}</div>`
 wire(root.querySelector('form'),register,()=>render(root,session))
}
