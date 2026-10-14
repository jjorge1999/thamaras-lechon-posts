#!/usr/bin/env python3
"""Make a 15s 1080x1350 promo video from the lechon photo (Ken Burns + text beats + fire-crackle audio).
Usage: python3 tools/make_video.py out.mp4"""
import os, sys, subprocess, tempfile, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H, FPS, DUR = 1080, 1350, 30, 15.0
GOLD=(240,196,98); MAROON=(92,15,5); CREAM=(255,246,224); YEL=(255,225,77); DARK=(38,12,6)
F = lambda k,s: ImageFont.truetype({"b":"/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf","r":"/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf","s":"/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"}[k], s)

src = Image.open(os.path.join(HERE, "assets", "lechon_whole.jpg")).convert("RGB")
# upscale once so crops stay sharp-ish
base = src.resize((src.width*2, src.height*2), Image.LANCZOS)
base = ImageEnhance.Contrast(base).enhance(1.08)

# beats: (start, end, crop start (cx,cy,zoom), crop end, line1, line2)
BEATS = [
 (0.0, 3.6, (0.62,0.55,1.00),(0.55,0.52,1.18), "ALAS 3 SA BUNTAG", "nag-ihaw na mi"),
 (3.6, 7.2, (0.30,0.45,1.25),(0.22,0.40,1.45), "Crispy sa gawas.", "Juicy sa sulod."),
 (7.2,10.8, (0.70,0.60,1.30),(0.45,0.55,1.05), "Bida sa imong handaan", "Birthday  •  Fiesta  •  Reunion"),
 (10.8,15.0,(0.50,0.52,1.05),(0.50,0.52,1.12), None, None),
]

def ease(t): return t*t*(3-2*t)

def photo_frame(cx, cy, z):
    # crop region with aspect W:H from base; z>=1 zooms in
    bw, bh = base.size
    ch = bh / z; cw = ch * W / H
    if cw > bw: cw = bw; ch = cw * H / W
    x0 = min(max(cx*bw - cw/2, 0), bw - cw); y0 = min(max(cy*bh - ch/2, 0), bh - ch)
    return base.crop((int(x0), int(y0), int(x0+cw), int(y0+ch))).resize((W, H), Image.BILINEAR)

def overlay(img, t, beat):
    s, e, _, _, l1, l2 = beat
    img = img.convert("RGBA")
    shade = Image.new("RGBA", (W, H), (0,0,0,0)); sd = ImageDraw.Draw(shade)
    for i in range(H):  # top + bottom vignette
        a = 0
        if i < 520: a = int(200 * (1 - i/520))
        if i > H-360: a = max(a, int(210 * (i-(H-360))/360))
        sd.line([(0,i),(W,i)], fill=(20,6,2,a))
    img = Image.alpha_composite(img, shade)
    d = ImageDraw.Draw(img)
    d.text((W//2, 70), "THAMARA'S LECHON", font=F("s",50), fill=GOLD, anchor="mm", stroke_width=2, stroke_fill=MAROON)
    if l1:
        k = min(1.0, (t - s) / 0.45)  # slide/fade in
        a = int(255 * ease(k)); dy = int(40 * (1 - ease(k)))
        txt = Image.new("RGBA", (W, H), (0,0,0,0)); td = ImageDraw.Draw(txt)
        f1 = F("b", 84 if len(l1) <= 18 else 70)
        td.text((W//2, 230+dy), l1, font=f1, fill=YEL+(a,), anchor="mm", stroke_width=6, stroke_fill=MAROON+(a,))
        k2 = min(1.0, max(0.0, (t - s - 0.5) / 0.45)); a2 = int(255 * ease(k2))
        td.text((W//2, 330), l2, font=F("b", 52 if len(l2) <= 20 else 40), fill=CREAM+(a2,), anchor="mm", stroke_width=4, stroke_fill=MAROON+(a2,))
        img = Image.alpha_composite(img, txt)
        d = ImageDraw.Draw(img)
        d.text((W//2, H-60), "Lapinigan, San Francisco, Agusan del Sur", font=F("r", 28), fill=CREAM, anchor="mm")
    else:
        k = min(1.0, (t - s) / 0.5); a = int(235 * ease(k))
        card = Image.new("RGBA", (W, H), (0,0,0,0)); cd = ImageDraw.Draw(card)
        cd.rectangle((0, 0, W, H), fill=(30,9,4,int(a*0.55)))
        cd.rounded_rectangle((90, 760, 990, 1180), radius=36, fill=(28,9,4,a), outline=GOLD+(a,), width=4)
        img = Image.alpha_composite(img, card); d = ImageDraw.Draw(img)
        if k > 0.4:
            d.text((W//2, 300), "Naa kay handaan", font=F("b", 78), fill=YEL, anchor="mm", stroke_width=6, stroke_fill=MAROON)
            d.text((W//2, 400), "this weekend?", font=F("b", 78), fill=YEL, anchor="mm", stroke_width=6, stroke_fill=MAROON)
            d.text((W//2, 840), "Whole Lechon  •  Lechon Belly", font=F("b", 40), fill=GOLD, anchor="mm")
            pulse = 1 + 0.03*np.sin((t-s)*6)
            bw, bh = int(780*pulse), int(120*pulse)
            d.rounded_rectangle((W//2-bw//2, 920-bh//2+40, W//2+bw//2, 920+bh//2+40), radius=bh//2, fill=YEL, outline=MAROON, width=5)
            d.text((W//2, 948), "MESSAGE LANG MI", font=F("b", 50), fill=MAROON, anchor="mm")
            d.text((W//2, 1000), "para ma-reserve!", font=F("r", 32), fill=MAROON, anchor="mm")
            d.text((W//2, 1110), "(0951) 781 4902", font=F("b", 52), fill=CREAM, anchor="mm")
            d.text((W//2, H-70), "Lapinigan, San Francisco, Agusan del Sur", font=F("r", 30), fill=CREAM, anchor="mm")
    return img.convert("RGB")

def audio(path):
    sr = 44100; n = int(sr*DUR); rng = np.random.default_rng(20261014)
    brown = np.cumsum(rng.normal(0, 1, n)); brown -= np.convolve(brown, np.ones(2000)/2000, mode="same")
    brown = brown / (np.abs(brown).max()+1e-9) * 0.10
    crackle = np.zeros(n)
    for _ in range(int(DUR*9)):
        i = rng.integers(0, n-800); L = rng.integers(60, 600)
        crackle[i:i+L] += rng.normal(0, 1, L) * np.exp(-np.linspace(0, 6, L)) * rng.uniform(0.15, 0.55)
    t = np.arange(n)/sr
    # warm pad: Am - F - C - G, one per ~3.75s
    chords = [(220,261.6,329.6),(174.6,220,261.6),(130.8,164.8,196),(196,246.9,293.7)]
    pad = np.zeros(n)
    for ci, ch in enumerate(chords):
        a, b = int(ci*n/4), int((ci+1)*n/4); tt = t[a:b]-t[a]
        env = np.minimum(1, tt/0.6) * np.minimum(1, (tt[-1]-tt)/0.6+0.05)
        pad[a:b] = sum(np.sin(2*np.pi*f*tt)*0.5+np.sin(2*np.pi*f*2*tt)*0.12 for f in ch) * env
    pad = pad/ (np.abs(pad).max()+1e-9) * 0.16 * np.minimum(1, t/2.0)
    mix = brown + crackle*0.6 + pad
    fade = np.minimum(1, (DUR - t)/1.2); mix *= fade
    mix = np.clip(mix/ (np.abs(mix).max()+1e-9) * 0.8, -1, 1)
    data = (mix*32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(data.tobytes())

def main(out):
    tmp = tempfile.mkdtemp()
    nframes = int(DUR*FPS)
    for fi in range(nframes):
        t = fi / FPS
        bi = next(i for i,b in enumerate(BEATS) if b[0] <= t < b[1]) if t < DUR else len(BEATS)-1
        s, e, a, b, *_ = BEATS[bi]; p = ease((t - s) / (e - s))
        cx, cy, z = [a[k] + (b[k]-a[k])*p for k in range(3)]
        fr = overlay(photo_frame(cx, cy, z), t, BEATS[bi])
        # crossfade into next beat during last 0.3s
        if bi < len(BEATS)-1 and e - t < 0.3:
            nb = BEATS[bi+1]; nfr = overlay(photo_frame(*nb[2]), nb[0], nb)
            fr = Image.blend(fr, nfr, 1 - (e - t)/0.3)
        fr.save(f"{tmp}/f{fi:04d}.jpg", quality=92)
    audio(f"{tmp}/a.wav")
    subprocess.run(["ffmpeg","-y","-loglevel","error","-framerate",str(FPS),"-i",f"{tmp}/f%04d.jpg","-i",f"{tmp}/a.wav",
        "-c:v","libx264","-pix_fmt","yuv420p","-profile:v","high","-crf","20","-c:a","aac","-b:a","160k",
        "-shortest","-movflags","+faststart",out], check=True)
    print(out)

if __name__ == "__main__":
    main(sys.argv[1])
