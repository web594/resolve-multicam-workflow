# Historie dieses Skills

Kurz eintragen: Datum — was geändert — warum. Neueste oben.

## 2026-07-21 — Autonom bis fertiger Multicam-Schnitt + stehende Antworten (Sitzung Projekt-A)
Skill so erweitert, dass Claude ohne Rückfragen bis zum gegradeten Multicam-Schnitt mit Titel kommt.
Neu in `SKILL.md`: **Berechtigungen & stehende Antworten** (request_access, Relink offline Medien,
und die vom Nutzer festgelegten Defaults) — der Nutzer will kein Nachfragen mehr bei entschiedenen
Punkten. Konkret:
- **≥2 Kameras → IMMER geschnittene Multicam** (Schritt 6 verpflichtend; Rezept + Schwarzloch-Render-
  Test; Projekt-A-Referenzskripte `vorlagen/mcbuild/*_projekt-a.py`).
- **Grade propagiert live** über die Winkel-Quell-Timelines durch den Multicam-Clip (Schritt 7).
- **⭐ Gleiche Node-Inhalte = geteilte Nodes via COLOR GROUP** (API: `AddColorGroup`,
  `AssignToColorGroup`, `GetPre-/GetPostClipNodeGraph().SetLUT`): Pre-Clip=ARRI, Clip=Korrektur pro
  Kamera, Post-Clip=Rec709→LogC/Filmstock/Kino. Eine Änderung wirkt auf alle Kameras. Propagiert
  durch Multicam (verifiziert). Vorlage `vorlagen/build_group_look.py` (Schritt 7).
- **LUT-vs-Wert-Regel** + **3-LUT-Look-Kette** (Schritt 7), Vorlage `grade_angle.py`.
- **Titel OVERLAY statt Ripple** (`vorlagen/titel_overlay.py`; `fallstricke.md` Punkt 6).
- **Schritt 8 Nachbearbeiten NICHT-DESTRUKTIV**: Anfang nur Marker (`AddMarker`), Löschkandidaten
  nur gelb (`SetClipColor`), nie schneiden/löschen. Verwackelte/unscharfe Winkel per Analyse finden
  (`vorlagen/analyze_quality.py`, ffmpeg+numpy: Schärfe/Bewegung pro Segment) und per GUI-Rechtsklick
  „Multicam-Perspektive wechseln → Angle N" tauschen. **Bewegung/Schwenk ist OK — nur Unschärfe/
  Wackeln tauschen**; Objektivwechsel = Fast-Schwarzbild, ggf. im zu entfernenden Vorlauf.
- Zugehörige Memories: `grading-look-kette-praeferenz`, `nicht-destruktiv-markieren`,
  `projekt-a-projekt-a-projekt`.

## 2026-07-20 (später) — OFX-Setzen GELÖST
Fortsetzung mit nativem Referenz-OFX (per Computer-Use angelegt, Einzelschritt-Drag) + DB-Diff:
Es gab nie einen versteckten Aktivierungs-Speicher — die „toten" Transplantate hatten
**keyframe-animierte** Parameter, die im Ziel-Zeitbereich zu 0 auswerten. Mit keyframe-freiem
Body funktioniert alles: grade-copy überträgt OFX, DRX-Apply bei offenem Projekt rendert,
DB-Injektion rendert, Parameter numerisch patchen/hinzufügen rendert (0.4→1.0 verifiziert).
Rezept in `api-werkzeuge.md`, Fallen in `fallstricke.md`,
Vorlagen in `C:\claude\resolve-ctl\drx\ofx\`.

## 2026-07-20 — OFX-Transplantations-Experiment dokumentiert
Reverse-Engineering-Sitzung: OFX per DRX/DRT/DB-Injektion auf Nodes bringen. Ergebnis:
strukturell möglich (hängt an, Parameter da, Window maskiert), aber der Effekt **rechnet nie**
— Aktivierung liegt außerhalb der Projekt-DB. Details + verwertbare Neprojekt-drkenntnisse
(OFX-Body-Format, DRT=ZIP mit Grade-Bodies, CDL-Window-Trick, Blur-auf-Ramp-Falle) in
`fallstricke.md`. Zwei offene Folgeideen dort notiert (nativer OFX + DB-Diff; grade-copy-Test).

## 2026-07-20 — Skill angelegt
Gebündelt aus den Sitzungen zu Projekt-A, Projekt-C, Projekt-B und dem Werkzeugkasten
`C:\claude\resolve-ctl\` (Stand 19./20.07.2026: native Farbrad-Felder schreiben+lesen,
`node-add`, `grade-copy`, Fusion-Nodes, Titel-Vorlage).
Anlass: das Wissen ging beim Sitzungswechsel verloren.
Vorlagen-Skripte aus dem Projekt-B-Projekt kopiert.

---

## ➡️ Was noch offen ist — hier fortsetzen

Vollständige Fassung im Memory `resolve-automatisierung-stand` (dort steht der laufende Stand).

1. **OFX-Vorlagen-Bibliothek anlegen** ← nächster Schritt, vom Nutzer gewünscht.
   Je Plugin einmal per GUI auf `probe-tl` anhängen (Einzelschritt-Drag!), speichern, Body aus
   der Projekt-DB nach `C:\claude\resolve-ctl\drx\ofx\` sichern. **Keyframes vermeiden.**
   Kandidaten: FilmConvert Nitrate (SLog3 Kodak Ektar), Color Space Transform, Osiris,
   Neat Video, BeautySmooth. Danach: Param-Namen je Plugin dokumentieren und ein
   `rctl.py ofx <vorlage> [param=wert …]` bauen.
2. **Titel-Vorlage am echten Zielprojekt anwenden** — bisher nur im Wegwerf-Projekt getestet.
3. **Ungetestete API-Chancen prüfen:** `MediaPool.AutoSyncAudio`,
   `MediaPoolItem.TranscribeAudio` / `Timeline.CreateSubtitlesFromAudio`,
   `Timeline.AddTrack`/`SetTrackName`.
4. **Anpassungsclip-Grade** automatisch setzen — mit der jetzt bekannten DB-Injektion
   evtl. doch lösbar (bislang: `.drx` in der Galerie, 1 Klick nötig).
5. **`grade-show` bei Mehr-Node-Grades** liest ohne Node-Trennung — verfeinerbar.
6. Nach Resolve-Updates: Regler-IDs neu kalibrieren (`calibrate_drx.py`/`refine_cal.py`),
   `probe_api.py` erneut laufen lassen.
7. Testprojekt „zz claude api-probe (loeschbar)" ist löschbar — **außer `cal-tl` mit
   `cal_ramp.mp4`** (Re-Kalibrierung) und `probe-tl` (Werkbank für neue OFX-Vorlagen).
