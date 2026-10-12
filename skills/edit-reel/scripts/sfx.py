# Synthesized SFX (no licensing needed): whoosh, pop, click, riser, impact, key, ding, shutter, glitch, swoosh_up
import numpy as np, wave, sys, os
SR = 48000; out = sys.argv[1]; rng = np.random.default_rng(7)
def save(name, x):
    x = x / (np.max(np.abs(x)) + 1e-9) * 0.89
    st = np.stack([x, x], 1)
    w = wave.open(os.path.join(out, name + ".wav"), "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((st * 32767).astype(np.int16).tobytes()); w.close()
def t(d): return np.arange(int(SR * d)) / SR
def env(n, a, r):
    e = np.ones(n); A = int(a * SR); R = int(r * SR)
    if A: e[:A] = np.linspace(0, 1, A)
    if R: e[-R:] *= np.linspace(1, 0, R) ** 2
    return e
def bandsweep(x, f0, f1):
    # crude moving resonant filter: per-block FFT bandpass
    n = len(x); blk = 1024; y = np.zeros(n + blk)
    win = np.hanning(blk)
    for i in range(0, n - blk, blk // 2):
        fc = f0 * (f1 / f0) ** (i / n)
        X = np.fft.rfft(x[i:i + blk] * win); f = np.fft.rfftfreq(blk, 1 / SR)
        X *= np.exp(-((np.log(f + 1) - np.log(fc)) ** 2) / 0.35)
        y[i:i + blk] += np.fft.irfft(X)
    return y[:n]
n = rng.standard_normal(int(SR * 0.6))
save("whoosh", bandsweep(n, 300, 4000) * np.sin(np.linspace(0, np.pi, len(n))) ** 1.5)
n = rng.standard_normal(int(SR * 0.45))
save("whoosh_down", bandsweep(n, 5000, 250) * np.sin(np.linspace(0, np.pi, len(n))) ** 1.5)
tt = t(0.12); f = 900 * np.exp(-tt * 25) + 300
save("pop", np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 40))
tt = t(0.04); save("click", rng.standard_normal(len(tt)) * np.exp(-tt * 300) + np.sin(2 * np.pi * 3000 * tt) * np.exp(-tt * 200))
tt = t(2.0); f = 120 * (16 ** (tt / 2)); ri = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.4 + bandsweep(rng.standard_normal(len(tt)), 200, 6000) * 0.6
save("riser", ri * (tt / 2) ** 2)
tt = t(1.2); f = 55 * np.exp(-tt * 3) + 35
save("impact", np.tanh(3 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 3.5)) + rng.standard_normal(len(tt)) * np.exp(-tt * 30) * 0.6)
tt = t(0.05); save("key", (rng.standard_normal(len(tt)) * 0.5 + np.sin(2 * np.pi * 1800 * tt)) * np.exp(-tt * 140))
tt = t(1.4); save("ding", (np.sin(2 * np.pi * 1318 * tt) + 0.5 * np.sin(2 * np.pi * 2637 * tt) + 0.25 * np.sin(2 * np.pi * 3951 * tt)) * np.exp(-tt * 3.5))
tt = t(0.25); sh = rng.standard_normal(len(tt)) * (np.exp(-tt * 60) + 0.7 * np.exp(-np.maximum(tt - 0.09, 0) * 60) * (tt > 0.09))
save("shutter", sh)
tt = t(0.35); g = np.sign(np.sin(2 * np.pi * 180 * tt)) * (rng.random(len(tt)) > 0.5) + rng.standard_normal(len(tt)) * 0.4
g *= np.repeat(rng.random(len(tt) // 800 + 1) > 0.4, 800)[:len(tt)]
save("glitch", g * env(len(tt), 0.005, 0.05))
tt = t(0.18); f = 400 + 2200 * tt / 0.18
save("swipe_up", np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.linspace(0, np.pi, len(tt))) * 0.6)
print("ok")
