// A record of exposure and choices, never a claim of spoken proficiency.
export const expressions=[
 {tag:'在哪里',zh:'面馆在哪里？',py:'Miànguǎn zài nǎlǐ?',en:'Where is the noodle shop?',use:'问地点 · Ask where something is',pattern:'地点 + 在哪里？',tip:'换一个地点：洗手间在哪里？ · Where is the restroom?',match:t=>t.includes('在哪里')},
 {tag:'我要',zh:'我要这个。',py:'Wǒ yào zhège.',en:'I would like this.',use:'点餐或接受 · Order or accept',pattern:'我要 + 东西',tip:'我要水。 · I would like water. 这里的“要”可以表示想要。',match:t=>t.includes('我要')},
 {tag:'我不要',zh:'我不要辣。',py:'Wǒ bú yào là.',en:'No spice for me.',use:'表达不想要 · Say what you do not want',pattern:'我不要 + 东西',tip:'我不要这个。 · I do not want this. “不”在“要”前读 bú。',match:t=>t.includes('我不要')},
 {tag:'多少钱',zh:'这个多少钱？',py:'Zhège duōshao qián?',en:'How much is this?',use:'询价 · Ask the price',pattern:'东西 + 多少钱？',tip:'水多少钱？ · How much is the water? “一共”表示总计。',match:t=>t.includes('多少钱')},
 {tag:'我听不懂',zh:'我听不懂。',py:'Wǒ tīng bu dǒng.',en:'I do not understand.',use:'请求帮助 · Ask for help understanding',pattern:'我 + 听不懂',tip:'不是答错了。听不懂时可以直接说出来。 · Use it whenever you cannot follow.',match:t=>t.includes('听不懂')},
 {tag:'这个',zh:'这是什么？',py:'Zhè shì shénme?',en:'What is this?',use:'询问眼前的东西 · Ask about something nearby',pattern:'这 / 这个 + 是什么？',tip:'“这个”指眼前或近处的东西；“那个”指较远的东西。',match:t=>t.includes('这个')||t.startsWith('这是')},
 {tag:'那个',zh:'那个多少钱？',py:'Nàge duōshao qián?',en:'How much is that?',use:'指向较远的东西 · Point to something farther away',pattern:'那个 + 问题',tip:'这个 = this one；那个 = that one。',match:t=>t.includes('那个')},
 {tag:'你是谁',zh:'你是谁？',py:'Nǐ shì shéi?',en:'Who are you?',use:'询问身份 · Ask who someone is',pattern:'你 + 是 + 谁？',tip:'面对突然出现的陌生人很直接；普通自我介绍可以说“我叫……” 。',match:t=>t.includes('你是谁')},
 {tag:'我不认识',zh:'我不认识你。',py:'Wǒ bú rènshi nǐ.',en:'I do not know you.',use:'澄清关系 · Say you do not know someone',pattern:'我不认识 + 人',tip:'我不认识他。 · I do not know him. “也”表示 also / either。',match:t=>t.includes('不认识')}
];
export function lessonSummary(learning){return expressions.map(row=>({...row,encountered:(learning.phrase_exposure?.[row.tag]||0)>0,selected:Object.entries(learning.selected_expressions||{}).filter(([text])=>row.match(text)).map(([text,count])=>({text,count}))}));}
