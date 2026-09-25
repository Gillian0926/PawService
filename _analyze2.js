const fs = require('fs');
const path = require('path');

function normId(p) {
  let aid;
  if (p.source && p.source !== 'arxiv') aid = p.id;
  else { aid = p.id.split('/').pop(); aid = aid.replace(/v\d+$/, ''); }
  return aid;
}

// map id -> raw date
const id2date = {};
for (const f of fs.readdirSync('data/raw').filter(x=>x.endsWith('.json')).sort()) {
  const d = f.replace('.json','');
  for (const p of JSON.parse(fs.readFileSync(path.join('data/raw',f),'utf8'))) id2date[normId(p)] = d;
}

for (const f of fs.readdirSync('data/summaries').filter(x=>x.endsWith('.json')).sort()) {
  const arr = JSON.parse(fs.readFileSync(path.join('data/summaries',f),'utf8'));
  const byDate = {};
  let unknown=0;
  for (const e of arr) { const d = id2date[e.id]; if (d) byDate[d]=(byDate[d]||0)+1; else unknown++; }
  console.log(f, '=>', JSON.stringify(byDate), 'unknown:', unknown);
}
