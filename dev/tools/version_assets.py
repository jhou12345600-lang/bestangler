"""Content hashes for every image the manifest references -> assets.json "ver" {path: hash}. The game appends ?v=<hash>
so a browser never pairs a cached old image with new frame data. Run last, after every asset change.
python3 -I version_assets.py OUT_DIR"""
import sys, json, hashlib, os
OUT = sys.argv[1].rstrip('/') + '/'
man = json.load(open(OUT + 'assets.json'))
files = set(man.get('atlas', []))
for sec in ('img', 'anim'):
    for v in man.get(sec, {}).values():
        if isinstance(v, dict) and v.get('f'): files.add(v['f'])
ver = {}
for f in sorted(files):
    if os.path.exists(OUT + f): ver[f] = hashlib.md5(open(OUT + f, 'rb').read()).hexdigest()[:8]
man['ver'] = ver
json.dump(man, open(OUT + 'assets.json', 'w'), ensure_ascii=False, separators=(',', ':'))
print('versioned', len(ver), 'files')
