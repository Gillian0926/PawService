#!/usr/bin/env python3
"""Fetch recent arXiv papers for configured categories and save as JSON.

Run:  .venv/bin/python fetch.py
Output: data/raw/YYYY-MM-DD.json  (deduplicated across categories)
"""
import feedparser
import json
import os
import sys
from datetime import datetime, timezone

# (arxiv category, topic label)  —— 抓取范围，可自行增删
CATEGORIES = [
    # 计算机
    ("cs.LG", "计算机/机器学习"),
    ("cs.CL", "计算机/自然语言处理"),
    ("cs.AI", "计算机/人工智能"),
    ("cs.CV", "计算机/计算机视觉"),
    ("cs.CR", "计算机/安全与隐私"),
    ("cs.SE", "计算机/软件工程"),
    ("cs.DS", "计算机/数据科学"),
    # 材料
    ("cond-mat.mtrl-sci", "材料/材料科学"),
    ("physics.app-ph", "材料/应用物理"),
    ("cond-mat.mes-hall", "材料/介观与纳米"),
]

MAX_PER_CAT = 8
DATA_DIR = "data/raw"


def fetch_category(cat):
    url = (f"http://export.arxiv.org/api/query?search_query=cat:{cat}"
           f"&sortBy=submittedDate&sortOrder=descending&max_results={MAX_PER_CAT}")
    d = feedparser.parse(url)
    out = []
    for e in d.entries:
        out.append({
            "id": e.get("id", "").strip(),
            "title": " ".join(e.get("title", "").split()),
            "published": e.get("published", ""),
            "authors": [a.get("name", "") for a in e.get("authors", [])],
            "abstract": " ".join((e.get("summary", "") or "").split()),
            "category": cat,
            "link": e.get("link", ""),
        })
    return out


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    all_papers = []
    seen = set()
    for cat, label in CATEGORIES:
        try:
            papers = fetch_category(cat)
            for p in papers:
                key = p["id"].rsplit("/", 1)[-1]
                if key in seen:
                    continue
                seen.add(key)
                p["topic"] = label
                all_papers.append(p)
            print(f"{cat}: {len(papers)}", file=sys.stderr)
        except Exception as ex:
            print(f"{cat}: ERROR {ex}", file=sys.stderr)

    out_path = os.path.join(DATA_DIR, f"{today}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(all_papers, f, ensure_ascii=False, indent=2)
    print(f"TOTAL {len(all_papers)} -> {out_path}")


if __name__ == "__main__":
    main()
