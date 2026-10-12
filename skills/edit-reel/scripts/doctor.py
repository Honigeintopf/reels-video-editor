"""Check whether this machine has everything the reels-video-editor skill needs.

usage: python doctor.py [videoordner]
Only checks and prints; installs nothing. With [videoordner] it also checks
<videoordner>/_tools (HyperFrames) and <videoordner>/_assets/vendor (GSAP, Three).
Exit code 0 = all required parts found, 1 = something is missing.
"""
import importlib.util, os, platform, shutil, subprocess, sys

OS = platform.system()  # "Darwin", "Windows", "Linux"
missing = []

def ok(name, detail=""): print(f"  ok      {name}{'  ' + detail if detail else ''}")
def bad(name, fix): print(f"  FEHLT   {name}\n          -> {fix}"); missing.append(name)
def opt(name, fix): print(f"  optional {name}\n          -> {fix}")

def version(cmd):
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
        return (out.stdout or out.stderr).strip().splitlines()[0]
    except Exception:
        return ""

INSTALL = {
    "ffmpeg": {"Darwin": "brew install ffmpeg", "Windows": "winget install Gyan.FFmpeg (danach Terminal neu starten)",
               "Linux": "sudo apt install ffmpeg"},
    "node": {"Darwin": "brew install node", "Windows": "winget install OpenJS.NodeJS.LTS",
             "Linux": "https://nodejs.org (LTS) oder Paketmanager"},
}

print(f"System: {OS} {platform.machine()}, Python {platform.python_version()}\n")

print("Programme")
ff_dir = os.environ.get("FFMPEG_DIR")
for tool in ("ffmpeg", "ffprobe"):
    path = os.path.join(ff_dir, tool + (".exe" if os.name == "nt" else "")) if ff_dir else shutil.which(tool)
    if path and os.path.exists(path):
        ok(tool, version([path, "-version"])[:60])
    else:
        bad(tool, INSTALL["ffmpeg"].get(OS, "https://ffmpeg.org") + "  (oder FFMPEG_DIR setzen)")
for tool in ("node", "npx"):
    path = shutil.which(tool)
    if path:
        ok(tool, version([path, "--version"]))
    else:
        bad(tool, INSTALL["node"].get(OS, "https://nodejs.org"))

print("\nPython-Pakete")
import sysconfig
managed = sys.prefix == sys.base_prefix and os.path.exists(
    os.path.join(sysconfig.get_paths()["stdlib"], "EXTERNALLY-MANAGED"))
VENV = os.path.join(os.path.expanduser("~"), ".venvs", "reels")
VENV_PY = os.path.join(VENV, "Scripts" if os.name == "nt" else "bin", "python")
if managed:  # Homebrew/Debian Python refuses pip install outside a venv (PEP 668)
    print(f"  Hinweis  Dieses Python erlaubt kein pip install. Einmal anlegen: {sys.executable} -m venv {VENV}\n"
          f"          Danach alle Skripte mit {VENV_PY} starten.")
PIP = f"{VENV_PY if managed else sys.executable} -m pip install"
PKGS = [("numpy", "numpy", True), ("PIL", "pillow", True), ("faster_whisper", "faster-whisper", True)]
for mod, pip_name, required in PKGS:
    if importlib.util.find_spec(mod):
        ok(pip_name)
    elif required:
        bad(pip_name, f"{PIP} {pip_name}")
if importlib.util.find_spec("faster_whisper"):
    model = os.environ.get("WHISPER_MODEL", "large-v3")
    print(f"          Whisper-Modell: {model} (Download beim ersten Lauf; large-v3 ca. 3 GB."
          " Schneller: WHISPER_MODEL=medium)")
    if OS == "Darwin":
        print("          macOS: Whisper läuft auf der CPU (kein CUDA). 1 min Ton dauert grob 1-3 min.")

if len(sys.argv) > 1:
    root = os.path.abspath(sys.argv[1])
    print(f"\nArbeitsordner {root}")
    tools = os.path.join(root, "_tools")
    if os.path.exists(os.path.join(tools, "node_modules", "hyperframes")):
        ok("HyperFrames in _tools/")
        print("          Chrome/ffmpeg für HyperFrames prüfen: cd _tools && npx hyperframes doctor")
    else:
        bad("HyperFrames", f"mkdir -p \"{tools}\" && cd \"{tools}\" && npm init -y && npm i hyperframes@latest")
    vendor = os.path.join(root, "_assets", "vendor")
    for f in ("gsap.min.js", "three.min.js"):
        if os.path.exists(os.path.join(vendor, f)):
            ok(f"_assets/vendor/{f}")
        else:
            bad(f"_assets/vendor/{f}", "siehe SKILL.md, Abschnitt 0 (per npm holen und kopieren)")
    fonts = os.path.join(root, "_assets", "fonts")
    if os.path.isdir(fonts) and any(n.lower().endswith((".ttf", ".otf")) for n in os.listdir(fonts)):
        ok("_assets/fonts/")
    else:
        opt("_assets/fonts/", "Inter als TTF ablegen (https://github.com/rsms/inter/releases)")

print()
if missing:
    print(f"{len(missing)} Teil(e) fehlen: {', '.join(missing)}")
    sys.exit(1)
print("Alles da.")
