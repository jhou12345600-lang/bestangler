"""休閒池新版素材（官方 2026-11 pond1.rar）→ OUT/img + OUT/assets.json
python3 -I pond1v2_assets.py OUT_DIR"""
import sys, json
from PIL import Image
OUT = sys.argv[1].rstrip('/') + '/'
R = '/home/claude/raw/Bestfisher/images/pond1v2/'
man = json.load(open(OUT + 'assets.json'))
def single(key, src, q=88):
    im = Image.open(R + src).convert('RGBA'); f = 'img/' + key + '.webp'
    im.save(OUT + f, 'WEBP', quality=q, method=5)
    man['img'][key] = {'f': f, 'w': im.width, 'h': im.height, 's': 1}
for key, src in [('p1-top', 'bg-top.png'), ('p1-floor', 'floor.png'), ('p1-rail', 'Wooden railing.png'), ('p1-rail-broken', 'Wooden railing brogen.png'),
                 ('p1-wood', 'wood.png'), ('p1-grass', 'grass.png'), ('p1-grass2', 'grass2.png')]:
    single(key, src)
# water surface: fully opaque, the shader mirror-tiles it every 720 px
im = Image.open(R + 'bg-water.png').convert('RGB'); im.save(OUT + 'img/p1-water.webp', 'WEBP', quality=88, method=5)
man['img']['p1-water'] = {'f': 'img/p1-water.webp', 'w': im.width, 'h': im.height, 's': 1}
json.dump(man, open(OUT + 'assets.json', 'w'), ensure_ascii=False, separators=(',', ':'))
print('ok')
