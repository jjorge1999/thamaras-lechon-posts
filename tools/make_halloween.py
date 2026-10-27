"""Halloween kids-event graphic in the premium gold & embers style.
Usage: python3 tools/make_halloween.py out.jpg"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import premium as P
W, H = P.W, P.H

def pumpkin(size=520):
    s = size
    yy, xx = np.mgrid[0:s, 0:s].astype(np.float32)
    cx, cy = s / 2, s * 0.56; rx, ry = 0.47 * s, 0.37 * s
    nx, ny = (xx - cx) / rx, (yy - cy) / ry
    # slightly flattened top/bottom with lobed silhouette
    ang = np.arctan2(ny, nx); r = np.sqrt(nx ** 2 + ny ** 2)
    edge = 1 - 0.05 * np.abs(np.sin(ang * 3))
    body = r < edge
    nz = np.sqrt(np.clip(1 - np.clip(r / edge, 0, 1) ** 2, 0, 1))
    ribs = 0.5 + 0.5 * np.cos(np.clip(nx, -1, 1) * np.pi * 2.5)          # vertical lobes
    light = 0.25 + 0.75 * nz * (0.65 + 0.35 * ribs) - 0.25 * ny - 0.12 * nx
    light = np.clip(light, 0.05, 1.2)
    rgb = np.stack([np.clip(235 * light + 15, 0, 255), np.clip(110 * light ** 1.2, 0, 255), np.clip(18 * light, 0, 255)], -1)
    im = Image.fromarray(rgb.astype(np.uint8), "RGB").convert("RGBA")
    im.putalpha(Image.fromarray((body * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2)))
    d = ImageDraw.Draw(im)
    d.polygon([(cx - 20, cy - ry + 14), (cx + 16, cy - ry + 14), (cx + 34, cy - ry - 60), (cx + 4, cy - ry - 66)], fill=(66, 58, 26, 255))
    d.line([(cx - 6, cy - ry + 10), (cx + 14, cy - ry - 58)], fill=(110, 100, 50, 255), width=4)
    face = Image.new("L", (s, s), 0); f = ImageDraw.Draw(face)
    f.polygon([(cx - 0.30 * s, cy - 0.03 * s), (cx - 0.09 * s, cy - 0.03 * s), (cx - 0.17 * s, cy - 0.17 * s)], fill=255)
    f.polygon([(cx + 0.30 * s, cy - 0.03 * s), (cx + 0.09 * s, cy - 0.03 * s), (cx + 0.17 * s, cy - 0.17 * s)], fill=255)
    f.polygon([(cx - 0.045 * s, cy + 0.05 * s), (cx + 0.045 * s, cy + 0.05 * s), (cx, cy - 0.03 * s)], fill=255)
    f.chord((cx - 0.30 * s, cy - 0.0 * s, cx + 0.30 * s, cy + 0.25 * s), 0, 180, fill=255)
    for k in (-0.15, 0.0, 0.15):
        f.rectangle((cx + k * s - 0.03 * s, cy + 0.12 * s, cx + k * s + 0.03 * s, cy + 0.155 * s), fill=0)
    # dark carved rim, then bright candle glow inside
    rim = Image.new("RGBA", (s, s), (90, 30, 5, 0)); rim.putalpha(face.filter(ImageFilter.MaxFilter(9)))
    im = Image.alpha_composite(im, rim)
    inner = P.vgrad(s, s, [(0, (255, 252, 200)), (0.5, (255, 214, 90)), (0.85, (255, 150, 30)), (1, (230, 100, 10))]).convert("RGBA"); inner.putalpha(face)
    halo = Image.new("RGBA", (s, s), (255, 190, 60, 0)); halo.putalpha(face.filter(ImageFilter.GaussianBlur(16)).point(lambda v: min(255, v * 2)))
    im = Image.alpha_composite(im, halo); im = Image.alpha_composite(im, inner)
    return im

def main(out):
    img = P.background("night", seed=31, glow_box=(160, 560, 920, 1120))
    img = P.embers(img, seed=31, n=170)
    # bats
    d = ImageDraw.Draw(img)
    def bat(cx, cy, s):
        d.polygon([(cx, cy), (cx - 60 * s, cy - 25 * s), (cx - 45 * s, cy), (cx - 70 * s, cy + 5 * s), (cx - 30 * s, cy + 12 * s), (cx, cy + 20 * s),
                   (cx + 30 * s, cy + 12 * s), (cx + 70 * s, cy + 5 * s), (cx + 45 * s, cy), (cx + 60 * s, cy - 25 * s)], fill=(14, 6, 22, 230))
        d.ellipse((cx - 12 * s, cy - 12 * s, cx + 12 * s, cy + 14 * s), fill=(14, 6, 22, 230))
    bat(930, 250, 0.9); bat(130, 560, 0.7); bat(960, 600, 0.55)
    img = P.brand(img)
    img = P.date_pill(img, "SABADO • OCT 31", 205)
    img = P.metal_text(img, "TRICK OR TREAT", P.fit("TRICK OR TREAT", "display", 118, W - 80), 330, stops=P.FIRE)
    img = P.metal_text(img, "sa Thamara's!", P.font("script", 120), 450, glow_a=110)
    img = P.soft_text(img, "Libre nga candy para sa mga bata!", P.font("sansb", 40), 545)
    # pumpkin + candies with depth
    pk = pumpkin(520); img.alpha_composite(pk, (W // 2 - 260, 560))
    cands = [((214, 40, 140), 150, 25, 130, 860, 0), ((40, 70, 210), 150, -20, 770, 850, 0), ((190, 110, 40), 130, 12, 300, 935, 0),
             ((40, 70, 210), 120, 30, 660, 945, 0), ((214, 40, 140), 240, -30, -150, 1080, 7), ((210, 160, 50), 240, 25, 880, 1080, 7),
             ((190, 110, 40), 110, -15, 40, 700, 3), ((150, 60, 200), 110, 20, 890, 700, 3)]
    for i, (col, sz, ang, x, y, blur) in enumerate(cands):
        c = P.depth_blur(P.wrapped_candy(col, sz, ang, seed=i), blur)
        img.alpha_composite(c, (int(x), int(y)))
    img = P.soft_text(img, "Dad-a ang mga bata — naka-costume o dili!", P.fit("Dad-a ang mga bata — naka-costume o dili!", "sansb", 36, W - 100), 1150)
    img = P.cta(img, "ADTO NA SA KARENDERIA", 1230, w=740)
    img = P.footer(img, "Samtang naa pa ang candy  •  ☎ (0951) 781 4902", 1308)
    img.convert("RGB").save(out, quality=93); print(out)

if __name__ == "__main__":
    main(sys.argv[1])
