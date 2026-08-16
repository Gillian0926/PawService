#!/usr/bin/env python3
"""Fetch top-conference paper lists (DBLP) + venue submissions (OpenReview).

Modes:
  --mode confs        DBLP 顶会完整列表 -> data/conferences/<VENUE>-<YEAR>.json
  --mode openreview   OpenReview 最新投稿 -> data/raw/conferences-YYYY-MM-DD.json
  --mode all          both (default)

Run:  python3 fetch_conferences.py [--mode all|confs|openreview] [--years 2026 2025]
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.request
import urllib.parse
from datetime import datetime, timezone, timedelta
from http.cookiejar import CookieJar

BASE = os.path.dirname(os.path.abspath(__file__))
CONF_DIR = os.path.join(BASE, 'data', 'conferences')
RAW_DIR = os.path.join(BASE, 'data', 'raw')
UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/126.0 Safari/537.36')

# DBLP venue 名称 -> (年份, topic 标签)。topic 需与 build.py 的 TOPIC_ORDER 对应。
CONFERENCES = [
    # 计算机视觉（ECCV 为偶数年举办，无 2025）
    ('CVPR', '计算机/计算机视觉'),
    ('ICCV', '计算机/计算机视觉'),
    ('ECCV', '计算机/计算机视觉'),
    # 机器学习 / AI
    ('NeurIPS', '计算机/机器学习'),
    ('ICML', '计算机/机器学习'),
    ('ICLR', '计算机/机器学习'),
    ('AAAI', '计算机/人工智能'),
    # NLP
    ('ACL', '计算机/自然语言处理'),
    ('EMNLP', '计算机/自然语言处理'),
    ('NAACL', '计算机/自然语言处理'),
    # 数据 / 数据库
    ('SIGMOD', '计算机/数据科学'),
    ('PVLDB', '计算机/数据科学'),   # VLDB 的论文以 PVLDB 期刊形式收录
    ('KDD', '计算机/数据科学'),
    # 系统 / 软件
    ('SIGCOMM', '计算机/软件工程'),
    ('SOSP', '计算机/软件工程'),
    ('OSDI', '计算机/软件工程'),
]

# OpenReview 投稿 invitation（ICLR/NeurIPS/ICML 的 Submission 邀请）
OPENREVIEW_INVITATIONS = [
    'ICLR.cc/2026/Conference/-/Submission',
    'NeurIPS.cc/2026/Conference/-/Submission',
    'ICML.cc/2026/Conference/-/Submission',
]
OPENREVIEW_TOPIC = '计算机/机器学习'
OPENREVIEW_DAYS = 2  # 只保留最近 N 天的新投稿


def http_get(url, headers=None, timeout=30, opener=None):
    req = urllib.request.Request(url, headers={
        'User-Agent': UA,
        'Accept': 'application/json,text/html,*/*',
        **(headers or {}),
    })
    with (opener or urllib.request.build_opener()).open(req, timeout=timeout) as r:
        return r.read().decode('utf-8', 'replace')


# ---------- DBLP ----------

def fetch_dblp_venue(venue, year):
    """抓一个会议一年的完整论文列表，返回论文 dict 列表（按 DBLP key 去重）。
    带失败重试（指数退避），间隔放慢以避免 DBLP 限流（500）。"""
    out, seen = [], set()
    f = 0
    h = 1000
    while True:
        q = urllib.parse.quote(f'venue:{venue} year:{year}')
        url = f'https://dblp.org/search/publ/api?q={q}&format=json&h={h}&f={f}'
        data = None
        for attempt in range(4):
            try:
                data = json.loads(http_get(url))
                break
            except Exception as ex:
                print(f'  [dblp] {venue} {year} page f={f} try{attempt + 1}: {ex}', file=sys.stderr)
                time.sleep(8 + 8 * attempt)  # 8s / 16s / 24s 退避，等限流恢复
        if data is None:
            print(f'  [dblp] {venue} {year}: giving up after retries', file=sys.stderr)
            break
        hits = (data.get('result') or {}).get('hits') or {}
        total = int(hits.get('@total') or 0)
        sent = int(hits.get('@sent') or 0)
        for hit in hits.get('hit') or []:
            info = hit.get('info') or {}
            key = info.get('key') or ''
            if not key or key in seen:
                continue
            seen.add(key)
            authors = info.get('authors') or {}
            al = authors.get('author') or []
            if isinstance(al, dict):
                al = [al]
            out.append({
                'id': 'dblp:' + key,
                'source': 'dblp',
                'title': ' '.join((info.get('title') or '').split()),
                'authors': [a.get('text', '') for a in al if isinstance(a, dict)],
                'year': info.get('year'),
                'venue': info.get('venue') or venue,
                'pages': info.get('pages'),
                'doi': info.get('doi'),
                'link': info.get('ee') or info.get('url') or f'https://dblp.org/rec/{key}',
                'dblp_key': key,
                'topic': dict(CONFERENCES)[venue],
            })
        if f + sent >= total or sent == 0:
            break
        f += sent
        time.sleep(4)  # 分页之间留间隔，避免限流
    return out


def run_confs(years):
    os.makedirs(CONF_DIR, exist_ok=True)
    total = 0
    for venue, _ in CONFERENCES:
        for year in years:
            papers = fetch_dblp_venue(venue, year)
            if not papers:
                print(f'[dblp] {venue} {year}: EMPTY (skipped, likely not in DBLP yet)')
                continue
            path = os.path.join(CONF_DIR, f'{venue}-{year}.json')
            with open(path, 'w', encoding='utf-8') as fp:
                json.dump(papers, fp, ensure_ascii=False, indent=1)
            print(f'[dblp] {venue} {year}: {len(papers)} papers -> {path}')
            total += len(papers)
            time.sleep(3)  # 会议之间留间隔，避免限流
    print(f'[dblp] DONE, {total} total')


# ---------- OpenReview ----------

def make_opener():
    """带 cookie jar 的 opener：先访问主页拿 cookie，再请求 API。"""
    jar = CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    try:
        http_get('https://openreview.net/', opener=opener)
    except Exception:
        pass
    return opener


def fetch_openreview_recent(opener):
    """抓最近 OPENREVIEW_DAYS 天提交的投稿。返回 (论文列表, 各 invitation 状态)。"""
    papers, status = [], {}
    since = datetime.now(timezone.utc) - timedelta(days=OPENREVIEW_DAYS)
    since_ts = int(since.timestamp() * 1000)
    for inv in OPENREVIEW_INVITATIONS:
        q = urllib.parse.quote(inv)
        url = f'https://api.openreview.net/notes?invitation={q}&limit=100&sort=ctime:desc'
        try:
            data = json.loads(http_get(url, opener=opener))
        except Exception as ex:
            status[inv] = f'ERROR {ex}'
            print(f'  [openreview] {inv}: ERROR {ex}', file=sys.stderr)
            continue
        notes = data.get('notes') or []
        if not notes and data.get('name'):
            status[inv] = f'blocked: {data.get("name")}'
            print(f'  [openreview] {inv}: blocked ({data.get("name")})', file=sys.stderr)
            continue
        cnt = 0
        for n in notes:
            ctime = n.get('ctime') or 0
            if ctime < since_ts:
                continue
            content = n.get('content') or {}
            title = content.get('title') if isinstance(content.get('title'), str) else (
                (content.get('title') or {}).get('value', '') if isinstance(content.get('title'), dict) else '')
            auth = content.get('authors')
            authors = auth if isinstance(auth, list) else []
            if isinstance(auth, dict):
                authors = auth.get('value', [])
            papers.append({
                'id': 'or:' + n.get('id', ''),
                'source': 'openreview',
                'title': ' '.join((title or '').split()),
                'authors': [str(a) for a in authors],
                'link': f'https://openreview.net/forum?id={n.get("id", "")}',
                'invitation': inv,
                'ctime': ctime,
                'published': datetime.fromtimestamp(ctime / 1000, tz=timezone.utc).strftime('%Y-%m-%d'),
                'topic': OPENREVIEW_TOPIC,
            })
            cnt += 1
        status[inv] = f'{cnt} new in {OPENREVIEW_DAYS}d'
        print(f'  [openreview] {inv}: {cnt} new', file=sys.stderr)
        time.sleep(0.5)
    return papers, status


def run_openreview():
    os.makedirs(RAW_DIR, exist_ok=True)
    opener = make_opener()
    papers, _ = fetch_openreview_recent(opener)
    if not papers:
        print('[openreview] nothing fetched (likely blocked) — skipping output')
        return
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    path = os.path.join(RAW_DIR, f'conferences-{today}.json')
    with open(path, 'w', encoding='utf-8') as fp:
        json.dump(papers, fp, ensure_ascii=False, indent=1)
    print(f'[openreview] {len(papers)} papers -> {path}')


# ---------- main ----------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--mode', choices=['all', 'confs', 'openreview'], default='all')
    ap.add_argument('--years', nargs='+', default=['2026', '2025'])
    args = ap.parse_args()

    if args.mode in ('all', 'confs'):
        run_confs(args.years)
    if args.mode in ('all', 'openreview'):
        run_openreview()


if __name__ == '__main__':
    main()
