"""Render the male angler sprite set.
Outputs (in out/): boy-idle.png, boy-fight.png (back view), boy-catch.png (front, holding gripper),
boy-head.png (portrait), and boy.json with hand / gripper positions in image pixels.
"""
import base64, io, json, os, sys
from playwright.sync_api import sync_playwright
from PIL import Image, ImageFilter, ImageEnhance

ARGS = ['--use-gl=angle', '--use-angle=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist', '--enable-unsafe-swiftshader']
OUT = '/home/claude/char3d/out/'
os.makedirs(OUT, exist_ok=True)

GRIP = {}
for f in '1234':
    GRIP[f'R_Finger{f}'] = [0, 0, 70]; GRIP[f'R_Finger{f}1'] = [0, 0, 80]; GRIP[f'R_Finger{f}2'] = [0, 0, 60]
LREL = {}
for f in '1234':
    LREL[f'L_Finger{f}'] = [0, 0, -25]; LREL[f'L_Finger{f}1'] = [0, 0, -35]

POSES = {
    'idle': {'R_UpperArm': [0, -38, 8], 'R_Forearm': [0, -25, -25], 'L_UpperArm': [0, 38, 4], 'L_Forearm': [0, 10, -10], **GRIP, **LREL},
    'fight': {'R_UpperArm': [0, 20, -20], 'R_Forearm': [0, 85, 0], 'L_UpperArm': [0, 32, -6], 'L_Forearm': [0, 30, -25], 'Spine1': [0, 0, 3], **GRIP, **LREL},
}
HAT = {'dy': -5.5, 'dz': -0.5, 'tilt': -4, 'scale': 1.17}


def shot(pg, opts):
    url = pg.evaluate('o => shoot(o)', opts)
    return Image.open(io.BytesIO(base64.b64decode(url.split(',')[1]))).convert('RGBA')


def grade(im):
    """Match the warm, slightly cyan-tinted lighting of the original renders."""
    rgb = im.convert('RGB')
    rgb = ImageEnhance.Contrast(rgb).enhance(1.06)
    rgb = ImageEnhance.Color(rgb).enhance(1.08)
    rgb = rgb.filter(ImageFilter.UnsharpMask(radius=1.2, percent=55, threshold=2))
    out = rgb.convert('RGBA'); out.putalpha(im.getchannel('A'))
    return out


with sync_playwright() as p:
    b = p.chromium.launch(args=ARGS)
    pg = b.new_page()
    errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto('http://localhost:8790/render.html'); pg.wait_for_function('window.ready===true', timeout=60000)
    pg.evaluate("setup({model:'m05/Male_Adult_05.fbx', prefix:'m009'})")
    pg.evaluate('h => addHat(h)', HAT)
    meta = {}
    # ---- back views: one fixed camera for both poses so the feet line up
    W, H = 1000, 1400
    cam = {'w': W, 'h': H, 'az': 180, 'el': 14, 'dist': 1000, 'fov': 13.5, 'ty': .5}
    for name, ps in POSES.items():
        pg.evaluate('resetPose()'); pg.evaluate('p => pose(p)', ps)
        im = grade(shot(pg, cam))
        hand = pg.evaluate(f'boneScreen("R_Hand", {W}, {H})')
        im.save(OUT + f'boy-{name}-full.png')
        meta[name] = {'hand': hand}
    # common crop box over both poses
    boxes = [Image.open(OUT + f'boy-{n}-full.png').getchannel('A').getbbox() for n in POSES]
    bx = (min(x[0] for x in boxes) - 4, min(x[1] for x in boxes) - 4, max(x[2] for x in boxes) + 4, max(x[3] for x in boxes) + 2)
    for n in POSES:
        Image.open(OUT + f'boy-{n}-full.png').crop(bx).save(OUT + f'boy-{n}.png')
        h = meta[n]['hand']; meta[n]['hand'] = [round(h[0] - bx[0], 1), round(h[1] - bx[1], 1)]
    meta['backBox'] = [bx[2] - bx[0], bx[3] - bx[1]]
    # ---- front view holding the gripper (catch screen)
    pg.evaluate('resetPose()')
    pg.evaluate('p => pose(p)', {'R_UpperArm': [0, -10, -55], 'R_Forearm': [0, 0, -95], 'R_Hand': [0, 0, 0],
                                  'L_UpperArm': [0, 52, 18], 'L_Forearm': [0, 0, 75], 'L_Hand': [0, 25, 0], **GRIP})
    pg.evaluate('h => addHat(h)', {'dy': -10.0, 'dz': -1.5, 'tilt': -13, 'scale': 1.15})
    pg.evaluate('addGripper()')
    FW, FH = 900, 1500
    im = grade(shot(pg, {'w': FW, 'h': FH, 'az': 8, 'el': 4, 'dist': 1000, 'fov': 13.5, 'ty': .5}))
    tip = pg.evaluate(f'objScreen(R.gripTip, {FW}, {FH})')
    bb = im.getchannel('A').getbbox(); im = im.crop(bb)
    im.save(OUT + 'boy-catch.png')
    meta['catch'] = {'tip': [round(tip[0] - bb[0], 1), round(tip[1] - bb[1], 1)], 'size': list(im.size)}
    # ---- head portrait for the HUD
    pg.evaluate('resetPose()')
    if True:
        pg.evaluate('R.grip && R.grip.parent.remove(R.grip)')
    hp = pg.evaluate("(()=>{const v=new R.THREE.Vector3(); R.bones.Head.getWorldPosition(v); return v.toArray()})()")
    url = pg.evaluate("""(hp) => { const T=R.THREE; R.renderer.setSize(460, 520, false);
        const cam = new T.PerspectiveCamera(16, 460/520, 5, 4000);
        cam.position.set(hp[0] + 55, hp[1] + 16, hp[2] + 215); cam.lookAt(hp[0] + 2, hp[1] + 9, hp[2]);
        R.cam = cam; R.renderer.render(R.scene, cam); return R.renderer.domElement.toDataURL('image/png'); }""", hp)
    head = grade(Image.open(io.BytesIO(base64.b64decode(url.split(',')[1]))).convert('RGBA'))
    head.save(OUT + 'boy-head.png')
    json.dump(meta, open(OUT + 'boy.json', 'w'), indent=1)
    print(json.dumps(meta), errs[:3])
    b.close()
