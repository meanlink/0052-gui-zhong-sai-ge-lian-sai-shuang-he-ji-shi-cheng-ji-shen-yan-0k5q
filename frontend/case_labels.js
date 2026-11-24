export const phases={registered:'已登记'}
export const boxLabel=row=>row.tag+' / '+row.owner_club
export const local=new Intl.DateTimeFormat('zh-CN',{timeZone:'Asia/Shanghai',dateStyle:'short',timeStyle:'short'})
export const timestamp=new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Shanghai',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',second:'2-digit',fractionalSecondDigits:3,hourCycle:'h23'})
export function formTime(value) {
 const parts=Object.fromEntries(timestamp.formatToParts(new Date(value)).map(x=>[x.type,x.value]))
 return `${parts.year}-${parts.month}-${parts.day}T${parts.hour}:${parts.minute}:${parts.second}.${parts.fractionalSecond}`
}
export const fixedZone=value=>value+(/T[0-9]{2}:[0-9]{2}$/.test(value)?':00':'')+'+08:00'
