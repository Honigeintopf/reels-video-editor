"""Shared helpers for one video project.

Copy this folder to <videoordner>/<video>/_scripts/ . Expected layout:
  <videoordner>/_assets/        fonts, sfx, emoji, vendor (gsap.min.js, three.min.js)
  <videoordner>/_tools/         npm project with hyperframes installed
  <videoordner>/<video>/_basis/ base_1080.mp4, voice.wav, words.json, fg.webm ...
  <videoordner>/<video>/NN-variante/build.py
"""
import json, os, shutil, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("VIDEO_ROOT", os.path.dirname(HERE)).replace("\\", "/")
BASIS = ROOT + "/_basis"
ASSETS = os.environ.get("VIDEO_ASSETS", os.path.dirname(ROOT) + "/_assets").replace("\\", "/")
FONTS = ASSETS + "/fonts"

def _tool(name):
    """ffmpeg/ffprobe: FFMPEG_DIR env var, else PATH (winget installs are often missing from the Bash PATH)."""
    d = os.environ.get("FFMPEG_DIR")
    if d:
        return os.path.join(d, name + (".exe" if os.name == "nt" else ""))
    p = shutil.which(name)
    if not p:
        raise SystemExit(f"{name} nicht gefunden: FFMPEG_DIR setzen oder ffmpeg in den PATH legen")
    return p
FF = _tool("ffmpeg"); FP = _tool("ffprobe")

def duration(mp4):
    return float(subprocess.check_output([FP, "-v", "error", "-show_entries", "format=duration",
                                          "-of", "csv=p=0", mp4]).decode().strip())
DUR = duration(BASIS + "/base_1080.mp4") if os.path.exists(BASIS + "/base_1080.mp4") else None
HOOK = None  # set per variant in build.py

def words():
    return json.load(open(BASIS + "/words.json", encoding="utf-8"))

def chunks(max_words=4, max_chars=24, max_gap=0.35):
    """Group words into caption phrases; break at punctuation, long gaps, length."""
    ws = words(); out = []; cur = []
    for i, w in enumerate(ws):
        cur.append(w)
        txt = " ".join(x["t"] for x in cur)
        nxt = ws[i + 1] if i + 1 < len(ws) else None
        brk = (nxt is None or w["t"][-1] in ".,?!" or len(cur) >= max_words
               or len(txt) + 1 + len(nxt["t"]) > max_chars or nxt["s"] - w["e"] > max_gap)
        if brk:
            out.append({"s": cur[0]["s"], "e": cur[-1]["e"], "words": cur, "t": txt})
            cur = []
    # extend each chunk towards the next one (no flicker, no overlap), max +0.4 s
    for a, b in zip(out, out[1:]):
        a["e"] = min(b["s"] - 0.04, a["e"] + 0.4)
    out[-1]["e"] = min(DUR or 1e9, out[-1]["e"] + 0.5)
    return out

def strip_punct(t):
    return t.rstrip(".,!?")

def run(args, **kw):
    print(" ".join(str(a) for a in args)[:300], "...")
    subprocess.run([str(a) for a in args], check=True, **kw)

def export(render_mp4, preview_mp4):
    """Quick 1-pass preview (only for drafts; looks soft on phones, prefer export_hq)."""
    run([FF, "-y", "-v", "error", "-i", render_mp4, "-c:v", "libx264", "-preset", "slow", "-crf", "25",
         "-maxrate", "3.6M", "-bufsize", "7M", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
         "-movflags", "+faststart", preview_mp4])

def export_hq(render_mp4, preview_mp4, workdir, video_kbps=None):
    """2-pass H.264 phone preview that uses the full <30 MB budget (SendUserFile limit)."""
    if video_kbps is None:  # 28 MB total, minus 160k audio
        video_kbps = min(6000, int(28 * 8 * 1024 / duration(render_mp4) - 170))
    log = workdir + "/2pass"
    base = [FF, "-y", "-v", "error", "-i", render_mp4, "-c:v", "libx264", "-preset", "veryslow", "-tune", "film",
            "-b:v", f"{video_kbps}k", "-pix_fmt", "yuv420p", "-passlogfile", log]
    run(base + ["-pass", "1", "-an", "-f", "mp4", os.devnull])
    run(base + ["-pass", "2", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", preview_mp4])

def contact_sheet(mp4, png, n=12, cols=6):
    step = duration(mp4) / n
    run([FF, "-y", "-v", "error", "-i", mp4, "-vf",
         f"fps=1/{step:.3f},scale=270:480,tile={cols}x{(n + cols - 1)//cols}:padding=6:margin=6:color=0x111111",
         "-frames:v", "1", png])

def ass_time(t):
    t = max(0, t); h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"

# Safe zones for 1080x1920 (union of Instagram Reels + TikTok UI). Bottom checked on a real post.
SAFE = {"top": 270, "bottom": 1680, "left": 65, "right": 940}

def safe_overlay(png_in, png_out):
    """Tint the platform-UI zones red on a 1080x1920 frame (or a snapshot of it) to check layouts."""
    from PIL import Image, ImageDraw
    im = Image.open(png_in).convert("RGBA"); sx, sy = im.width / 1080, im.height / 1920
    ov = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(ov); red = (255, 40, 40, 90)
    d.rectangle([0, 0, im.width, SAFE["top"] * sy], fill=red)
    d.rectangle([0, SAFE["bottom"] * sy, im.width, im.height], fill=red)
    d.rectangle([0, SAFE["top"] * sy, SAFE["left"] * sx, SAFE["bottom"] * sy], fill=red)
    d.rectangle([SAFE["right"] * sx, SAFE["top"] * sy, im.width, SAFE["bottom"] * sy], fill=red)
    im.alpha_composite(ov); im.convert("RGB").save(png_out)
