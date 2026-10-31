import {lessonSummary} from './learning.mjs';
// Derive only facts already reached; this does not change saves or reveal later twists.
export function notebook(story){
 const n=story.view(),s=story.state,scene=Number(n.scene_id.slice(1));
 const facts=[{zh:'你刚到北京，想先找家店吃饭。',en:'You have just arrived in Beijing. Your first plan is to find dinner.'}];
 if(s.asked_directions)facts.push({zh:'你向路人阿姨问了面馆在哪里。',en:'You asked a passerby where to find the noodle shop.'});
 if(scene>=1)facts.push({zh:'你走进好运面馆，老板娘招呼你点餐。',en:'You entered Good Fortune Noodles. The owner invited you to order.'});
 if(s.item_selected&&(scene>=4||n.id==='served')){const item=story.data.menu.find(x=>x.id===s.item_selected);facts.push({zh:`你点了${item.zh}${s.wants_water?'和矿泉水':''}，一共${story.values().total}元。`,en:`Your order is ${item.en}${s.wants_water?' and water':''}, totaling ¥${story.values().total}.`});}
 if(s.first_reaction||['gu','gu_arrival'].includes(n.id))facts.push({zh:'一个陌生男人带着红色文件袋来到你桌旁。',en:'A stranger has approached your table with a red document envelope.'});
 if(s.inheritance_response||n.id==='billion')facts.push({zh:'他声称十亿元遗产属于你。这个说法还没有得到证实。',en:'He claims a billion-yuan inheritance belongs to you. His claim has not been verified.'});
 if(s.trust_alignment||n.id==='rival')facts.push({zh:'第二个男人出现，说前一个男人认错人了。',en:'A second man appeared and said the first had mistaken your identity.'});
 if(['name','silence','sms','end'].includes(n.id))facts.push({zh:'老板娘认出文件上的一个名字。她以为那个人已经死了。',en:'The owner recognized a name in the document. She believed that person was dead.'});
 if(['sms','end'].includes(n.id))facts.push({zh:'陌生短信叫你明天中午去文件上的地址，并警告你不要相信他们。',en:'An unknown sender told you to visit the address tomorrow at noon, and warned you not to trust them.'});
 const expressions=lessonSummary(story.learning).filter(r=>r.encountered||r.selected.length||n.learning_tags.includes(r.tag));
 return {facts,expressions};
}
