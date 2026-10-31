"""Build web assets for 神釣手 2D remaster.
python -I build_assets.py RAW_IMAGES_DIR WORK_DIR OUT_DIR
Every manifest entry gives sizes in logical px (the 720x1280 design space) plus `s`
(texture pixels per logical px).
"""
import sys, os, re, json, glob
import numpy as np
from PIL import Image, ImageFilter

R, W, OUT = sys.argv[1].rstrip("/") + "/", sys.argv[2].rstrip("/") + "/", sys.argv[3].rstrip("/") + "/"
os.makedirs(OUT + "img", exist_ok=True)
ESR_A = W + "esr_out/"
ESR_C = W + "esr_outC/"
man = {"img": {}, "atlas": [], "ui": {}, "anim": {}, "meta": {}}
Q = 86


def save_webp(im, name, q=Q):
    p = OUT + "img/" + name + ".webp"
    if im.mode == "RGBA" and im.getchannel("A").getextrema()[0] == 255:
        im = im.convert("RGB")
    im.save(p, "WEBP", quality=q, method=5)
    return "img/" + name + ".webp"


def up2(im):
    """Lanczos 2x with mild unsharp mask, alpha-safe."""
    im = im.convert("RGBA")
    big = im.resize((im.width * 2, im.height * 2), Image.LANCZOS)
    rgb = big.convert("RGB").filter(ImageFilter.UnsharpMask(radius=1.6, percent=60, threshold=2))
    rgb.putalpha(big.getchannel("A"))
    return rgb


def esr_or_up(esr_path, raw_path):
    if esr_path and os.path.exists(esr_path):
        return Image.open(esr_path).convert("RGBA")
    return up2(Image.open(raw_path))


def single(key, im, s, q=Q):
    f = save_webp(im, key, q)
    man["img"][key] = {"f": f, "w": round(im.width / s, 2), "h": round(im.height / s, 2), "s": s}


# ---------- backgrounds / big singles (2x) ----------
for p in range(1, 5):
    for part in ["bg-top", "bg-water", "wood-grass"]:
        single(f"pond{p}-{part}", esr_or_up(f"{ESR_A}pond{p}-{part}.png", f"{R}fishing/pond{p}/{part}.png"), 2)
    if os.path.exists(f"{R}fishing/pond{p}/fog.png"):
        single(f"pond{p}-fog", up2(Image.open(f"{R}fishing/pond{p}/fog.png")), 2, 80)
for c in ["cloud1", "cloud2", "cloud3"]:
    single(f"pond-{c}", esr_or_up(f"{ESR_A}pond1-{c}.png", f"{R}fishing/pond1/{c}.png"), 2)
single("cover-bg", esr_or_up(ESR_A + "cover-bg.png", R + "cover/m-cover-bg.jpg"), 2, 84)
for n in ["BG-sky", "BG-water", "BG-shore", "BG-boat", "BG-cloud1", "BG-cloud2", "UI-right-board", "UI-down-board", "win"]:
    single("catch-" + n, esr_or_up(f"{ESR_A}catch-{n}.png", f"{R}catch/{n}.png"), 2)
single("victory", esr_or_up(ESR_A + "victory.png", R + "fishing/victory.png"), 2)
single("victory-light", up2(Image.open(R + "fishing/victory-light.png")), 2)
single("win-lightwheel", up2(Image.open(R + "catch/win-lightwheel.png")), 2)
for g in ["girl-idle", "girl-fight"]:
    single(g, esr_or_up(f"{ESR_A}{g}.png", f"{W}{g}.png"), 2, 90)
man["meta"]["girlAnchor"] = json.load(open(W + "girl-anchor.json"))
mp = ESR_C + "lobby__new-map.png"
single("lobby-map", Image.open(mp).convert("RGB") if os.path.exists(mp) else Image.open(R + "lobby/new-map.jpg").convert("RGB"), 2 if os.path.exists(mp) else 1, 84)
for c in ["lobby-bg-cloud1", "lobby-bg-cloud2", "lobby-bg-cloud3"]:
    single(c, Image.open(f"{R}lobby/{c}.png").convert("RGBA"), 1)
single("girl-shadow", up2(Image.open(R + "fishing/girl/girl-shadow.png")), 2)
single("fight-bed", up2(Image.open(R + "fighting/bg-water-bed.png")), 2)
single("fight-surface", Image.open(R + "fighting/bg-water-surface.png").convert("RGBA"), 1)

# ---------- official underwater fight background (from the 2026 spec; HUD removed by tools/uwbg.py)
if os.path.exists(W + "uw-bg.png"):
    single("uw-bg", Image.open(W + "uw-bg.png").convert("RGB"), 1.5, 82)

# ---------- male angler (rendered from the MIT-licensed Microsoft Rocketbox avatar library) ----------
BOY = "/home/claude/char3d/out/"
if os.path.exists(BOY + "boy.json"):
    bj = json.load(open(BOY + "boy.json"))
    idle = Image.open(BOY + "boy-idle.png").convert("RGBA"); fight = Image.open(BOY + "boy-fight.png").convert("RGBA")
    W_, H_ = idle.size
    sb = H_ / 505.0                       # texture px per logical px: about the girl's on-screen height
    a = np.array(idle.getchannel("A")); legs = a[int(H_ * .6):]
    cols = np.where(legs.max(0) > 40)[0]; body_cx = (cols.min() + cols.max()) / 2
    ax_ = 392 - body_cx / sb; ay_ = 1266 - H_ / sb
    single("boy-idle", idle, sb, 90); single("boy-fight", fight, sb, 90)
    cat = Image.open(BOY + "boy-catch.png").convert("RGBA")
    sc_ = cat.size[1] / 870.0
    ca = np.array(cat.getchannel("A")); lc = np.where(ca[int(cat.size[1] * .6):].max(0) > 40)[0]
    single("boy-catch", cat, sc_, 88)
    head = Image.open(BOY + "boy-head.png").convert("RGBA")
    single("boy-head", head, 2, 88)
    # walk cycle strip (3/4 back view facing screen-left; mirrored when walking right)
    wj = json.load(open(BOY + "boy-walk.json")); ws = Image.open(BOY + "boy-walk.png").convert("RGBA")
    single("boy-walk", ws, sb, 88)
    wa = np.array(ws.crop((0, 0, wj["fw"], wj["fh"])).getchannel("A"))
    tc = np.where(wa[int(wj["fh"] * .2):int(wj["fh"] * .45)].max(0) > 40)[0]
    walk_meta = {"n": wj["n"], "fw": round(wj["fw"] / sb, 2), "fh": round(wj["fh"] / sb, 2), "cx": round((tc.min() + tc.max()) / 2 / sb, 1),
                 "hands": [[round(h[0] / sb, 1), round(h[1] / sb, 1)] for h in wj["hands"]]}
    man["meta"]["boy"] = {
        "anchor": {"x": round(ax_, 1), "y": round(ay_, 1), "w": round(W_ / sb, 1), "h": round(H_ / sb, 1)},
        "handIdle": [round(ax_ + bj["idle"]["hand"][0] / sb, 1), round(ay_ + bj["idle"]["hand"][1] / sb, 1)],
        "handFight": [round(ax_ + bj["fight"]["hand"][0] / sb, 1), round(ay_ + bj["fight"]["hand"][1] / sb, 1)],
        "catchW": round(cat.size[0] / sc_, 1), "catchH": round(cat.size[1] / sc_, 1),
        "catchCx": round(((lc.min() + lc.max()) / 2) / sc_, 1),
        "catchTip": [round(bj["catch"]["tip"][0] / sc_, 1), round(bj["catch"]["tip"][1] / sc_, 1)],
        "walk": walk_meta,
    }

# ---------- UI atlas (2x) ----------
UI_PATTERNS = ["fighting-top-UI/*.png", "fishing/*.[pP][nN][gG]", "top-UI/*.png", "*.png", "fishing/POP-catch/*.png",
               "fishing/POP-tackle/*.png", "lobby/pond-board/*.png", "lobby/button-*.png", "lobby/up-button-[!m]*.png",
               "lobby/up-button-missions.png", "tackle-icons/*/*.png", "catch/UI-*.png", "catch/button-*.png",
               "catch/coin-*.png", "lobby/shop/*.png", "lobby/tackle/*.png", "cover/*.png",
               "fishing/time-number*.png", "lobby/mine/*.png"]
SKIP = ("UI-right-board", "UI-down-board", "victory", "lobby-bg", "button-locky-lightwheel", "loading-reel-motion")
pieces = []
seen = set()
for pat in UI_PATTERNS:
    for f in sorted(glob.glob(R + pat)):
        rel = os.path.relpath(f, R)
        if any(s in rel for s in SKIP) or rel in seen or rel.endswith(".psd"):
            continue
        seen.add(rel)
        key = re.sub(r"\.(png|PNG)$", "", rel)
        esr = ESR_C + rel.replace("/", "__")
        esr = re.sub(r"\.(png|PNG)$", ".png", esr)
        im = esr_or_up(esr, f)
        bb = im.getchannel("A").getbbox()
        if not bb:
            continue
        pieces.append((key, im, (im.width, im.height)))


def pack(items, maxw=4096, pad=2):
    """Shelf packer. items: (key, im). returns list of atlases [(img, {key:(x,y,w,h)})]."""
    items = sorted(items, key=lambda t: -t[1].height)
    atlases = []
    cur, rects, x, y, rowh = None, {}, pad, pad, 0
    used_h = 0

    def flush():
        if rects:
            atlases.append((cur.crop((0, 0, maxw, used_h + pad)), dict(rects)))

    cur = Image.new("RGBA", (maxw, maxw))
    for key, im in items:
        w, h = im.size
        if x + w + pad > maxw:
            x, y, rowh = pad, y + rowh + pad, 0
        if y + h + pad > maxw:
            flush()
            cur, rects, x, y, rowh, used_h = Image.new("RGBA", (maxw, maxw)), {}, pad, pad, 0, 0
        cur.paste(im, (x, y))
        rects[key] = (x, y, w, h)
        used_h = max(used_h, y + h)
        x += w + pad
        rowh = max(rowh, h)
    flush()
    return atlases


for i, (img, rects) in enumerate(pack([(k, im) for k, im, _ in pieces])):
    f = save_webp(img, f"ui{i}", 90)
    man["atlas"].append(f)
    for k, (x, y, w, h) in rects.items():
        man["ui"][k] = {"a": i, "x": x, "y": y, "w": w, "h": h, "s": 2}


# ---------- animations ----------
def anim(key, frames, s, cols=None, maxw=4096, q=Q, extra=None):
    """frames: list of PIL RGBA at texture scale. Crop to union bbox, grid-pack."""
    fw, fh = frames[0].size
    bb = None
    for fr in frames:
        b = fr.getchannel("A").getbbox() if fr.mode == "RGBA" else (0, 0, fr.width, fr.height)
        if b:
            bb = b if bb is None else (min(bb[0], b[0]), min(bb[1], b[1]), max(bb[2], b[2]), max(bb[3], b[3]))
    bb = bb or (0, 0, fw, fh)
    cw, ch = bb[2] - bb[0], bb[3] - bb[1]
    n = len(frames)
    if cols is None:
        cols = max(1, min(n, maxw // cw))
    rows = (n + cols - 1) // cols
    sheet = Image.new(frames[0].mode, (cols * cw, rows * ch))
    for i, fr in enumerate(frames):
        sheet.paste(fr.crop(bb), ((i % cols) * cw, (i // cols) * ch))
    f = save_webp(sheet, "anim-" + key, q)
    man["anim"][key] = {"f": f, "n": n, "cols": cols, "cw": cw, "ch": ch, "ox": round(bb[0] / s, 2),
                        "oy": round(bb[1] / s, 2), "fw": round(fw / s, 2), "fh": round(fh / s, 2), "s": s, **(extra or {})}


def frames_in(d, pat=r".*\.png$"):
    fs = sorted(f for f in os.listdir(d) if re.match(pat, f, re.I))
    return [os.path.join(d, f) for f in fs]


def num_key(p):
    m = re.findall(r"(\d+)", os.path.basename(p))
    return int(m[-1]) if m else 0


SPECIES = {
    # key: (catch/fish dir, fishing/fish-catch dir, fishing/fish-fight dir, fighting/fish dir, head, icon, name label, esr key)
    "carp": ("carp", "carp", "carp", "carp-swimming", "carp", "carp", "carp", "carp"),
    "crucian": ("crusian crap", "crusian crap", "crusian crap", "crusian crap", "crusian.crap", "crusian crap", "crusian_crap", "crusian_crap"),
    "tilapia": ("Tilapia", "Tilapia", "Tilapia", "Tilapia", "niloticus2", "Tilapia", None, "tilapia"),
    "niloticus": ("niloticus", "niloticus", "niloticus", "niloticus", "niloticus", "niloticus", "niloticus", "niloticus"),
    "bbass": ("BBass", "BBass", "BBass", "BBass-swimming", "black.bass", "bbass", "BBass", "bbass"),
    "culter": ("Culter alburnus", "Culter alburnus", "Culter alburnus", "Culter alburnus-swimming", "Culter.alburnus", "Culter alburnus", "Culter_alburnus", "culter_alburnus"),
    "grouper": ("Grouper", "Grouper", "Grouper", "Grouper", "grouper", "grouper", "grouper", "grouper"),
    "giantgrouper": ("gaint_grouper", "Grouper", "Grouper", "gaint_grouper", "giantgrouper", "gaint_grouper", "giantgrouper", "gaint_grouper"),
    "corvina": ("corvina", "corvina", "corvina", "corvina-swimming", "Red.drum", "corvina", "Red_drum", "corvina"),
    "peacock": ("peacock-bass", "peacock-bass", "peacock-bass", "peacock-bass", "peacoca.bass", "peacock_bass", "peacoca_bass", "peacock-bass"),
    "rainbow": ("rainbow-cichlid", "rainbow_cichlid", "Rainbow_cichlid", "Rainbow-cichlid", "rainbow.cichlid", "rainbow", "rainbow_cichlid", "rainbow-cichlid"),
    "tinfoil": ("tinfoil_barb", "tinfoil_barb", "tinfoil_barb", "tinfoil_barb-swimming", "tinfoil.barb", "tinfoil_barb", "tinfoil_barb", "tinfoil_barb"),
    "whitegrunt": ("white_grunt", "white_grunt", "white_grunt", "white_grunt", "white.grunt", "white_grunt", "white_grunt", "white_grunt"),
}
man["meta"]["species"] = {}
done_fight = {}
for sp, (cdir, ldir, fdir, udir, head, icon, label, ekey) in SPECIES.items():
    info = {}
    # hanging fish on the catch screen (ESRGAN every other frame, else raw every other frame 2x)
    esr = sorted(glob.glob(f"{ESR_A}cf-{ekey}-*.png"))
    if esr:
        fr = [Image.open(p).convert("RGBA") for p in esr]
    else:
        fr = [up2(Image.open(p)) for p in sorted(frames_in(R + "catch/fish/" + cdir), key=num_key)[::2]]
    a0 = np.array(fr[0].getchannel("A"))
    top = int(np.argmax(a0.max(1) > 40))
    xs = np.where(a0[top:top + 8].max(0) > 40)[0]
    anim("hang-" + sp, fr, 2, extra={"ax": round(float(xs.mean()) / 2, 1), "ay": round(top / 2, 1)})
    # landing (lifted out of water) 23 frames 1x
    fr = [Image.open(p).convert("RGBA") for p in sorted(frames_in(R + "fishing/fish-catch/" + ldir), key=num_key)]
    anim("land-" + sp, fr, 1)
    # fight: 16 directions x 12 frames, scaled to 0.64
    if fdir in done_fight:
        man["anim"]["fight-" + sp] = man["anim"]["fight-" + done_fight[fdir]]
    else:
        d = R + "fishing/fish-fight/" + fdir
        by = {}
        for f in os.listdir(d):
            m = re.search(r"swimming(\d\d)\.(\d+)\.png$", f, re.I)
            if m:
                by.setdefault(int(m.group(1)), []).append((int(m.group(2)), f))
        fr = []
        for k in range(1, 17):
            lst = [f for _, f in sorted(by[k])][:23]
            while len(lst) < 23:
                lst.append(lst[-1])
            for f in lst:
                im = Image.open(os.path.join(d, f)).convert("RGBA")
                fr.append(im.resize((128, 128), Image.LANCZOS))
        anim("fight-" + sp, fr, 0.64, cols=16, extra={"dirs": 16, "per": 23})
        done_fight[fdir] = sp
    # underwater side view: 12 swim + 12 return at 0.5
    d = R + "fighting/fish/" + udir
    allf = sorted(os.listdir(d))
    ret = sorted([f for f in allf if "return" in f.lower()], key=lambda f: num_key(f))
    swim = sorted([f for f in allf if "return" not in f.lower()], key=lambda f: num_key(f))
    pick = swim[:23] + ret[:23]
    fr = []
    for f in pick:
        im = Image.open(os.path.join(d, f)).convert("RGBA")
        fr.append(im.resize((im.width // 2, im.height // 2), Image.LANCZOS))
    anim("under-" + sp, fr, 0.5, extra={"swim": len(swim[:23]), "ret": len(ret[:23])})
    info.update(head="fighting-top-UI/fish-UI-head-" + head, icon="fishing/POP-catch/fish_icon_" + icon,
                label=("catch/UI-right-fishname-" + label) if label else None)
    man["meta"]["species"][sp] = info

# effects
fr = [Image.open(p).convert("RGBA") for p in sorted(frames_in(R + "fishing/water-patten"), key=num_key)]
anim("splash", fr, 1)
fr = [Image.open(p).convert("RGBA") for p in sorted(frames_in(R + "catch/fireworks"), key=num_key)]
anim("fireworks", fr, 1)
fr = [Image.open(p).convert("RGB").resize((640, 612), Image.LANCZOS) for p in sorted(frames_in(R + "fighting/underwave-animate"), key=num_key)[::2]]
anim("underwave", fr, 0.5, cols=5, q=80)
fr = [Image.open(p).convert("RGB") for p in sorted(frames_in(R + "catch/BG-water", r".*\.jpg$"), key=num_key)]
anim("catchwater", fr, 1, cols=4, q=80)
fr = [Image.open(p).convert("RGBA") for p in sorted(frames_in(R + "cover", r"loading-reel-motion.*"), key=num_key)]
anim("loadreel", fr, 1)
fr = [Image.open(p).convert("RGBA") for p in sorted(frames_in(R + "lobby", r"lobby-bg-bird_.*"), key=num_key)]
anim("bird", fr, 1)
fr = [Image.open(p).convert("RGBA") for p in sorted(frames_in(R + "fighting-top-UI/fish-UI-angry"), key=num_key)]
anim("angry", fr, 1)
fr = [Image.open(p).convert("RGBA") for p in sorted(frames_in(R + "lobby", r"up-button-mission-ecffect_.*"), key=num_key)]
fr = [f.resize((200, 209)) for f in fr]
anim("missionfx", fr, 1)
# catch-screen girl (ESRGAN every other frame, cropped box) at 1.5x
meta = json.load(open(W + "esr_meta.json"))
box = meta["catchGirlBox"]
esr = sorted(glob.glob(ESR_A + "cg-*.png"))
if esr:
    fr = [Image.open(p).convert("RGBA") for p in esr]
    fr = [f.resize((int(f.width * 0.75), int(f.height * 0.75)), Image.LANCZOS) for f in fr]
else:
    fr = [Image.open(p).convert("RGBA").crop(box) for p in sorted(glob.glob(R + "catch/girl/*.png"))[::2]]
    fr = [f.resize((int(f.width * 1.5), int(f.height * 1.5)), Image.LANCZOS) for f in fr]
anim("catchgirl", fr, 1.5, q=88, extra={"bx": box[0], "by": box[1]})

json.dump(man, open(OUT + "assets.json", "w"), ensure_ascii=False, separators=(",", ":"))
tot = sum(os.path.getsize(os.path.join(OUT + "img", f)) for f in os.listdir(OUT + "img"))
print("files", len(os.listdir(OUT + "img")), "MB", round(tot / 1e6, 1), "ui atlases", len(man["atlas"]), "ui pieces", len(man["ui"]))

# angler animation atlases (original girl frames per rod + rendered male frames) merge into assets.json
os.system(f'python3 -I {os.path.dirname(os.path.abspath(__file__))}/angler_anim.py {OUT}')
