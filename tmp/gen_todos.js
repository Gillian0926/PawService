const fs = require('fs');
const rawDir = 'data/raw', sumDir = 'data/summaries';
const raws = fs.readdirSync(rawDir).filter(f => f.endsWith('.json')).sort();
const summarized = new Set();
for (const f of fs.readdirSync(sumDir).filter(f => f.endsWith('.json'))) {
  try { for (const e of JSON.parse(fs.readFileSync(sumDir + '/' + f, 'utf8'))) summarized.add(e.id); } catch (e) {}
}
const idOf = p => p.id.split('/').pop().replace(/v[0-9]+$/, '');
const lastDate = {};
for (const f of raws) {
  const d = f.replace('.json', '');
  const j = JSON.parse(fs.readFileSync(rawDir + '/' + f, 'utf8'));
  for (const p of j) lastDate[idOf(p)] = d;
}
const byDate = {};
for (const f of raws) {
  const d = f.replace('.json', '');
  const j = JSON.parse(fs.readFileSync(rawDir + '/' + f, 'utf8'));
  for (const p of j) {
    const id = idOf(p);
    if (summarized.has(id)) continue;
    if (lastDate[id] !== d) continue;
    (byDate[d] = byDate[d] || []).push({ id, title: p.title, abstract: p.abstract, category: p.category, topic: p.topic });
  }
}
let tot = 0;
for (const d of Object.keys(byDate).sort()) { tot += byDate[d].length; console.log(d, byDate[d].length); }
console.log('total', tot);
fs.mkdirSync('tmp', { recursive: true });
for (const d of Object.keys(byDate).sort()) fs.writeFileSync('tmp/todo-' + d + '.json', JSON.stringify(byDate[d], null, 1));
console.log('todos written');
