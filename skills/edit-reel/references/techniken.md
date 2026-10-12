# Techniken für Fortgeschrittene

Alles hier lief in echten Renders (HyperFrames 0.8.14x, Chromium, Three r150 UMD aus `_assets/vendor/`).

## Split-Screen per Transform

- Panel oben 860–960 px hoch. Person unten: Container `#bottom` per GSAP `y: 0 → PANEL`, das Video darin `y: -460` (Ausschnitt so wählen, dass das Gesicht in der unteren Hälfte sitzt). Kein `top`/`height` animieren (Lint-Fehler).
- Szene im Panel nach unten in den sicheren Bereich schieben: `cam.setViewOffset(W, H, 0, -120, W, H)`.
- Zwei WebGL-Canvases (Panel + Vollbild-Overlay) verdoppeln ungefähr die Renderzeit (50 s ≈ 4 min).

## Three.js r150 – Farben und Licht

- Materialfarben: `new THREE.Color(hex).convertSRGBToLinear()`. `scene.background` dagegen roher Hex-Wert. Sonst stimmen Markenfarben nicht.
- Boden als `ShadowMaterial` (nur Schatten), sonst wird ein heller Hintergrund vom Licht weiß.
- Canvas-Texturen mit Schrift erst zeichnen, wenn `document.fonts.check('800 40px "Inter"')` true ist.
- Viele gleiche Objekte (Balken, Figuren): `InstancedMesh`. Fake-Spiegelung = zweites InstancedMesh, an y gespiegelt, 20 % Deckkraft. Leuchten aus der Instanzfarbe per `onBeforeCompile` (`totalEmissiveRadiance += vColor * 0.6`).

## Labels als HTML an 3D-Punkten

Statt Text-Texturen: `vec.clone().project(cam)` → Pixel, HTML-Label dort positionieren (per GSAP `x`/`y`), mit `off: [dx, dy]` und Clamp auf die Safe Zone. Gestochen scharf, echte Fonts + Emojis. Klammern über Bereichen bekommen ihre Breite aus zwei projizierten Punkten. Für `.tag`/`.bubble` `display:flex`, für Karten `block`.

## Objekt ploppt zwischen den Händen

1. Gestik-Stelle in Frames mit 10 fps + Zeitstempel finden (oft ein Jump-Cut von ~0,7 s).
2. Panel fährt weg (Vollbild, 0,6 s) und ist **fertig, bevor** das Objekt erscheint.
3. Objekt ploppt exakt auf den Cut in einem eigenen transparenten Vollbild-Renderer, schwebt danach neben dem Kopf mit Label und fliegt beim Zurück-Split in die Szene.
4. Kein Flug quer übers Bild während eines Übergangs – das Video verschiebt sich, das Objekt landet sonst im Gesicht. Positionen (Gesicht, Hände) am Standbild in 1080er Koordinaten ausmessen.

## Großes Wort hinter dem Kopf

Ebenen: Video (z 1) → Wort (z 2) → `fg.webm`-Maske deckungsgleich (z 3) → Captions/Bühne. Wort z. B. Inter 900, 140 px, weiß→Markenfarbe-Verlauf, Lichtkante. Buchstaben fahren von der Mitte auseinander gestaffelt ein (x/y/Blur) – nur Transforms. Parameter (`DEPTH`, `BIG`, `BIG_Y`, `BIG_SIZE`) oben in `build.py`.

## Glassmorphismus und Liquid Glass

- **Mattglas:** `backdrop-filter: blur() saturate()` funktioniert im Render. Figuren mit Verlauf + Glanzpunkt.
- **Liquid Glass (Rand-Refraktion):** pro Glas-Element eine Displacement-Map als Canvas (abgerundetes Rechteck als SDF, ~18 px Rand, Vektor zur Mitte, smoothstep) → SVG `feImage` → `feDisplacementMap scale ≈ 46`, eingehängt per `backdrop-filter: url(#id) blur(3px) saturate(1.5) brightness(1.06)`. Lazy beim ersten `hf-seek` bauen, wenn Fonts geladen sind.
- **Bevel statt Rand:** mehrere `inset`-Schatten (1,5 px Lichtkante, 16 px innerer Glow, Spitzlicht oben links, Schatten unten rechts). Getönte Varianten (lila/grün/orange/gold), dunkle Schrift mit weißer Prägung.
- **„After-Effects“-Bewegung:** Karten poppen mit `back.out(1.6)` ab Scale 0,72; Buchstaben steigen gestaffelt auf und werden scharf (`y 16→0`, `blur 7→0`, 16 ms Versatz); danach läuft einmal ein Lichtstreif übers Glas (`xPercent 0→450`).
- Fallen: Buchstaben-Spans in Flex-Containern in einen Wrapper packen, sonst wird jeder Buchstabe ein Flex-Item mit `gap` (gesperrte Schrift). Allgemeines `.lg { position: relative }` überschreibt absolut positionierte Karten → `position` gezielt setzen. Auf gleichmäßiger Wand sieht man Refraktion kaum; den edlen Eindruck machen Bevel + Lichtstreif + Buchstaben-Animation.

## Mixed Reality im Vollbild

Transparenter Three.js-Canvas über dem Video, `fg.webm` darüber, Labels obendrauf.
1. Prüfen, ob die Kamera über alle Schnitte stillsteht (SIFT + `cv2.estimateAffinePartial2D` auf dem Hintergrund, Person per Maske ausblenden).
2. Kamera einmessen: Fluchtpunkt aus zwei Kanten (Decke/Wand), Brennweite bei iPhone-Hauptkamera in 1080×1920 ≈ 1507 px, `setViewOffset(2·VPx, 2·VPy, 0, 0, W, H)` legt den Fluchtpunkt an die richtige Stelle.
3. Decke per Verlauf leicht abdunkeln (unter der Maske) und farbiges Licht additiv drauflegen → wirkt wie echte Beleuchtung.

## Stil-Varianten effizient

Ein `build.py`, Stil als CSS-Datei pro Variante (`--stil=glas-hell`), Themen als Schalter (`THEMA = "a" | "b"`), Ausgabe jeweils in eigenen Ordner. 2–3 Richtungen als Standbild-Vergleich (`stil-vergleich.jpg`) zeigen, erst nach Wahl voll rendern.
