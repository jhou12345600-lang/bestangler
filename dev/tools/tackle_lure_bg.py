"""裝備配置 board for lure rods (官方 2026-11-25：選路亞竿時不顯示浮標框): the board art with the float slot, its connector
and the bobber on the line painted out (raw/tackle/BG-lure.png, made from fishing/POP-tackle/BG by inpainting).
python3 -I tackle_lure_bg.py OUT_DIR"""
import sys, json
from PIL import Image
OUT = sys.argv[1].rstrip('/') + '/'
man = json.load(open(OUT + 'assets.json'))
im = Image.open('/home/claude/raw/tackle/BG-lure.png').convert('RGBA')
im.save(OUT + 'img/tackle-bg-lure.webp', 'WEBP', quality=90, method=5)
man['img']['tackle-bg-lure'] = {'f': 'img/tackle-bg-lure.webp', 'w': im.width / 2, 'h': im.height / 2, 's': 2}
json.dump(man, open(OUT + 'assets.json', 'w'), ensure_ascii=False, separators=(',', ':'))
print('ok', im.size)
