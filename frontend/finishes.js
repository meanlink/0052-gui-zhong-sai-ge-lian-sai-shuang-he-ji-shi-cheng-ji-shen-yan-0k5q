import {h,badge,empty} from './base.js'
import {heading,choices,feedback,table,stateBadge} from './view.js'
import {wire,canEdit} from './forms.js'
import {finishes,record,correction} from './finish_store.js'
import {clocks,shortTime} from './finish_times.js'
export async function render(root,session){
 const state=await finishes()
 const bookOf=(meet,code)=>state.books.find(b=>b.meet===meet&&b.group_code===code)
 root.innerHTML=heading('归巢击钟','每条成绩归入一个放飞组，同时保留主盒与见证盒原值和复录原因。成绩簿签发后的迟到击钟只重开所属组，其他组照常查榜。')+`
 <div class="return-clicks"><section>${state.groups.map(g=>{
 const audit=state.audits.find(a=>a.meet===g.meet)
 const book=bookOf(g.meet,g.code)
 return `<article class="panel" data-book="${h(book?.status||'none')}"><h2>${h(g.club)} · ${h(g.code)}</h2>
 <p>放飞 ${shortTime(g.released_at)} ${book?stateBadge(book.status)+`<small class="book-version"> v${h(book.version)} · 第${h(book.calibration_epoch)}代校点</small>`:badge('待签发','pending')}</p>
 ${state.clicks.filter(x=>x.meet===g.meet&&x.group_code===g.code).map(row=>{
 const flag=audit?.results.find(r=>r.bird===row.bird)
 return `<div class="click-line"><div><strong>${h(row.bird)}</strong><small> v${row.revision}</small></div>
 <span>${shortTime(row.primary_at)} / ${shortTime(row.witness_at)}</span>${badge(flag?.flag|| (flag?'一致':'待审验'),flag?.flag?'held':'')}
 ${flag?.flag&&session.role==='reviewer'?`<details><summary>退回复录</summary><form data-fix class="compact-form"><input type="hidden" name="meet" value="${h(row.meet)}"><input type="hidden" name="bird" value="${h(row.bird)}">${clocks(row)}<label>复录原因<input name="reason" required minlength="6"></label><button>保存复录并重开本组成绩簿</button>${feedback}</form></details>`:''}</div>`}).join('')}</article>`}).join('')}
 <h2>复录簿</h2>${table(['足环','修订','旧主盒','旧见证盒','缘由'],state.corrections.map(x=>[x.bird,x.revision,shortTime(x.prior_primary),shortTime(x.prior_witness),x.reason]))}</section>
 ${canEdit(session)?`<aside>${state.meets.filter(m=>m.status==='open').map(m=>`<form data-record class="panel compact-form"><h2>新击钟 · ${h(m.code)}</h2>
 <input type="hidden" name="meet" value="${h(m.code)}"><label>归属放飞组<select name="group_code">${choices(state.groups.filter(g=>g.meet===m.code),g=>g.club,g=>g.code)}</select></label><label>足环号<input name="bird" pattern="[0-9]{4,8}" required></label>
 ${clocks()}<label>来源<input name="remark" required minlength="4"></label><button>录入双盒击钟</button>${feedback}</form>`).join('')}</aside>`:''}</div>`
 for(const form of root.querySelectorAll('[data-record]')) wire(form,record,()=>render(root,session))
 for(const form of root.querySelectorAll('[data-fix]')) wire(form,correction,()=>render(root,session))
}
