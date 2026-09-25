const fs = require('fs');
const path = require('path');
function normId(p){let aid;if(p.source&&p.source!=='arxiv')aid=p.id;else{aid=p.id.split('/').pop();aid=aid.replace(/v\d+$/,'');}return aid;}
const id2date={};
for (const f of fs.readdirSync('data/raw').filter(x=>x.endsWith('.json')).sort()){const d=f.replace('.json','');for(const p of JSON.parse(fs.readFileSync(path.join('data/raw',f),'utf8')))id2date[normId(p)]=d;}
const arr=JSON.parse(fs.readFileSync('data/summaries/2026-09-01.json','utf8'));
const unk=arr.filter(e=>!id2date[e.id]);
console.log('unknown count',unk.length);
console.log(unk.slice(0,10).map(e=>e.id).join('\n'));
