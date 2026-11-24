import {api} from './base.js'
export const ledgers = () => api('/api/standings')
export const history = meet => api('/api/standings/' + encodeURIComponent(meet) + '/history')
export async function publish({meet, notes}) {
  const result = await api('/api/standings/' + encodeURIComponent(meet) + '/publish', 'POST', {notes})
  const parts = []
  if (result.new_versions?.length) parts.push('新版成绩簿：' + result.new_versions.join('、'))
  if (result.reopened?.length) parts.push('恢复在榜：' + result.reopened.join('、'))
  if (result.unchanged?.length) parts.push('保持在榜：' + result.unchanged.join('、'))
  return {...result, message: parts.length ? parts.join('；') : '本次签发未产生变化'}
}
