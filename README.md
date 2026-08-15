# PawService 📚

思岐的云端文献助手 —— 自动抓取 **计算机 + 材料** 方向的 arXiv 论文，做**分类 + 中文摘要**。

## 工作流

1. VPS 每天定时运行 `fetch.py`，抓取 arXiv 最新论文 → `data/raw/YYYY-MM-DD.json`
2. 爪爪（🦉）读原始数据，做分类 + 中文一句话摘要 → `data/summaries/YYYY-MM-DD.md`
3. `git push` 到 GitHub，本地 `git pull` 同步查看

## 目录结构

- `fetch.py` —— arXiv 抓取脚本
- `data/raw/` —— 原始抓取数据（JSON）
- `data/summaries/` —— 分类与中文摘要（Markdown）

## 抓取范围

- 计算机：cs.LG / cs.CL / cs.AI / cs.CV / cs.CR / cs.SE / cs.DS
- 材料：cond-mat.mtrl-sci / physics.app-ph / cond-mat.mes-hall
