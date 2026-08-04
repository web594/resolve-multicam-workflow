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
schlägt auf alle Schnitte durch — aber nur auf **Clip-Ebene**, siehe `fallstricke.md`.

## 4. Transkript (`vorlagen/transcribe.py`)

faster-whisper `large-v3` auf CUDA über den Hauptton (16 kHz mono via ffmpeg).
Ergebnis: `segments.json` + `words.json`. Wortebene ist für den Schnittplan die bessere Basis.

⚠️ Whisper erzeugt manchmal **Riesensegmente ohne Wort-Zeitstempel** (Projekt-B: 223 s am Stück).
Der Schnittplan muss solche Löcher mechanisch füllen (siehe Schritt 5).

## 5. Auto-Schnittplan (`vorlagen/make_cutplan.py`)

Prinzip: **eine Leitkamera als Standard**, Cutaways an Sprechpausen.

⭐ **Schnitt-Tempo: geringfügig ruhiger** (Nutzer-Vorgabe 27.07.2026, nach Projekt-A). Begründung
des Nutzers: manche Schnitte kamen zu früh — „wenn gerade ein Schnitt war, dem Zuschauer etwas
mehr Zeit lassen, sich auf das Bild einzustellen; und wenn danach gleich wieder nur kurz eine
andere Einstellung kommt, diese etwas länger". Es genügen wenige Sekunden mehr pro Einstellung.
Bewährte Werte (Projekt-B-2: 21 Einstellungen, ⌀ 23,6 s, kürzeste 10,5 s — vorher ⌀ 21,5 s ab 4 s):

| Parameter | ruhig | vorher |
|---|---|---|
| `MIN_SHOT` (Mindestlänge einer Einstellung) | **6,0 s** | 4,0 |
| `CUT_MIN` / `CUT_MAX` (Cutaway-Länge) | **6,0 / 11,0 s** | 4,0 / 8,0 |
| `PARA_GAP` (Absatzpause, löst Cutaway aus) | **1,2 s** | 1,0 |
| `MAX_STD` (Zwangswechsel) | **50 s** | 40 |
| **`CALM_GAP`** (neu: Sperre nach einem Cutaway) | **12 s** | – |
| mechanische Teilung `SPLIT_MAX/HOLD/CUT` | **55 / 42 / 10 s** | 45 / 34 / 7 |

Außerdem zwei Regeln gegen Unruhe am Filmanfang: der **erste Span ist immer die Leitkamera**
(`gap_before = 0` für i = 0, `last_cut_end` ab Sprechbeginn) und **vor dem inhaltlichen Anfang
(`ANFANG`) werden keine Cutaways ausgelöst** — sonst fällt 2 s hinter dem Filmstart ein Schnitt.

- Phrasen an Wortpausen ≥ 0,4 s; Cutaway an Absatzpausen (≥ 1,2 s);
  **Zwangswechsel nach 50 s**, damit es nicht einschläft.
- Bei mehreren Cutaway-Kameras abwechselnd (Projekt-C: weit/seiteL, seiteR nur Reserve).
- **Lange Spans ohne Wortzeiten mechanisch unterteilen** (>45 s → z. B. 34 s Leit + 7 s Cutaway).
- **Leitkamera + welche Kameras überhaupt im Auto-Schnitt vorkommen: beim Nutzer erfragen.**
  (Projekt-B: weit = Standard, seite = Auflockerung, weil es keine frontale nah gab.)
- Ergebnis `cut_plan.json` (Spans mit Ton-Sekunden + Winkel).

## 6. Schnitt-Timeline bauen — bei ≥2 Kameras IMMER Multicam mit Schnitten

**Standard-Lieferung bei mehreren Kameras ist die geschnittene Multicam** (nicht bloß die
verschachtelte Schnitt-Timeline): so kann der Nutzer beim Bearbeiten jeden Clip anklicken und auf
eine andere Kamera umschalten. Die verschachtelte Variante entsteht als Zwischenschritt, das
**auszuliefernde Ergebnis ist die Multicam-Schnitt-Timeline**.

### ⭐⭐ Der Multicam-Clip wird per DRT GEBAUT — keine Maus, kein GUI-Klick

**Verbindlich (Nutzer-Anweisung 27.07.2026): so und nicht anders. Nicht vergessen.**
Verifiziert am Projekt Projekt-B-2 (Resolve 21.0.3): Multicam-Clip + 21 Winkel-Schnitte
vollautomatisch, 0 Winkelfehler. Die offizielle API hat zwar **kein** `CreateMultiCamClip`
(geprüft an `resolve/pm/proj/mp/tl` — nur `AutoSyncAudio`), aber ein Multicam-Clip ist im DRT
nur XML und lässt sich daher erzeugen.

**Was ein Multicam-Clip im DRT ist** (`.drt` = ZIP mit `project.xml`, `MediaPool/Master/MpFolder.xml`,
`SeqContainer/<uuid>.xml`):
- ein `<Sm2MpMulticamClip>`-Element in `MpFolder.xml` (mit eigener `<Sm2Sequence>`), und
- ein **Definitions-SeqContainer**: pro Kamera **ein Track** mit `<UserDefinedName>Angle N</UserDefinedName>`,
  darin ein Clip mit `<MediaRef>` = **DbId der Quell-Timeline**, `<Start>` (Start-TC in Frames,
  inkl. 108000), `<Duration>`, `<MediaStartTime>` (= Start/FPS).
- Die Schnittclips der Timeline verweisen per `<MediaRef>` auf den Multicam-Clip; die **Winkelziffer**
  steht in ihrem `FieldsBlob` hinter `4b616d657261c2a0` („Kamera"+NBSP): `31`=Angle 1, `32`=Angle 2.

**Zahlenformate (reverse-engineered):**
| Feld | Format |
|---|---|
| `MediaExtents` | 2 **little-endian** doubles als Hex: `[start_s, dauer_s]` |
| `MediaTimemapBA` | `"02"` + **big-endian** double (Dauer des Quellmediums in s) |
| `MediaStartTime` | Start-TC der Quelle in Sekunden (Frames/FPS) |
| `Start`/`Duration`/`In` | Frames; `In` = **ton-Frame − MC0** (MC0 = frühester Angle-Start) |

**Ablauf (Vorlagen in `vorlagen/mcbuild/`):**
1. `apply_cut.py` → verschachtelte Schnitt-Timeline, dann `Timeline.Export(pfad, 1)` = **Basis-DRT**.
2. Aus **irgendeinem älteren Projekt mit Multicam** eine Timeline als **Muster-DRT** exportieren
   (liefert die Muster-Elemente und die passenden Blobs).
3. **`build_mc_drt.py`** — setzt Multicam-Element + Definitionscontainer ins Basis-DRT und biegt die
   Schnittclips um (Winkel je Clip aus dem Kameranamen des Nesting-Clips).
4. **`import_mc2.py`** → `ImportTimelineFromFile`; danach Timeline umbenennen, Hauptton auf A1 prüfen.
5. **`verify_mc.py`** → Clipanzahl, 0 Lücken/Überlappungen, **0 Winkelfehler ggü. Plan**, Winkelverteilung.

⛔ **DIE Falle — niemals neue UUIDs würfeln.** Die Zuordnung *Sequence → Definitionscontainer* steht
**nicht** im Klartext-XML, sondern **UTF-16-kodiert in den zstd-`FieldsBlob`s von `MpFolder.xml`**.
Wer dem Multicam neue `DbId`s gibt, erhält einen Clip **ohne Angles**: `Frames 0`, schwarzes Bild,
und der Definitionscontainer taucht beim Re-Export gar nicht mehr auf. **Also die `DbId`s von
Multicam-Element, Sequence und Container aus dem Muster unverändert übernehmen** — beim Import
vergibt Resolve ohnehin frische IDs. (Diagnose, falls es doch klemmt: `Frames`-Property des
Multicam-Clips lesen — >0 = Angles gefunden; und die Timeline re-exportieren: fehlt ein Container
mit „Angle 1", wurde er ignoriert.)

Weitere Punkte:
- **MC0** = frühester Angle-Start in ton-Frames; Multicam-Frame = ton-Frame − MC0.
- **Angle-Mapping selbst bestimmen** (Reihenfolge der Tracks): bewährt **Angle 1 = Leitkamera**.
  Prüfen lässt es sich hinterher an den Clipnamen (`… - Angle 1`) und am gerenderten Frame.
- **Import erzeugt Kopien der Angle-Quell-Timelines** (`… weit import` usw.) — das ist gewollt und
  entspricht dem bewährten Aufbau: der **Grade liegt clip-seitig auf diesen import-Timelines** und
  propagiert durch den Multicam-Clip in alle Schnitte.
- Mehrfach-Versuche hinterlassen `… import 1/2/3`-Duplikate → mit `cleanup.py` aufräumen.
- **Schwarzloch-Test (Pflicht):** kleinen H264-Render der Multicam-Timeline ziehen und mit
  `ffmpeg -vf blackdetect=d=0.2:pix_th=0.10` über ALLE Frames prüfen — 0 Schwarzbilder erwartet.

## 7. Verifizieren + Grading

`vorlagen/verify_cut.py`: Clipanzahl je Winkel, **0 Lücken, 0 Überlappungen**, Gesamtdauer,
Tonspur-Länge, bei Multicam zusätzlich Winkel-Abgleich gegen `cut_plan.json`. Zahlen berichten.

Danach Grading — bewährte Kette pro Kamera auf **Clip-Ebene der Quell-Timeline**:
1. Log→ARRI-Wandlung (bei Sony S-Log3 nicht Sonys LUT — macht rötliche Haut;
   eigene ARRI-Emulations-LUT, `generate_sony2arri_lut.py` bei Projekt-C)
2. Korrektur (Hautton, Helligkeit über Gamma, Weißabgleich)
3. Film-/Kino-Look (ImpulZ / FilmConvert Kodak Ektar / eigene Kino-LUT)
4. Kamera-Angleich (z. B. weit an nah)
5. Feinschliff

⭐⭐ **Look aus einem Vorgängerprojekt übernehmen — NICHT allein per DRX** (teuer gelernt, Projekt-B-2).
`grade-save`/`grade-apply` bringt zwar alle Nodes, LUT-Namen, OFX und Power Windows mit, **aber
nicht die vollständige Verdrahtung**: Nodes in Nebenzweigen (Layer-Mixer/Key) tragen im Ziel
nichts mehr bei. Symptom: Der Baum sieht vollständig aus, aber **nur der Hauptstrang wirkt**
(bei Projekt-B-2: nur FilmConvert + der letzte Primärbalance-Node), das Bild bleibt flau und neutral.
Nachweis per Render-Messung: Quellprojekt RGB (141, 123, 107) = warm, Ziel (121, 119, 115) = neutral;
im Quellprojekt bewirkte allein die ARRI-LUT Δ 22,6, im Ziel < 0,1.
- **Prüfen, ob der Look wirklich angekommen ist** — nie nur die Node-Liste vergleichen: je einen
  **Render** (nicht Viewer, der cached!) von Quelle und Ziel ziehen und die mittleren RGB-Werte
  vergleichen. `vorlagen/wirkt_render.py` misst die Wirkung einzelner Nodes per 20-Frame-Render.
- **Zuverlässiger Weg: Galerie/PowerGrade-Still** (projektübergreifend) — im Altprojekt Still
  greifen, im neuen Projekt auf den Clip anwenden. Erhält die Verdrahtung **und** die
  Original-Node-Labels (`arri Shared Node`, `filconv Shared Node` …), woran man den geglückten
  Transfer erkennt. Braucht 1–2 Klicks des Nutzers; per API unzuverlässig.
- Danach mit `CopyGrades` auf die übrigen Kameras verteilen (erhält geteilte Nodes).

Weiteres zum DRX-Weg:
- **Ausgeschaltete Nodes des Altprojekts NICHT mit übernehmen** — sie kommen stumm mit und
  verwirren später. Vorher klären, welche aus sind (die API kann es nicht lesen, s. `fallstricke.md`).
- ⚠️ Der **DRX-Weg zerreißt geteilte Nodes**: aus den Shared Nodes des Altprojekts werden pro
  Zielkamera **eigene Kopien** (erkennbar an durchnummerierten Labels „Shared Node 1–8" bei der
  ersten, „9–16" bei der zweiten Kamera). **Fix: `grade-apply` nur auf die ERSTE Kamera, dann mit
  `TimelineItem.CopyGrades(ziele)` auf die übrigen verteilen** — `CopyGrades` überträgt geteilte
  Nodes als **dieselben** Objekte, eine Änderung wirkt danach auf alle Kameras (verifiziert:
  LUT auf Kamera A gewechselt → erschien sofort auf Kamera B). Nebenbei ist das auch der
  einfachste Weg, überzählige Nodes loszuwerden — die API kann Nodes nicht einzeln löschen.
- Der Look sitzt selten in den auffälligen LUT-Namen allein: bei Projekt-B ergaben die drei
  „Haupt"-LUTs ohne den Rest der Kette ein deutlich blasseres Bild.

### ⭐ Referenz-Look Projekt-B (Endstand Projekt-B-2) — Ausgangspunkt fürs Weiterverbessern

Der Nutzer hat den Look aus Zeitmangel so verwendet und will ihn **beim nächsten Mal gemeinsam
verbessern („welche Nodes und LUTs")**. Endstand: **11 Nodes, geteilt über beide Kameras**:

| # | Node | Inhalt |
|---|---|---|
| 1 | `arri` | LUT `Projekt-B_ARRI_exp-1p60` (S-Log3 → ARRI) |
| 2 | `kodak aktar fc` | LUT `Rec709_Kodak Ektar 100_FC` (ImpulZ) + Key |
| 3 | `filconv` | OFX **FilmConvert Nitrate** + Key |
| 4 | `709 to cin` | LUT `Rec709_Kodak Ektar 100_CIN` + Key |
| 5 | `cin to koda` | LUT `Cineon to Kodak 2383 FPE (D50)_Impulz` + Offset |
| 6 | `lut br` | LUT `Blade Runner` + 3D-Qualifizierer |
| 7 | `beauty smooth` | OFX DCTL (eigenes Hautglättungs-Plugin) |
| 8 | `glanzlichter-` | Primärbalance + Qualifizierer + externer Key |
| 9 | `kreis maske` | Power Window |
| 10 | – | Primärbalance + Offset |
| 11 | – | **Hautfarbe**: Offset + *Farbton vs. Farbton* + *Farbton vs. Sättigung* (Kurven) + 3D-Qualifizierer |

⭐ **Node 11 ist die Antwort auf „die Haut soll mehr Farbe bekommen":** ein eigener Node mit
**Farbton-vs-Sättigung-Kurve über einen Hautton-Qualifizierer** — nicht global die Sättigung
anheben. Diesen Node hat der Nutzer selbst gebaut; die Kurven/Qualifizierer sind per API nicht
setzbar (nur per GUI) → bei Bedarf Bildschirmsteuerung erbitten oder den Nutzer machen lassen.

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
- **Clip-Ebene** (pro Kamera): Korrektur-Node (z. B. weit Temp +200, nah neutral).
- **Group Post-Clip** (geteilt): `Rec709→LogC` → `Filmstock` → `Kino`.

**API-Rezept** (kein Rechtsklick-Gefummel nötig):
```python
grp = proj.AddColorGroup("Look <Projekt>")          # proj.GetColorGroupsList()/DeleteColorGroup
for it in alle_quell_clips:                          # beide Kameras, alle Teile
    it.GetNodeGraph().ResetAllGrades()               # Clip-Ebene platten
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

### ⭐ Was der Nutzer nach der Übergabe SELBST machen musste (Projekt-B-2) — künftig mitliefern

Am fertigen Projekt abgelesen. Der **Ablauf** ist allgemein; die **Inhalte** von Titel und
Einspieler sind es **nicht** — ⚠️ die sind pro Reihe/Kunde verschieden (Nutzer-Hinweis
27.07.2026). Konkrete Texte/Clips also nie aus einem anderen Projekt übernehmen, sondern für
die jeweilige Reihe erfragen oder aus einer früheren Folge **derselben** Reihe ablesen.
Die folgenden Beispielwerte stammen aus der Reihe Projekt-B und gelten nur dort: 

1. **Arbeitskopie `<Projekt> Multicam auswahl`** anlegen (Duplikat der Multicam-Schnitt-Timeline).
   Dort wird gefeilt — die gelieferte `… Multicam Schnitt` bleibt als unveränderter Stand liegen.
   **In der Kopie darf geschnitten werden** (das ist nicht destruktiv, das Original bleibt).
2. **Vorlauf am Anfang-Marker abtrennen** (bei Projekt-B-2 wurde exakt am Marker `Anfang` geschnitten,
   der Vorlauf blieb als orange markierter Clip stehen). Ende analog.
3. **Einspieler/Fremdclips** — ⚠️ **reihenspezifisch, nicht verallgemeinern.** Ob es überhaupt
   welche gibt, welche und wo, ist bei jeder Reihe anders (bei Projekt-B ein 6,5-s-Clip mit
   eigenem Ton auf A1). Material kommt vom Nutzer → nachfragen, nicht annehmen.
4. **Endmontage `<Projekt> zus`** (dieselbe Struktur wie bei Projekt-E/Projekt-B-1):
   - **V1 + A1**: das **gerenderte** Video des Feinschnitts (`<Projekt> 1 15.mp4`)
   - **A2**: die extern **nachbearbeitete Tonspur** (dort `verb1, … ton-esv2-70p`)
   - **V3**: Balken-Clip **„Einfarbig"**, **V4**: Titel (bei Projekt-B „Simple White", Frame 35–320
     bzw. 0–352, Text `DR. MAX MUSTERMANN` / `BERUFSBEZEICHNUNG`) — ⚠️ **Titelgestaltung und Text sind
     reihenspezifisch**, nur die Technik ist allgemein: `titel_overlay.py`, OVERLAY statt Ripple
     (Spuren sperren, s. `fallstricke.md`).
