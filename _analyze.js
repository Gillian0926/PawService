const fs = require('fs');
const path = require('path');

function normId(p) {
  let aid;
  if (p.source && p.source !== 'arxiv') aid = p.id;
  else {
    aid = p.id.split('/').pop();
    aid = aid.replace(/v\d+$/, '');
  }
  return aid;
}

const sumIds = new Set();
for (const f of fs.readdirSync('data/summaries').filter(x=>x.endsWith('.json'))) {
  const arr = JSON.parse(fs.readFileSync(path.join('data/summaries',f),'utf8'));
  for (const e of arr) sumIds.add(e.id);
}
console.log('total summary ids:', sumIds.size);

const rawFiles = fs.readdirSync('data/raw').filter(x=>x.endsWith('.json')).sort();
for (const f of rawFiles) {
  const arr = JSON.parse(fs.readFileSync(path.join('data/raw',f),'utf8'));
  let have=0, miss=0;
  const missIds=[];
  for (const p of arr) {
    const id = normId(p);
    if (sumIds.has(id)) have++; else { miss++; missIds.push(id); }
  }
  console.log(`${f}: total=${arr.length} summed=${have} missing=${miss}`);
}
