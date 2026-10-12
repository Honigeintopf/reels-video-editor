"""Tiny helpers to write HyperFrames compositions from Python."""
import os, shutil, html
from common import *
FPS = 30
def q(t): return round(round(t * FPS) / FPS, 4)
def esc(s): return html.escape(s)
def at(word, near, ws=None):
    """Start time of `word` closest to `near` seconds. Hang every cue on this, never hard-code times."""
    ws = ws or words()
    c = [w for w in ws if strip_punct(w["t"]).lower() == word.lower()]
    w = min(c, key=lambda w: abs(w["s"] - near)); assert abs(w["s"] - near) < 1.0, (word, near, w["s"])
    return w["s"]
def clip(id_, start, end, inner, cls="", z=5):
    return (f'<div id="{id_}" class="clip {cls}" style="z-index:{z}" data-start="{q(start)}" '
            f'data-duration="{q(end - start)}">{inner}</div>')
def setup_public(pub, base="base_1080.mp4", fonts=(), extra=(), three=False):
    os.makedirs(pub + "/fonts", exist_ok=True); os.makedirs(pub + "/vendor", exist_ok=True); os.makedirs(pub + "/assets", exist_ok=True)
    def cp(src, dst):
        if not os.path.exists(dst) or os.path.getsize(dst) != os.path.getsize(src): shutil.copy(src, dst)
    cp(BASIS + "/" + base, pub + "/base.mp4")
    cp(ASSETS + "/vendor/gsap.min.js", pub + "/vendor/gsap.min.js")
    if three: cp(ASSETS + "/vendor/three.min.js", pub + "/vendor/three.min.js")
    for f in fonts: cp(FONTS + "/" + f, pub + "/fonts/" + f)
    for src, name in extra: cp(src, pub + "/assets/" + name)
def page(comp_id, css, body, js, dur=None, lang="de"):
    dur = dur or DUR
    return f"""<!doctype html>
<html lang="{lang}"><head><meta charset="utf-8"><style>
{css}
</style></head><body>
<div id="root" data-composition-id="{comp_id}" data-start="0" data-duration="{dur}" data-fps="{FPS}" data-width="1080" data-height="1920">
{body}
<script src="vendor/gsap.min.js"></script>
<script>
const tl = gsap.timeline({{ paused: true }});
{js}
window.__timelines = window.__timelines || {{}};
window.__timelines["{comp_id}"] = tl;
</script>
</div></body></html>
"""
HF_DIR = os.environ.get("HF_DIR", os.path.dirname(ROOT) + "/_tools")
def hf(*args):
    npx = ["cmd", "/c", "npx"] if os.name == "nt" else ["npx"]
    run([*npx, "hyperframes", *args], cwd=HF_DIR)

def snapshot(here, times, pub="public"):
    """Single frames + contact sheet in <pub>/snapshots/ (seconds). Check these before a full render."""
    hf("snapshot", here + "/" + pub, "--at", ",".join(f"{t:.2f}" for t in times))

def finish(here, pub="public", quality="delivery", hq=True):
    """Render HyperFrames project, normalize to -14 LUFS, export preview + contact sheet.
    hq=True: lossless PNG frame extraction, CRF 10 render, video stream copied (no re-encode), 2-pass preview."""
    raw = here + "/work/raw.mp4"; os.makedirs(here + "/work", exist_ok=True)
    if hq:
        hf("render", here + "/" + pub, "-o", raw, "--crf", "10", "--fps", "30", "--video-frame-format", "png", "--quiet")
        run([FF, "-y", "-v", "error", "-i", raw, "-c:v", "copy", "-af", "loudnorm=I=-14:TP=-1.5:LRA=9",
             "-c:a", "aac", "-b:a", "320k", "-ar", "48000", "-movflags", "+faststart", here + "/render.mp4"])
    else:
        hf("render", here + "/" + pub, "-o", raw, "--quality", quality, "--fps", "30", "--quiet")
        run([FF, "-y", "-v", "error", "-i", raw, "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p", "-r", "30",
             "-af", "loudnorm=I=-14:TP=-1.5:LRA=9", "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-movflags", "+faststart",
             here + "/render.mp4"])
    export_hq(here + "/render.mp4", here + "/preview.mp4", here + "/work")
    contact_sheet(here + "/render.mp4", here + "/kontaktbogen.png")
