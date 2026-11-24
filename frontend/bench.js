import {h,badge,empty} from './base.js'
import {heading,choices,feedback,table} from './view.js'
import {wire,canEdit} from './forms.js'
import {bench,capture,synchronize} from './bench_store.js'
import {formTime,local} from './case_labels.js'
import {offsets} from './offset_strip.js'
export async function render(root,session){
 const state=await bench()
 root.innerHTML=heading('双盒校点','先核对赛台有效时窗，再对两只盒子分别估计时差。每盒至少三个有效校点。')+`<div class="bench-layout"><section>
 ${state.meets.map(m=>{const audit=state.audits.find(a=>a.meet===m.code)
 return `<article class="panel"><h2>${h(m.title)} · ${h(m.desk)}</h2><p>${local.format(new Date(m.calibration_from))} → ${local.format(new Date(m.calibration_to))}</p>
 ${audit?offsets(audit.offsets)+badge(audit.blocked+' 条待复录',audit.blocked?'held':'ready'):empty('尚无有效双盒审验。')}
 ${table(['计时盒','标准时点','盒内读数','校点员'],state.anchors.filter(a=>a.meet===m.code).map(a=>[a.box,formTime(a.reference_at).split('T')[1],formTime(a.recorded_at).split('T')[1],a.inspector]))}
 ${canEdit(session)&&m.status==='open'?`<form data-audit><input type="hidden" name="meet" value="${h(m.code)}"><button>审验双盒并复核击钟</button>${feedback}</form>`:''}</article>`}).join('')}</section>
 ${canEdit(session)?`<aside>${state.meets.filter(m=>m.status==='open').map(m=>`<form class="panel compact-form" data-anchor><h2>登记录点 · ${h(m.code)}</h2><input type="hidden" name="meet" value="${h(m.code)}">
 <label>计时盒<select name="box">${choices([m.primary_box,m.witness_box],x=>x,x=>x)}</select></label>
 <label>标准时点（北京时间）<input name="reference_at" type="datetime-local" required step=".001"></label>
 <label>盒内读数（北京时间）<input name="recorded_at" type="datetime-local" required step=".001"></label>
 <label>校点员<input name="inspector" required minlength="3"></label><button>保存校点</button>${feedback}</form>`).join('')}</aside>`:''}</div>`
 for(const form of root.querySelectorAll('[data-anchor]'))wire(form,capture,()=>render(root,session))
 for(const form of root.querySelectorAll('[data-audit]'))wire(form,data=>synchronize(data.meet),()=>render(root,session))
}
