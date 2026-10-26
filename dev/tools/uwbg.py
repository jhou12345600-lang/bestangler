"""Official underwater background (神釣手1.docx) -> work/uw-bg.png without the baked-in HUD."""
import sys
import numpy as np
from PIL import Image, ImageFilter
src, out = sys.argv[1], sys.argv[2]
im = Image.open(src).convert('RGB'); W, H = im.size          # 2356 x 1178
a = np.asarray(im).astype(np.float32)
# HUD sits at the top centre (portrait, bars, distance, fish head): x 850-1500, y 0-135
x0, x1, y1 = 790, 1570, 205
w = x1 - x0
patch = a[:y1, 4:4 + w].copy()                 # same rows, just to the left
# feather the patch edges into the original
mask = np.ones((y1, w), np.float32)
f = 45
ramp = np.linspace(0, 1, f)
mask[:, :f] *= ramp; mask[:, -f:] *= ramp[::-1]
mask[-f:, :] *= ramp[::-1][:, None]
region = a[:y1, x0:x1]
a[:y1, x0:x1] = region * (1 - mask[..., None]) + patch * mask[..., None]
res = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
# scale to the game's 1280-px-tall stage at 1.5x for sharpness
th = 1280 * 3 // 2
res = res.resize((round(W * th / H), th), Image.LANCZOS)
res.save(out)
print(res.size)
