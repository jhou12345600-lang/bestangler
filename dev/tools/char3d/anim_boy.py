"""Render the male angler's fishing animations (same frame numbers as the original girl set).
python3 anim_boy.py probe poses.json out.png      -> contact sheet of explicit poses
python3 anim_boy.py render FAMILY                 -> out/anim/<FAMILY>/NNNN.png + meta.json   (FAMILY: H, C, L)
"""
import base64, io, json, math, os, sys
from playwright.sync_api import sync_playwright
from PIL import Image, ImageEnhance, ImageFilter, ImageDraw
ARGS = ['--use-gl=angle', '--use-angle=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist', '--enable-unsafe-swiftshader']
W, H = 1200, 2000
CAM = {'w': W, 'h': H, 'az': 180, 'el': 14, 'dist': 1000, 'fov': 31.9, 'ty': 120}
SCALE = 1.25   # texture px per logical px (the girl frames are 1:1)

GRIP = {}
for f in '1234':
    GRIP[f'R_Finger{f}'] = [0, 0, 70]; GRIP[f'R_Finger{f}1'] = [0, 0, 80]; GRIP[f'R_Finger{f}2'] = [0, 0, 60]
LGRIP = {}
for f in '1234':
    LGRIP[f'L_Finger{f}'] = [0, 0, 60]; LGRIP[f'L_Finger{f}1'] = [0, 0, 70]; LGRIP[f'L_Finger{f}2'] = [0, 0, 50]
LREL = {}
for f in '1234':
    LREL[f'L_Finger{f}'] = [0, 0, -25]; LREL[f'L_Finger{f}1'] = [0, 0, -35]


# ---------------- keyframes (frame numbers follow the original girl animation) ----------------
IDLE = {'R_UpperArm': [0, -38, 8], 'R_Forearm': [0, -25, -25], 'L_UpperArm': [0, 38, 4], 'L_Forearm': [0, 10, -10]}
FIGHT = {'R_UpperArm': [0, 20, -20], 'R_Forearm': [0, 85, 0], 'L_UpperArm': [0, 22, -12], 'L_Forearm': [0, 20, -20], 'Spine1': [0, 0, -3]}
ROD_IDLE = {'dir': [-.1, .55, .85], 'bend': [0, -1, .3], 'k': .06}
ROD_FIGHT = {'dir': [-.4, 1, .2], 'bend': [.9, -.25, .6], 'k': .5}
def P(base, **kw):
    out = {k: list(v) for k, v in base.items()}
    for k, v in kw.items(): out[k] = v
    return out
KEY = {
    1: (IDLE, ROD_IDLE, None),
    17: (P(IDLE, Spine1=[0, 1.5, 0], R_UpperArm=[0, -37, 7]), {'dir': [-.11, .57, .84], 'bend': [0, -1, .3], 'k': .07}, None),
    32: (IDLE, ROD_IDLE, None),
    # 揚竿 pull
    33: (IDLE, ROD_IDLE, None),
    36: (P(FIGHT, R_UpperArm=[0, 30, -28], R_Forearm=[0, 92, -6], Spine1=[0, 0, -7]), {'dir': [-.2, 1, -.1], 'bend': [.8, -.3, .6], 'k': .55}, None),
    39: (P(FIGHT, R_UpperArm=[0, 34, -26], R_Forearm=[0, 95, -6], Spine1=[0, 0, -8]), {'dir': [-.25, 1, -.05], 'bend': [.8, -.3, .6], 'k': .5}, None),
    44: (P(IDLE, R_UpperArm=[0, 5, -12], R_Forearm=[0, 62, -10], L_UpperArm=[0, 28, -8]), {'dir': [-.3, 1, .3], 'bend': [.6, -.3, .6], 'k': .3}, None),
    50: (P(IDLE, R_UpperArm=[0, -22, 0], R_Forearm=[0, 20, -20]), {'dir': [-.2, .9, .5], 'bend': [0, -.5, 1], 'k': .12}, None),
    56: (IDLE, ROD_IDLE, None),
    # 搏魚 fight loop
    57: (FIGHT, ROD_FIGHT, None),
    60: (P(FIGHT, R_UpperArm=[0, 24, -24], Spine1=[0, -1.5, -4]), {'dir': [-.3, 1, .3], 'bend': [.9, -.25, .6], 'k': .52}, None),
    63: (P(FIGHT, R_UpperArm=[0, 21, -21]), {'dir': [-.34, 1, .26], 'bend': [.9, -.25, .6], 'k': .48}, None),
    # 大魚中鉤
    64: (FIGHT, ROD_FIGHT, None),
    67: (P(FIGHT, R_UpperArm=[0, -10, -45], R_Forearm=[0, 40, -20], Spine1=[0, 0, 10]), {'dir': [-.2, .5, 1], 'bend': [0, -1, .5], 'k': .6}, None),
    70: (P(FIGHT, R_UpperArm=[0, -25, -60], R_Forearm=[0, 10, -10], Spine1=[0, 0, 12]), {'dir': [0, -.2, 1], 'bend': [0, -1, 0], 'k': .3}, None),
    # 撈魚 get: rod up in the right hand, the net in the left
    71: (P(FIGHT, L_UpperArm=[0, 18, -45], L_Forearm=[0, 0, -8], Spine1=[0, 5, 4]), {'dir': [-.25, 1, .1], 'bend': [.7, -.2, .6], 'k': .25}, {'dir': [1, -.55, .75], 'len': 85, 'normal': [0, 1, 0], 'kind': 1}),
    73: (P(FIGHT, L_UpperArm=[0, 24, -40], L_Forearm=[0, 0, -15], Spine1=[0, 5, 4]), {'dir': [-.25, 1, .1], 'bend': [.7, -.2, .6], 'k': .25}, {'dir': [1, -.5, .6], 'len': 75, 'normal': [0, 1, 0], 'kind': 1}),
    74: (P(FIGHT, L_UpperArm=[0, 45, -22], L_Forearm=[0, 0, -55], Spine1=[0, 3, 2]), {'dir': [-.2, 1, .05], 'bend': [.7, -.2, .6], 'k': .22}, {'dir': [1, -.35, .3], 'len': 30, 'normal': [0, 1, 0], 'kind': 2}),
    77: (P(FIGHT, L_UpperArm=[0, 50, -18], L_Forearm=[0, 0, -62], Spine1=[0, 2, 0]), {'dir': [-.15, 1, .05], 'bend': [.7, -.2, .6], 'k': .2}, {'dir': [1, -.3, .2], 'len': 26, 'normal': [0, 1, 0], 'kind': 2}),
    82: (P(FIGHT, L_UpperArm=[0, 50, -18], L_Forearm=[0, 0, -62], Spine1=[0, 2, 0]), {'dir': [-.15, 1, .05], 'bend': [.7, -.2, .6], 'k': .2}, {'dir': [1, -.3, .2], 'len': 26, 'normal': [0, 1, 0], 'kind': 2}),
    85: (P(FIGHT, L_UpperArm=[0, 18, -45], L_Forearm=[0, 0, -8], Spine1=[0, 5, 4]), {'dir': [-.25, 1, .1], 'bend': [.7, -.2, .6], 'k': .25}, {'dir': [1, -.55, .75], 'len': 85, 'normal': [0, 1, 0], 'kind': 1}),
    # 拋竿 throw
    86: (IDLE, ROD_IDLE, None),
    89: (P(IDLE, R_UpperArm=[0, 10, -25], R_Forearm=[0, 70, -10]), {'dir': [-.15, 1, .35], 'bend': [0, -1, .2], 'k': .05}, None),
    92: (P(IDLE, R_UpperArm=[0, 40, -10], R_Forearm=[0, 80, 0], Spine1=[0, 0, -4]), {'dir': [-.05, 1, 0], 'bend': [0, 0, 1], 'k': .02}, None),
    95: (P(IDLE, R_UpperArm=[0, 45, 5], R_Forearm=[0, 85, 0], Spine1=[0, 0, -7]), {'dir': [0, 1, -.45], 'bend': [0, -.3, -1], 'k': .12}, None),
    98: (P(IDLE, R_UpperArm=[0, 30, -50], R_Forearm=[0, 40, -20], Spine1=[0, 0, 8]), {'dir': [-.05, .75, 1], 'bend': [0, -.3, 1], 'k': .25}, None),
    101: (P(IDLE, R_UpperArm=[0, -5, -60], R_Forearm=[0, 15, -20], Spine1=[0, 0, 10]), {'dir': [-.05, .35, 1], 'bend': [0, -1, .2], 'k': .1}, None),
    113: (P(IDLE, R_UpperArm=[0, -8, -58], R_Forearm=[0, 12, -20], Spine1=[0, 0, 9]), {'dir': [-.05, .32, 1], 'bend': [0, -1, .2], 'k': .08}, None),
    116: (P(IDLE, R_UpperArm=[0, -20, -30], R_Forearm=[0, 0, -25], Spine1=[0, 0, 4]), {'dir': [-.1, .45, .9], 'bend': [0, -1, .3], 'k': .07}, None),
    124: (IDLE, ROD_IDLE, None),
}
FAMILY = {'H': {'len': 165, 'style': 'pole'}, 'C': {'len': 185, 'style': 'cast'}, 'L': {'len': 145, 'style': 'lure'}}
SEQ = {'idle': (1, 32, 4), 'pull': (33, 56, 2), 'fight': (57, 63, 1), 'big': (64, 70, 2), 'get': (71, 85, 1), 'throw': (86, 124, 2)}
PICK = sorted({n for a, b, s in SEQ.values() for n in list(range(a, b + 1, s)) + [b]})
def seq_of(n):
    for k, (a, b, s) in SEQ.items():
        if a <= n <= b: return a, b
def lerp(a, b, t): return a + (b - a) * t
def state_at(n, fam):
    a, b = seq_of(n)
    ks = sorted(k for k in KEY if a <= k <= b)
    lo = max(k for k in ks if k <= n); hi = min(k for k in ks if k >= n)
    t = 0 if hi == lo else (n - lo) / (hi - lo)
    t = t * t * (3 - 2 * t)
    A, B = KEY[lo], KEY[hi]
    bones = set(A[0]) | set(B[0])
    pose = {bn: [lerp((A[0].get(bn) or [0, 0, 0])[i], (B[0].get(bn) or [0, 0, 0])[i], t) for i in range(3)] for bn in bones}
    pose.update(GRIP); pose.update(LGRIP if (A[2] or B[2]) else LREL)
    rod = {'dir': [lerp(A[1]['dir'][i], B[1]['dir'][i], t) for i in range(3)], 'bend': [lerp(A[1]['bend'][i], B[1]['bend'][i], t) for i in range(3)],
           'k': lerp(A[1]['k'], B[1]['k'], t), **FAMILY[fam]}
    net = None
    if A[2] and B[2]:
        net = {'dir': [lerp(A[2]['dir'][i], B[2]['dir'][i], t) for i in range(3)], 'len': lerp(A[2]['len'], B[2]['len'], t), 'normal': [0, 1, 0],
               'kind': A[2]['kind'] if t < .5 else B[2]['kind']}
    return {'pose': pose, 'rod': rod, 'net': net}


def grade(im):
    rgb = im.convert('RGB'); rgb = ImageEnhance.Contrast(rgb).enhance(1.06); rgb = ImageEnhance.Color(rgb).enhance(1.08)
    rgb = rgb.filter(ImageFilter.UnsharpMask(radius=1.2, percent=55, threshold=2)); out = rgb.convert('RGBA'); out.putalpha(im.getchannel('A')); return out


def open_page(p):
    b = p.chromium.launch(args=ARGS); pg = b.new_page()
    pg.goto('http://localhost:8790/render.html'); pg.wait_for_function('window.ready===true', timeout=60000)
    pg.evaluate("o => setup(o)", {'model': 'm10/Male_Adult_10.fbx', 'prefix': 'm024'})
    pg.evaluate("shootFix(o)", CAM) if False else None
    return b, pg


def render(pg, st):
    pg.evaluate('resetPose()')
    pg.evaluate('p => pose(p)', st['pose'])
    pg.evaluate('o => setRod(o)', st.get('rod'))
    pg.evaluate('o => setNet(o)', st.get('net'))
    url = pg.evaluate('o => shootFix(o)', {**CAM, 'az': st.get('az', 180)})
    im = grade(Image.open(io.BytesIO(base64.b64decode(url.split(',')[1]))).convert('RGBA'))
    tip = pg.evaluate(f'R.rodTip ? ptScreen(R.rodTip, {W}, {H}) : null')
    net = pg.evaluate(f'R.netTop ? ptScreen(R.netTop, {W}, {H}) : null')
    feet = pg.evaluate(f'feetScreen({W}, {H})')
    return im, tip, net, feet


def sheet(items, out, cw=300):
    ch = int(cw * H / W * .95)
    img = Image.new('RGB', (cw * min(len(items), 8), ch * ((len(items) + 7) // 8)), (50, 110, 130))
    for i, (lab, im, tip, net) in enumerate(items):
        k = cw / W
        bg = Image.new('RGBA', im.size, (50, 110, 130, 255)); bg.alpha_composite(im)
        d = ImageDraw.Draw(bg)
        if tip: d.ellipse((tip[0] - 9, tip[1] - 9, tip[0] + 9, tip[1] + 9), fill='red')
        if net: d.ellipse((net[0] - 9, net[1] - 9, net[0] + 9, net[1] + 9), fill='yellow')
        sm = bg.resize((cw, int(H * k))).crop((0, int(H * k) - ch, cw, int(H * k)))
        ImageDraw.Draw(sm).text((4, 4), str(lab), fill='white')
        img.paste(sm.convert('RGB'), ((i % 8) * cw, (i // 8) * ch))
    img.save(out)


if __name__ == '__main__':
    mode = sys.argv[1]
    with sync_playwright() as p:
        b, pg = open_page(p)
        if mode == 'probe':
            P = json.load(open(sys.argv[2])); items = []
            for lab, st in P.items():
                st['pose'] = {**st.get('pose', {})}
                im, tip, net, feet = render(pg, st); items.append((lab, im, tip, net))
            sheet(items, sys.argv[3])

        elif mode == 'keys':   # preview the keyframes only
            fam = sys.argv[2]; items = []
            for n in sorted(KEY):
                im, tip, net, feet = render(pg, state_at(n, fam)); items.append((n, im, tip, net))
            sheet(items, sys.argv[3])
        elif mode == 'render':
            fam = sys.argv[2]; d = f'/home/claude/char3d/out/anim/{fam}/'; os.makedirs(d, exist_ok=True)
            meta = {'scale': SCALE, 'frames': {}}
            for n in PICK:
                st = state_at(n, fam)
                im, tip, net, feet = render(pg, st)
                im.save(d + f'{n:04d}.png')
                kind = st['net']['kind'] if st['net'] else 0
                meta['frames'][str(n)] = {'tip': tip, 'net': net, 'kind': kind}
                meta['feetY'] = feet[1]
            json.dump(meta, open(d + 'meta.json', 'w'))
            print('done', fam, len(PICK))
        b.close()
