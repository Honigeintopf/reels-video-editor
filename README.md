# Reels Video Editor für Claude Code

Du nimmst ein Video auf, gibst es Claude Code und sagst: „Mach da ein Reel draus.“
Claude säubert den Ton, schreibt Untertitel mit Wort-Timing, baut eine Hook-Caption und erklärende Grafiken und exportiert das Ganze fertig für Instagram Reels, TikTok und YouTube Shorts (1080×1920).

Alles läuft lokal auf deinem Rechner. Du brauchst kein Schnittprogramm und kein CapCut-Abo, nur Claude Code.

## Was du brauchst

- **Claude Code** mit einem Claude-Abo (Pro oder Max). Das Plugin läuft nicht im normalen Claude-Chat im Browser, weil es Programme auf deinem Rechner braucht.
- **ffmpeg**, **Node.js** und **Python 3**. Wenn dir was fehlt, sagt Claude dir beim ersten Start genau, was du installieren musst, und hilft dir dabei.
- Etwas Platz und Geduld beim ersten Mal: Das Spracherkennungs-Modell lädt einmalig ca. 3 GB herunter.

Läuft auf macOS, Windows und Linux.

## Installieren

In Claude Code eingeben:

```
/plugin marketplace add Honigeintopf/reels-video-editor
/plugin install reels-video-editor@honigeintopf-skills
```

Falls Claude Code danach fragt: `/reload-plugins`.

Oder im Terminal:

```bash
claude plugin marketplace add Honigeintopf/reels-video-editor
claude plugin install reels-video-editor@honigeintopf-skills
```

## Benutzen

Leg dein Video in einen Ordner, öffne Claude Code in dem Ordner und schreib zum Beispiel:

> Mach aus video.mov ein Reel. Hook: „Warum dein Code nie skaliert“.

Beim ersten Mal prüft Claude, ob alles installiert ist, und richtet den Ordner ein. Danach zeigt es dir erst Standbilder, damit du den Stil absegnen kannst, und rendert dann das fertige Video.

Du kannst den Skill auch direkt aufrufen: `/reels-video-editor:edit-reel`.

## Updates

```bash
claude plugin update reels-video-editor@honigeintopf-skills
```

Automatische Updates kannst du in Claude Code einschalten: `/plugin` → **Marketplaces** → `honigeintopf-skills` → **Enable auto-update**.

## Deinstallieren

```bash
claude plugin uninstall reels-video-editor@honigeintopf-skills
```

## Ohne Plugin-System

Du kannst den Skill-Ordner auch von Hand kopieren:

```bash
git clone https://github.com/Honigeintopf/reels-video-editor
cp -r reels-video-editor/skills/edit-reel ~/.claude/skills/
```

Dann heißt er einfach `/edit-reel`. Updates musst du dann selbst holen.

## Was drin ist

- `skills/edit-reel/SKILL.md`: die Anleitung, die Claude vor dem Schneiden liest (Pipeline, Safe Zones, Hook- und Untertitel-Regeln, Stil)
- `skills/edit-reel/scripts/`: Python-Helfer für Ton, Transkript, Untertitel, Render, Vorschau, Soundeffekte und `doctor.py` für den Setup-Check
- `skills/edit-reel/references/techniken.md`: fortgeschrittene Techniken (3D-Szenen, Text hinter dem Kopf, Glas-Look)

Grafiken werden mit [HyperFrames](https://github.com/heygen-com/hyperframes), [GSAP](https://gsap.com) und [Three.js](https://threejs.org) gebaut. Die werden beim ersten Start per npm geholt und liegen nicht in diesem Repo.

## Lizenz

MIT, siehe [LICENSE](LICENSE).
