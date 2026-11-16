"""Pack char3d/out/boy-walk.png (walk2.py, 16 frames) into OUT/img + OUT/assets.json.
The walk strip is rendered at 1000 px height (idle/fight at 1400) with the same camera, so its texture
scale is the idle scale * 1000/1400. 'rate' = gait cycles per second that keeps the stance foot planted
while the dock scrolls at 1.25 world units (375 px) per second.   python3 -I boy_walk_update.py OUT_DIR"""
import sys, json
import numpy as np
from PIL import Image
OUT = sys.argv[1].rstrip('/') + '/'; BOY = '/home/claude/char3d/out/'
man = json.load(open(OUT + 'assets.json'))
idle = Image.open(BOY + 'boy-idle.png'); sb = idle.size[1] / 505.0 * 1000 / 1400
wj = json.load(open(BOY + 'boy-walk.json')); ws = Image.open(BOY + 'boy-walk.png').convert('RGBA')
ws.save(OUT + 'img/boy-walk.webp', 'WEBP', quality=88, method=5)
man['img']['boy-walk'] = {'f': 'img/boy-walk.webp', 'w': round(ws.width / sb, 2), 'h': round(ws.height / sb, 2), 's': sb}
wa = np.array(ws.crop((0, 0, wj['fw'], wj['fh'])).getchannel('A'))
tc = np.where(wa[int(wj['fh'] * .2):int(wj['fh'] * .45)].max(0) > 40)[0]
rate = 375 / (wj['stanceTravel'] / sb)
man['meta']['boy']['walk'] = {'n': wj['n'], 'fw': round(wj['fw'] / sb, 2), 'fh': round(wj['fh'] / sb, 2), 'cx': round((tc.min() + tc.max()) / 2 / sb, 1),
                              'hands': [[round(h[0] / sb, 1), round(h[1] / sb, 1)] for h in wj['hands']], 'rate': round(rate, 3)}
json.dump(man, open(OUT + 'assets.json', 'w'), ensure_ascii=False, separators=(',', ':'))
w = man['meta']['boy']['walk']; print(w['n'], w['fw'], w['fh'], w['cx'], w['rate'])
