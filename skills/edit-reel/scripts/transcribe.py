"""Transcript with word timings + pause candidates.

usage: python transcribe.py <_basis-ordner> [sprache]
needs: <_basis>/voice.wav (48 kHz, already cleaned). Writes transcript.json, words.json,
sentences.json, pauses.json. Correct technical terms in FIX and re-run with --no-whisper.
Model: WHISPER_MODEL env var (default large-v3; medium/small are faster, slightly less exact).
"""
import sys, os, json, wave
import numpy as np
FIX = {}  # e.g. {"Loadbalancing": "Load Balancing"}

basis = sys.argv[1]; lang = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith("--") else "de"
os.chdir(basis)
if "--no-whisper" not in sys.argv:
    from faster_whisper import WhisperModel
    model = os.environ.get("WHISPER_MODEL", "large-v3")
    try:
        m = WhisperModel(model, device="cuda", compute_type="float16")
    except Exception as e:  # no NVIDIA GPU (e.g. every Mac) or missing cublas64_12.dll on Windows
        print("CUDA nicht nutzbar, nehme CPU:", e, file=sys.stderr)
        m = WhisperModel(model, device="cpu", compute_type="int8")
    segs, info = m.transcribe("voice.wav", language=lang, word_timestamps=True, vad_filter=False, beam_size=5)
    tr = []
    for s in segs:
        w = [{"w": x.word, "s": round(x.start, 2), "e": round(x.end, 2), "p": round(x.probability, 2)} for x in s.words]
        tr.append({"s": round(s.start, 2), "e": round(s.end, 2), "t": s.text, "words": w})
        print(f"[{s.start:6.2f}-{s.end:6.2f}] {s.text}")
    json.dump(tr, open("transcript.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
tr = json.load(open("transcript.json", encoding="utf-8"))

words = []
for s in tr:
    for w in s["words"]:
        t = w["w"].strip()
        for k, v in FIX.items(): t = t.replace(k, v)
        words.append({"t": t, "s": w["s"], "e": w["e"]})
# whisper start drift: a word may not start before the previous one ends
for a, b in zip(words, words[1:]):
    if b["s"] < a["e"]: b["s"] = a["e"]
json.dump(words, open("words.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
sents = [{"s": s["words"][0]["s"], "e": s["words"][-1]["e"], "t": s["t"].strip()} for s in tr if s["words"]]
for x in sents:
    for k, v in FIX.items(): x["t"] = x["t"].replace(k, v)
json.dump(sents, open("sentences.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# pauses via RMS envelope (silencedetect is unreliable on quiet phone audio)
w = wave.open("voice.wav"); sr = w.getframerate(); ch = w.getnchannels()
a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
if ch > 1: a = a.reshape(-1, ch).mean(1)
hop = int(sr * 0.01); n = len(a) // hop
db = 20 * np.log10(np.sqrt(np.mean(a[:n * hop].reshape(n, hop) ** 2, axis=1) + 1e-12))
thr = np.percentile(db, 10) + 10
q = db < thr; gaps = []; i = 0
while i < n:
    if q[i]:
        j = i
        while j < n and q[j]: j += 1
        if j - i >= 15: gaps.append((round(i / 100, 2), round(j / 100, 2)))
        i = j
    else: i += 1
json.dump(gaps, open("pauses.json", "w"))
print("Wörter:", len(words), "| Pausen-Schwelle", round(thr, 1), "dB |", len(gaps), "Pausen")
