"""Male angler walk cycle v2 (官方 2026-11: 走路腳怪怪的).
Joint angles follow standard sagittal gait curves (hip / knee / ankle vs gait phase, heel strike at 0),
the lowest foot is kept on the ground every frame, and the stance foot's travel is measured so the game
can match the step rate to the walking speed (no foot sliding).
-> out/boy-walk.png strip + out/boy-walk.json  (python3 walk2.py [az] [frames])"""
import base64, io, json, math, sys
from playwright.sync_api import sync_playwright
from PIL import Image, ImageEnhance, ImageFilter
ARGS = ['--use-gl=angle', '--use-angle=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist', '--enable-unsafe-swiftshader']
OUT = sys.argv[3] if len(sys.argv) > 3 else '/home/claude/char3d/out/'
AZ = float(sys.argv[1]) if len(sys.argv) > 1 else 80
N = int(sys.argv[2]) if len(sys.argv) > 2 else 16
GRIP = {}
for f in '1234':
    GRIP[f'R_Finger{f}'] = [0, 0, 70]; GRIP[f'R_Finger{f}1'] = [0, 0, 80]; GRIP[f'R_Finger{f}2'] = [0, 0, 60]
PV = float(__import__('os').environ.get('PV', 3))
# NOROD=1: walking without the rod (官方 2026-11-19: 男生走路也套用女孩的走法 — side view, rod put away, both arms swing)
NOROD = __import__('os').environ.get('NOROD', '1') == '1'
EF = float(__import__('os').environ.get('EF', -.45))   # elbow bend direction
MODEL, PREFIX = 'm10/Male_Adult_10.fbx', 'm024'
# (phase, degrees); hip + = flexion (leg forward), knee + = flexion, ankle + = toe down
HIP = [(0, 26), (.12, 22), (.3, 6), (.5, -12), (.6, -6), (.73, 16), (.87, 28)]
KNEE = [(0, 3), (.13, 15), (.3, 5), (.45, 4), (.6, 36), (.72, 58), (.85, 26), (.95, 3)]
ANK = [(0, -2), (.07, 5), (.3, -7), (.47, -9), (.6, 14), (.68, 10), (.8, -3), (.92, -4)]


def curve(K, t):
    """periodic Catmull-Rom through the key points"""
    t %= 1; n = len(K)
    i = max(j for j in range(n) if K[j][0] <= t)
    p = [K[(i + k) % n] for k in (-1, 0, 1, 2)]
    t0, t1 = p[1][0], p[2][0] + (1 if i + 1 >= n else 0)
    u = (t - t0) / (t1 - t0)
    a, b, c, d = (q[1] for q in p)
    return .5 * ((2 * b) + (-a + c) * u + (2 * a - 5 * b + 4 * c - d) * u * u + (-a + 3 * b - 3 * c + d) * u ** 3)


def pose_at(ph):
    L, R = ph, ph + .5
    hl, hr = curve(HIP, L), curve(HIP, R)
    s = math.sin(2 * math.pi * ph)
    return {
        'L_Thigh': [0, 0, hl], 'R_Thigh': [0, 0, hr],
        # on this rig a NEGATIVE calf angle bends the knee backward (positive bent it forward: the old walk's bug),
        # and a positive foot angle lifts the toe
        'L_Calf': [0, 0, -curve(KNEE, L)], 'R_Calf': [0, 0, -curve(KNEE, R)],
        'L_Foot': [0, 0, -curve(ANK, L)], 'R_Foot': [0, 0, -curve(ANK, R)],
        # left arm swings against the left leg; right hand keeps the rod
        **({'L_UpperArm': [0, 41, -4 - .8 * (hr - 8)], 'L_Forearm': [0, 0, EF * (12 + .25 * max(0, hr - 8))],
             'L_Hand': [0, 0, 0]} if NOROD else {'L_UpperArm': [0, 0, 34 + .75 * (hl - 7)], 'L_Forearm': [0, 0, -14 - 6 * max(0, (7 - hl) / 20)]}),
        **({'R_UpperArm': [0, -41, -4 - .8 * (hl - 8)], 'R_Forearm': [0, 0, EF * (12 + .25 * max(0, hl - 8))]} if NOROD else
           {'R_UpperArm': [0, 0, -12], 'R_Forearm': [0, 0, -68]}),
        'Pelvis': [0, -PV * s, 0], 'Spine1': [0, PV * 1.2 * s, 0], **({} if NOROD else GRIP)}


def grade(im):
    rgb = im.convert('RGB'); rgb = ImageEnhance.Contrast(rgb).enhance(1.06); rgb = ImageEnhance.Color(rgb).enhance(1.08)
    rgb = rgb.filter(ImageFilter.UnsharpMask(radius=1.2, percent=55, threshold=2)); out = rgb.convert('RGBA'); out.putalpha(im.getchannel('A')); return out


SHOOT = """o => { const T = R.THREE; R.renderer.setSize(o.w, o.h, false);
  const by = n => { const v = new T.Vector3(); R.bones[n].getWorldPosition(v); return v; };
  if (!R.rest) { R.model.position.y = 0; R.model.updateMatrixWorld(true); const box = new T.Box3().setFromObject(R.model);
    R.rest = { c: box.getCenter(new T.Vector3()), min: box.min.y, h: box.getSize(new T.Vector3()).y, y0: R.model.position.y,
               feet: ['L_Foot', 'L_Toe0', 'R_Foot', 'R_Toe0'].map(n => by(n).y) }; }
  // keep the lowest foot point on the ground
  R.model.position.y = R.rest.y0; R.model.updateMatrixWorld(true);
  const ys = ['L_Foot', 'L_Toe0', 'R_Foot', 'R_Toe0'].map((n, i) => by(n).y - R.rest.feet[i]);
  R.model.position.y = R.rest.y0 - Math.min(...ys); R.model.updateMatrixWorld(true);
  const cam = new T.PerspectiveCamera(13.5, o.w / o.h, 10, 4000); const az = o.az * Math.PI / 180, el = 12 * Math.PI / 180, d = 1000;
  const tg = new T.Vector3(R.rest.c.x, R.rest.min + R.rest.h * .5, R.rest.c.z);
  cam.position.set(tg.x + Math.sin(az) * Math.cos(el) * d, tg.y + Math.sin(el) * d, tg.z + Math.cos(az) * Math.cos(el) * d); cam.lookAt(tg); R.cam = cam;
  R.renderer.render(R.scene, cam);
  const sc = n => { const v = by(n); v.project(cam); return [(v.x * .5 + .5) * o.w, (-v.y * .5 + .5) * o.h]; };
  return { url: R.renderer.domElement.toDataURL('image/png'), hand: sc('R_Hand'), lt: sc('L_Toe0'), rt: sc('R_Toe0'), lf: sc('L_Foot'), rf: sc('R_Foot') }; }"""

if __name__ == '__main__':
    with sync_playwright() as p:
        b = p.chromium.launch(args=ARGS); pg = b.new_page()
        pg.goto('http://localhost:8790/render.html'); pg.wait_for_function('window.ready===true', timeout=60000)
        pg.evaluate('o => setup(o)', {'model': MODEL, 'prefix': PREFIX})
        W, H = 640, 1000
        frames, info = [], []
        for i in range(N):
            pg.evaluate('resetPose()'); pg.evaluate('p => pose(p)', pose_at(i / N))
            r = pg.evaluate(SHOOT, {'w': W, 'h': H, 'az': AZ})
            frames.append(grade(Image.open(io.BytesIO(base64.b64decode(r['url'].split(',')[1]))).convert('RGBA'))); info.append(r)
        b.close()
    bb = [f.getchannel('A').getbbox() for f in frames]
    box = (min(x[0] for x in bb) - 4, min(x[1] for x in bb) - 4, max(x[2] for x in bb) + 4, max(x[3] for x in bb) + 2)
    fw, fh = box[2] - box[0], box[3] - box[1]
    strip = Image.new('RGBA', (fw * N, fh))
    for i, f in enumerate(frames): strip.paste(f.crop(box), (i * fw, 0))
    strip.save(OUT + 'boy-walk.png')
    # stance-foot travel (left foot, phase .1 -> .5, mid stance) in sprite px per cycle
    i0, i1 = round(.1 * N), round(.5 * N)
    lf = [(r['lf'][0] + r['lt'][0]) / 2 for r in info]
    travel = (lf[i1] - lf[i0]) / ((i1 - i0) / N)
    json.dump({'n': N, 'fw': fw, 'fh': fh, 'hands': [[round(r['hand'][0] - box[0], 1), round(r['hand'][1] - box[1], 1)] for r in info],
               'stanceTravel': round(travel, 1), 'lf': [round(x - box[0], 1) for x in lf]}, open(OUT + 'boy-walk.json', 'w'))
    prev = strip.resize((strip.width // 3, strip.height // 3)); bg = Image.new('RGBA', prev.size, (90, 130, 160, 255)); bg.alpha_composite(prev)
    bg.save('/tmp/claude-0/-home-claude/532eeb54-5e76-51ac-a797-997d04cd23db/scratchpad/walk2.png'); print(fw, fh, 'travel/cycle', round(travel, 1), [round(x) for x in lf])
