"""Original budots-style dance beat (synthesised from scratch, royalty-free).
Usage: python3 tools/budots_track.py out.wav [duration] [seed] [riser_time]"""
import sys, numpy as np, wave
SR = 44100
out = sys.argv[1]; DUR = float(sys.argv[2]) if len(sys.argv) > 2 else 15.0
seed = int(sys.argv[3]) if len(sys.argv) > 3 else 1; RISE = float(sys.argv[4]) if len(sys.argv) > 4 else None
rng = np.random.default_rng(seed)
BPM = 124; beat = 60 / BPM; step = beat / 4
N = int(SR * DUR); mix = np.zeros(N)
def add(sig, t, g=1.0):
    i = int(t * SR); j = min(N, i + len(sig))
    if i < N: mix[i:j] += sig[:j - i] * g
def env(n, a=0.002, d=0.15):
    t = np.arange(n) / SR; return np.minimum(t / a, 1) * np.exp(-t / d)
def kick():
    n = int(0.35 * SR); t = np.arange(n) / SR
    f = 50 + 120 * np.exp(-t * 30); return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9)
def clap():
    n = int(0.2 * SR); x = rng.uniform(-1, 1, n) * env(n, 0.001, 0.06)
    return np.convolve(x, np.ones(6) / 6, "same")
def hat(o=False):
    n = int((0.12 if o else 0.04) * SR); x = rng.uniform(-1, 1, n)
    x = np.diff(np.concatenate([[0], x])); return x * env(n, 0.0005, 0.05 if o else 0.012)
def tone(freq, length, wave_="saw", d=0.12):
    n = int(length * SR); t = np.arange(n) / SR
    if wave_ == "saw": x = 2 * ((t * freq) % 1) - 1
    elif wave_ == "sq": x = np.sign(np.sin(2 * np.pi * freq * t))
    else: x = np.sin(2 * np.pi * freq * t)
    return x * env(n, 0.003, d)
hz = lambda m: 440 * 2 ** ((m - 69) / 12)
# chord loop (original): Am - F - C - G, one bar each
prog = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]
bass = [45, 41, 48, 43]
# original hook melody, 16 steps per bar pattern (None = rest)
hook = [[76, None, 74, 76, None, 79, None, 76, 74, None, 72, None, 74, None, None, None],
        [72, None, 72, 74, None, 76, None, 72, 69, None, None, 72, None, 74, None, None]]
bars = int(DUR / (beat * 4)) + 1
for b in range(bars):
    t0 = b * beat * 4; ch = prog[b % 4]; intro = b == 0
    for s in range(16):
        t = t0 + s * step
        # budots kick: four-on-floor plus syncopated pickup
        if s in (0, 4, 8, 12) or (s == 14 and b % 2): add(kick(), t, 0.9)
        if not intro:
            if s in (4, 12): add(clap(), t, 0.5)
            add(hat(s % 4 == 2), t, 0.18 if s % 2 else 0.1)
            if s in (2, 6, 10, 14):  # offbeat chord stabs
                for m in ch: add(tone(hz(m + 12), step * 1.5, "sq", 0.07), t, 0.07)
            if s in (0, 3, 6, 8, 11, 14):  # bouncy bass
                add(tone(hz(bass[b % 4]), step * 2, "sin", 0.18), t, 0.45)
            if b >= 2:
                m = hook[b % 2][s]
                if m: add(tone(hz(m), step * 1.6, "saw", 0.1), t, 0.11)
        else:
            if s % 4 == 2:
                for m in ch: add(tone(hz(m + 12), step * 1.5, "sq", 0.07), t, 0.06)
if RISE:  # noise riser into the end card
    n = int(1.0 * SR); x = rng.uniform(-1, 1, n) * np.linspace(0, 1, n) ** 2
    add(np.convolve(x, np.ones(4) / 4, "same"), RISE - 1.0, 0.25)
# fade out
f = int(1.2 * SR); mix[-f:] *= np.linspace(1, 0, f)
mix = np.tanh(mix * 1.4); mix /= np.max(np.abs(mix)) * 1.05
st = np.stack([mix, np.roll(mix, 30)], 1)
with wave.open(out, "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((st * 32767).astype(np.int16).tobytes())
print(out)
