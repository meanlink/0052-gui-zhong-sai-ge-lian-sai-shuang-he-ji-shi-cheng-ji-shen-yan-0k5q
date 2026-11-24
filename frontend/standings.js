import {h,badge,empty} from './base.js'
import {heading,feedback} from './view.js'
import {wire} from './forms.js'
import {ledgers,archive} from './archive_store.js'
import {ranking} from './ranking_table.js'
import {offsets} from './offset_strip.js'
export async function render(root,session){
 const data=await ledgers()
 root.innerHTML=heading('成绩归档','按所属放飞组计算相对用时；双盒异常、缺失新版审验会阻断归档。')+`
 <div class="score-mast">${data.meets.map(m=>{
 const score=data.ledgers.find(x=>x.meet===m.code)
 return `<article><header><h2>${h(m.title)}</h2>${badge(score?'已归档':'待归档',score?'approved':'')}</header>
 ${score?offsets(score.evidence)+Array.from(Map.groupBy(score.standings,r=>r.group),([key,rows])=>`
 <section><h3>${h(rows[0].club)} · ${h(key)}</h3>${ranking(rows)}</section>`).join('')+`<p class="score-note">${h(score.notes)} · ${h(score.approved_by)}</p>`:
 session.role==='reviewer'?`<form class="panel compact-form"><input type="hidden" name="meet" value="${h(m.code)}"><label>归档批注<input name="notes" minlength="6" required></label><button>签发分组成绩簿</button>${feedback}</form>`:empty('待复核员签发分组成绩。')}</article>`}).join('')}</div>`
 for(const form of root.querySelectorAll('form')) wire(form,archive,()=>render(root,session))
}
