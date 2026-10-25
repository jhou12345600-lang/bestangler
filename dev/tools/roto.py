"""Polygon-guided GrabCut roto.
usage: python -I roto.py SPEC.json
SPEC: {"src":..., "out":..., "view":..., "fg":[[[x,y],...],...], "holes":[[...]], "band":6}
"""
import sys, json
import numpy as np
import cv2

spec = json.load(open(sys.argv[1]))
img = cv2.imread(spec["src"])
h, w = img.shape[:2]
poly = np.zeros((h, w), np.uint8)
for p in spec["fg"]:
    cv2.fillPoly(poly, [np.array(p, np.int32)], 255)
for p in spec.get("holes", []):
    cv2.fillPoly(poly, [np.array(p, np.int32)], 0)
band = spec.get("band", 6)
k = np.ones((3, 3), np.uint8)
sure_fg = cv2.erode(poly, k, iterations=band)
maybe = cv2.dilate(poly, k, iterations=band)
mask = np.full((h, w), cv2.GC_BGD, np.uint8)
mask[maybe > 0] = cv2.GC_PR_BGD
mask[poly > 0] = cv2.GC_PR_FGD
mask[sure_fg > 0] = cv2.GC_FGD
bgd, fgd = np.zeros((1, 65)), np.zeros((1, 65))
cv2.grabCut(img, mask, None, bgd, fgd, 5, cv2.GC_INIT_WITH_MASK)
fg = ((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD)).astype(np.uint8) * 255
fg = cv2.morphologyEx(fg, cv2.MORPH_OPEN, k)
alpha = cv2.GaussianBlur(fg, (3, 3), 0.8)

# colour decontamination at the edge
solid = (alpha >= 250).astype(np.float32)
acc = cv2.blur(img.astype(np.float32) * solid[..., None], (9, 9))
ws = cv2.blur(solid, (9, 9))[..., None]
fill = np.where(ws > 0.02, acc / np.maximum(ws, 1e-4), img)
edge = (alpha > 0) & (alpha < 250)
out = img.copy()
out[edge] = (0.35 * img[edge] + 0.65 * fill[edge]).astype(np.uint8)
rgba = np.dstack([out, alpha])
ys, xs = np.where(alpha > 0)
x0, y0, x1, y1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
cv2.imwrite(spec["out"], rgba[y0:y1, x0:x1])
json.dump({"x": int(x0), "y": int(y0), "w": int(x1 - x0), "h": int(y1 - y0)}, open(spec["out"] + ".json", "w"))
if spec.get("view"):
    v = img.copy() // 3
    v[alpha > 128] = img[alpha > 128]
    cnt, _ = cv2.findContours(poly, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
    cv2.drawContours(v, cnt, -1, (0, 0, 255), 1)
    crop = v[max(0, y0 - 20):y1 + 20, max(0, x0 - 20):x1 + 20]
    cv2.imwrite(spec["view"], cv2.resize(crop, None, fx=2, fy=2, interpolation=cv2.INTER_NEAREST))
print("bbox", x0, y0, x1, y1)
