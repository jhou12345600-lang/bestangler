"""Render the male angler's walk cycle (3/4 back view, facing screen-left) -> out/boy-walk.png strip + boy-walk.json"""
import base64, io, json, math, sys
from playwright.sync_api import sync_playwright
from PIL import Image, ImageEnhance, ImageFilter
ARGS = ['--use-gl=angle', '--use-angle=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist', '--enable-unsafe-swiftshader']
OUT = '/home/claude/char3d/out/'
AZ = float(sys.argv[1]) if len(sys.argv) > 1 else 128
N = 8
GRIP = {}
for f in '1234':
    GRIP[f'R_Finger{f}'] = [0, 0, 70]; GRIP[f'R_Finger{f}1'] = [0, 0, 80]; GRIP[f'R_Finger{f}2'] = [0, 0, 60]
HAT = {'dy': -5.5, 'dz': -0.5, 'tilt': -4, 'scale': 1.17}
def grade(im):
    rgb = im.convert('RGB'); rgb = ImageEnhance.Contrast(rgb).enhance(1.06); rgb = ImageEnhance.Color(rgb).enhance(1.08)
    rgb = rgb.filter(ImageFilter.UnsharpMask(radius=1.2, percent=55, threshold=2)); out = rgb.convert('RGBA'); out.putalpha(im.getchannel('A')); return out
def pose_at(ph):
    s, c = math.sin(ph), math.cos(ph)
    th = 26 * s
    return {
        'L_Thigh': [0, 0, -th], 'R_Thigh': [0, 0, th],
        'L_Calf': [0, 0, 6 + 40 * max(0, c)], 'R_Calf': [0, 0, 6 + 40 * max(0, -c)],
        'L_Foot': [0, 0, -10 * max(0, c)], 'R_Foot': [0, 0, -10 * max(0, -c)],
        'L_UpperArm': [0, 0, 34 + 22 * s], 'L_Forearm': [0, 0, -12 - 8 * max(0, -s)],
        'R_UpperArm': [0, 0, -12], 'R_Forearm': [0, 0, -68],
        'Spine1': [0, 4 * s, 0], 'Pelvis': [0, -3 * s, 0], **GRIP}
with sync_playwright() as p:
    b = p.chromium.launch(args=ARGS); pg = b.new_page()
    pg.goto('http://localhost:8790/render.html'); pg.wait_for_function('window.ready===true', timeout=60000)
    pg.evaluate("setup({model:'m05/Male_Adult_05.fbx', prefix:'m009'})")
    pg.evaluate('h => addHat(h)', HAT)
    W, H = 900, 1400
    frames, hands = [], []
    for i in range(N):
        pg.evaluate('resetPose()'); pg.evaluate('p => pose(p)', pose_at(2 * math.pi * i / N))
        # fixed framing: shoot() frames the bounding box, which changes with the pose; use the rest box instead
        url = pg.evaluate("""o => { const T=R.THREE; R.renderer.setSize(o.w,o.h,false);
          if(!R.fixC){ const box=new T.Box3().setFromObject(R.model); R.fixC=box.getCenter(new T.Vector3()); R.fixMin=box.min.y; R.fixH=box.getSize(new T.Vector3()).y; }
          const cam=new T.PerspectiveCamera(13.5,o.w/o.h,10,4000); const az=o.az*Math.PI/180, el=12*Math.PI/180, d=1000;
          const tg=new T.Vector3(R.fixC.x, R.fixMin+R.fixH*.5, R.fixC.z);
          cam.position.set(tg.x+Math.sin(az)*Math.cos(el)*d, tg.y+Math.sin(el)*d, tg.z+Math.cos(az)*Math.cos(el)*d); cam.lookAt(tg); R.cam=cam;
          R.renderer.render(R.scene,cam); return R.renderer.domElement.toDataURL('image/png'); }""", {'w': W, 'h': H, 'az': AZ})
        frames.append(grade(Image.open(io.BytesIO(base64.b64decode(url.split(',')[1]))).convert('RGBA')))
        hands.append(pg.evaluate(f'boneScreen("R_Hand", {W}, {H})'))
    b.close()
bb = [f.getchannel('A').getbbox() for f in frames]
box = (min(x[0] for x in bb) - 4, min(x[1] for x in bb) - 4, max(x[2] for x in bb) + 4, max(x[3] for x in bb) + 2)
fw, fh = box[2] - box[0], box[3] - box[1]
strip = Image.new('RGBA', (fw * N, fh))
for i, f in enumerate(frames): strip.paste(f.crop(box), (i * fw, 0))
strip.save(OUT + 'boy-walk.png')
# feet centre (x) from the rest frame silhouette bottom
json.dump({'n': N, 'fw': fw, 'fh': fh, 'hands': [[round(h[0] - box[0], 1), round(h[1] - box[1], 1)] for h in hands]}, open(OUT + 'boy-walk.json', 'w'))
prev = strip.resize((strip.width // 3, strip.height // 3)); bg = Image.new('RGBA', prev.size, 'white'); bg.alpha_composite(prev)
bg.save('/tmp/claude-0/-home-claude/532eeb54-5e76-51ac-a797-997d04cd23db/scratchpad/walk.png'); print(fw, fh)
