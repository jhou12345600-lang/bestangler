"""新版大廳素材（官方 2026-11 lobby.rar）→ OUT/img + OUT/assets.json
python3 -I lobby2_assets.py OUT_DIR"""
import sys, json
from PIL import Image
OUT = sys.argv[1].rstrip('/') + '/'
R = '/home/claude/raw/Bestfisher/images/lobby2/'
man = json.load(open(OUT + 'assets.json'))
def single(key, im, s, q=84):
    f = 'img/' + key + '.webp'
    im.save(OUT + f, 'WEBP', quality=q, method=5)
    man['img'][key] = {'f': f, 'w': round(im.width / s, 2), 'h': round(im.height / s, 2), 's': s}
single('lobby-map2', Image.open(R + 'map-BG.jpg').convert('RGB'), 1, 86)
single('lobby-topbg', Image.open(R + 'top UI-bg.png').convert('RGBA'), 1, 90)
for i in (1, 2, 3):
    single(f'lobby2-cloud{i}', Image.open(R + f'lobby-bg-cloud{i}.png').convert('RGBA'), 1, 90)
single('lobby2-locky', Image.open(R + 'button-locky.png').convert('RGBA'), 1, 92)
single('lobby2-lightwheel', Image.open(R + 'button-locky-lightwheel.png').convert('RGBA'), 1, 90)
json.dump(man, open(OUT + 'assets.json', 'w'), ensure_ascii=False, separators=(',', ':'))
print('ok')
