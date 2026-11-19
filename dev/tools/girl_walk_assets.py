"""Girl walk cycle from the official frames (官方 2026-11-19: 更改女孩走路) -> OUT/img/girl-walk.webp + meta.girlWalk.
raw: raw/Bestfisher/images/girlwalk/girl-WALK.0125-0140.png (720x1280, same canvas and scale as her fishing frames,
ground at y 1122, facing left, no rod). 16 frames = one full stride, played at the original 24 fps.
python3 -I girl_walk_assets.py OUT_DIR"""
import sys, glob, json
import numpy as np
from PIL import Image
OUT = sys.argv[1].rstrip('/') + '/'
RAW = '/home/claude/raw/Bestfisher/images/girlwalk/'
fs = sorted(glob.glob(RAW + 'girl-WALK.*.png'))
ims = [Image.open(f).convert('RGBA') for f in fs]
bb = [im.getchannel('A').getbbox() for im in ims]
box = (min(b[0] for b in bb) - 3, min(b[1] for b in bb) - 3, max(b[2] for b in bb) + 3, 1124)
fw, fh = box[2] - box[0], box[3] - box[1]
strip = Image.new('RGBA', (fw * len(ims), fh))
for i, im in enumerate(ims): strip.paste(im.crop(box), (i * fw, 0))
strip.save(OUT + 'img/girl-walk.webp', 'WEBP', quality=88, method=5)
# body centre: middle of the torso (rows 700-800) averaged over the cycle
cs = []
for im in ims:
    a = np.array(im.getchannel('A'))[700:800] > 60; c = np.where(a.any(0))[0]; cs.append((c.min() + c.max()) / 2)
man = json.load(open(OUT + 'assets.json'))
man['img']['girl-walk'] = {'f': 'img/girl-walk.webp', 'w': strip.width, 'h': fh, 's': 1}
man['meta']['girlWalk'] = {'n': len(ims), 'fw': fw, 'fh': fh, 'cx': round(float(np.mean(cs)) - box[0], 1), 'rate': 1.5, 'noRod': True}
json.dump(man, open(OUT + 'assets.json', 'w'), ensure_ascii=False, separators=(',', ':'))
print(man['meta']['girlWalk'], strip.size)
