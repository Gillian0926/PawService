#!/usr/bin/env python3
"""Compare the two most recent raw fetches; print overlap & structure."""
import json, os, glob

base = os.path.dirname(os.path.abspath(__file__))
raw_dir = os.path.join(base, 'data', 'raw')
files = sorted(glob.glob(os.path.join(raw_dir, '*.json')))
if len(files) < 2:
    print('Need at least 2 raw files, got:', files)
    raise SystemExit(0)

def load(p):
    with open(p, encoding='utf-8') as f:
        return json.load(f)

def ids_of(d):
    if isinstance(d, dict):
        for k, v in d.items():
            if isinstance(v, list) and v and isinstance(v[0], dict):
                return [p.get('id') or p.get('arxiv_id') or p.get('url') for p in v], list(v[0].keys())
        return list(d.keys()), list(d.keys())
    if isinstance(d, list) and d and isinstance(d[0], dict):
        return [p.get('id') or p.get('arxiv_id') or p.get('url') for p in d], list(d[0].keys())
    return None, None

newest, prev = files[-1], files[-2]
d_new, d_old = load(newest), load(prev)
ids_new, keys_new = ids_of(d_new)
ids_old, _ = ids_of(d_old)

print('newest:', os.path.basename(newest))
print('prev  :', os.path.basename(prev))
print('type  :', type(d_new).__name__, '| len:', len(d_new) if hasattr(d_new, '__len__') else '?')
print('keys  :', keys_new)
print('same as prev:', ids_new == ids_old, '| new:', len(set(ids_new) - set(ids_old)), '| gone:', len(set(ids_old) - set(ids_new)))
if ids_new:
    print('sample ids:', ids_new[:5])
