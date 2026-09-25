// Validate data/summaries/<date>.json ids against data/raw/<date>.json
import fs from 'fs';

const date = process.argv[2];
if (!date) { console.error('usage: node tmp/validate.mjs YYYY-MM-DD'); process.exit(1); }

function normId(p) {
  if (p.source && p.source !== 'arxiv') return String(p.id);
  let a = String(p.id).split('/').pop();
  return a.replace(/v1/g, '').replace(/v2/g, '').replace(/v3/g, '').replace(/v4/g, '');
}

const raw = JSON.parse(fs.readFileSync(`data/raw/${date}.json`, 'utf8')).map(normId);
const sumPath = `data/summaries/${date}.json`;
if (!fs.existsSync(sumPath)) { console.log(`FAIL: ${sumPath} not found`); process.exit(2); }
const sum = JSON.parse(fs.readFileSync(sumPath, 'utf8'));

const rawSet = new Set(raw);
const sumIds = sum.map(e => e.id);
const sumSet = new Set(sumIds);
const missing = raw.filter(id => !sumSet.has(id));
const extra = sumIds.filter(id => !rawSet.has(id));
const dup = sumIds.filter((id, i) => sumIds.indexOf(id) !== i);

const badEntry = sum.filter(e => !e.id || !e.summary || typeof e.summary !== 'string' || e.summary.trim().length < 15)
  .map(e => e.id || '(no id)');
const longIds = sumIds.filter(id => !rawSet.has(id));

console.log(`date=${date} raw=${raw.length} summaries=${sum.length}`);
console.log(`missing=${missing.length} extra=${extra.length} dup=${dup.length} shortOrEmpty=${badEntry.length}`);
if (missing.length) console.log('MISSING: ' + missing.join(', '));
if (extra.length) console.log('EXTRA: ' + extra.join(', '));
if (dup.length) console.log('DUP: ' + dup.join(', '));
if (badEntry.length) console.log('BAD(short summary): ' + badEntry.join(', '));
const ok = !missing.length && !extra.length && !dup.length && !badEntry.length && sum.length === raw.length;
console.log(ok ? 'OK' : 'NOT OK');
process.exit(ok ? 0 : 1);
