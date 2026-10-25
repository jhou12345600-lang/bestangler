"""Real-ESRGAN x2 (RRDBNet) upscaler, CPU, alpha-aware.
usage: python -I esrgan.py MODEL OUT_DIR IN_FILE [IN_FILE...]
Outputs PNG with the same base name into OUT_DIR. Alpha is upscaled with Lanczos.
"""
import sys, os
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image

torch.set_num_threads(max(1, os.cpu_count() or 1))


class RDB5(nn.Module):
    def __init__(s, nf=64, gc=32):
        super().__init__()
        s.conv1 = nn.Conv2d(nf, gc, 3, 1, 1)
        s.conv2 = nn.Conv2d(nf + gc, gc, 3, 1, 1)
        s.conv3 = nn.Conv2d(nf + 2 * gc, gc, 3, 1, 1)
        s.conv4 = nn.Conv2d(nf + 3 * gc, gc, 3, 1, 1)
        s.conv5 = nn.Conv2d(nf + 4 * gc, nf, 3, 1, 1)
        s.l = nn.LeakyReLU(0.2, True)

    def forward(s, x):
        x1 = s.l(s.conv1(x))
        x2 = s.l(s.conv2(torch.cat((x, x1), 1)))
        x3 = s.l(s.conv3(torch.cat((x, x1, x2), 1)))
        x4 = s.l(s.conv4(torch.cat((x, x1, x2, x3), 1)))
        x5 = s.conv5(torch.cat((x, x1, x2, x3, x4), 1))
        return x5 * 0.2 + x


class RRDB(nn.Module):
    def __init__(s, nf, gc=32):
        super().__init__()
        s.rdb1, s.rdb2, s.rdb3 = RDB5(nf, gc), RDB5(nf, gc), RDB5(nf, gc)

    def forward(s, x):
        return s.rdb3(s.rdb2(s.rdb1(x))) * 0.2 + x


class RRDBNet(nn.Module):
    def __init__(s, scale=2, nf=64, nb=23):
        super().__init__()
        s.scale = scale
        inc = 3 * (4 if scale == 2 else 1)
        s.conv_first = nn.Conv2d(inc, nf, 3, 1, 1)
        s.body = nn.Sequential(*[RRDB(nf) for _ in range(nb)])
        s.conv_body = nn.Conv2d(nf, nf, 3, 1, 1)
        s.conv_up1 = nn.Conv2d(nf, nf, 3, 1, 1)
        s.conv_up2 = nn.Conv2d(nf, nf, 3, 1, 1)
        s.conv_hr = nn.Conv2d(nf, nf, 3, 1, 1)
        s.conv_last = nn.Conv2d(nf, 3, 3, 1, 1)
        s.l = nn.LeakyReLU(0.2, True)

    def forward(s, x):
        if s.scale == 2:
            x = F.pixel_unshuffle(x, 2)
        f = s.conv_first(x)
        f = f + s.conv_body(s.body(f))
        f = s.l(s.conv_up1(F.interpolate(f, scale_factor=2, mode="nearest")))
        f = s.l(s.conv_up2(F.interpolate(f, scale_factor=2, mode="nearest")))
        return s.conv_last(s.l(s.conv_hr(f)))


def load(model_path):
    net = RRDBNet(scale=2)
    sd = torch.load(model_path, map_location="cpu")
    sd = sd.get("params_ema", sd.get("params", sd))
    net.load_state_dict(sd, strict=True)
    net.eval()
    return net


@torch.no_grad()
def run(net, rgb, tile=192, pad=12):
    H0, W0 = rgb.shape[:2]
    rgb = np.pad(rgb, ((0, H0 % 2), (0, W0 % 2), (0, 0)), mode="edge")
    x = torch.from_numpy(np.ascontiguousarray(rgb)).permute(2, 0, 1).float().unsqueeze(0) / 255.0
    _, _, h, w = x.shape
    tile -= tile % 2
    pad -= pad % 2
    out = torch.zeros(1, 3, h * 2, w * 2)
    for y0 in range(0, h, tile):
        for x0 in range(0, w, tile):
            y1, x1 = min(y0 + tile, h), min(x0 + tile, w)
            py0, px0 = max(y0 - pad, 0), max(x0 - pad, 0)
            py1, px1 = min(y1 + pad, h), min(x1 + pad, w)
            o = net(x[:, :, py0:py1, px0:px1])
            oy, ox = (y0 - py0) * 2, (x0 - px0) * 2
            out[:, :, y0 * 2:y1 * 2, x0 * 2:x1 * 2] = o[:, :, oy:oy + (y1 - y0) * 2, ox:ox + (x1 - x0) * 2]
    res = (out.clamp(0, 1)[0].permute(1, 2, 0).numpy() * 255 + 0.5).astype(np.uint8)
    return res[: H0 * 2, : W0 * 2]


def main():
    model, outdir, files = sys.argv[1], sys.argv[2], sys.argv[3:]
    os.makedirs(outdir, exist_ok=True)
    net = load(model)
    for f in files:
        name = os.path.splitext(os.path.basename(f))[0] + ".png"
        dst = os.path.join(outdir, name)
        if os.path.exists(dst):
            continue
        im = Image.open(f)
        has_a = im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info)
        im = im.convert("RGBA")
        arr = np.array(im)
        rgb, a = arr[:, :, :3].copy(), arr[:, :, 3]
        if has_a:
            # bleed colour into transparent pixels so edges don't halo dark
            bg = Image.fromarray(rgb).filter(__import__("PIL.ImageFilter").ImageFilter.BoxBlur(4))
            m = a < 8
            rgb[m] = np.array(bg)[m]
        try:
            up = run(net, rgb)
        except Exception as e:  # keep the batch going
            print("FAIL", f, e, flush=True)
            continue
        res = Image.fromarray(up)
        if has_a:
            alpha = Image.fromarray(a).resize(res.size, Image.LANCZOS)
            res.putalpha(alpha)
        res.save(dst)
        print("ok", dst, res.size, flush=True)


if __name__ == "__main__":
    main()
