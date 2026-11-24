import {h,badge,empty} from './base.js'
import {heading,feedback,stateBadge} from './view.js'
import {wire} from './forms.js'
import {ledgers,history,publish} from './archive_store.js'
import {ranking} from './ranking_table.js'
import {offsets} from './offset_strip.js'
import {local} from './case_labels.js'

const chip = state => stateBadge(state)

function groupCard(meet, group, book, session) {
  const club = h(group.club)
  if (!book) {
    return `<article class="panel score-group"><header><h2>${club} · ${h(group.code)}</h2>
      ${badge('待签发','pending')}</header>${empty('该组尚未签发成绩簿。')}</article>`
  }
  const body = book.status === 'withdrawn'
    ? `<p class="empty-state">共用校点已更正，旧榜撤下；全部组按同一版校点审验通过后统一切换新榜。</p>`
    : offsets(book.evidence) + ranking(book.standings)
  return `<article class="panel score-group" data-state="${h(book.status)}"><header>
    <h2>${club} · ${h(group.code)}</h2>
    <div class="group-chips">${chip(book.status)}${badge('v' + book.version + ' · 第' + book.calibration_epoch + '代校点','')}</div></header>
    ${body}
    <p class="score-note">${h(book.notes)} · ${h(book.approved_by)} · ${local.format(new Date(book.created_at))}</p>
    <details data-history data-meet="${h(meet)}" data-group="${h(group.code)}">
      <summary>回查历次签发（含原校点证据）</summary><div class="history-slot">加载中…</div></details>
  </article>`
}

export async function render(root, session) {
  const data = await ledgers()
  root.innerHTML = heading('成绩归档', '迟到击钟只重开所属放飞组，其他组照常查榜；共用校点更正后各组立即撤榜，按同一版校点审验通过才统一切换新榜。') + `
  <div class="score-mast">${data.meets.map(m => {
    const groups = data.groups.filter(g => g.meet === m.code)
    const books = new Map(data.books.filter(b => b.meet === m.code).map(b => [b.group_code, b]))
    const audit = data.audit_epochs.find(a => a.meet === m.code)
    const epoch = data.current_epoch.find(e => e.code === m.code)?.calibration_epoch
    const reviewing = [...books.values()].filter(b => b.status !== 'published').length
    return `<section class="meet-block"><div class="meet-head"><h1>${h(m.title)}（${h(m.code)}）</h1>
      <div class="group-chips">${badge('校点第 ' + epoch + ' 代','')}
      ${audit ? badge('审验 blocked=' + audit.blocked, audit.blocked ? 'held' : 'ready') : badge('尚无审验','pending')}
      ${reviewing ? badge(reviewing + ' 个组复核中','held') : badge('各组在榜','ready')}</div></div>
      <div class="group-grid">${groups.map(g => groupCard(m.code, g, books.get(g.code), session)).join('')}</div>
      ${session.role === 'reviewer' && m.status === 'open' ? `
      <form class="panel compact-form publish-form"><input type="hidden" name="meet" value="${h(m.code)}">
        <label>签发批注（同次审验重复提交不新增成绩簿）<input name="notes" minlength="6" maxlength="180" required></label>
        <button>按当前审验签发/切换分组成绩簿</button>${feedback}</form>` : ''}</section>`
  }).join('')}</div>`

  for (const form of root.querySelectorAll('.publish-form')) {
    wire(form, publish, () => render(root, session))
  }
  for (const details of root.querySelectorAll('[data-history]')) {
    details.addEventListener('toggle', async () => {
      if (!details.open || details.dataset.loaded) return
      const slot = details.querySelector('.history-slot')
      try {
        const payload = await history(details.dataset.meet)
        const rows = payload.books.filter(b => b.group_code === details.dataset.group)
        slot.innerHTML = rows.length ? rows.map(b => `
          <div class="history-item" data-state="${h(b.status)}">
            <div><strong>v${h(b.version)}</strong> ${chip(b.status)}
              <small>第 ${h(b.calibration_epoch)} 代校点 · ${local.format(new Date(b.created_at))}${b.superseded_at ? ' · 替代于 ' + local.format(new Date(b.superseded_at)) : ''}</small></div>
            ${b.status === 'superseded' || b.status === 'withdrawn' ? offsets(b.evidence) + ranking(b.standings) : '<p class="score-note">当前在榜版本见上方。</p>'}
            <p class="score-note">${h(b.notes)} · ${h(b.approved_by)}</p>
          </div>`).join('') : empty('暂无历史签发。')
        details.dataset.loaded = '1'
      } catch (error) {
        slot.textContent = error.message
      }
    })
  }
}
