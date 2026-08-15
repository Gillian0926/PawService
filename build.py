#!/usr/bin/env python3
"""Merge raw + summary data -> site/papers.json + data/summaries/*.md"""
import json
import glob
import os
from collections import OrderedDict

RAW_DIR = 'data/raw'
SUM_DIR = 'data/summaries'
SITE_DIR = 'docs'

TOPIC_ORDER = [
    '计算机/机器学习', '计算机/自然语言处理', '计算机/人工智能', '计算机/计算机视觉',
    '计算机/安全与隐私', '计算机/软件工程', '计算机/数据科学',
    '材料/材料科学', '材料/应用物理', '材料/介观与纳米',
]

CROSSOVER_ORDER = ['计算材料学', '计算建模', '材料器件', 'AI4Science', '量子信息', '机器学习材料']


def load_raw():
    papers = {}
    for f in sorted(glob.glob(os.path.join(RAW_DIR, '*.json'))):
        date = os.path.basename(f).replace('.json', '')
        for p in json.load(open(f, encoding='utf-8')):
            aid = p['id'].rsplit('/', 1)[-1]
            aid = aid.replace('v1', '').replace('v2', '').replace('v3', '').replace('v4', '')
            papers[aid] = {
                'id': aid, 'date': date, 'title': p['title'],
                'authors': p.get('authors', []),
                'link': 'https://arxiv.org/abs/' + aid,
                'category': p['category'], 'topic': p['topic'],
            }
    return papers


def load_summaries():
    s = {}
    for f in sorted(glob.glob(os.path.join(SUM_DIR, '*.json'))):
        for e in json.load(open(f, encoding='utf-8')):
            s[e['id']] = {'summary': e.get('summary', ''), 'crossover': e.get('crossover')}
    return s


def gen_markdown(date, papers):
    cross = [p for p in papers if p.get('crossover')]
    lines = [
        '# 文献速览 · ' + date, '',
        '> 抓取 %d 篇，爪爪分类 + 中文摘要 🦉' % len(papers),
        '> 分类体系见 [`CLASSIFICATION.md`](CLASSIFICATION.md)；原始数据：`data/raw/%s.json`' % date, '',
    ]
    if cross:
        lines += ['## 🔬 交叉学科精选（材料 × 计算机，%d 篇）' % len(cross), '',
                  '> 思岐研究生方向，优先看这里 👇', '']
        for ctag in CROSSOVER_ORDER:
            sub = [p for p in cross if p.get('crossover') == ctag]
            if not sub:
                continue
            lines += ['### ' + ctag, '']
            for p in sub:
                lines.append('- **%s** — %s。[arXiv:%s](%s)' % (p['title'], p['summary'], p['id'], p['link']))
            lines.append('')
        lines += ['---', '']

    by_topic = OrderedDict()
    for t in TOPIC_ORDER:
        by_topic[t] = [p for p in papers if p['topic'] == t]
    for t, sub in by_topic.items():
        if not sub:
            continue
        lines += ['## %s（%d 篇）' % (t, len(sub)), '']
        for p in sub:
            tag = ' `[交叉·%s]`' % p['crossover'] if p.get('crossover') else ''
            lines.append('- **%s**%s — %s。[arXiv:%s](%s)' % (p['title'], tag, p['summary'], p['id'], p['link']))
        lines.append('')

    out = os.path.join(SUM_DIR, date + '.md')
    open(out, 'w', encoding='utf-8').write('\n'.join(lines))
    print('generated ' + out + ' (%d papers)' % len(papers))


def main():
    papers = load_raw()
    sums = load_summaries()
    for aid, s in sums.items():
        if aid in papers:
            papers[aid]['summary'] = s['summary']
            papers[aid]['crossover'] = s['crossover']
        else:
            print('WARN: summary for unknown id ' + aid)

    os.makedirs(SITE_DIR, exist_ok=True)
    plist = sorted(papers.values(), key=lambda x: x['date'], reverse=True)
    json.dump(plist, open(os.path.join(SITE_DIR, 'papers.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print(SITE_DIR + '/papers.json: %d papers' % len(plist))

    by_date = {}
    for p in plist:
        by_date.setdefault(p['date'], []).append(p)
    for date in sorted(by_date, reverse=True):
        gen_markdown(date, by_date[date])


if __name__ == '__main__':
    main()
