#!/usr/bin/env python3
"""Thamara's brand-style Facebook graphic (matches the owner's Nov 2026 banners).

Layout: dark bokeh background, gold serif header with sparkles, outlined white
headline with doodle rays, script subline with hand-drawn underline, hero food
photo, optional red badge, gold line-icon bullets, yellow CTA pill, footer.

Usage:  python3 make_brand_post.py spec.json out.jpg

spec.json fields
  tag       small yellow pill under the header (e.g. "LECHON PARA SA HANDAAN") [optional]
  headline  big hook, 1-2 lines (keep under ~28 chars per line)
  sub       one script line under the headline
  hero      "lechon" | "bowls" | "palamig" | path to an image in the repo     [optional]
  badge     short text in the red badge, "\n" for a line break (e.g. "I-RESERVE\nNA!") [optional]
  items     up to 3 bullets: {"icon": "fire|bag|bowl|calendar|chat|pin|clock|heart|check|gift",
            "text": "**gold part** normal part"}  (a plain string uses the "check" icon)
  cta       text in the yellow pill (e.g. "MESSAGE LANG MI")
  seed      optional int, changes the bokeh pattern (default: from the headline)
Prices are blocked: any peso amount in the spec aborts (owner rule for daily posts).
Pass --allow-prices only for owner-approved promo banners.
"""
import base64, json, os, random, re, sys, tempfile
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "assets", "fonts", "brand")
HERO = os.path.join(HERE, "assets", "hero")
PHONE = "(0951) 781 4902"
PLACE = "Thamara’s Lechon & Carinderia, Lapinigan, San Francisco, Agusan del Sur"
PRICE_RE = re.compile(r"(₱|php|\bp\s?\d|\d+\s?(pesos?|php))", re.I)

ICONS = {  # 64x64 line icons, drawn with stroke="currentColor"
    "bag": '<path d="M14 22h36l-3 34H17z"/><path d="M24 22c0-8 4-13 8-13s8 5 8 13"/><path d="M24 36h16M24 44h10"/>',
    "bowl": '<path d="M8 32h48c0 14-10 22-24 22S8 46 8 32z"/><path d="M18 26c2-8 8-11 14-11s12 3 14 11"/><path d="M22 58h20"/>',
    "calendar": '<rect x="9" y="14" width="46" height="42" rx="6"/><path d="M9 26h46M21 8v12M43 8v12"/><path d="M20 36h4M30 36h4M40 36h4M20 46h4M30 46h4M40 46h4"/>',
    "fire": '<path d="M32 6c2 10 14 16 14 30a14 14 0 0 1-28 0c0-7 4-10 7-14 1 5 3 7 6 8-2-8-1-16 1-24z"/><path d="M26 48c0-5 4-6 6-10 4 3 6 6 6 10a6 6 0 0 1-12 0z"/>',
    "chat": '<path d="M10 14h44a4 4 0 0 1 4 4v26a4 4 0 0 1-4 4H30L18 58V48h-8a4 4 0 0 1-4-4V18a4 4 0 0 1 4-4z"/><path d="M18 27h28M18 36h18"/>',
    "pin": '<path d="M32 58S14 40 14 26a18 18 0 0 1 36 0c0 14-18 32-18 32z"/><circle cx="32" cy="26" r="7"/>',
    "clock": '<circle cx="32" cy="32" r="24"/><path d="M32 16v17l11 7"/>',
    "heart": '<path d="M32 54S8 38 8 22a12 12 0 0 1 24-3 12 12 0 0 1 24 3c0 16-24 32-24 32z"/>',
    "check": '<circle cx="32" cy="32" r="24"/><path d="M20 33l8 8 16-18"/>',
    "gift": '<rect x="8" y="24" width="48" height="12" rx="3"/><path d="M12 36v20h40V36M32 24v32"/><path d="M32 24c-8 0-14-3-14-8s8-6 14 8c6-14 14-13 14-8s-6 8-14 8z"/>',
}


def b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def bokeh(seed, path, w=1080, h=1350):
    """Warm blurred-light background like the owner's banners."""
    rnd = random.Random(seed)
    base = Image.new("RGB", (w, h), (52, 30, 14))
    glow = Image.new("RGB", (w, h), (0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse((-200, 380, w + 200, h + 300), fill=(132, 76, 28))
    glow = glow.filter(ImageFilter.GaussianBlur(220))
    base = Image.blend(base, glow, 0.9)
    layer = Image.new("RGB", (w, h), (0, 0, 0))
    d = ImageDraw.Draw(layer)
    palette = [(255, 196, 90), (255, 160, 60), (240, 210, 120), (120, 150, 70), (255, 120, 50)]
    for _ in range(60):
        r = rnd.randint(18, 70)
        x, y = rnd.randint(-40, w + 40), rnd.randint(-40, h + 40)
        c = rnd.choice(palette)
        k = rnd.uniform(0.22, 0.55)
        d.ellipse((x - r, y - r, x + r, y + r), fill=tuple(int(v * k) for v in c))
    layer = layer.filter(ImageFilter.GaussianBlur(24))
    out = Image.eval(Image.blend(base, layer, 0.6), lambda v: v)
    # vignette
    vg = Image.new("L", (w, h), 0)
    ImageDraw.Draw(vg).ellipse((-260, -200, w + 260, h + 200), fill=255)
    vg = vg.filter(ImageFilter.GaussianBlur(200))
    dark = Image.new("RGB", (w, h), (30, 16, 7))
    out = Image.composite(out, dark, vg)
    out.save(path, quality=92)


def icon_svg(name):
    body = ICONS.get(name, ICONS["check"])
    return ('<svg viewBox="0 0 64 64" width="70" height="70" fill="none" stroke="#f0c462" '
            'stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round">%s</svg>' % body)


def md(text):
    t = (text.replace("&", "&amp;").replace("<", "&lt;"))
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)


SPARK = ('<svg viewBox="0 0 40 40" width="%d" height="%d" fill="none" stroke="#f0c462" stroke-width="2.4" '
         'stroke-linejoin="round"><path d="M20 3c1.5 9 5 15 17 17-12 2-15.500 8-17 17-1.500-9-5-15-17-17 12-2 15.500-8 17-17z"/></svg>')
RAYS_L = ('<svg viewBox="0 0 90 90" width="96" height="96" stroke="#f0c462" stroke-width="5" stroke-linecap="round">'
          '<path d="M10 52l24-6M18 28l22 12M42 8l8 24"/></svg>')
RAYS_R = ('<svg viewBox="0 0 90 90" width="96" height="96" stroke="#f0c462" stroke-width="5" stroke-linecap="round">'
          '<path d="M80 52L56 46M72 28L50 40M48 8l-8 24"/></svg>')
MEGA = ('<svg viewBox="0 0 64 64" width="66" height="66" fill="none" stroke="#7a1d0c" stroke-width="3.4" '
        'stroke-linecap="round" stroke-linejoin="round"><path d="M10 26h12l24-12v36L22 38H10z"/>'
        '<path d="M22 38l4 14h8l-4-14"/><path d="M52 24c3 3 3 13 0 16M57 19c6 6 6 20 0 26"/></svg>')
PHONE_SVG = ('<svg viewBox="0 0 64 64" width="26" height="26" fill="#fff6e0"><path d="M16 6l10 4 2 12-6 4c4 8 8 12 16 16l4-6 12 2 4 10c0 6-6 10-12 10C26 58 6 38 6 18c0-6 4-12 10-12z"/></svg>')


def build_html(spec, bg_path, hero_path):
    tag = spec.get("tag")
    headline = spec.get("headline", "")
    lines = [l for l in headline.split("\n") if l.strip()] or [headline]
    longest = max(len(l) for l in lines)
    hsize = 150 if longest <= 11 else 132 if longest <= 15 else 112 if longest <= 20 else 96 if longest <= 26 else 82
    items = spec.get("items", [])[:3]
    rows = []
    for it in items:
        if isinstance(it, str):
            it = {"icon": "check", "text": it}
        rows.append('<div class="row"><div class="ic">%s</div><div class="tx">%s</div></div>'
                    % (icon_svg(it.get("icon", "check")), md(it["text"])))
    badge = ""
    if spec.get("badge"):
        bt = "<br>".join(md(x) for x in spec["badge"].split("\n"))
        badge = ('<div class="badge"><svg class="rim" viewBox="0 0 200 200"><defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">'
                 '<stop offset="0" stop-color="#ffe08a"/><stop offset="1" stop-color="#c8891b"/></linearGradient></defs>'
                 '%s<circle cx="100" cy="100" r="80" fill="#b3261e" stroke="#ffe08a" stroke-width="3"/></svg>'
                 '<div class="stars">★ ★ ★</div><div class="bt">%s</div></div>' % (
                     "".join('<circle cx="%.1f" cy="%.1f" r="9" fill="url(#g)"/>' % (
                         100 + 92 * __import__("math").cos(i * 3.14159 / 12), 100 + 92 * __import__("math").sin(i * 3.14159 / 12))
                         for i in range(24)) + '<circle cx="100" cy="100" r="92" fill="url(#g)"/>', bt))
    hero = ""
    if hero_path:
        im = Image.open(hero_path)
        wide = im.width / im.height >= 2.5
        mode = "" if wide else (" contain" if spec.get("hero_fit") == "contain" else " cover")
        hero = '<div class="hero%s"><div class="fv"><div class="fh"><img src="data:image/jpeg;base64,%s"></div></div>%s</div>' % (mode, b64(hero_path), badge)
    elif badge:
        hero = '<div class="hero nohero">%s</div>' % badge
    tagh = '<div class="tag">%s</div>' % md(tag) if tag else ""
    sub = spec.get("sub", "")
    cta = spec.get("cta", "MESSAGE LANG MI")
    css_fonts = "".join(
        "@font-face{font-family:'%s';font-weight:%d;src:url(data:font/woff2;base64,%s) format('woff2');}" % (fam, wt, b64(os.path.join(FONTS, fn)))
        for fam, wt, fn in [("PF", 800, "playfair-display-latin-800-normal.woff2"), ("Baloo", 800, "baloo-2-latin-800-normal.woff2"),
                            ("Caveat", 700, "caveat-latin-700-normal.woff2"), ("Pop", 500, "poppins-latin-500-normal.woff2"),
                            ("Pop", 600, "poppins-latin-600-normal.woff2"), ("Pop", 700, "poppins-latin-700-normal.woff2")])
    html = """<!doctype html><html><head><meta charset="utf-8"><style>
%FONTS%
*{box-sizing:border-box;margin:0;padding:0}
html,body{width:1080px;height:1350px;overflow:hidden}
body{background:#1b0f07 url(data:image/jpeg;base64,%BG%) center/cover;font-family:'Pop',sans-serif;color:#fff6e0;position:relative}
.col{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;padding:34px 48px 30px}
.top{position:relative;width:100%;text-align:center}
.brand{font-family:'PF';font-weight:800;font-size:74px;letter-spacing:3px;line-height:1.05;
  background:linear-gradient(180deg,#ffd873 0%,#e9a82e 100%);-webkit-background-clip:text;background-clip:text;color:transparent;
  filter:drop-shadow(0 3px 2px rgba(0,0,0,.55))}
.brandsub{font-weight:500;font-size:24px;letter-spacing:2.5px;margin-top:2px;color:#fff6e0}
.sp{position:absolute}
.tag{margin-top:16px;background:linear-gradient(180deg,#ffd75a,#f3b11f);color:#5a1608;font-weight:700;font-size:30px;
  padding:8px 34px;border-radius:40px;border:3px solid #fff0b8;box-shadow:0 4px 10px rgba(0,0,0,.45);letter-spacing:.5px}
.hl{position:relative;margin-top:22px;text-align:center;width:100%}
.hl h1{font-family:'Baloo';font-weight:800;font-size:%HSIZE%px;line-height:.98;color:#fff;
  -webkit-text-stroke:14px #5a1608;paint-order:stroke fill;text-shadow:0 6px 0 #5a1608,0 10px 18px rgba(0,0,0,.5);letter-spacing:.5px}
.rl{position:absolute;left:-4px;top:-46px;transform:scale(.8)}.rr{position:absolute;right:-4px;top:-46px;transform:scale(.8)}
.sub{font-family:'Caveat';font-weight:700;font-size:50px;color:#ffd873;margin-top:6px;line-height:1.05;text-align:center;
  text-shadow:0 2px 6px rgba(0,0,0,.6)}
.sub span{display:inline-block;padding-bottom:14px;background:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 400 14' preserveAspectRatio='none'><path d='M3 9 C90 2 200 12 397 5' fill='none' stroke='%23f0c462' stroke-width='5' stroke-linecap='round'/></svg>") bottom/100% 12px no-repeat}
.hero{position:relative;width:100%;flex:1 1 auto;min-height:260px;margin-top:6px;display:flex;align-items:center;justify-content:center}
.hero .fv{width:1300px;max-width:none;-webkit-mask-image:linear-gradient(to bottom,transparent 0,#000 12%,#000 90%,transparent 100%);mask-image:linear-gradient(to bottom,transparent 0,#000 12%,#000 90%,transparent 100%)}
.hero .fh{-webkit-mask-image:linear-gradient(to right,transparent 0,#000 14%,#000 86%,transparent 100%);mask-image:linear-gradient(to right,transparent 0,#000 14%,#000 86%,transparent 100%)}
.hero img{display:block;width:100%;height:auto}
.hero.cover{min-height:0}.hero.cover .fv,.hero.cover .fh{width:1080px;height:100%}.hero.cover img{height:100%;object-fit:cover;object-position:%POS%}
.hero.contain .fv,.hero.contain .fh{width:auto;height:100%}.hero.contain img{height:100%;width:auto}
.badge{position:absolute;left:6px;top:-6px;width:206px;height:206px;display:flex;align-items:center;justify-content:center;
  filter:drop-shadow(0 8px 10px rgba(0,0,0,.55));transform:rotate(-6deg)}
.badge .rim{position:absolute;inset:0;width:100%;height:100%}
.badge .stars{position:absolute;top:34px;color:#ffe08a;font-size:20px;letter-spacing:3px}
.badge .bt{position:relative;margin-top:22px;font-family:'Baloo';font-weight:800;font-size:38px;line-height:.95;color:#fff;
  text-align:center;-webkit-text-stroke:7px #6d130d;paint-order:stroke fill}
.nohero{flex:1 1 auto;min-height:260px}.nohero .badge{position:relative;left:0;top:0;width:330px;height:330px;transform:rotate(-5deg)}.nohero .badge .bt{font-size:62px;-webkit-text-stroke:11px #6d130d}.nohero .badge .stars{top:58px;font-size:30px}
.rows{width:100%;padding:0 34px;display:flex;flex-direction:column;gap:20px;margin-top:10px}
.row{display:flex;align-items:center;gap:22px}
.ic{width:70px;height:70px;flex:0 0 70px;filter:drop-shadow(0 2px 3px rgba(0,0,0,.5))}
.tx{font-weight:600;font-size:36px;line-height:1.15;color:#fff6e0;text-shadow:0 2px 6px rgba(0,0,0,.6)}
.tx b{font-weight:700;color:#ffd873}
.cta{margin-top:20px;width:100%;height:104px;border-radius:60px;background:linear-gradient(180deg,#ffe066 0%,#f4b81f 100%);
  border:5px solid #fff0b8;box-shadow:0 8px 18px rgba(0,0,0,.55),inset 0 -6px 0 rgba(160,90,0,.25);
  display:flex;align-items:center;justify-content:center;gap:18px;font-weight:700;font-size:49px;color:#5a1608;letter-spacing:.5px}
.foot{margin-top:14px;text-align:center;font-weight:500;font-size:25px;line-height:1.35;color:#fff6e0;text-shadow:0 2px 5px rgba(0,0,0,.7)}
.foot .ph{display:inline-flex;align-items:center;gap:8px;vertical-align:middle}
</style></head><body><div class="col">
<div class="top">
  <div class="sp" style="left:6px;top:8px">%SP34%</div><div class="sp" style="left:58px;top:70px">%SP22%</div>
  <div class="sp" style="right:6px;top:8px">%SP34%</div><div class="sp" style="right:58px;top:70px">%SP22%</div>
  <div class="brand">THAMARA'S LECHON</div>
  <div class="brandsub">&amp; CARINDERIA &bull; LAPINIGAN</div>
</div>
%TAG%
<div class="hl"><div class="rl">%RL%</div><div class="rr">%RR%</div><h1>%HEAD%</h1></div>
<div class="sub"><span>%SUB%</span></div>
%HERO%
<div class="rows">%ROWS%</div>
<div class="cta">%MEGA%<span>%CTA%</span></div>
<div class="foot">%PLACE%<br><span class="ph">%PHONESVG% %PHONE%</span></div>
</div></body></html>"""
    rep = {"%FONTS%": css_fonts, "%BG%": b64(bg_path), "%HSIZE%": str(hsize),
           "%SP34%": SPARK % (34, 34), "%SP22%": SPARK % (22, 22), "%TAG%": tagh, "%RL%": RAYS_L, "%RR%": RAYS_R,
           "%HEAD%": "<br>".join(md(l) for l in lines), "%SUB%": md(sub), "%HERO%": hero, "%ROWS%": "".join(rows),
           "%MEGA%": MEGA, "%CTA%": md(cta), "%PLACE%": md(spec.get("place", PLACE)), "%POS%": spec.get("hero_pos", "50% 58%"), "%PHONESVG%": PHONE_SVG, "%PHONE%": PHONE}
    for k, v in rep.items():
        html = html.replace(k, v)
    return html


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    allow = "--allow-prices" in sys.argv
    if len(args) != 2:
        raise SystemExit(__doc__)
    spec = json.load(open(args[0], encoding="utf-8"))
    if not allow and PRICE_RE.search(json.dumps(spec, ensure_ascii=False)):
        raise SystemExit("Spec contains a price or peso amount - not allowed for daily posts.")
    hero = spec.get("hero")
    hero_path = None
    if hero:
        hero_path = hero if os.path.exists(hero) else os.path.join(HERO, hero + ".jpg")
        if not os.path.exists(hero_path):
            raise SystemExit("hero image not found: %s" % hero)
    seed = spec.get("seed", sum(ord(c) for c in spec.get("headline", "x")))
    tmp = tempfile.mkdtemp()
    bg = os.path.join(tmp, "bg.jpg")
    bokeh(seed, bg)
    html = build_html(spec, bg, hero_path)
    hp = os.path.join(tmp, "post.html")
    open(hp, "w", encoding="utf-8").write(html)
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        try:
            b = p.chromium.launch()
        except Exception:
            b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium")
        pg = b.new_page(viewport={"width": 1080, "height": 1350}, device_scale_factor=1.5)
        pg.goto("file://" + hp)
        pg.wait_for_timeout(400)
        png = os.path.join(tmp, "out.png")
        pg.screenshot(path=png)
        # overflow check: column content must fit inside the canvas
        over = pg.evaluate("(() => {const c=document.querySelector('.col');return c.scrollHeight - c.clientHeight})()")
        b.close()
    Image.open(png).convert("RGB").save(args[1], quality=92)
    print("saved", args[1], "overflow_px=%s" % over)


if __name__ == "__main__":
    main()
