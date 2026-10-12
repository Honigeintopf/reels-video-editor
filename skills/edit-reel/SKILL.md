---
name: edit-reel
description: Schneidet, gestaltet und rendert Talking-Head-Reels/TikToks (1080×1920, 30 fps) komplett per Code – Ton säubern, Transkript mit Wort-Timings, Hook-Caption, ruhige Untertitel, erklärende Motion-Grafiken (HyperFrames + GSAP, Three.js-3D, Text hinter dem Kopf), Safe Zones, HQ-Render und Handy-Vorschau. Verwenden, wenn ein Rohvideo zu einem Reel/TikTok/Short bearbeitet, mit Captions/Grafiken versehen, in mehreren Stil-Varianten exploriert oder neu gerendert werden soll.
compatibility: Nur Claude Code (lokal). Braucht ffmpeg, Python 3 (numpy, pillow, faster-whisper) und Node.js; HyperFrames, GSAP und Three werden beim ersten Start per npm geholt.
license: MIT
---

# Reels-Video-Editor

Du schneidest, gestaltest und renderst Hochkant-Videos (1080×1920, 30 fps) per Code auf dem Rechner des Users (macOS, Windows oder Linux). Ziel: Grafiken, die **erklären**, nicht nur betonen – ruhig, edel, gut lesbar.

> Erster Start in einem neuen Arbeitsordner: Lege `AGENTS.md` (Vorlieben des Users, gelernte Lektionen) und `WERKZEUGKASTEN.md` (installierte Tools, Fallen auf diesem Rechner) an und pflege sie bei jedem Video. Abschnitt 9 sagt, was dort hingehört.

## 0. Ersteinrichtung (einmal pro Rechner bzw. Arbeitsordner)

Skripte und Referenzen dieses Skills liegen in `${CLAUDE_SKILL_DIR}/scripts/` und `${CLAUDE_SKILL_DIR}/references/`.

1. `python ${CLAUDE_SKILL_DIR}/scripts/doctor.py [<videoordner>]` ausführen. Es prüft ffmpeg, Node/npx, die Python-Pakete (numpy, pillow, faster-whisper) und mit Ordner-Angabe auch `_tools/` und `_assets/`. Es installiert nichts, sondern nennt pro fehlendem Teil den passenden Befehl für dieses Betriebssystem.
2. Fehlendes **nach kurzer Rückfrage** installieren. Meldet `doctor.py`, dass dieses Python kein `pip install` erlaubt (Homebrew, Debian), das vorgeschlagene venv anlegen und **alle Skripte mit dessen Python starten**. Scheitert `pip install faster-whisper` an der Python-Version, ein Python 3.12 für das venv nehmen.
3. HyperFrames und Bibliotheken in den Arbeitsordner holen (GSAP und Three werden nicht mitgeliefert):
   ```bash
   mkdir -p _tools _assets/vendor _assets/fonts && cd _tools
   npm init -y && npm i hyperframes@latest gsap@3.12.5 three@0.150.1
   cp node_modules/gsap/dist/gsap.min.js node_modules/three/build/three.min.js ../_assets/vendor/
   npx hyperframes doctor
   ```
4. Font Inter als TTF nach `_assets/fonts/` legen (https://github.com/rsms/inter/releases).
5. Ergebnis in `WERKZEUGKASTEN.md` festhalten (Pfade, Python-Interpreter, Versionen), damit das nächste Video sofort startet.

## 1. Arbeitsweise

- **Rohvideos nur lesen und kopieren, nie verändern.**
- **Ordner pro Video:** `<video>/_basis/` (gemeinsame Vorarbeit, einmal gebaut), `<video>/_scripts/` (Kopie von `${CLAUDE_SKILL_DIR}/scripts/`), pro Variante `<video>/NN-stilname/` mit `build.py`, `public/`, `work/`, `render.mp4`, `preview.mp4`, `NOTIZ.md`, `QUELLEN.md`. Gemeinsam für alle Videos: `_assets/` (Fonts, SFX, Emojis, `vendor/` mit GSAP + Three) und `_tools/` (npm-Projekt mit HyperFrames).
- **Neues Format → erst explorieren:** 2–5 klar unterschiedliche Stil-Varianten. Bei reinen Stilfragen reichen **Standbild-Vergleiche** (Stil als CSS-Datei pro Variante, `build.py --stil=…`); erst nach der Wahl voll rendern.
- **Früh zeigen, dann iterieren.** Jede fertige Vorschau sofort zeigen, nicht gesammelt am Ende: Gibt es ein Tool zum Dateisenden (z. B. `SendUserFile`, Limit 30 MB), schicken; sonst Pfad nennen und die Datei öffnen (`open` auf macOS, `start` auf Windows, `xdg-open` auf Linux).
- **Erst Einzelbilder, dann Vollrender:** Snapshots + Kontaktbogen + Safe-Zone-Overlay ansehen, bevor ein Render Minuten kostet.
- **Selbst entscheiden**, nur bei echter Blockade fragen; kurz sagen, was du gewählt hast. Kostenpflichtige Dienste (KI-Video-Credits o. ä.) erst nach Budget-Freigabe.
- **Erst prüfen, ob das Video schon geschnitten ist** (Jump-Cuts, eingebrannter Titel). Dann nicht neu schneiden, außer der User fragt. Rohmaterial mit Pausen und Versprechern bekommt zuerst einen Rohschnitt (Pipeline, Schritt 4b).
- **Handoff:** Fragt der User nach einem Handoff-Prompt, fang die Arbeit NICHT selbst an. Doku aktualisieren und einen kurzen Prompt geben, der auf die Doku verweist, Ziel und Rahmen nennt und den Weg offen lässt.

## 2. Pipeline

Helfer in `${CLAUDE_SKILL_DIR}/scripts/` (nach `<video>/_scripts/` kopieren): `common.py` (Pfade, `words`, `chunks`, `export_hq`, `contact_sheet`, `safe_overlay`), `hf.py` (`setup_public`, `clip`, `page`, `at`, `snapshot`, `finish`), `transcribe.py`, `sfx.py`, `doctor.py`. ffmpeg wird über `FFMPEG_DIR` oder den PATH gefunden. GSAP 3.12.5, Three r150 und Fonts liegen nach der Ersteinrichtung (Abschnitt 0) in `_assets/`.

1. **Quelle prüfen** (`ffprobe` + `loudnorm`-Messung): Codec, Auflösung, Rotation, Lautheit, eingebrannter Titel? iPhone-Material ist 4K (H.264 mit Rotation −90° oder HEVC 2160×3840); ffmpeg dreht automatisch.
2. **Ton → `_basis/voice.wav` (48 kHz):**
   - Roher, leiser iPhone-Ton (≈ −40 LUFS): `highpass=f=80,afftdn=nr=10:nf=-50,equalizer=f=300:t=q:w=1:g=-2,equalizer=f=3500:t=q:w=1:g=2,acompressor=threshold=-26dB:ratio=3:attack=10:release=150:makeup=2,loudnorm=I=-14:TP=-1.5:LRA=7`
   - Schon bearbeiteter Ton (≈ −22 bis −26 LUFS, kleine LRA): nur `highpass=f=70,loudnorm=I=-14`.
3. **HQ-Basis direkt aus 4K → `_basis/base_1080.mp4`:** `scale=1080:1920:flags=lanczos+accurate_rnd+full_chroma_int,unsharp=5:5:0.35`, `-crf 11`, **`-g 15 -keyint_min 15`** (sonst friert das Bild beim Seeken ein). **`voice.wav` als Tonspur mit hinein** (`-c:v copy`), sonst bricht der Render bei `data-has-audio="true"` ab („expected: audio“). Eingebrannten Titel auf flacher Wand vorher per `delogo` entfernen (Clean Plate).
4. **Transkript:** `python <video>/_scripts/transcribe.py <video>/_basis de` → `words.json`, `sentences.json`, `pauses.json` (faster-whisper, Modell per `WHISPER_MODEL`, Standard `large-v3`, Wort-Timings; Pausen per RMS-Hüllkurve, weil `silencedetect` bei leisem Ton versagt). Fachbegriffe in `FIX` korrigieren, mit `--no-whisper` neu ableiten.
   - **4b. Rohschnitt (nur bei ungeschnittenem Material):** Aus `pauses.json` und `words.json` eine Schnittliste bauen: Pausen über ~0,35 s auf ~0,15 s kürzen, doppelte Anläufe und Versprecher (gleicher Satzanfang mehrfach) nur in der letzten Fassung behalten. Schnittliste dem User als Text zeigen, dann per `trim`/`atrim` + `concat` aus `base_1080.mp4` und `voice.wav` schneiden (Schnitte auf Wortgrenzen, 2 Frames Luft) und das Transkript für das geschnittene Video neu erzeugen.
5. **Personen-Maske einmal fürs ganze Video** (wenn Text hinter den Kopf oder Objekte zwischen Person und Hintergrund sollen): `npx hyperframes remove-background base_1080.mp4 -o fg.webm --quality best` (CPU ≈ 11 min für 55 s). Clips per `data-media-start` trimmen. ffmpeg liest den Alpha nur mit `-c:v libvpx-vp9` **vor** dem `-i`.
6. **Komposition aus Python:** `build.py` schreibt `public/index.html` (HyperFrames). **Alle Zeitpunkte an Wort-Timings hängen** (`at("Türsteher", 4.96)`), nie hart codieren. Was der User oft ändert (`HOOK`, `SPLIT`, Stil-Schalter), als Variablen ganz oben.
7. **Prüfen:** `snapshot(here, [1.0, 6.9, …])` → PNGs + Kontaktbogen in `public/snapshots/`, dann `safe_overlay()` drüber. Lint-Meldungen ernst nehmen.
8. **Render:** `finish(here)` = `hyperframes render --crf 10 --fps 30 --video-frame-format png` (Standard-JPG-Extraktion wird weich/blockig), danach nur Ton auf −14 LUFS (`-c:v copy`), 2-Pass-Vorschau mit vollem 30-MB-Budget, Kontaktbogen. **Nicht** CRF 25 für die Vorschau – sieht auf dem Handy „low quality“ aus.

## 3. HyperFrames-Regeln (lint erzwingt sie)

- Nur Transforms animieren: `x`, `y`, `scale`, `rotation`, `opacity`, `filter`. **`top`/`height`/`letterSpacing` per GSAP sind Fehler** (`gsap_non_transform_motion`). Split-Screen also per `y` auf Container + Video; Tracking-in per `x`-Versatz pro Buchstabe.
- Kein CSS-`transform` auf Elementen, die GSAP bewegt (`fromTo` nehmen). Nie `visibility`/`autoAlpha` auf `.clip` tweenen. Jedes `<audio>` braucht eine `id`. Fonts nur lokal per `@font-face`.
- Warnungen `nested_structure_needs_subcomposition` betreffen nur die Studio-Ansicht. Warnungen zu doppelten `fromTo` dagegen ernst nehmen.
- Pro Arbeitsordner einmal `_tools/`: `npm init -y && npm i hyperframes@latest`, `npx hyperframes doctor` prüft Chrome + ffmpeg. Offizielle Doku/Skills: `github.com/heygen-com/hyperframes` → `skills/` (v. a. `hyperframes-core`, `embedded-captions`, `talking-head-recut`).

**Three.js in HyperFrames:** Szene als reine Funktion der Zeit rendern und auf `window.addEventListener("hf-seek", e => renderAt(e.detail.time))` hören, sonst friert WebGL im Render ein. `renderer.setPixelRatio(2)`. Kamera als Keyframes `[t, ziel, zoom]` mit Easing, Figuren-Wege als Wegpunkt-Listen. Weitere Techniken (Farben in r150, Labels an 3D-Punkten, Objekte zwischen den Händen, Mixed Reality, Liquid Glass, großes Wort hinter dem Kopf): **`${CLAUDE_SKILL_DIR}/references/techniken.md`**.

## 4. Safe Zones – Pflicht

Die Insta/TikTok-UI liegt über dem Video. **Text, Hook, Labels nur in der Box x 65–940, y 270–1680.** Hook-Oberkante ≥ 280.

| Zone | Was dort liegt |
|---|---|
| y < 270 | Statusleiste, Insta-Header, TikTok „Folge ich / Für dich“ |
| y > 1680 | Username, Beschreibung, Audio-Zeile, Navigation (Untertitel bei y ≈ 1600 sind frei – am echten Post geprüft) |
| x > 940 | Like/Kommentar/Teilen |
| x < 65 | Rand |

Grafiken dürfen als Hintergrund in die Ränder laufen, ihr Inhalt (Figuren, Labels, Diagramm-Kern) nicht. Labels, die an 3D-Punkten hängen, auf die Box clampen.

## 5. Hook & Captions

- **Hook-Caption oben = Thema bzw. die Alltagssituation**, die das Video erklärt (z. B. „Der Plan schafft’s nie aus dem Gruppenchat“), **nicht ein Detail aus dem Beispiel**. Die Stimme startet direkt mit dem Inhalt; Caption liefert Kontext, Stimme Inhalt. Untertitel-Zeile in Klammern ordnet ein („(Lösung eines Informatikers)“). Fragen funktionieren auch („Warum hat sie Schluss gemacht? 💔“). Im Zweifel **2 Hook-Optionen früh** als Standbild zeigen.
- Hook-Look: weiße abgerundete Label-Boxen, eine pro Zeile, dunkle Schrift (Inter 800, 58 px / 2. Zeile 600, 40 px), kleines Pop-in.
- **Untertitel:** ruhig, Inter 600–700, ~58 px, weiß mit weichem Schatten, Phrasen ≤ 4 Wörter / ≤ 24 Zeichen (`chunks()`), das gerade gesprochene Wort geht von 45 % auf 100 % Deckkraft. Keine Überlappung (Ende = Start der nächsten − 0,04 s).
- **Fachbegriffe** als kleine Info-Pills („Türsteher = Load Balancer“), exakt aufs gesprochene Wort getimt.
- **Schnelles Gerede mit vielen Pronomen:** Pronomen in den Untertiteln in der Farbe der gemeinten Person einfärben, dazu handgezeichnete Zeigepfeile (Caveat) zur Figur.
- Schwach erklärte Stellen über **schärfere Grafik-Titel** retten, nicht den Ton anfassen.
- Tippfehler in eingebrannten Original-Titeln korrigieren und den User darauf hinweisen.

## 6. Stil – bewährter Ausgangspunkt (an den User anpassen)

- ⭐ **Three.js-Erklärszene im Split-Screen:** helles, isometrisches 3D, das die Erklärung *nachspielt* (Figuren als Kapseln, weiche Schatten, Markenfarben, Hintergrund z. B. `#ECEDF3`). Oben Szene (Panel ~860–960 px), unten Person, farbige Trennlinie.
- ⭐ **Einstieg:** erst die Person im Vollbild mit Hook, nach ~2 s (`SPLIT`) gleitet die Szene herein und das Video schrumpft nach unten (0,8 s `power3.inOut`, nur `y`).
- ⭐ **Vollbild mit Objekten neben/über dem Kopf:** kleine 3D-Objekte/Figuren ploppen in den freien Raum (Decke über dem Kopf, y ≈ 290–660), keine hereingleitende Szene.
- ⭐ **Keynote-Stil:** schwarze Folien mit Person als Bild-im-Bild, wenige starke Elemente, ein großes Wort hinter dem Kopf.
- ⭐ **Edel:** helles Glassmorphismus (Mattglas-Karten, `backdrop-filter` läuft im Render) bis Liquid Glass mit Buchstaben-Animation („After-Effects-Style“).
- **Gestik = Einladung:** Wenn die Person gestikuliert oder zur Seite tritt, Grafik in den frei werdenden Raum. Vorher Frames mit 10 fps + Zeitstempel ansehen – Gesten sind oft nur ~0,7 s lange Jump-Cuts.
- **Klare Symbole statt UI-Nachbauten:** ein App-Icon mit Badge wirkt auf dem Handy besser als ein Mini-Chatfenster mit viel Text.
- **Keine Musik** (Standard), dezente SFX (Pop, Whoosh) ok: `python scripts/sfx.py <ordner>` synthetisiert sie → keine Lizenzfragen.
- **Meist abgelehnt:** Camcorder/VHS/REC-Look, Glitch- und Effekt-Stapel („too much“), Editorial mit zu vielen Textebenen. Laute Retention-Edits (Wort-Pop-Captions, Emojis, Zoom-Cuts) nur auf Wunsch.

## 7. Werkzeuge im Vergleich

| Tool | Eindruck |
|---|---|
| **HyperFrames (HeyGen) + GSAP** | Bester Allrounder: HTML/CSS/GSAP → Video. Captions, Erklär-Grafiken, Text hinter dem Kopf. Snapshots schnell, Render ~2–4 min. |
| **HyperFrames + Three.js** | Am erklärendsten, am meisten Code (~250 Zeilen Szene). Favorit. |
| Remotion 4 | Schnellster Render (~65 s für 55 s), `spring()` gut für Pops. Bei Wort-Pop-Captions kein Flex-Layout mit Überschwingern. |
| Pillow + ffmpeg | Volle Typo-Kontrolle, alles selbst bauen. |
| ffmpeg-Filterketten / libass | Schnell für Looks und feste Untertitel, unhandlich für Animation. |

## 8. Plattform-Fallen

**macOS**
- ffmpeg und Node per Homebrew (`brew install ffmpeg node`). Homebrew-Python erlaubt kein globales `pip install` → venv (Abschnitt 0).
- Kein CUDA: Whisper läuft auf der CPU (`int8`), `large-v3` grob 1–3 min pro Minute Ton. Für schnelle Entwürfe `WHISPER_MODEL=medium`.
- `remove-background` läuft auf der CPU und braucht für ein 1-Minuten-Video mehrere Minuten; nur bauen, wenn Text hinter den Kopf soll.

**Windows**

- ffmpeg per `winget install Gyan.FFmpeg` steht oft nicht im PATH der Bash-Shell → `FFMPEG_DIR` setzen oder PATH exportieren.
- faster-whisper auf CUDA scheitert gern an fehlender `cublas64_12.dll` → `transcribe.py` fällt auf CPU/int8 zurück (80 s Audio ≈ 1–2 min).
- OpenCV 5 hat kein `CascadeClassifier` mehr → Gesichts-/Handpositionen am Standbild ausmessen (1080er Koordinaten).
- npm-Richtlinie kann Install-Skripte blocken (`EALLOWSCRIPTS`) → **nicht umgehen**. `remove-background` braucht `onnxruntime-node`; ging mit `npm install onnxruntime-node@1.21.1 --prefix "<home>/.cache/hyperframes/optional/onnxruntime-node@1.21.1" --ignore-scripts`.
- Python ohne `-I` starten, wenn Pakete in der User-Site liegen.

## 9. Lieferung & Doku

Pro Variante: `render.mp4` (Posting-Datei, 1080×1920, 30 fps, H.264, −14 LUFS), `preview.mp4` (< 30 MB, zum Verschicken aufs Handy), `kontaktbogen.png`, `NOTIZ.md` (Idee in 2 Sätzen, Tools, was gut war / was nicht), `QUELLEN.md` (Links + Lizenzstatus aller Assets). Bei mehreren Varianten eine `UEBERSICHT.md` (Variante, Tool, Status) mit Empfehlung für 1–2 Richtungen.

Nach jedem Video in `AGENTS.md` festhalten: was dem User gefiel/missfiel (mit seinen Worten), Hook-Lektionen, neue Techniken mit Verweis auf die Referenz-Variante. In `WERKZEUGKASTEN.md`: installierte Versionen, Pfade, Fallen. Marken-Assets (Farben, Fonts, Logo) dort mit Pfad notieren.
