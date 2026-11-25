"""Boy reel-cranking loops (官方 2026-11-25：拋出後收線、中魚後搏魚都要有捲線動作；路亞竿/投竿不能用手竿的動作).
frames 125-140 = 收線 retrieve (rod forward and low), 141-156 = 搏魚 crank fight (rod raised and bent).
The left palm follows the reel's turning handle (numeric IK each frame).
python3 anim_reel.py probe out.png        contact sheet (back + side views)
python3 anim_reel.py render FAMILY        out/anim/<FAMILY>R/NNNN.png + meta.json   (FAMILY: C, L)"""
import base64, io, json, math, os, sys
from playwright.sync_api import sync_playwright
from PIL import Image, ImageDraw
sys.argv_ = sys.argv; sys.argv = ['x']
from anim_boy import ARGS, W, H, CAM, SCALE, GRIP, LGRIP, FAMILY, grade
sys.argv = sys.argv_
N = 16
import os as _os
TW = float(_os.environ.get('TW', 12))
POSES = {
    # rod out over the water at about 30 degrees on the right side, so the reel and the cranking left hand show beside the body
    'retrieve': {'body': {'Pelvis': [0, TW * .4, 0], 'Spine1': [0, TW * .6, 2], 'Neck': [0, -TW * .5, 4]}, 'rh': [-27, 21, 20], 'rinit': [0, 10, -10, 0, 60, -10],
                 'rod': {'dir': [-.18, .5, 1], 'bend': [0, -1, .25], 'k': .07}},
    # fighting: rod raised high and bent hard toward the fish, leaning back a little
    'fight': {'body': {'Pelvis': [0, TW * .45, 0], 'Spine1': [0, TW * .65, -7], 'Neck': [0, -TW * .55, 7]}, 'rh': [-28, 25, 21], 'rinit': [0, 10, -10, 0, 60, -10],
              'rod': {'dir': [-.26, .95, .72], 'bend': [.15, -.45, 1], 'k': .4}},
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
    pel = pg.evaluate(BONE, 'Pelvis')
    rh = [pel[0] + P['rh'][0], pel[1] + P['rh'][1] + math.sin(a) * bob * .5, pel[2] + P['rh'][2]]
    r = pg.evaluate('a => ikArm("R", a[0], a[1], {reg: .003})', [rh, P['rinit']])
    rod = {**P['rod'], **FAMILY[fam], 'crank': a}
    rod['k'] = rod['k'] * (1 + .06 * math.sin(a * 2))      # the rod tip pumps a little with each turn
    pg.evaluate('o => setRod(o)', rod)
    knob = pg.evaluate('R.knob')
    l = pg.evaluate('a => ikArm("L", a[0], a[1], {reg: .0004})', [knob, prevL or [0, 25, -30, 0, 40, -30]])
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
                        t = bg.crop((300, 450, 900, 1350)).resize((400, 600)); ImageDraw.Draw(t).text((4, 4), f'{kind} {i} az{az} eL{l["err"]:.1f} eR{r["err"]:.1f}', fill='white'); tiles.append(t)
            o = Image.new('RGB', (400 * len(tiles), 600)); [o.paste(t.convert('RGB'), (k * 400, 0)) for k, t in enumerate(tiles)]; o.save(sys.argv[2])
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
