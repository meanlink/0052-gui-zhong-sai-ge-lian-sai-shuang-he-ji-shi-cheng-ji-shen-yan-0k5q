import {mount} from './base.js'
import {render as seals} from './seals.js'
import {render as handoffs} from './handoffs.js'
import {render as bench} from './bench.js'
import {render as finishes} from './finishes.js'
import {render as standings} from './standings.js'

const pages = {
  seals: '封条登记',
  handoffs: '赛台交接',
  bench: '双盒校点',
  finishes: '归巢击钟',
  standings: '成绩归档'
}
const renderers = {seals, handoffs, bench, finishes, standings}
mount({title: '归钟 · 赛鸽联赛双盒计时成绩审验', kicker: '禾湾计时联盟 · 赛绩审验簿', pages, render: (key, root, session) => renderers[key](root, session)})
