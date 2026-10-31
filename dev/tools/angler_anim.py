"""Angler animation atlases (girl = original 神釣手 frames per rod; boy = rendered from char3d/out/anim).
python3 -I angler_anim.py OUT_DIR   -> writes OUT_DIR/img/ang-<char>-<code>.webp and merges OUT_DIR/assets.json
Per frame metadata (logical px, relative to the angler's feet centre):
  [sx, sy, w, h, ox, oy, tipx, tipy, netx, nety, netKind]   netKind 0 = none, 1 = pole reaching out, 2 = bag held up
"""
import sys, os, re, glob, json
import numpy as np
from PIL import Image
from scipy import ndimage

OUT = sys.argv[1].rstrip('/') + '/'
RAW = '/home/claude/raw/Bestfisher/images/fishing/girl/'
BOYD = '/home/claude/char3d/out/anim/'
CODES = ['H1', 'H2', 'H3', 'C300', 'C360', 'UL', 'ML', 'MH']
SEQ = {'idle': (1, 32, 4), 'pull': (33, 56, 2), 'fight': (57, 63, 1), 'big': (64, 70, 2), 'get': (71, 85, 1), 'throw': (86, 124, 2)}
PICK = sorted({n for a, b, s in SEQ.values() for n in list(range(a, b + 1, s)) + [b]})
FEET_Y = 1115


def num(p):
    return int(re.findall(r'(\d+)', os.path.basename(p))[-1])


def disk(r):
    y, x = np.ogrid[-r:r + 1, -r:r + 1]
    return x * x + y * y <= r * r


def analyse(im, n, cx, rod_hint=None):
    a = np.array(im)
    al = a[..., 3] > 40
    r, g, b = [a[..., i].astype(int) for i in range(3)]
    thick = ndimage.binary_opening(al, structure=disk(5))
    thin = al & ~ndimage.binary_dilation(thick, structure=disk(2))
    H, W = al.shape
    yy, xx = np.mgrid[0:H, 0:W]
    green = al & (g > r + 25) & (g > b + 5) & (xx < cx) & (yy > 820)
    # the rod: thin parts, not the white/silver net pole, not left of the body during the landing
    cand = thin & ~green
    if 71 <= n <= 85:
        cand &= xx > cx - 10
    lab, k = ndimage.label(cand, structure=np.ones((3, 3)))
    tip = None
    if k:
        sizes = ndimage.sum(cand, lab, range(1, k + 1))
        best = int(np.argmax(sizes)) + 1
        if sizes[best - 1] > 60:
            # faint tip pixels belong to the rod too: grow the component through low-alpha thin pixels
            faint = (a[..., 3] > 10) & ~ndimage.binary_dilation(thick, structure=disk(2)) & ~green
            if 71 <= n <= 85: faint &= xx > cx - 10
            lab2, _ = ndimage.label(faint, structure=np.ones((3, 3)))
            ids = np.unique(lab2[lab == best]); ids = ids[ids > 0]
            comp = np.isin(lab2, ids)
            # geodesic walk from the grip (the rod pixel closest to the body) to the far end
            dist = ndimage.distance_transform_edt(~thick)
            ys, xs = np.where(comp)
            i0 = int(np.argmin(dist[ys, xs]))
            from collections import deque
            seen = {(int(ys[i0]), int(xs[i0])): 0}; q = deque([(int(ys[i0]), int(xs[i0]))]); far = (0, ys[i0], xs[i0])
            cs = set(zip(ys.tolist(), xs.tolist()))
            while q:
                y0, x0 = q.popleft(); dd = seen[(y0, x0)]
                if dd > far[0]: far = (dd, y0, x0)
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        nb = (y0 + dy, x0 + dx)
                        if nb in cs and nb not in seen: seen[nb] = dd + 1; q.append(nb)
            tip = [int(far[2]), int(far[1])]
    if tip is None:  # rod hidden behind the body / pointing at the camera: take the right hand area top
        tip = rod_hint
    net, kind = None, 0
    if 71 <= n <= 85:
        if green.sum() > 2500:
            ys, xs = np.where(green)
            top = ys.min()
            band = xs[ys < top + 25]
            net, kind = [int(band.mean()), int(top + 12)], 2
        else:
            left = al & (xx < cx - 50) & (yy > 700)
            if left.any():
                ys, xs = np.where(left)
                i = np.argmin(xs)
                net, kind = [int(xs[i]), int(ys[i])], 1
    return tip, net, kind


def pack(frames, maxw=2048, pad=2):
    """shelf pack; frames: list of (key, PIL crop). returns sheet, rects"""
    order = sorted(range(len(frames)), key=lambda i: -frames[i][1].height)
    x = y = sh = 0
    rects = [None] * len(frames)
    for i in order:
        w, h = frames[i][1].size
        if x + w > maxw:
            x, y, sh = 0, y + sh + pad, 0
        rects[i] = (x, y, w, h)
        x += w + pad; sh = max(sh, h)
    sheet = Image.new('RGBA', (maxw, y + sh))
    for i, (k, im) in enumerate(frames):
        sheet.paste(im, rects[i][:2])
    bb = sheet.getbbox()
    return sheet.crop((0, 0, bb[2], bb[3])), rects


def build(char, code, files, scale, feet_y, cx, out_meta, out_img, prev):
    frames, info = [], []
    last_tip = None
    for n in PICK:
        im = Image.open(files[n]).convert('RGBA')
        if char == 'girl':
            tip, net, kind = analyse(im, n, cx, last_tip)
        else:
            m = prev[str(n)]
            tip, net, kind = m['tip'], m.get('net'), m.get('kind', 0)
        last_tip = tip
        bb = im.getchannel('A').getbbox()
        crop = im.crop(bb)
        frames.append((n, crop))
        info.append((n, bb, tip, net, kind))
    sheet, rects = pack(frames)
    key = f'ang-{char}-{code}'
    rgb = sheet
    rgb.save(OUT + 'img/' + key + '.webp', 'WEBP', quality=84, method=5)
    meta = {}
    for (n, bb, tip, net, kind), r in zip(info, rects):
        f = lambda v: round(v / scale, 1)
        meta[n] = [r[0], r[1], r[2], r[3], f(bb[0] - cx), f(bb[1] - feet_y), f(tip[0] - cx), f(tip[1] - feet_y),
                   f(net[0] - cx) if net else 0, f(net[1] - feet_y) if net else 0, kind]
    out_img[key] = {'f': 'img/' + key + '.webp', 'w': round(sheet.width / scale, 1), 'h': round(sheet.height / scale, 1), 's': scale}
    out_meta[key] = {'s': scale, 'fr': meta}
    return sheet


def main():
    man = json.load(open(OUT + 'assets.json'))
    man['meta'].setdefault('ang', {})
    for code in CODES:
        files = {num(p): p for p in glob.glob(RAW + code + '/*.png')}
        a = np.array(Image.open(files[1]).getchannel('A')) > 40
        legs = a[FEET_Y - 90:FEET_Y - 20]
        cols = np.where(legs.any(0))[0]
        cx = (cols.min() + cols.max()) / 2
        build('girl', code, files, 1, FEET_Y, cx, man['meta']['ang'], man['img'], None)
        print('girl', code, 'cx', cx, os.path.getsize(OUT + f'img/ang-girl-{code}.webp') // 1024, 'KB')
    for fam in ['H', 'C', 'L']:
        mj = BOYD + fam + '/meta.json'
        if not os.path.exists(mj):
            continue
        m = json.load(open(mj))
        files = {int(k): BOYD + fam + f'/{int(k):04d}.png' for k in m['frames']}
        a = np.array(Image.open(files[1]).getchannel('A')) > 40
        ys = np.where(a.any(1))[0]; feet = ys.max() + 1
        legs = a[feet - int(90 * m['scale']):feet - int(20 * m['scale'])]
        cols = np.where(legs.any(0))[0]; cx = (cols.min() + cols.max()) / 2
        build('boy', fam, files, m['scale'], feet, cx, man['meta']['ang'], man['img'], m['frames'])
        print('boy', fam, os.path.getsize(OUT + f'img/ang-boy-{fam}.webp') // 1024, 'KB')
    man['meta']['angSeq'] = SEQ
    json.dump(man, open(OUT + 'assets.json', 'w'), ensure_ascii=False, separators=(',', ':'))


if __name__ == '__main__':
    main()
