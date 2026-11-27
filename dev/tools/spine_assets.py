"""Spine skeletons from the official team (官方 2026-11-28 測試：角色動作改用 Spine 骨架動畫，省圖、加快載入).
raw/spine/<name>/skeleton.{json,atlas,png} -> OUT/spine/<name>/: json minified, the atlas page converted to WebP
(alpha kept) and the atlas pointed at it. The runtime (lib/spine-canvas.min.js, official spine-ts 3.8 canvas build)
is loaded only when a scene needs it.   python3 -I spine_assets.py OUT_DIR"""
import sys, os, json
from PIL import Image
OUT = sys.argv[1].rstrip('/') + '/'
RAW = '/home/claude/raw/spine/'
for name in sorted(os.listdir(RAW)):
    s, d = RAW + name + '/', OUT + 'spine/' + name + '/'
    os.makedirs(d, exist_ok=True)
    js = json.load(open(s + 'skeleton.json', encoding='utf8'))
    # Spine 3.8.75 exports are refused by the official runtime (that editor build wrote some curve data wrongly).
    # An export with no curves at all is unaffected, so it is marked as a 3.8 export the runtime accepts; anything
    # with curves needs a re-export from Spine 3.8.99.
    if js.get('skeleton', {}).get('spine') == '3.8.75':
        raw = open(s + 'skeleton.json', encoding='utf8').read()
        if '"curve"' in raw: raise SystemExit(f'{name}: exported with Spine 3.8.75 and uses curves - please re-export with Spine 3.8.99')
        js['skeleton']['spine'] = '3.8.99'; js['skeleton']['exportedWith'] = '3.8.75 (no curves, accepted as 3.8.99)'
        print(name, 'note: Spine 3.8.75 export without curves, marked 3.8.99')
    json.dump(js, open(d + 'skeleton.json', 'w', encoding='utf8'), ensure_ascii=False, separators=(',', ':'))
    atlas = open(s + 'skeleton.atlas', encoding='utf8').read()
    pages = [l.strip() for l in atlas.splitlines() if l.strip().lower().endswith('.png')]
    for pgf in pages:
        im = Image.open(s + pgf).convert('RGBA'); w = pgf[:-4] + '.webp'
        im.save(d + w, 'WEBP', quality=86, method=6); atlas = atlas.replace(pgf, w)
        print(name, pgf, os.path.getsize(s + pgf) // 1024, 'KB ->', os.path.getsize(d + w) // 1024, 'KB')
    open(d + 'skeleton.atlas', 'w', encoding='utf8').write(atlas)
