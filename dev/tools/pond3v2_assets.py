"""路亞池新版素材（官方 2026-11-25 pond2.rar：沼澤背景、水面、枯木、石岸、草）→ OUT/img + OUT/assets.json
python3 -I pond3v2_assets.py OUT_DIR"""
import sys, json
from PIL import Image
OUT = sys.argv[1].rstrip('/') + '/'
R = '/home/claude/raw/Bestfisher/images/pond3v2/'
man = json.load(open(OUT + 'assets.json'))
def single(key, src, q=88, scale=1.0):
    im = Image.open(R + src).convert('RGBA')
    if scale != 1: im = im.resize((round(im.width * scale), round(im.height * scale)), Image.LANCZOS)
    f = 'img/' + key + '.webp'; im.save(OUT + f, 'WEBP', quality=q, method=5)
    man['img'][key] = {'f': f, 'w': im.width, 'h': im.height, 's': 1}
for key, src in [('p3-top', 'bg-top.png'), ('p3-floor', 'floor.png'), ('p3-grass', 'grass.png'),
                 ('p3-wood1', 'deadwood1.png'), ('p3-wood2', 'deadwood2.png'), ('p3-wood3', 'deadwood3.png'), ('p3-wood4', 'deadwood4.png')]:
    single(key, src)
im = Image.open(R + 'bg-water.png').convert('RGB'); im.save(OUT + 'img/p3-water.webp', 'WEBP', quality=88, method=5)
man['img']['p3-water'] = {'f': 'img/p3-water.webp', 'w': im.width, 'h': im.height, 's': 1}
json.dump(man, open(OUT + 'assets.json', 'w'), ensure_ascii=False, separators=(',', ':'))
print('ok')
