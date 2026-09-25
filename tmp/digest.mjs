// Compact digest of a raw arXiv batch -> tmp/digest_<date>.txt
// Mimics build.py id normalization so summary ids always match.
import fs from 'fs';
import path from 'path';

const file = process.argv[2];
if (!file) { console.error('usage: node tmp/digest.mjs data/raw/YYYY-MM-DD.json'); process.exit(1); }
const date = path.basename(file).replace('.json', '');
const arr = JSON.parse(fs.readFileSync(file, 'utf8'));

function normId(p) {
  if (p.source && p.source !== 'arxiv') return String(p.id);
  let a = String(p.id).split('/').pop();
  return a.replace(/v1/g, '').replace(/v2/g, '').replace(/v3/g, '').replace(/v4/g, '');
}

const out = [];
out.push(`# DIGEST ${date}  total=${arr.length}`);
out.push('');
arr.forEach((p, i) => {
  const abs = (p.abstract || '').replace(/\s+/g, ' ').trim();
  out.push(`## [${i + 1}] id=${normId(p)} | topic=${p.topic || ''} | cat=${p.category || ''} | src=${p.source || 'arxiv'}`);
  out.push(`T: ${(p.title || '').replace(/\s+/g, ' ').trim()}`);
  out.push(`A: ${abs.slice(0, 1100)}`);
  out.push('');
});
const outp = path.join('tmp', `digest_${date}.txt`);
fs.writeFileSync(outp, out.join('\n'));
console.log(`wrote ${outp} (${arr.length} papers, ${out.join('\n').length} chars)`);
