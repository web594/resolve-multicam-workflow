# DaVinci Resolve - Multicam-Film-Workflow (Claude Agent Skill)

*A Claude Code / Agent skill that automates the repetitive prep for multi-camera talk & event
videos in DaVinci Resolve Studio, so a human editor can take over and finish in Resolve.*
*(Skill-Inhalt auf Deutsch.)*

Erstellt und gepflegt von **[wunder-media](https://wunder-media.de)** - Film & Livestream fuer
Veranstaltungen in Muenchen.

## Idee: KI macht die Vorarbeit, der Mensch bearbeitet frei weiter

Wiederkehrende, zeitraubende Handgriffe uebernimmt die KI - **Tonsynchronisation**, **automatischer
Multicam-Rohschnitt aus dem gesprochenen Wort**, das **Grundgeruest des Kino-Looks** und eine
**automatische Qualitaetspruefung** (Unschaerfe/Wackeln -> Kamera-Wechsel). Das Ergebnis ist ein
**ganz normales DaVinci-Resolve-Projekt**: der Cutter arbeitet im gewohnten Programm einfach weiter,
kann alles frei veraendern, und **jeder Film wird von einem Menschen durchgesehen**, der die
Feinarbeit macht. Tempo der Automatisierung + Urteil eines echten Editors.

## Was der Skill kann

- **Ton-Sync** je Kamera per Kreuzkorrelation gegen den Hauptton (Offsets als JSON).
- **Projekt/Bins/Quell-Timelines** je Kamera per Resolve-Python-API.
- **Transkript** (faster-whisper) -> **Auto-Schnittplan** aus Sprechpausen.
- **Geschnittene Multicam** mit echten Winkeln (DRT-Winkel-Patch) - pro Clip umschaltbar.
- **Grading als geteilte Nodes** ueber eine **Color Group** (eine Aenderung wirkt auf alle Kameras),
  Look-Kette: Log->ARRI-Wandlung -> Filmstock-Emulation -> Kino-LUT; Korrekturen als regelbare Nodes.
- **Nicht-destruktive Nachbearbeitung**: Anfang nur per Marker, Loeschkandidaten nur gelb;
  verwackelte/unscharfe Winkel automatisch finden (ffmpeg+numpy) und tauschen.
- **Titel-Vorspann** als OVERLAY (ohne Ripple).

## Voraussetzungen

- **DaVinci Resolve Studio 21+**, Einstellungen -> System -> Allgemein -> *External Scripting = Local*.
- **Python 3.x** mit `numpy`; fuer das Transkript zusaetzlich `faster-whisper` (CUDA empfohlen);
  **ffmpeg** im PATH.
- **LUTs** stellst du selbst bereit: eine Log->ARRI-Wandlung, eine Filmstock-Emulation
  (z. B. VisionColor ImpulZ) und eine Kino-/Show-LUT.
- Einige Skripte rufen einen **begleitenden Resolve-Scripting-CLI** (`rctl.py`) auf; dieser ist
  **nicht** enthalten. Die eigentlichen API-Techniken stehen aber direkt in den Skripten
  (offizielle `DaVinciResolveScript`-API) und sind so nachvollziehbar/portierbar.

## Installation

1. Ordner nach `~/.claude/skills/resolve-multicam-skill/` kopieren (bzw. in dein Claude-Code-Setup).
2. In den Skripten unter `vorlagen/` die **Pfad- und Namens-Konstanten am Dateikopf** an dein System
   anpassen (Arbeitsordner, LUT-Namen, Timeline-Namen). Die Beispiele nutzen Windows-Pfade.
3. Ablauf lesen: `SKILL.md` -> `references/ablauf.md`.

## Hinweis / Ehrlichkeit

Der Skill entstand fuer einen konkreten Studio-Aufbau und ist als **Referenz-/Startpunkt** gedacht,
nicht als Ein-Klick-Installation. Projektnamen in den Beispielen sind anonymisiert (Projekt-A, -B, ...).

## Lizenz

MIT - siehe `LICENSE`. (c) wunder-media. Wenn es dir hilft, freuen wir uns ueber einen Link zurueck.
