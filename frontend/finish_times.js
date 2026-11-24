import {formTime} from './case_labels.js'
export function clocks(row={}){
 const field=(key,label)=>`<label>${label}<input name="${key}" value="${row[key]?formTime(row[key]):''}" type="datetime-local" required step=".001"></label>`
 return field('primary_at','主盒击钟（北京时间）')+field('witness_at','见证盒击钟（北京时间）')
}
export const shortTime=value=>formTime(value).split('T')[1]
