"""Pack char3d/out/boy-catch.png into OUT/img + OUT/assets.json (same math as build_assets.py).
python3 -I boy_catch_update.py OUT_DIR"""
import sys, json
import numpy as np
from PIL import Image
OUT = sys.argv[1].rstrip('/') + '/'; BOY = '/home/claude/char3d/out/'
man = json.load(open(OUT + 'assets.json')); bj = json.load(open(BOY + 'boy.json'))
cat = Image.open(BOY + 'boy-catch.png').convert('RGBA'); sc_ = cat.size[1] / 870.0
ca = np.array(cat.getchannel('A')); lc = np.where(ca[int(cat.size[1] * .6):].max(0) > 40)[0]
cat.save(OUT + 'img/boy-catch.webp', 'WEBP', quality=88, method=5)
man['img']['boy-catch'] = {'f': 'img/boy-catch.webp', 'w': round(cat.width / sc_, 2), 'h': round(cat.height / sc_, 2), 's': sc_}
b = man['meta']['boy']
b.update({'catchW': round(cat.size[0] / sc_, 1), 'catchH': round(cat.size[1] / sc_, 1), 'catchCx': round(((lc.min() + lc.max()) / 2) / sc_, 1),
          'catchTip': [round(bj['catch']['tip'][0] / sc_, 1), round(bj['catch']['tip'][1] / sc_, 1)]})
json.dump(man, open(OUT + 'assets.json', 'w'), ensure_ascii=False, separators=(',', ':'))
print(b['catchW'], b['catchH'], b['catchTip'])
