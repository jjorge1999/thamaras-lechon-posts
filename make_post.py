#!/usr/bin/env python3
"""Generate a Thamara's Lechon Facebook post graphic (1080x1350, no prices).

Usage:
  python3 make_post.py spec.json out.jpg

spec.json fields:
  style:     "lechon" | "lechon_sliced" | "karenderia" | "bbq" | "poll"
  tag:       short label in the pill (e.g. "PARA SA HANDAAN")
  headline:  big hook text (keep under ~40 chars; wraps to 2-3 lines)
  sub:       one supporting line
  items:     list of 1-3 menu item names (no prices)   [not used by poll]
  poll_a / poll_b: the two options                     [poll only]
  cta:       call to action, e.g. "MESSAGE LANG MI"
  cta_sub:   small line under the CTA
"""
import json, math, os, re, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1080, 1350
GOLD = (240, 196, 98); MAROON = (92, 15, 5); CREAM = (255, 246, 224)
YEL = (255, 225, 77); DARK = (38, 12, 6); GREEN = (30, 140, 60)
PHONE = "(0951) 781 4902"
PLACE = "Lapinigan, San Francisco, Agusan del Sur"

def font(kind, size):
    c = {
        "serif": ["/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"],
        "bold": ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"],
        "reg": ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"],
    }[kind]
    for p in c:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default(size)

PRICE_RE = re.compile(r"(₱|php|\bp\s?\d|\d+\s?(pesos?|php))", re.I)

def check_no_price(spec):
    blob = json.dumps(spec, ensure_ascii=False)
    if PRICE_RE.search(blob):
        raise SystemExit("Spec contains a price or peso amount - not allowed.")

def wrap(d, text, f, maxw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=f) <= maxw:
            cur = t
        else:
            if cur: lines.append(cur)
            cur = w
    if cur: lines.append(cur)
    return lines

def fit_headline(d, text, maxw, max_lines=3, start=92, min_size=52):
    s = start
    while s >= min_size:
        f = font("bold", s)
        lines = wrap(d, text, f, maxw)
        if len(lines) <= max_lines:
            return f, lines
        s -= 6
    f = font("bold", min_size)
    return f, wrap(d, text, f, maxw)[:max_lines]

def photo_bg(name, box_h=620, top=420):
    src = Image.open(os.path.join(HERE, "assets", name)).convert("RGB")
    # cover-fit into W x box_h
    r = max(W / src.width, box_h / src.height)
    src = src.resize((int(src.width * r) + 1, int(src.height * r) + 1), Image.LANCZOS)
    x = (src.width - W) // 2; y = (src.height - box_h) // 2
    ph = src.crop((x, y, x + W, y + box_h))
    ph = ImageEnhance.Contrast(ph).enhance(1.08)
    m = Image.new("L", (W, box_h), 0)
    ImageDraw.Draw(m).ellipse((120, 30, W - 120, box_h + 60), fill=255)
    m = m.filter(ImageFilter.GaussianBlur(110))
    ph = Image.composite(ImageEnhance.Brightness(ph).enhance(1.15),
                         ImageEnhance.Brightness(ph).enhance(0.42), m)
    img = Image.new("RGB", (W, H), DARK)
    img.paste(ph, (0, top))
    img = img.convert("RGBA")
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
    for i in range(150):
        a = int(255 * (1 - i / 150))
        od.line([(0, top + i), (W, top + i)], fill=DARK + (a,))
        od.line([(0, top + box_h - 1 - i), (W, top + box_h - 1 - i)], fill=DARK + (a,))
    img = Image.alpha_composite(img, ov)
    beam = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(beam).polygon([(470, 150), (610, 150), (880, top + box_h - 60), (200, top + box_h - 60)],
                                 fill=(255, 240, 200, 50))
    return Image.alpha_composite(img, beam.filter(ImageFilter.GaussianBlur(30)))

def warm_bg(seed_hue=0):
    img = Image.new("RGB", (W, H), DARK)
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(g).ellipse((60, 260, W - 60, 1060), fill=(230, 120, 40, 120))
    img = Image.alpha_composite(img.convert("RGBA"), g.filter(ImageFilter.GaussianBlur(160)))
    # subtle pattern dots
    p = Image.new("RGBA", (W, H), (0, 0, 0, 0)); pd = ImageDraw.Draw(p)
    for yy in range(0, H, 54):
        for xx in range((yy // 54) % 2 * 27, W, 54):
            pd.ellipse((xx - 2, yy - 2, xx + 2, yy + 2), fill=(255, 210, 140, 22))
    return Image.alpha_composite(img, p)

def draw_bowl(d, cx, cy, s=1.0):
    # steaming bowl of ulam with rice
    d.ellipse((cx - 230*s, cy - 40*s, cx + 230*s, cy + 40*s), fill=(140, 60, 25))
    d.pieslice((cx - 230*s, cy - 200*s, cx + 230*s, cy + 200*s), 0, 180, fill=(250, 240, 225))
    d.pieslice((cx - 210*s, cy - 180*s, cx + 210*s, cy + 180*s), 0, 180, fill=(235, 220, 200))
    d.ellipse((cx - 230*s, cy - 42*s, cx + 230*s, cy + 42*s), fill=(250, 240, 225))
    d.ellipse((cx - 205*s, cy - 32*s, cx + 205*s, cy + 32*s), fill=(150, 70, 25))
    for i, (dx, dy, r) in enumerate([(-110, -6, 34), (-30, -12, 40), (60, -4, 36), (130, -10, 28), (5, 8, 30)]):
        d.ellipse((cx + (dx - r)*s, cy + (dy - r*0.6)*s, cx + (dx + r)*s, cy + (dy + r*0.6)*s),
                  fill=[(120, 50, 20), (170, 80, 30), (110, 45, 18), (190, 95, 35), (140, 60, 22)][i])
    d.rectangle((cx - 40*s, cy + 196*s, cx + 40*s, cy + 210*s), fill=(220, 205, 185))
    for k in (-90, 0, 90):
        x = cx + k*s
        d.line([(x, cy - 70*s), (x - 20*s, cy - 120*s), (x + 10*s, cy - 170*s), (x - 10*s, cy - 220*s)],
               fill=(255, 245, 225), width=int(10*s), joint="curve")

def draw_skewers(d, cx, cy, s=1.0):
    # charcoal grill with barbecue sticks
    d.rounded_rectangle((cx - 330*s, cy + 40*s, cx + 330*s, cy + 120*s), radius=20, fill=(60, 30, 20))
    for i in range(-300, 301, 40):
        d.ellipse((cx + (i - 16)*s, cy + 55*s, cx + (i + 16)*s, cy + 85*s),
                  fill=[(255, 120, 30), (220, 70, 20), (255, 170, 60)][(i // 40) % 3])
    for j in range(-6, 7, 2):
        y = cy + 30*s
        d.line([(cx - 330*s, y), (cx + 330*s, y)], fill=(130, 130, 130), width=4)
    for k, off in enumerate((-220, -110, 0, 110, 220)):
        x = cx + off*s
        d.line([(x - 120*s, cy - 140*s), (x + 120*s, cy + 20*s)], fill=(215, 180, 120), width=int(8*s))
        for t in range(4):
            px = x - 80*s + t*45*s; py = cy - 113*s + t*30*s
            d.rounded_rectangle((px - 26*s, py - 20*s, px + 26*s, py + 20*s), radius=10,
                                fill=[(150, 55, 20), (175, 70, 25), (130, 45, 15)][(k + t) % 3])
    for k in (-200, 0, 200):
        x = cx + k*s
        d.line([(x, cy - 160*s), (x - 20*s, cy - 200*s), (x + 12*s, cy - 240*s)],
               fill=(255, 235, 210), width=int(9*s), joint="curve")

def header(d, tag):
    d.text((W // 2, 64), "THAMARA'S LECHON", font=font("serif", 54), fill=GOLD, anchor="mm",
           stroke_width=2, stroke_fill=MAROON)
    d.text((W // 2, 114), "& CARINDERIA  •  LAPINIGAN", font=font("reg", 22), fill=CREAM, anchor="mm")
    if tag:
        f = font("bold", 26); tw = d.textlength(tag, font=f) + 50
        d.rounded_rectangle((W / 2 - tw / 2, 146, W / 2 + tw / 2, 190), radius=22, fill=YEL)
        d.text((W // 2, 168), tag, font=f, fill=MAROON, anchor="mm")

def headline_block(d, text, sub, top=215):
    f, lines = fit_headline(d, text, 960)
    lh = int(f.size * 1.12)
    y = top
    for ln in lines:
        d.text((W // 2, y + lh // 2), ln, font=f, fill=YEL, anchor="mm", stroke_width=5, stroke_fill=MAROON)
        y += lh
    if sub:
        sf = font("reg", 30)
        for ln in wrap(d, sub, sf, 940)[:2]:
            d.text((W // 2, y + 22), ln, font=sf, fill=CREAM, anchor="mm")
            y += 40
    return y

def item_chips(img, items, y):
    if not items: return img
    d = ImageDraw.Draw(img); f = font("bold", 30)
    items = items[:3]
    widths = [d.textlength(t, font=f) + 56 for t in items]
    rows, cur, curw = [], [], 0
    for t, w_ in zip(items, widths):
        if curw + w_ > 960 and cur:
            rows.append(cur); cur, curw = [], 0
        cur.append((t, w_)); curw += w_ + 16
    if cur: rows.append(cur)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
    for r in rows:
        total = sum(w_ for _, w_ in r) + 16 * (len(r) - 1); x = (W - total) / 2
        for t, w_ in r:
            ld.rounded_rectangle((x, y, x + w_, y + 58), radius=29, fill=(28, 9, 4, 230), outline=GOLD, width=3)
            ld.text((x + w_ / 2, y + 29), t, font=f, fill=GOLD, anchor="mm")
            x += w_ + 16
        y += 72
    return Image.alpha_composite(img, lay)

def footer(d, cta, cta_sub):
    d.rounded_rectangle((150, 1180, 930, 1272), radius=46, fill=YEL, outline=MAROON, width=4)
    d.text((W // 2, 1214), cta or "MESSAGE LANG MI", font=font("bold", 38), fill=MAROON, anchor="mm")
    d.text((W // 2, 1251), cta_sub or "para ma-reserve!", font=font("reg", 25), fill=MAROON, anchor="mm")
    d.text((W // 2, 1312), f"☎ {PHONE}", font=font("bold", 30), fill=CREAM, anchor="mm")

def make(spec, out):
    check_no_price(spec)
    style = spec.get("style", "lechon")
    if style in ("lechon", "lechon_sliced"):
        tmp = ImageDraw.Draw(Image.new("RGB", (W, H)))
        yend = headline_block(tmp, spec["headline"], spec.get("sub"))
        top = int(yend) + 10
        img = photo_bg("lechon_whole.jpg" if style == "lechon" else "lechon_sliced.jpg", box_h=1100 - top, top=top)
        d = ImageDraw.Draw(img)
        header(d, spec.get("tag"))
        headline_block(d, spec["headline"], spec.get("sub"))
        img = item_chips(img, spec.get("items"), 1095)
    elif style in ("karenderia", "bbq"):
        img = warm_bg()
        d = ImageDraw.Draw(img)
        header(d, spec.get("tag"))
        y = headline_block(d, spec["headline"], spec.get("sub"))
        cy = max(y + (330 if style == 'karenderia' else 330), 720)
        (draw_bowl if style == "karenderia" else draw_skewers)(d, W // 2, cy, 1.1)
        img = item_chips(img, spec.get("items"), 1010)
    elif style == "poll":
        img = warm_bg()
        d = ImageDraw.Draw(img)
        header(d, spec.get("tag") or "COMMENT DIRI")
        y = headline_block(d, spec["headline"], spec.get("sub"))
        top = max(y + 50, 480)
        for i, opt in enumerate((spec["poll_a"], spec["poll_b"])):
            x0 = 70 + i * 490
            lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
            ld.rounded_rectangle((x0, top, x0 + 450, top + 440), radius=30, fill=(28, 9, 4, 230), outline=GOLD, width=4)
            img = Image.alpha_composite(img, lay); d = ImageDraw.Draw(img)
            d.ellipse((x0 + 165, top + 40, x0 + 285, top + 160), fill=YEL, outline=MAROON, width=4)
            d.text((x0 + 225, top + 100), "A" if i == 0 else "B", font=font("bold", 64), fill=MAROON, anchor="mm")
            f = font("bold", 40)
            ls = wrap(d, opt, f, 320)[:3]
            yy = top + 250 - (len(ls) - 1) * 26
            for ln in ls:
                d.text((x0 + 225, yy), ln, font=f, fill=GOLD, anchor="mm"); yy += 54
        d.ellipse((W // 2 - 50, top + 170, W // 2 + 50, top + 270), fill=MAROON, outline=YEL, width=4)
        d.text((W // 2, top + 220), "O", font=font("bold", 48), fill=YEL, anchor="mm")
        d.text((W // 2, top + 500), "I-comment ang A o B! 👇".replace(" 👇", ""), font=font("bold", 34), fill=CREAM, anchor="mm")
    else:
        raise SystemExit(f"unknown style {style}")
    d = ImageDraw.Draw(img)
    footer(d, spec.get("cta"), spec.get("cta_sub"))
    img.convert("RGB").save(out, quality=92)
    print(out)

if __name__ == "__main__":
    spec = json.load(open(sys.argv[1], encoding="utf-8"))
    make(spec, sys.argv[2])
