"""Girl reel-crank frames from one original fight frame (官方 2026-11-25：女角收線要有捲線動作).
The left hand (with the handle knob it grips) is cut out as a layer and carried round the reel's handle circle;
the forearm stretches/compresses smoothly back to where it disappears behind the hat; the handle arm is redrawn
from the reel axis to the knob each frame.  crank(img, angle) -> RGBA image (same size), info dict."""
import math
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage


def analyse(im):
    a = np.array(im.convert('RGBA')).astype(int)
    r, g, b, al = a[..., 0], a[..., 1], a[..., 2], a[..., 3]
    H, W = al.shape
    skin = (al > 170) & (r > 135) & (r - b > 30) & (r > g) & (g > 75)
    hat = (al > 200) & (r > 175) & (g > 170) & (b > 150)
    blue = (al > 60) & (b > r + 25)
    rows = np.where(hat.sum(1) >= 12)[0]
    if not len(rows): return None
    ht = int(rows.min())
    band = np.zeros_like(skin); band[max(0, ht - 80):ht + 3] = True
    lab, n = ndimage.label(skin & band)
    if n == 0: return None
    sizes = ndimage.sum(np.ones_like(lab), lab, range(1, n + 1))
    hand = lab == int(np.argmax(sizes)) + 1
    ys, xs = np.where(hand)
    # the reel: blue pixels right of the hand, about its height
    bz = np.zeros_like(blue); bz[ys.min() - 15:ys.max() + 25, xs.max() - 10:xs.max() + 70] = True
    by, bx = np.where(blue & bz)
    A = np.array([bx.mean(), by.mean()]) if len(bx) else np.array([xs.max() + 25, ys.mean() + 10])
    reel_left = (bx.min() if len(bx) else xs.max() + 8)
    # grip: the fingertips' area, the top-right quarter of the hand
    q = (xs > np.percentile(xs, 55)) & (ys < np.percentile(ys, 50))
    grip = np.array([xs[q].mean(), ys[q].mean()]) if q.any() else np.array([xs.max(), ys.min()])
    # the layer that moves: everything opaque above the hat line, left of the reel (hand, fingers, the knob they hold)
    yy, xx = np.mgrid[0:H, 0:W]
    layer = (al > 0) & ~blue & (yy < ht + 3) & (yy > ys.min() - 22) & (xx < reel_left - 1) & (xx > xs.min() - 30)
    lab3, _ = ndimage.label(layer)
    keep = np.unique(lab3[ndimage.binary_dilation(hand, iterations=2) & layer]); keep = keep[keep > 0]
    layer = np.isin(lab3, keep)
    # the handle: the dark knob above the fingers and its stem down to the reel's side (the hub)
    dark = (al > 140) & (r + g + b < 200)
    kz = np.zeros_like(dark); kz[max(0, ys.min() - 25):ys.min() + 4, int(grip[0]) - 8:int(A[0]) + 2] = True
    ky, kx = np.where(dark & kz)
    if len(kx) >= 6:
        knob = np.array([kx.mean(), ky.mean()])
        hz = np.zeros_like(dark); hz[int(knob[1]) + 3:int(knob[1]) + 17, int(knob[0]):int(A[0]) + 2] = True
        hy, hx = np.where((al > 100) & ~blue & hz & ~skin)
        hub = np.array([np.median(hx), hy.max()]) if len(hx) else (knob + A) / 2
        box = np.zeros_like(dark); box[int(knob[1]) - 8:int(hub[1]), int(knob[0]) - 10:int(hub[0]) + 3] = True
        layer |= box & (al > 0) & ~blue
    else:
        knob = grip.copy(); hub = grip + (A - grip) * .35
    layer = ndimage.binary_dilation(layer, iterations=1) & (al > 0) & ~blue   # take the soft edges along
    ay, ax = np.where(layer)
    lo = ay >= ay.max() - 3
    base = np.array([ax[lo].mean(), ay.max()], float)
    return dict(ht=ht, grip=grip, A=A, base=base, layer=layer, knob=knob, hub=hub)


def crank(im, ang, info=None, A1=6., A2=7.):
    """the hand, holding the handle knob, goes round with the handle: a=0 is the original frame. A1: half the swing along
    the handle (hub -> knob), A2: across it (the circle seen from behind is a narrow ellipse)"""
    info = info or analyse(im)
    if info is None: return im, None
    a = np.array(im.convert('RGBA')).astype(np.float32)
    H, W = a.shape[:2]
    grip, hub, knob0 = info['grip'], info['hub'], info['knob']
    u = knob0 - hub; u = u / max(np.linalg.norm(u), 1e-3); n = np.array([-u[1], u[0]])
    d = A1 * (math.cos(ang) - 1) * u + A2 * math.sin(ang) * n
    knob = knob0 + d
    L = info['layer']
    layer = a.copy(); layer[~L] = 0
    basei = a.copy(); basei[L] = 0
    B, G = info['base'], grip
    v = G - B; L2 = max((v ** 2).sum(), 1)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    def tt(qx, qy):
        t = np.clip(((qx - B[0]) * v[0] + (qy - B[1]) * v[1]) / L2, 0, 1); return t * t * (3 - 2 * t)
    qx, qy = xx.copy(), yy.copy()
    for _ in range(8):
        t = tt(qx, qy); qx = xx - d[0] * t; qy = yy - d[1] * t
    warped = np.stack([ndimage.map_coordinates(layer[..., c], [qy, qx], order=1, mode='constant') for c in range(4)], -1)
    out = Image.fromarray(np.clip(basei, 0, 255).astype(np.uint8))
    dr = ImageDraw.Draw(out)   # the handle arm from the hub on the reel's side to the knob in the hand
    hb = hub + d   # where the moved stem ends: join it back to the hub on the reel
    dr.line([tuple(hub), tuple(hb)], fill=(150, 120, 40, 255), width=3)
    dr.line([tuple(hub + [-.6, -.6]), tuple(hb + [-.6, -.6])], fill=(235, 200, 90, 255), width=1)
    dr.ellipse([hub[0] - 2.2, hub[1] - 2.2, hub[0] + 2.2, hub[1] + 2.2], fill=(210, 176, 70, 255), outline=(90, 70, 20, 255))
    out.alpha_composite(Image.fromarray(np.clip(warped, 0, 255).astype(np.uint8)))
    return out, dict(knob=knob, hub=hub)
