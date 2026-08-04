# DaVinci Resolve - Multicam-Film-Workflow (Claude Agent Skill)

*A Claude Code / Agent skill that automates the repetitive prep for multi-camera talk & event
videos in DaVinci Resolve Studio, so a human editor can take over and finish in Resolve.*
*(Skill-Inhalt auf Deutsch.)*

Erstellt und gepflegt von **[wunder-media](https://wunder-media.de)** - Film & Livestream fuer
Veranstaltungen in Muenchen. Fragen, Anmerkungen, Erfahrungsberichte: gerne ueber
[wunder-media.de](https://wunder-media.de).

## Idee: KI macht die Vorarbeit, der Mensch bearbeitet frei weiter

Wiederkehrende, zeitraubende Handgriffe uebernimmt die KI - **Tonsynchronisation**, **automatischer
Multicam-Rohschnitt aus dem gesprochenen Wort**, das **Grundgeruest des Kino-Looks** und eine
**automatische Qualitaetspruefung** (Unschaerfe/Wackeln -> Kamera-Wechsel). Das Ergebnis ist ein
**ganz normales DaVinci-Resolve-Projekt**: der Cutter arbeitet im gewohnten Programm einfach weiter,
kann alles frei veraendern, und **jeder Film wird von einem Menschen durchgesehen**, der die
Feinarbeit macht. Tempo der Automatisierung + Urteil eines echten Editors.

**Die Grenze verlaeuft bewusst nicht bei "kann die KI das?", sondern bei "braucht die KI dafuer
laenger als ein Mensch?"** - Qualifizierer/Power Windows ziehen, Shared Nodes verknuepfen,
Feinschnitt und Gestaltung bleiben beim Menschen. Die Tabelle dazu steht in
`references/vorbild-projekt.md`.

## Was der Skill kann

- **Ton-Sync** je Kamera per Kreuzkorrelation gegen den Hauptton (Offsets als JSON).
- **Projekt/Bins/Quell-Timelines** je Kamera per Resolve-Python-API.
- **Transkript** (faster-whisper) -> **Auto-Schnittplan** aus Sprechpausen (ruhiges Schnitt-Tempo).
- ⭐ **Geschnittene Multicam komplett per Skript** - der Multicam-Clip *und* die Winkel-Schnitte
  werden als DRT gebaut und importiert, **ohne einen einzigen GUI-Klick** (`vorlagen/mcbuild/`).
- **Grading**: die 5-Node-Kette (Log-Dekodierung/Filmstock -> Primaerkorrektur -> Finish-LUT ->
  Haut-Sekundaer -> Halation/Vignette), per **DRX in Sekundenbruchteilen** auf alle Kameras
  uebertragbar; alternativ die aeltere 3-LUT-Kette ueber eine **Color Group** (geteilte Nodes).
  Korrekturen immer als regelbare Node-Werte, nie als zusaetzlich gebackene LUT.
- **Nicht-destruktive Nachbearbeitung**: Anfang nur per Marker, Loeschkandidaten nur gelb;
  verwackelte/unscharfe Winkel automatisch finden (ffmpeg+numpy) und tauschen.
- **Titel-Vorspann** als OVERLAY (ohne Ripple), **Grafik-Einblendungen** und eine
  **9:16-Kurzfassung** fuer Social (Crop, Untertitel, -14 LUFS).
- **Verifikation** an jeder Stelle: Luecken/Ueberlappungen/Winkelfehler, Schwarzbild-Render-Test,
  Overlay-Pruefung, Wirkungsmessung einzelner Grading-Nodes.

## Nicht alle Projekte sind gleich

**Gleich bleibt normalerweise nur das Multicam-Vorgehen selbst.** Verschieden sind:

- **Anzahl der Kameras** (2, 3, 4 ...) - je Kamera eine Quell-Timeline und ein Angle,
  Angle 1 = Leitkamera; das DRT-Verfahren skaliert unveraendert.
- **Anzahl und Art der Tonquellen** - eine ist der Sync-Master, alle anderen werden dagegen
  synchronisiert und als eigene Spuren gefuehrt (gemischt wird nicht automatisch).
- **Titel, Einspieler, Grafik-Einblendungen** - die unterscheiden sich pro Projekt in **Text
  UND Aufbau**. Bei einer wiederkehrenden Reihe wird der Aufbau aus einer frueheren Folge
  **derselben** Reihe uebernommen, bei einem Einzelprojekt erfragt. Allgemein ist nur die
  Technik, nie der Inhalt.

Details: `references/vorbild-projekt.md` (Soll-Zustand eines uebergabefertigen Projekts,
Mediathek-Aufraeumen, Arbeitsteilung).

## Voraussetzungen

- **DaVinci Resolve Studio 21+**, Einstellungen -> System -> Allgemein -> *External Scripting = Local*.
- **Python 3.x** mit `numpy`; fuer das Transkript zusaetzlich `faster-whisper` (CUDA empfohlen);
  **ffmpeg** im PATH.
- **LUTs und OFX-Plugins** stellst du selbst bereit. Die Beispielwerte nennen die Produkte, die
  hier im Einsatz sind (FilmConvert Nitrate, VisionColor OSIRIS/ImpulZ, der mitgelieferte
  Film Look Creator von Resolve) - der Ablauf funktioniert mit jeder gleichwertigen Kette.
- Einige Skripte rufen einen **begleitenden Resolve-Scripting-CLI** (`rctl.py`) auf; dieser ist
  **nicht** enthalten. Die eigentlichen API-Techniken stehen aber direkt in den Skripten
  (offizielle `DaVinciResolveScript`-API) und sind so nachvollziehbar/portierbar.

## Installation

1. Ordner nach `~/.claude/skills/resolve-multicam-skill/` kopieren (bzw. in dein Claude-Code-Setup).
2. In den Skripten unter `vorlagen/` die **Pfad- und Namens-Konstanten am Dateikopf** an dein System
   anpassen (Arbeitsordner, LUT-Namen, Timeline-Namen). Die Beispiele nutzen Windows-Pfade.
3. Ablauf lesen: `SKILL.md` -> `references/ablauf.md` -> `references/vorbild-projekt.md`.

## Aufbau

| Datei | Inhalt |
|---|---|
| `SKILL.md` | Kurzablauf, stehende Entscheidungen, Regeln fuer die Arbeit am echten Projekt |
| `references/ablauf.md` | die 9 Schritte von den Rohdaten bis zur Auslieferung |
| `references/vorbild-projekt.md` | Soll-Zustand eines uebergabefertigen Projekts + Arbeitsteilung |
| `references/kino-look-nodekette.md` | die Grading-Kette als Rezept, mit gemessenen Werten |
| `references/api-werkzeuge.md` | was die Resolve-API kann - und wo ihre harten Grenzen sind |
| `references/fallstricke.md` | teuer erlernte Fallen mit Symptom, Ursache, Loesung |
| `references/grafik-einblendungen.md` | Infografiken/Overlays + Auslieferung (lang + 9:16) |
| `references/historie.md` | Aenderungslog |
| `vorlagen/` | lauffaehige Skripte (sync, prep, transcribe, cutplan, mcbuild, verify, overlays) |

## Hinweis / Ehrlichkeit

Der Skill entstand fuer einen konkreten Studio-Aufbau und ist als **Referenz-/Startpunkt** gedacht,
nicht als Ein-Klick-Installation. **Projekt-, Kunden- und Personennamen sind durchgehend
anonymisiert** (Projekt-A, -B, ...; Reihe-R; Thema-X/-Y/-Z) - die Beispiele beschreiben also echte
Faelle, nennen aber keine echten Auftraege. Verweise auf "Memory `...`" zeigen auf die privaten
Arbeitsnotizen des Autors und sind hier bewusst nicht enthalten; der jeweilige Kern steht im Text.

## Lizenz

MIT - siehe `LICENSE`. (c) wunder-media. Wenn es dir hilft, freuen wir uns ueber einen Link zurueck.
