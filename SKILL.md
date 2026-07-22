---
name: resolve-multicam-workflow
description: Automate multi-camera talk/event videos in DaVinci Resolve Studio via the Python API — audio sync, auto multicam cut from a Whisper transcript, film-look grading with shared Color-Group nodes, non-destructive QC (blur/shake detection + angle switch), overlay titles. DaVinci-Resolve-Filmprojekt anlegen und bearbeiten: Ton-Sync per Kreuzkorrelation, Quell-Timelines per Python-API, Auto-Multicam-Schnitt aus Whisper-Transkript, Grading-Kette, geteilte Nodes. Nutzen bei "neues Resolve-Projekt", "Kameras synchronisieren", "Multicam schneiden", "Resolve per Skript steuern". Von wunder-media (https://wunder-media.de).
---

# Resolve-Filmprojekt anlegen (wunder-media)

Bewährte Pipeline aus den Projekten Projekt-A → Projekt-C → Projekt-B. **Immer diesen Ablauf
nehmen, nicht neu erfinden.** Arbeitsordner pro Projekt: `C:\claude\resolve-prep\<kurzname>\`.

## Zuerst lesen (in dieser Reihenfolge)

1. `references/ablauf.md` — die 8 Schritte von Rohdaten bis fertigem Multicam-Schnitt mit Titel.
   Die früher offenen „Entscheidungen" sind jetzt oben in **Berechtigungen & stehende Antworten**
   beantwortet — nicht erneut erfragen.
2. `references/api-werkzeuge.md` — was Resolve per Skript kann (rctl.py, grade-set,
   node-add, Fusion, Titel-Vorlage) und wo die harten API-Grenzen sind.
3. `references/fallstricke.md` — teuer erlernte Fallen. **Vor jedem Schritt kurz prüfen,
   ob dort etwas zum aktuellen Schritt steht.** Das spart die meisten Sackgassen.
4. `vorlagen/` — lauffähige Vorlagen-Skripte (aus Projekt-B, dem saubersten Projekt).
   Kopieren nach `C:\claude\resolve-prep\<kurzname>\`, Kopf-Konstanten anpassen, laufen lassen.

## Kurzfassung des Ablaufs

| # | Schritt | Werkzeug |
|---|---------|----------|
| 1 | Rohdaten sichten (ffprobe: Kameras, Teile, fps, Ton-Kanäle, Log/Rec709) | `references/ablauf.md` |
| 2 | Ton-Sync gegen Hauptton (Tascam/dr10L), Offsets als JSON | `vorlagen/sync.py` |
| 3 | Projekt + Bins + Import + Quell-Timeline je Kamera | `vorlagen/prep.py` |
| 4 | Transkript (faster-whisper large-v3, CUDA) | `vorlagen/transcribe.py` |
| 5 | Auto-Schnittplan aus Sprechpausen | `vorlagen/make_cutplan.py` |
| 6 | Schnitt-Timeline. **Bei ≥2 Kameras IMMER Multicam-mit-Schnitten** (DRT-Winkel-Patch) | `vorlagen/mcbuild/` |
| 7 | Verifizieren (Lücken, Überlappungen, Winkel, **Schwarzbild-Render**), dann Grading (3-LUT-Kette, **geteilte Nodes**) | `vorlagen/verify_cut.py` |
| 8 | Nachbearbeiten: **richtigen Anfang finden, Organisatorisches raus, verwackelte/unscharfe Winkel tauschen**; Titel-Vorspann (Overlay) | `references/ablauf.md` |

**Voraussetzung immer:** Resolve läuft, Einstellungen → System → Allgemein →
„Externes Scripting" = **Lokal**. Bei `scriptapp("Resolve") is None` → Resolve komplett neu starten.

## Berechtigungen & stehende Antworten — NICHT mehr nachfragen

Der Nutzer hat das entschieden; Claude setzt es ohne Rückfrage um und legt das Projekt bis zum
fertigen, gegradeten Multicam-Schnitt mit Titel **selbstständig** an.

**Berechtigungen sofort zu Beginn holen (nicht einzeln nachfragen):**
- Computer-use gleich freischalten: `request_access(["DaVinci Resolve"])`, Grund „Resolve steuern
  (Multicam, Grading, Titel)". Deckt die ganze Pipeline; nur bei einem ZUSÄTZLICHEN Programm erneut
  anfragen. Resolve bei Bedarf per `open_application` starten.
- Skripten/Prüfen läuft über Bash + `py C:\claude\resolve-ctl\rctl.py …` und die Vorlagen-Skripte —
  fester Bestandteil, einfach ausführen (kein Nachfragen nötig).
- **Medien offline** (Projekt wurde auf anderer Platte angelegt, z. B. `E:`→`F:`)? Ohne Rückfrage
  neu verknüpfen: `mp.RelinkClips(clips, r"<Projektordner auf der aktuellen Platte>")`.

**Stehende fachliche Antworten (nie wieder erfragen):**
1. **≥2 Kameras → IMMER die geschnittene Multicam liefern** (echter Multicam-Clip + DRT-Winkel-Patch,
   `vorlagen/mcbuild/`), damit der Nutzer beim Bearbeiten jeden Clip auf eine andere Kamera umschalten
   kann. Nicht mehr fragen „Nesting oder Multicam".
2. **Look = feste 3-LUT-Kette:** 1) auf **ARRI** wandeln → 2) **Filmstock**-Emulation → 3) **Kino-LUT**
   obendrauf. LUT-Pfade/Details im Memory `grading-look-kette-praeferenz`. Look-Richtung NICHT
   erfragen — diese Kette bauen.
3. **LUTs NUR für diese drei Look-Schritte.** Jede Korrektur (Weißabgleich, Helligkeit, Farbstich/
   Magenta/Blau, Sättigung, Kontrast) als **regelbarer Resolve-Node-Wert**, nie als zusätzliche
   gebackene LUT — damit nachvollziehbar bleibt, was vom Original abweicht, und einzelne Werte
   zurückstellbar sind.
4. **⭐ Gleiche Node-Inhalte über Kameras hinweg = GETEILTE Nodes** (Shared Nodes): die identischen
   Look-Nodes (ARRI-Wandlung, Filmstock, Kino) als geteilte Nodes anlegen, damit eine Änderung auf
   ALLE Clips/Kameras wirkt. Nur kamera-spezifische Korrekturen (z. B. Angleich weit→nah) bleiben
   lokal. Details in `references/ablauf.md`/`fallstricke.md`.
5. **Andere Kameras an die Leitkamera angleichen** (per Korrektur-Node-Werten, nicht per LUT).
6. **Titeltext** aus Ordnername ableiten (Name + Bezeichnung; Datum + Ort, meist „München") und nur
   **inhaltlich gegenprüfen** lassen — nicht die ganze Titel-Prozedur erfragen.

**Nur das noch beim Nutzer lassen:**
- Die **subjektive Helligkeits-/Richtungsfeinheit**: Mitte-Frame zeigen, kurz „heller/dunkler?".
- **Zerstörerische Eingriffe an bereits vorhandener Nutzer-Arbeit** (fremde Timelines/Grades
  löschen/überschreiben). Das reine Anlegen der Pipeline auf einem neuen/leeren Projekt ist frei.

## Regeln für die Arbeit an echten Projekten

- **Pipeline autonom durchziehen.** Neues Projekt anlegen, syncen, schneiden (Multicam), graden
  (3-LUT-Kette + geteilte Nodes), Titel setzen — ohne Zwischenrückfragen (siehe **Berechtigungen &
  stehende Antworten**). Nur bei **zerstörerischen Eingriffen an bereits vorhandener Nutzer-Arbeit**
  (fremde Timelines/Grades löschen/überschreiben) vorher kurz bestätigen. Analysieren/Auslesen ist frei.
- **Look-Kette und -Richtung sind entschieden** (3-LUT-Kette, s. o.) — nicht mehr erfragen. Nur die
  **Feinhelligkeit** am Mitte-Frame kurz bestätigen lassen (hell & freundlich, Gesicht nicht zu hell,
  Helligkeit über Gamma, Gain niedrig).
- Jeden Schritt **verifizieren** und Zahlen nennen (Clipanzahl, Pearson, Lücken) — der Nutzer
  arbeitet damit weiter.
- Am Ende der Sitzung: Projekt-Memory unter
  `C:\Users\you\.claude\projects\C--claude\memory\` anlegen/aktualisieren (Muster:
  `projekt-b-projekt.md`) und in `MEMORY.md` verlinken.

## Diesen Skill weiterentwickeln

Der Skill ist ausdrücklich zum Wachsen gedacht. Wenn in einer Sitzung etwas Neues gelernt wird:

- **Neue API-Fähigkeit** (etwas geht jetzt per Skript, was vorher Maus war)
  → `references/api-werkzeuge.md` ergänzen **und** die Zeile in `references/fallstricke.md`
  streichen, falls sie dort als Grenze steht.
- **Neue Falle / Sackgasse** → `references/fallstricke.md`, mit Symptom + Ursache + Lösung.
- **Ablauf-Änderung** (andere Reihenfolge, neuer Schritt) → `references/ablauf.md`.
- **Besseres Skript** → Vorlage in `vorlagen/` ersetzen und unten in der Historie vermerken.
- Änderungen kurz in `references/historie.md` eintragen (Datum + was + warum), damit spätere
  Sitzungen den Stand nachvollziehen.

Faustregel: **alles, was beim nächsten Projekt Zeit spart, gehört hier hinein — nicht nur ins
Sitzungs-Memory.** Memory beschreibt einzelne Projekte, dieser Skill das wiederverwendbare Wie.
