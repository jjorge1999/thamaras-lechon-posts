"""Premium "gold & embers" look shared by all Thamara's graphics.

Metallic gold lettering with bevel + glow, script accent line, smoky dark
background with glowing embers, gold-framed plates and pills, blurred
foreground objects for depth. Pure Pillow + numpy, fonts are SIL OFL
(Cinzel, Great Vibes, Montserrat) in assets/fonts.
"""
import os, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FD = os.path.join(HERE, "assets", "fonts")
W, H = 1080, 1350

def font(kind, size):
    name = {"display": "Cinzel-Black", "display2": "Cinzel-Bold", "script": "GreatVibes",
            "sans": "Montserrat", "sansb": "Montserrat-Bold", "sansx": "Montserrat-ExtraBold"}[kind]
    return ImageFont.truetype(os.path.join(FD, name + ".ttf"), size)

SYM = lambda s: ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", s)

# ---------- gradients ----------
GOLD = [(0.0, (255, 246, 200)), (0.35, (236, 190, 96)), (0.55, (150, 96, 30)), (0.7, (214, 160, 70)), (1.0, (255, 232, 160))]
FIRE = [(0.0, (255, 236, 150)), (0.35, (255, 170, 40)), (0.6, (226, 96, 14)), (0.8, (255, 140, 30)), (1.0, (255, 214, 120))]
CREAM = [(0.0, (255, 250, 236)), (1.0, (242, 214, 160))]

def vgrad(w, h, stops):
    ys = np.linspace(0, 1, h)
    out = np.zeros((h, w, 3), np.float32)
    for c in range(3):
        col = np.interp(ys, [s[0] for s in stops], [s[1][c] for s in stops])
        out[:, :, c] = col[:, None]
    return Image.fromarray(out.astype(np.uint8), "RGB")

# ---------- background ----------
PALETTES = {
    "ember":   {"base": (22, 10, 8),  "glow": (255, 120, 30), "smoke": (120, 70, 50)},
    "night":   {"base": (20, 10, 34), "glow": (255, 130, 40), "smoke": (110, 80, 150)},
    "maroon":  {"base": (34, 8, 6),   "glow": (255, 110, 40), "smoke": (140, 60, 40)},
}

def smoke(seed, color, alpha=70):
    rnd = np.random.default_rng(seed)
    acc = np.zeros((H, W), np.float32)
    for scale, wgt in ((8, 1.0), (16, 0.5), (32, 0.25)):
        small = rnd.random((H // (H // scale) + 1, W // (W // scale) + 1)).astype(np.float32)
        im = Image.fromarray((small * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC)
        acc += np.asarray(im, np.float32) / 255 * wgt
    acc = (acc - acc.min()) / (acc.max() - acc.min())
    acc = np.clip((acc - 0.45) * 2.2, 0, 1)
    a = Image.fromarray((acc * alpha).astype(np.uint8)).filter(ImageFilter.GaussianBlur(40))
    layer = Image.new("RGBA", (W, H), color + (0,)); layer.putalpha(a)
    return layer

def background(palette="ember", seed=7, glow_box=(80, 520, 1000, 1150)):
    p = PALETTES[palette]
    img = Image.new("RGBA", (W, H), p["base"] + (255,))
    g = Image.new("RGBA", (W, H)); ImageDraw.Draw(g).ellipse(glow_box, fill=p["glow"] + (120,))
    img = Image.alpha_composite(img, g.filter(ImageFilter.GaussianBlur(180)))
    img = Image.alpha_composite(img, smoke(seed, p["smoke"]))
    return vignette(img)

def vignette(img, strength=200):
    y, x = np.ogrid[:H, :W]
    d = np.sqrt(((x - W / 2) / (W / 2)) ** 2 + ((y - H / 2) / (H / 1.7)) ** 2)
    a = np.clip((d - 0.65) * 1.6, 0, 1) * strength
    v = Image.new("RGBA", (W, H), (0, 0, 0, 0)); v.putalpha(Image.fromarray(a.astype(np.uint8)))
    return Image.alpha_composite(img, v)

def embers(img, seed=3, n=140, area=(0, 0, W, H)):
    rnd = random.Random(seed)
    lay = Image.new("RGBA", (W, H)); d = ImageDraw.Draw(lay)
    for _ in range(n):
        x = rnd.uniform(area[0], area[2]); y = rnd.uniform(area[1], area[3])
        r = rnd.choice([1.2, 1.6, 2.2, 2.2, 3, 4]); c = rnd.choice([(255, 190, 80), (255, 140, 40), (255, 220, 140)])
        if rnd.random() < 0.08:  # occasional streak
            L = rnd.uniform(6, 14); ang = rnd.uniform(-1.2, -0.3)
            d.line([(x, y), (x + L * np.cos(ang), y + L * np.sin(ang))], fill=c + (220,), width=2)
        else:
            d.ellipse((x - r, y - r, x + r, y + r), fill=c + (rnd.randint(150, 255),))
    glow = lay.filter(ImageFilter.GaussianBlur(5))
    return Image.alpha_composite(Image.alpha_composite(img, glow), lay)

# ---------- metallic text ----------
def _mask(text, fnt, pad=40):
    l, t, r, b = fnt.getbbox(text)
    m = Image.new("L", (r - l + pad * 2, b - t + pad * 2), 0)
    ImageDraw.Draw(m).text((pad - l, pad - t), text, font=fnt, fill=255)
    return m, pad

def fit(text, kind, size, maxw, minsize=30):
    while size > minsize:
        f = font(kind, size)
        if f.getlength(text) <= maxw: return f
        size -= 4
    return font(kind, minsize)

def metal_text(img, text, fnt, cy, stops=GOLD, cx=W // 2, outline=(40, 16, 6), glow=(255, 150, 40), glow_a=150, bevel=True):
    """Draw text centred at (cx, cy) with gradient fill, dark outline, bevel highlight, shadow and glow."""
    m, pad = _mask(text, fnt)
    w, h = m.size; x0, y0 = int(cx - w / 2), int(cy - h / 2)
    ow = max(3, fnt.size // 16)
    outer = m.filter(ImageFilter.MaxFilter(ow * 2 + 1))
    lay = Image.new("RGBA", img.size)
    # glow + drop shadow
    gl = Image.new("RGBA", (w, h), glow + (0,)); gl.putalpha(outer.filter(ImageFilter.GaussianBlur(fnt.size // 5)).point(lambda v: v * glow_a // 255))
    lay.alpha_composite(gl, (x0, y0))
    sh = Image.new("RGBA", (w, h), (0, 0, 0, 0)); sh.putalpha(outer.filter(ImageFilter.GaussianBlur(6)).point(lambda v: v * 200 // 255))
    lay.alpha_composite(sh, (x0 + ow, y0 + ow * 2))
    # outline (dark) then a thin gold rim then gradient face
    o = Image.new("RGBA", (w, h), outline + (255,)); o.putalpha(outer); lay.alpha_composite(o, (x0, y0))
    rim = m.filter(ImageFilter.MaxFilter(3))
    r = Image.new("RGBA", (w, h), (255, 220, 150, 255)); r.putalpha(rim); lay.alpha_composite(r, (x0, y0))
    face = vgrad(w, h, [(min(1, max(0, (s * (h - 2 * pad) + pad) / h)), c) for s, c in stops]).convert("RGBA"); face.putalpha(m)
    lay.alpha_composite(face, (x0, y0))
    if bevel:  # light from top-left, shade bottom-right
        hi = ImageChops.subtract(m, m.transform(m.size, Image.AFFINE, (1, 0, 2, 0, 1, 2))).filter(ImageFilter.GaussianBlur(1))
        hl = Image.new("RGBA", (w, h), (255, 255, 235, 0)); hl.putalpha(hi.point(lambda v: v * 200 // 255))
        lay.alpha_composite(hl, (x0, y0))
        lo = ImageChops.subtract(m, m.transform(m.size, Image.AFFINE, (1, 0, -2, 0, 1, -2))).filter(ImageFilter.GaussianBlur(1))
        ll = Image.new("RGBA", (w, h), (70, 30, 5, 0)); ll.putalpha(lo.point(lambda v: v * 160 // 255))
        lay.alpha_composite(ll, (x0, y0))
    return Image.alpha_composite(img, lay)

def soft_text(img, text, fnt, cy, fill=(250, 226, 180), cx=W // 2, shadow=180):
    m, pad = _mask(text, fnt); w, h = m.size; x0, y0 = int(cx - w / 2), int(cy - h / 2)
    lay = Image.new("RGBA", img.size)
    sh = Image.new("RGBA", (w, h), (0, 0, 0, 0)); sh.putalpha(m.filter(ImageFilter.GaussianBlur(5)).point(lambda v: v * shadow // 255))
    lay.alpha_composite(sh, (x0 + 2, y0 + 3))
    f = vgrad(w, h, [(0, tuple(min(255, c + 20) for c in fill)), (1, tuple(max(0, c - 25) for c in fill))]).convert("RGBA"); f.putalpha(m)
    lay.alpha_composite(f, (x0, y0))
    return Image.alpha_composite(img, lay)

# ---------- plates & pills ----------
def gold_plate(img, box, radius=None, fill=(28, 16, 10), border=6, glow=True):
    x0, y0, x1, y1 = [int(v) for v in box]; w, h = x1 - x0, y1 - y0
    radius = radius if radius is not None else h // 2
    lay = Image.new("RGBA", img.size)
    if glow:
        g = Image.new("L", img.size, 0); ImageDraw.Draw(g).rounded_rectangle(box, radius, fill=150)
        gg = Image.new("RGBA", img.size, (255, 160, 60, 0)); gg.putalpha(g.filter(ImageFilter.GaussianBlur(22)))
        lay.alpha_composite(gg)
    sh = Image.new("L", img.size, 0); ImageDraw.Draw(sh).rounded_rectangle((x0 + 4, y0 + 8, x1 + 4, y1 + 8), radius, fill=170)
    s = Image.new("RGBA", img.size, (0, 0, 0, 0)); s.putalpha(sh.filter(ImageFilter.GaussianBlur(8))); lay.alpha_composite(s)
    m = Image.new("L", (w, h), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), radius, fill=255)
    gold = vgrad(w, h, GOLD).convert("RGBA"); gold.putalpha(m); lay.alpha_composite(gold, (x0, y0))
    inner = Image.new("L", (w, h), 0)
    ImageDraw.Draw(inner).rounded_rectangle((border, border, w - 1 - border, h - 1 - border), max(2, radius - border), fill=255)
    if isinstance(fill, list):
        face = vgrad(w, h, fill).convert("RGBA")
    else:
        face = vgrad(w, h, [(0, tuple(min(255, c + 22) for c in fill)), (1, fill)]).convert("RGBA")
    face.putalpha(inner); lay.alpha_composite(face, (x0, y0))
    # thin inner gold line
    ln = Image.new("L", (w, h), 0)
    ImageDraw.Draw(ln).rounded_rectangle((border + 5, border + 5, w - 6 - border, h - 6 - border), max(2, radius - border - 5), outline=255, width=2)
    l = Image.new("RGBA", (w, h), (230, 186, 100, 0)); l.putalpha(ln.point(lambda v: v * 170 // 255)); lay.alpha_composite(l, (x0, y0))
    return Image.alpha_composite(img, lay)

GOLD_FACE = [(0, (255, 236, 170)), (0.45, (232, 182, 86)), (0.55, (200, 146, 60)), (1, (244, 204, 120))]

def cta(img, text, cy, sub=None, w=760):
    h = 118 if sub else 100
    box = (W / 2 - w / 2, cy - h / 2, W / 2 + w / 2, cy + h / 2)
    img = gold_plate(img, box, fill=GOLD_FACE, border=7)
    img = soft_text(img, text, fit(text, "sansx", 46, w - 90), cy - (16 if sub else 0), fill=(52, 22, 6), shadow=0)
    if sub:
        img = soft_text(img, sub, fit(sub, "sansb", 26, w - 120), cy + 30, fill=(80, 36, 10), shadow=0)
    return img

def date_pill(img, text, cy, size=36):
    f = font("sansx", size); w = f.getlength(text) + 90
    img = gold_plate(img, (W / 2 - w / 2, cy - 34, W / 2 + w / 2, cy + 34), fill=(36, 26, 22), border=5)
    return metal_text(img, text, f, cy, stops=CREAM, outline=(20, 10, 4), glow_a=0, bevel=False)

def chips(img, items, cy):
    if not items: return img
    f = font("sansb", 34)
    rows, row = [], []
    for it in items:
        test = row + [it]
        if sum(f.getlength(t) + 70 for t in test) + 24 * (len(test) - 1) > W - 140 and row:
            rows.append(row); row = [it]
        else:
            row = test
    rows.append(row)
    y = cy - (len(rows) - 1) * 45
    for r in rows:
        tw = sum(f.getlength(t) + 70 for t in r) + 24 * (len(r) - 1); x = W / 2 - tw / 2
        for t in r:
            w = f.getlength(t) + 70
            img = gold_plate(img, (x, y - 34, x + w, y + 34), fill=(30, 16, 10), border=4, glow=False)
            img = soft_text(img, t, f, y, fill=(250, 222, 160), cx=x + w / 2)
            x += w + 24
        y += 90
    return img

def brand(img, top=40):
    img = metal_text(img, "THAMARA'S LECHON", font("display", 64), top + 40, glow_a=60)
    img = soft_text(img, "&  CARINDERIA   •   LAPINIGAN", font("sansb", 24), top + 100, fill=(232, 206, 160))
    return img

def footer(img, text, cy=1300):
    # phone glyph from DejaVu (Montserrat subset lacks it)
    if "☎" in text:
        a, b = text.split("☎", 1)
        f = font("sansb", 30); fs = SYM(30)
        total = f.getlength(a) + fs.getlength("☎ ") + f.getlength(b.strip())
        x = W / 2 - total / 2
        img = soft_text(img, a, f, cy, cx=x + f.getlength(a) / 2)
        x += f.getlength(a)
        d = ImageDraw.Draw(img); d.text((x, cy - 20), "☎", font=fs, fill=(250, 222, 160)); x += fs.getlength("☎ ")
        return soft_text(img, b.strip(), f, cy, cx=x + f.getlength(b.strip()) / 2)
    return soft_text(img, text, fit(text, "sansb", 30, W - 120), cy)

def depth_blur(obj, radius):
    return obj.filter(ImageFilter.GaussianBlur(radius)) if radius else obj

def wrapped_candy(color, size=200, angle=0, seed=0):
    """Glossy foil-wrapped candy sprite (RGBA)."""
    rnd = random.Random(seed)
    s = size; im = Image.new("RGBA", (s * 2, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    dark = tuple(int(c * 0.45) for c in color); light = tuple(min(255, int(c * 1.5 + 60)) for c in color)
    cx, cy = s, s // 2
    for side in (-1, 1):  # twisted ends
        for k in range(7):
            yy = cy + (k - 3) * s * 0.07
            d.polygon([(cx + side * s * 0.42, cy + (k - 3) * s * 0.03), (cx + side * s * (0.85 + rnd.uniform(-.05, .08)), yy - s * 0.05),
                       (cx + side * s * (0.85 + rnd.uniform(-.05, .08)), yy + s * 0.05)], fill=[dark, color, light][k % 3] + (255,))
    body = vgrad(int(s * 0.9), int(s * 0.62), [(0, light), (0.3, color), (0.75, dark), (1, color)]).convert("RGBA")
    m = Image.new("L", body.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, body.size[0] - 1, body.size[1] - 1), int(s * 0.28), fill=255)
    body.putalpha(m); im.alpha_composite(body, (int(cx - s * 0.45), int(cy - s * 0.31)))
    d.rounded_rectangle((cx - s * 0.32, cy - s * 0.24, cx + s * 0.1, cy - s * 0.16), 6, fill=(255, 255, 255, 150))  # gloss
    for _ in range(18):  # foil sparkle
        x = cx + rnd.uniform(-s * 0.4, s * 0.4); y = cy + rnd.uniform(-s * 0.28, s * 0.28)
        d.ellipse((x - 2, y - 2, x + 2, y + 2), fill=(255, 255, 255, 170))
    return im.rotate(angle, resample=Image.BICUBIC, expand=True)
