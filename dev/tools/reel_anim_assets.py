"""Reel-cranking loops for the angler (官方 2026-11-25) -> OUT/img/ang-<char>-<code>R.webp + meta.ang[...]
frames 125-140: 收線 (retrieve), 141-156: 搏魚 cranking fight. Used for rods with a reel (lure / cast rods).
boy: rendered by char3d/anim_reel.py (out/anim/<FAM>R). girl: built from her original fight frames 57-63 by
warping the left hand (on the reel handle) round a small circle, so it turns the handle.
python3 -I reel_anim_assets.py OUT_DIR"""
import sys, json, glob, os, math
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, '/home/claude/tools')
OUT = sys.argv[1].rstrip('/') + '/'
BOYD = '/home/claude/char3d/out/anim/'
man = json.load(open(OUT + 'assets.json'))


def pack(frames, maxw=2048, pad=2):
    order = sorted(range(len(frames)), key=lambda i: -frames[i][1].height)
    x = y = sh = 0; rects = [None] * len(frames)
    for i in order:
        w, h = frames[i][1].size
        if x + w > maxw: x, y, sh = 0, y + sh + pad, 0
        rects[i] = (x, y, w, h); x += w + pad; sh = max(sh, h)
    sheet = Image.new('RGBA', (maxw, y + sh))
    for i, (k, im) in enumerate(frames): sheet.paste(im, rects[i][:2])
    bb = sheet.getbbox(); return sheet.crop((0, 0, bb[2], bb[3])), rects


def write(key, frames, info, scale):
    """frames: [(n, crop)], info: [(n, ox, oy, tipx, tipy)] in logical px relative to the feet anchor"""
    sheet, rects = pack(frames)
    sheet.save(OUT + 'img/' + key + '.webp', 'WEBP', quality=84, method=5)
    meta = {}
    for (n, ox, oy, tx, ty), r in zip(info, rects):
        meta[str(n)] = [r[0], r[1], r[2], r[3], round(ox, 1), round(oy, 1), round(tx, 1), round(ty, 1), 0, 0, 0]
    man['img'][key] = {'f': 'img/' + key + '.webp', 'w': round(sheet.width / scale, 1), 'h': round(sheet.height / scale, 1), 's': scale}
    man['meta']['ang'][key] = {'s': scale, 'fr': meta}
    print(key, sheet.size, os.path.getsize(OUT + 'img/' + key + '.webp') // 1024, 'KB')


# ---------- boy ----------
for fam in ['L', 'C']:
    d = BOYD + fam + 'R/'
    if not os.path.exists(d + 'meta.json'): continue
    m = json.load(open(d + 'meta.json')); scale = m['scale']
    a = np.array(Image.open(d + 'ref.png').getchannel('A')) > 40
    ys = np.where(a.any(1))[0]; feet = ys.max() + 1
    cols = np.where(a[feet - int(90 * scale):feet - int(20 * scale)].any(0))[0]; cx = (cols.min() + cols.max()) / 2
    frames, info = [], []
    for k, fm in sorted(m['frames'].items(), key=lambda kv: int(kv[0])):
        im = Image.open(d + f'{int(k):04d}.png').convert('RGBA'); bb = im.getchannel('A').getbbox()
        frames.append((int(k), im.crop(bb))); tip = fm['tip']
        info.append((int(k), (bb[0] - cx) / scale, (bb[1] - feet) / scale, (tip[0] - cx) / scale, (tip[1] - feet) / scale))
    write(f'ang-boy-{fam}R', frames, info, scale)


# ---------- girl: crank warp on her fight frames ----------
def warp(im, c, d, rad):
    """move the pixels around centre c by d with a smooth falloff (radius rad): backward mapping, no holes"""
    a = np.array(im).astype(np.float32); H, W = a.shape[:2]
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.hypot(xx - c[0], yy - c[1]) / rad
    wgt = np.clip(1 - r, 0, 1); wgt = wgt * wgt * (3 - 2 * wgt)
    sx = xx - d[0] * wgt; sy = yy - d[1] * wgt
    out = np.stack([ndimage.map_coordinates(a[..., ch], [sy, sx], order=1, mode='constant') for ch in range(4)], -1)
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))


def girl_hand(im):
    """the left hand on the reel handle: the skin blob left of the reel, highest skin area in the frame"""
    a = np.array(im.convert('RGBA')).astype(int)
    r, g, b, al = a[..., 0], a[..., 1], a[..., 2], a[..., 3]
    skin = (al > 200) & (r > 150) & (r - b > 40) & (r > g) & (g > 90)
    H = a.shape[0]
    skin[int(H * .45):] = False          # above the hat brim only (frames are bottom aligned at the feet)
    lab, n = ndimage.label(skin)
    if n == 0: return None
    best = None
    for i in range(1, n + 1):
        ys, xs = np.where(lab == i)
        if len(xs) < 60: continue
        cand = (ys.mean(), xs.mean(), len(xs))
        if best is None or cand[0] < best[0]: best = cand   # the highest blob is the cranking hand
    return (best[1], best[0]) if best else None


src = man['meta']['ang']
for code in ['UL', 'ML', 'MH', 'C300', 'C360']:
    key = f'ang-girl-{code}'
    if key not in src: continue
    sheet = Image.open(OUT + man['img'][key]['f']).convert('RGBA'); fr = src[key]['fr']; scale = src[key]['s']
    base = {n: sheet.crop((fr[str(n)][0], fr[str(n)][1], fr[str(n)][0] + fr[str(n)][2], fr[str(n)][1] + fr[str(n)][3])) for n in range(57, 64)}
    hands = {n: girl_hand(base[n]) for n in base}
    frames, info = [], []
    for seq, n0, bases, R in [('retrieve', 125, [57, 57, 58, 58, 57, 57, 63, 63, 57, 57, 58, 58, 57, 57, 63, 63], 10.0),
                              ('fight', 141, [57, 58, 59, 60, 61, 62, 63, 62, 61, 60, 59, 58, 57, 58, 59, 60], 12.0)]:
        for i, bn in enumerate(bases):
            a = 2 * math.pi * i / 16   # one turn of the handle per 16 frames (same as the boy)
            im = base[bn]; hc = hands[bn]
            if hc:
                d = (R * math.cos(a), R * .8 * math.sin(a))
                im = warp(im, hc, d, 58)
            f = fr[str(bn)]
            frames.append((n0 + i, im)); info.append((n0 + i, f[4], f[5], f[6], f[7]))
    write(key + 'R', frames, info, scale)

man['meta']['reelSeq'] = {'retrieve': [125, 140], 'fight': [141, 156]}
json.dump(man, open(OUT + 'assets.json', 'w'), ensure_ascii=False, separators=(',', ':'))
