"""Rebuild only the boy's angler atlases (ang-boy-L / ang-boy-C, …) from char3d/out/anim/<FAM> (anim_boy.py render).
Used when the girl's raw frames are not on this machine. python3 -I boy_ang_build.py OUT_DIR [FAM …]"""
import sys, os, json
sys.path.insert(0, '/home/claude/tools')
import numpy as np
from PIL import Image
import angler_anim as AA
OUT = AA.OUT
fams = sys.argv[2:] or ['H', 'C', 'L']
man = json.load(open(OUT + 'assets.json'))
for fam in fams:
    mj = AA.BOYD + fam + '/meta.json'
    if not os.path.exists(mj): print('skip', fam); continue
    m = json.load(open(mj))
    files = {int(k): AA.BOYD + fam + f'/{int(k):04d}.png' for k in m['frames']}
    a = np.array(Image.open(files[1]).getchannel('A')) > 40
    ys = np.where(a.any(1))[0]; feet = ys.max() + 1
    cols = np.where(a[feet - int(90 * m['scale']):feet - int(20 * m['scale'])].any(0))[0]; cx = (cols.min() + cols.max()) / 2
    AA.build('boy', fam, files, m['scale'], feet, cx, man['meta']['ang'], man['img'], m['frames'])
    print('boy', fam, os.path.getsize(OUT + f'img/ang-boy-{fam}.webp') // 1024, 'KB')
json.dump(man, open(OUT + 'assets.json', 'w'), ensure_ascii=False, separators=(',', ':'))
