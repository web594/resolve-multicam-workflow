# Ablauf: Projekt anlegen, Schritt für Schritt

Arbeitsordner anlegen: `C:\claude\resolve-prep\<kurzname>\`, Vorlagen aus `vorlagen/` hineinkopieren.

---

## 1. Rohdaten sichten

Rohdaten liegen typischerweise unter `E:\<JJMMTT Name>` oder `F:\…`.
**Alle Medien eines Projekts sollten auf EINER Platte liegen** (sonst Ärger mit Pfaden).

Ordner-Konvention des Nutzers (auch von `C:\claude\resolve-prep\prepare_project.py` erkannt):
- `k<Nr> <label> [<karte>v<n>]` → Kamera-Winkel; Doppelkarten (`1v2`/`2v2`) und
  XDCAM `XDROOT\Clip\*.MXF` zu **einem** Winkel zusammenführen; Shogun-Splitteile in Reihenfolge.
- `t…` → Ton (Sync-Master). `_D`-Datei = Backupspur, **nicht** in die Timeline.
- `p`-Ordner oder lose Videodatei im Hauptordner → Präsentation/Folien.
- Neuere Projekte nutzen auch schlichte Namen: `nah`, `weit`, `seite`, `dr10L`.

Mit ffprobe je Quelle klären und dem Nutzer berichten:
- Auflösung, **fps** (oft gemischt: 29.97 + 59.94 + 30.0 Screen), Codec, Dauer, Teile-Anzahl
- **Ton-Kanäle**: welche Spur trägt brauchbaren Ton? (XDCAM-MXF oft nur Track 1/2;
  Shogun-Ton kann komplett stumm sein, wenn kein SDI-Audio anlag → mit `volumedetect` prüfen)
- **Log oder Rec709**: Container-Tag lügt. Am Frame/Scope prüfen — S-Log3 hat Schwarzpunkt ~9 %.

**Timeline-fps wählen:** 59.94 konformt sauber zu 29.97 → 29.97 nehmen, **nicht** 30.0
(sonst Drift aller Kameras). Standard: 1920×1080, 29.97, DaVinci YRGB / Rec.709 (Scene).

## 2. Ton-Sync (`vorlagen/sync.py`)

Onset-Kreuzkorrelation jeder Kamera gegen den Hauptton (Tascam/dr10L), FFT-Grobsuche +
Mehrfenster-Verifikation. Ergebnis `offsets.json` mit Sekunden + Frames @29.97.

- Kopfkonstanten anpassen: `ROOT`, `REF` (Hauptton-wav), `CAMS` (Teile in Reihenfolge), `CACHE`.
- Kamera-Teile werden vor dem Sync **konkateniert** — Reihenfolge muss stimmen.
- Qualitätskriterium: **Pearson > 0,45 und Streuung < 0,5 s**. Darunter nicht weiterrechnen,
  sondern Ursache suchen (falsche Tonspur, stumme Kamera, falsches Teil).
- **Vorzeichen ist projektabhängig:** positiv = Tascam lief VOR den Kameras (Projekt-C,
  Projekt-B), negativ = Kameras liefen vor dem Ton (Projekt-A). Das bestimmt Schritt 3.
- Kein Ton auf einer Kamera? → Bild-Bewegungs-Sync ist möglich, aber aufwendig; erst prüfen,
  ob eine parallele interne Aufnahme (XDCAM-MXF) Ton hat.

## 3. Projekt + Bins + Quell-Timelines (`vorlagen/prep.py`)

Legt an: Projekt, je Quelle ein Bin, Import, und **pro Kamera eine Quell-Timeline**
`<Projektname> <label>` plus eine `… ton`.

Gemeinsame Zeitreferenz: **Start-TC = 01:00:00:00 + offset**, `01:00:00:00` = Ton-Start.
Damit gilt überall: `TC − 108000 = Ton-Frame`.

- **Offsets positiv** (Tascam vorne): Video ab Frame 0 ohne Trim, **Hauptton am Kopf um
  `off_frames` getrimmt** (`{"mediaPoolItem": ton, "startFrame": off_f, "mediaType": 2}`).
- **Offsets negativ** (Kameras vorne): umgekehrt, Kamera-Kopf trimmen.
- Existiert der Projektname schon, wird `(2)` angehängt statt zu überschreiben.

**Warum Quell-Timelines:** Farbe/Transform wird **einmal pro Kamera** dort eingestellt und
schlägt auf alle Schnitte durch — aber nur auf **Clip-Eprojekt-d**, siehe `fallstricke.md`.

## 4. Transkript (`vorlagen/transcribe.py`)

faster-whisper `large-v3` auf CUDA über den Hauptton (16 kHz mono via ffmpeg).
Ergebnis: `segments.json` + `words.json`. Worteprojekt-d ist für den Schnittplan die bessere Basis.

⚠️ Whisper erzeugt manchmal **Riesensegmente ohne Wort-Zeitstempel** (Projekt-B: 223 s am Stück).
Der Schnittplan muss solche Löcher mechanisch füllen (siehe Schritt 5).

## 5. Auto-Schnittplan (`vorlagen/make_cutplan.py`)

Prinzip: **eine Leitkamera als Standard**, Cutaways an Sprechpausen.

- Phrasen an Wortpausen ≥ 0,4 s; Cutaway an Absatzpausen (≥ 1,0–1,2 s);
  **Zwangswechsel nach 40–45 s**, damit es nicht einschläft.
- Bei mehreren Cutaway-Kameras abwechselnd (Projekt-C: weit/seiteL, seiteR nur Reserve).
- **Lange Spans ohne Wortzeiten mechanisch unterteilen** (>45 s → z. B. 34 s Leit + 7 s Cutaway).
- **Leitkamera + welche Kameras überhaupt im Auto-Schnitt vorkommen: beim Nutzer erfragen.**
  (Projekt-B: weit = Standard, seite = Auflockerung, weil es keine frontale nah gab.)
- Ergebnis `cut_plan.json` (Spans mit Ton-Sekunden + Winkel).

## 6. Schnitt-Timeline bauen — bei ≥2 Kameras IMMER Multicam mit Schnitten

**Standard-Lieferung bei mehreren Kameras ist die geschnittene Multicam** (nicht bloß die
verschachtelte Schnitt-Timeline): so kann der Nutzer beim Bearbeiten jeden Clip anklicken und auf
eine andere Kamera umschalten. Die verschachtelte Variante darf als Zwischenschritt entstehen, das
**auszuliefernde Ergebnis ist die Multicam-Schnitt-Timeline**.

Die API kann Winkel nicht schalten → DRT-Trick: Scaffold bauen → `.drt` exportieren → **Kamera-Byte
im XML patchen** → reimportieren. Vorlagen in `vorlagen/mcbuild/`:
`build_scaffold_mc.py` → `patch_mc.py` → `import_mc.py`. Bewährtes, funktionierendes Rezept
(Projekt-A 21.07.2026, siehe Memory `projekt-a-projekt-a-projekt`):

1. **Multicam-Clip von Hand anlegen** (GUI, Computer-use): die Quell-Timelines der Kameras
   auswählen → „Neuen Multicam-Clip mit ausgewählten Clips erstellen" → **Perspektivensync =
   Timecode**. Starten die Quell-Timelines alle bei `01:00:00:00` (= Ton-Frame 0, s. Schritt 3),
   ist **MC0 = 0** (Multicam-Frame = Ton-Frame). Sonst MC0 = Ton-Frame der Multicam-Start-TC.
2. **Angle-Mapping auslesen** (im Multicam-Viewer ansehen, welcher Angle welche Kamera ist —
   projektabhängig!) und in `patch_mc.py`/`import_mc.py` eintragen.
3. Segmente **identisch zum Schnittplan** erzprojekt-c (dieselbe Logik wie die verschachtelte Variante),
   patchen, importieren, Hauptton auf A1.
4. **Schwarzloch-Test (Pflicht):** kleinen 640×360-H264-Render der Multicam-Timeline ziehen und mit
   `ffmpeg -vf blackdetect=d=0.2:pix_th=0.10` über ALLE Frames prüfen — 0 Schwarzbilder erwartet.
   (2 Kameras aus sauberen Quell-Timelines waren sauber; bei Verdacht → geflachte Kamera-Dateien.)

⚠️ **Import projekt-dnnt die Timeline `… MC-Scaffold import`** → hinterher auf `… Multicam Schnitt`
umprojekt-dnnen; Import-Duplikate (Multicam/Quell-Timelines) in einen Backup-Bin schieben.
⚠️ Bei komplexeren Setups können Multicam-Winkel aus verschachtelten Timelines sporadische
~4-s-Schwarzlöcher erzprojekt-c (siehe `fallstricke.md`) — deshalb der Render-Test.

## 7. Verifizieren + Grading

`vorlagen/verify_cut.py`: Clipanzahl je Winkel, **0 Lücken, 0 Überlappungen**, Gesamtdauer,
Tonspur-Länge, bei Multicam zusätzlich Winkel-Abgleich gegen `cut_plan.json`. Zahlen berichten.

Danach Grading — bewährte Kette pro Kamera auf **Clip-Eprojekt-d der Quell-Timeline**:
1. Log→ARRI-Wandlung (bei Sony S-Log3 nicht Sonys LUT — macht rötliche Haut;
   eigene ARRI-Emulations-LUT, `generate_sony2arri_lut.py` bei Projekt-C)
2. Korrektur (Hautton, Helligkeit über Gamma, Weißabgleich)
3. Film-/Kino-Look (ImpulZ / FilmConvert Kodak Ektar / eigene Kino-LUT)
4. Kamera-Angleich (z. B. weit an nah)
5. Feinschliff

**Look-Aufbau des Nutzers (3 Look-LUTs):** 1) auf ARRI wandeln → 2) Film-Emulation
(ImpulZ-Filmstock) → 3) Kino-LUT obendrauf. Details/LUT-Pfade im Memory
`grading-look-kette-praeferenz`.

⭐ **HARTE REGEL — LUT vs. regelbarer Wert (Nutzer-Vorgabe, unbedingt einhalten):**
LUTs sind **nur** für die drei objektiven Look-Schritte erlaubt: **Log→ARRI-Wandlung,
Filmstock-Emulation, Kino-Look-LUT**. **ALLE** anderen Eingriffe — Weißabgleich/Temperatur,
Helligkeit/Belichtung, Farbverschiebungen (Magenta/Grün/Blau/Tönung), Sättigung, Kontrast,
Hautton — müssen als **einzelne Resolve-Nodes mit regelbaren Werten** gebaut werden
(Primaries/Lift-Gamma-Gain, Kurven, ColorSlice, Temp/Tönung), **NIE** als zusätzlich gebackene
LUT. **Grund:** Der Nutzer muss nachvollziehen können, was das Bild vom Original entfernt (sonst
wirkt es schnell unnatürlich), und **jeden einzelnen Wert zurückstellen** können — eine LUT ist
eine Blackbox. Beim Feintunen von Helligkeit/Wärme also **Node-Werte** ändern, nicht die LUT
tauschen. (Filmstock-Variante `_FPE`/`_CIN`/`_VS` oder Kino-Stärke zu wechseln ist erlaubt — das
sind die zulässigen Look-LUTs selbst.)

LUT per API setzen: `project.RefreshLUTList()` **zuerst**, dann `timelineItem.SetLUT(1, name)`.
Werte setzen: `rctl.py grade-set`. Details in `api-werkzeuge.md`.

⭐ **Grading einer Multicam-Schnitt-Timeline (Projekt-A 21.07.2026 verifiziert):** NICHT auf die
Hunderte Schnittclips backen. Stattdessen den Grade **clip-level auf die Winkel-Quell-Timelines**
legen (die „…import"-Timelines, die der Multicam-Clip als Angles nestet) — er **propagiert live
durch den Multicam-Clip auf alle Schnitte des Winkels** (cut-Clip bleibt clip-seitig 1 leerer
Node, zeigt aber den vollen Look). So gilt „einmal pro Kamera, jeder Wert regelbar" auch bei
Multicam. Rezept: pro Winkel-Quell-Timelime auf Teil 0 die Kette bauen, per
`TimelineItem.CopyGrades(rest)` auf die übrigen Teile kopieren. Versehentliche Clip-Grades auf
dem Schnitt mit `graph.ResetAllGrades()` entfernen (sonst doppelt).

⭐ **GLEICHE Node-Inhalte über Kameras = GETEILTE Nodes — via COLOR GROUP (API-Weg, Projekt-A
21.07.2026 verifiziert).** Die identischen Look-Nodes (ARRI-Wandlung, Filmstock, Kino) gehören in
die **geteilten Gruppen-Graphen**, damit **eine** Änderung auf **alle Kameras/Clips** wirkt; nur die
**kamera-spezifische** Korrektur (Angleich, WB/Helligkeit) bleibt lokal. Bewährte Aufteilung:
- **Group Pre-Clip** (geteilt): `Sony→ARRI`-LUT.
- **Clip-Eprojekt-d** (pro Kamera): Korrektur-Node (z. B. weit Temp +200, nah neutral).
- **Group Post-Clip** (geteilt): `Rec709→LogC` → `Filmstock` → `Kino`.

**API-Rezept** (kein Rechtsklick-Gefummel nötig):
```python
grp = proj.AddColorGroup("Look <Projekt>")          # proj.GetColorGroupsList()/DeleteColorGroup
for it in alle_quell_clips:                          # beide Kameras, alle Teile
    it.GetNodeGraph().ResetAllGrades()               # Clip-Eprojekt-d platten
    it.AssignToColorGroup(grp)                        # it.GetColorGroup()/RemoveFromColorGroup
pre  = grp.GetPreClipNodeGraph();  pre.SetLUT(1, "Sony_SLog3_to_ARRI_Rec709.cube")
post = grp.GetPostClipNodeGraph()                    # startet mit 1 Node
```
Nodes im Post-Clip-Graph ergänzen: Color-Seite Node-Modus auf **„Gruppe (nach Clipbearbeitung)"**
stellen, `Alt+S` je weiterem Node, dann `post.SetLUT(1..3, …)` per API. Korrektur: Node-Modus **„Clip"**,
Temp/Werte ins Panel tippen, per `CopyGrades` auf die übrigen Teile der Kamera. **Der Gruppen-Grade
propagiert live durch den Multicam-Clip in den Schnitt** (verifiziert). Vorlage `vorlagen/build_group_look.py`.
Reihenfolge im Bild: Group-Pre → Clip → Group-Post → Timeline.

**Titel-Vorspann** aus einem bestehenden Projekt übernehmen. **Auf einer Timeline mit Inhalt immer
OVERLAY, nie Ripple** (sonst wandern Video+Ton nach hinten → schwarze Lücke): vor jedem Insert alle
Spuren außer der Zielspur sperren. Fertiges Muster `titel_overlay.py`, Hintergrund in
`fallstricke.md` (Titel-Punkt 6). Titeltext aus Ordnername ableiten, nur inhaltlich gegenprüfen.

## 8. Nachbearbeiten (nach dem Schnitt, vor dem Render) — NICHT-DESTRUKTIV

Der Auto-Schnitt ist ein Rohschnitt. Vor dem Endrender durchgehen — aber **nichts wegschneiden oder
löschen, nur MARKIEREN** (Nutzer-Vorgabe, s. Memory `nicht-destruktiv-markieren`). Der Nutzer
entscheidet selbst, was tatsächlich raus.

- **Richtigen Anfang finden:** aus dem Transkript den inhaltlichen Einstieg bestimmen (oft erst nach
  1–3 min, z. B. „Guten Abend, herzlich willkommen"). Dort **nur einen Marker** setzen
  (`Timeline.AddMarker(frame, "Blue"/"Green", "Anfang", …)`) — **den Anfang NICHT wegschneiden**.
  Ende analog markieren (Ton läuft oft nach dem letzten Bild weiter).
- **Organisatorisches / zu Entfernendes** (Pausen-Ansagen, Technik-/Orga-Einschübe, Störungen): die
  betroffenen Clips **nur gelb einfärben** (`TimelineItem.SetClipColor("Yellow")`) — **NICHT löschen**.
- **Verwackelte/unscharfe Winkel tauschen (automatisch auffindbar):** den Schnitt-Render pro
  Cut-Segment auf **Unschärfe** (Laplace-Varianz) und **Bewegung** (Frame-Differenz) prüfen —
  Vorlage `vorlagen/analyze_quality.py` (ffmpeg → numpy, kein OpenCV nötig; misst je Segment gegen
  den **Kamera-eigenen** Median, Schnittgrenzen ±0,4 s ausschließen). Flags mit Frame aus dem Render
  gegenprüfen (`ffmpeg -ss T -frames:v 1`) und die **andere Kamera** an der Stelle ansehen (Quell-
  Timeline). Ist sie brauchbar → auf dem Multicam-Clip den Abschnitt **umschalten**:
  Edit-Seite, Clip anwählen → Rechtsklick → **„Multicam-Perspektive wechseln" → Angle N** (die API
  kann Winkel nicht schalten, dieser GUI-Weg schon; nicht-destruktiv).
  ⭐ **Nutzer-Vorgabe: Bewegung/Schwenk der Kamera ist OK — NUR Unschärfe und Wackeln tauschen.**
  Also **nicht** auf reine Bewegung (Frame-Differenz) hin tauschen; die Schärfe-Metrik ist das
  Kriterium. Auch ein unscharfer Vordergrund (jemand läuft kurz durchs Bild) ist ok, solange das
  **Motiv (Redner) scharf** ist. **Objektivwechsel/Schwarzbild** zeigt sich als extrem niedrige
  Min-Schärfe/Helligkeit — prüfen, ob er im ohnehin zu entfernenden Vorlauf (vor dem Anfang-Marker)
  liegt; dann kein Handlungsbedarf.
- Danach: Titel setzen (Schritt 7), Grading fein bestätigen, **erst dann** Endrender — Render nur auf
  ausdrücklichen Wunsch.
