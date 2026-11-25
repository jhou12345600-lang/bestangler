"""Boy reel-cranking loops (官方 2026-11-25：拋出後收線、中魚後搏魚都要有捲線動作；路亞竿/投竿不能用手竿的動作).
frames 125-140 = 收線 retrieve (rod forward and low), 141-156 = 搏魚 crank fight (rod raised and bent).
The left palm follows the reel's turning handle (numeric IK each frame).
python3 anim_reel.py probe out.png        contact sheet (back + side views)
python3 anim_reel.py render FAMILY        out/anim/<FAMILY>R/NNNN.png + meta.json   (FAMILY: C, L)"""
import base64, io, json, math, os, sys
from playwright.sync_api import sync_playwright
from PIL import Image, ImageDraw
sys.argv_ = sys.argv; sys.argv = ['x']
from anim_boy import ARGS, W, H, CAM, SCALE, GRIP, FAMILY, grade
sys.argv = sys.argv_
N = 16
import os as _os
# left hand closed round the handle knob (finger curl sign checked on this rig: LF)
LF = float(_os.environ.get('LF', 1))
LGRIP = {}
for _f in '1234':
    LGRIP[f'L_Finger{_f}'] = [0, 0, 55 * LF]; LGRIP[f'L_Finger{_f}1'] = [0, 0, 75 * LF]; LGRIP[f'L_Finger{_f}2'] = [0, 0, 55 * LF]
LGRIP['L_Finger0'] = [0, 0, 20 * LF]; LGRIP['L_Finger01'] = [0, 0, 25 * LF]
TW = float(_os.environ.get('TW', 5))
# 官方 2026-11-25：男角捲線動作跟女角一樣 — rod held up on the right with both hands at head height, the reel beside
# the head and the left hand reaching across to turn the handle. rh: right palm target relative to the right shoulder.
POSES = {
    'retrieve': {'body': {'Pelvis': [0, TW * .4, 0], 'Spine1': [0, TW * .6, 0], 'Neck': [0, -TW * .4, 3]}, 'rh': [-6, 20, 24], 'rinit': [0, 20, -20, 0, 85, -5],
                 'rod': {'dir': [-.34, 1, .42], 'bend': [.2, -.4, 1], 'k': .12}},
    'fight': {'body': {'Pelvis': [0, TW * .4, 0], 'Spine1': [0, TW * .6, -6], 'Neck': [0, -TW * .4, 7]}, 'rh': [-7, 24, 20], 'rinit': [0, 20, -20, 0, 85, -5],
              'rod': {'dir': [-.36, 1, .3], 'bend': [.3, -.35, 1], 'k': .42}},
}
BOB = {'retrieve': 1.0, 'fight': 2.2}


def open_page(p):
    b = p.chromium.launch(args=ARGS); pg = b.new_page()
    pg.goto('http://localhost:8790/render.html'); pg.wait_for_function('window.ready===true', timeout=60000)
    pg.evaluate("o => setup(o)", {'model': 'm10/Male_Adult_10.fbx', 'prefix': 'm024'})
    return b, pg


BONE = """n => { const v = new R.THREE.Vector3(); R.bones[n].getWorldPosition(v); return v.toArray(); }"""


def state(pg, kind, i, fam, prevL):
    P = POSES[kind]; ph = i / N; a = 2 * math.pi * ph
    bob = BOB[kind]
    body = {k: list(v) for k, v in P['body'].items()}
    body['Spine1'] = [body['Spine1'][0], body['Spine1'][1] + math.sin(a) * bob * .6, body['Spine1'][2] + math.cos(a) * bob * .4]
    pg.evaluate('resetPose()'); pg.evaluate('p => pose(p)', {**body, **GRIP, **LGRIP})
    sh = pg.evaluate(BONE, 'R_UpperArm')
    rh = [sh[0] + P['rh'][0], sh[1] + P['rh'][1] + math.sin(a) * bob * .5, sh[2] + P['rh'][2]]
    r = pg.evaluate('a => ikArm("R", a[0], a[1], {reg: .003})', [rh, P['rinit']])
    rod = {**P['rod'], **FAMILY[fam], 'crank': a}
    rod['k'] = rod['k'] * (1 + .06 * math.sin(a * 2))      # the rod tip pumps a little with each turn
    pg.evaluate('o => setRod(o)', rod)
    knob = pg.evaluate('R.knob')
    starts = [prevL] if prevL else []
    starts += [[0, 20, -20, 0, 85, -5], [0, 35, -35, 0, 60, -20], [20, 10, -40, 0, 100, 0], [-20, 30, -10, 0, 70, -30]]
    best = None
    for st0 in starts:
        l = pg.evaluate('a => ikArm("L", a[0], a[1], {reg: .00005, steps: [24, 12, 6, 3, 1.5, .7, .3, .15]})', [knob, st0])
        if best is None or l['err'] < best['err'] - .3: best = l
        if best['err'] < .6: break
    l = best; pg.evaluate('q => pose({L_UpperArm: q.slice(0, 3), L_Forearm: q.slice(3, 6)})', l['p'])
    pg.evaluate('o => setRod(o)', rod)   # rebuild after the final pose (rod follows the right hand)
    return r, l


def shoot(pg, az=180):
    url = pg.evaluate('o => shootFix(o)', {**CAM, 'az': az})
    im = grade(Image.open(io.BytesIO(base64.b64decode(url.split(',')[1]))).convert('RGBA'))
    tip = pg.evaluate(f'R.rodTip ? ptScreen(R.rodTip, {W}, {H}) : null')
    return im, tip


if __name__ == '__main__':
    mode = sys.argv[1]
    with sync_playwright() as p:
        b, pg = open_page(p)
        if mode == 'probe':
            tiles = []
            for kind in ['retrieve', 'fight']:
                prev = None
                for i in [0, 4, 8, 12]:
                    r, l = state(pg, kind, i, 'L', prev); prev = l['p']
                    for az in ([180, 120] if i == 0 else [180]):
                        im, tip = shoot(pg, az)
                        bg = Image.new('RGBA', im.size, (50, 110, 130, 255)); bg.alpha_composite(im)
                        t = bg.crop((300, 250, 900, 1150)).resize((400, 600)); ImageDraw.Draw(t).text((4, 4), f'{kind} {i} az{az} eL{l["err"]:.1f} eR{r["err"]:.1f}', fill='white'); tiles.append(t)
            o = Image.new('RGB', (400 * len(tiles), 600)); [o.paste(t.convert('RGB'), (k * 400, 0)) for k, t in enumerate(tiles)]; o.save(sys.argv[2])
        elif mode == 'zoom':   # close-up of the hands and reel through one turn
            tiles = []; prev = None; kind = sys.argv[3] if len(sys.argv) > 3 else 'retrieve'
            for rep in range(2):
                for i in range(N):
                    r, l = state(pg, kind, i, 'L', prev); prev = l['p']
                    if rep == 0 or i % 2: continue
                    im, tip = shoot(pg); bg = Image.new('RGBA', im.size, (50, 110, 130, 255)); bg.alpha_composite(im)
                    k = pg.evaluate(f'ptScreen(R.knob, {W}, {H})')
                    t = bg.crop((int(k[0]) - 110, int(k[1]) - 110, int(k[0]) + 110, int(k[1]) + 110)).resize((330, 330))
                    ImageDraw.Draw(t).text((4, 4), f'{i} eL{l["err"]:.1f}', fill='white'); tiles.append(t)
            o = Image.new('RGB', (330 * len(tiles), 330)); [o.paste(t.convert('RGB'), (k * 330, 0)) for k, t in enumerate(tiles)]; o.save(sys.argv[2])
        elif mode == 'render':
            fam = sys.argv[2]; d = f'/home/claude/char3d/out/anim/{fam}R/'; os.makedirs(d, exist_ok=True)
            meta = {'scale': SCALE, 'frames': {}}
            pg.evaluate('resetPose()'); pg.evaluate('o => setRod(o)', None); im, _ = shoot(pg); im.save(d + 'ref.png')   # standing, for feet/centre
            for kind, base in [('retrieve', 125), ('fight', 141)]:
                prev = None
                for rep in range(2):            # second pass starts from a settled left arm so the loop closes
                    for i in range(N):
                        r, l = state(pg, kind, i, fam, prev); prev = l['p']
                        if rep == 1:
                            im, tip = shoot(pg); im.save(d + f'{base + i:04d}.png'); meta['frames'][str(base + i)] = {'tip': tip, 'net': None, 'kind': 0, 'errL': round(l['err'], 2)}
            json.dump(meta, open(d + 'meta.json', 'w')); print('done', fam, max(v['errL'] for v in meta['frames'].values()))
        b.close()
