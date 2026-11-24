import {h,empty} from './base.js'
import {heading,choices,feedback} from './view.js'
import {wire,canEdit} from './forms.js'
import {boxes} from './box_store.js'
import {stops,note} from './handoff_store.js'
import {boxLabel,local} from './case_labels.js'
export async function render(root,session) {
 const [registry,rows]=await Promise.all([boxes(),stops()])
 root.innerHTML=heading('赛台交接','按封条验收比赛台的主盒和独立核验盒。两盒均到赛台才可生成校点证据。')+`<div class="chain-layout"><section>
 ${registry.cases.map(c=>`<article><h2>${h(boxLabel(c))}</h2><ol>${rows.filter(r=>r.tag===c.tag).map(r=>`<li><time>${local.format(new Date(r.clock_at))}</time><strong>${h(r.location)}</strong><small>${h(r.witness)}</small></li>`).join('')||empty('尚无交接记录。')}</ol></article>`).join('')}</section>
 ${canEdit(session)?`<form class="panel compact-form"><h2>登记交接节点</h2><label>器材<select name="tag">${choices(registry.cases.filter(c=>['registered','misrouted'].includes(c.phase)),boxLabel,c=>c.tag)}</select></label>
 <label>地点<select name="location">${choices(registry.points,p=>p,p=>p)}</select></label><label>时间（北京时间）<input name="clock_at" type="datetime-local" required></label><label>封条<input name="seal" required></label><label>见证人<input name="witness" minlength="2" required></label><button>记入交接链</button>${feedback}</form>`:''}</div>`
 wire(root.querySelector('form'),note,()=>render(root,session))
}
