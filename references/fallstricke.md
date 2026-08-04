# Fallstricke — teuer erlernt, nicht nochmal hineinlaufen

## Verbindung / Setup

- **`scriptapp("Resolve")` → None**, obwohl Scripting auf „Lokal" steht: Resolve läuft seit
  einem Update ohne erreichbaren Skript-Server. **Fix: Resolve komplett neu starten.**
- **Medien auf einer Platte:** liegen Kameras auf E: und eine Quelle auf F:, gibt es Ärger.
  Vor dem Anlegen zusammenziehen.
- **Verzerrter Ton bei der Wiedergabe:** zuerst **Wiedergabe-Framerate = Timeline-Framerate**
  prüfen — nicht-destruktiver Fix, kein Grading-Problem.

## Timeline / fps

- **Timeline-fps 29.97, nicht 30.0.** 59.94-Material konformt sauber zu 29.97; 30.0 lässt alle
  Kameras driften.
- **Start-TC-Konvention einhalten:** `01:00:00:00` = Ton-Frame 0, jede Kamera-Timeline
  `01:00:00:00 + offset`. Sonst stimmt später nichts zusammen.
- **Vorzeichen der Offsets prüfen**, nicht annehmen: Tascam kann vor oder nach den Kameras
  gelaufen sein. Bestimmt, ob Ton oder Kamera getrimmt wird.

## Ton / Sync

- **Shogun-Ton kann auf allen Kanälen stumm sein** (kein SDI-Audio angelegt). Vor dem Sync mit
  ffmpeg `volumedetect` prüfen; ggf. die parallele interne XDCAM-MXF nutzen (Ton oft nur auf
  Track 1/2 bzw. Track 2 = internes Mikro).
- **`_D`-Datei des dr10L ist die Backupspur** — nicht in die Timeline.
- **Resolves eingebauter GUI-Sound-Sync scheitert auf Timeline-Winkeln** („keine Übereinstimmung"),
  selbst bei kräftigem Raumton. Immer die eigene Kreuzkorrelation nehmen.
- Sync-Qualität: **Pearson > 0,45, Streuung < 0,5 s.** Darunter nicht weiterbauen.

## Transkript / Schnittplan

- **Whisper-Löcher:** einzelne Riesensegmente (>200 s) ohne Wort-Zeitstempel. Weder Segment-
  noch Wortebene liefert dort Schnittpunkte → lange Spans **mechanisch unterteilen**.
- Anfang einer Aufnahme ist fast immer **Setup-Geplänkel** — Kopf später trimmen, den Nutzer
  fragen, ab wo der Film beginnen soll.

## Grading

- ⭐⭐ **AUSGESCHALTETE Nodes IMMER erkennen — und beim Übernehmen eines Looks NICHT mitnehmen**
  (Nutzer-Vorgabe 27.07.2026). Wird ein Look aus einem alten Projekt übernommen (`grade-save`/
  `grade-apply`, `CopyGrades`, DRX), kommen **deaktivierte Nodes stumm mit** — sie sind
  Karteileichen, die den Baum aufblähen und beim Lesen in die Irre führen („warum verändert
  Node 2 nichts?"). **Vor der Übernahme prüfen, welche Nodes im Quellprojekt aus sind, und diese
  weglassen.** Beispiel Projekt-B: im Quellprojekt waren `Projekt-B_Korrektur_v5` und
  `Projekt-B_Kino_mittel` **abgeschaltet** — der Look kommt allein aus der ImpulZ/FilmConvert/
  Blade-Runner-Kette; im neuen Projekt gehören diese zwei Nodes gar nicht erst hinein.
  ⚠️ **Die API kann den Zustand nicht lesen:** `NodeGraph` hat nur `SetNodeEnabled`, **kein**
  `GetNodeEnabled` (Resolve 21 geprüft). Deshalb:
  - Beim Sichten eines Fremd-Looks **den Node-Graph ansehen** (Screenshot/Color-Seite) — ein
    ausgeschalteter Node ist am Schalter unten links im Node-Kachel erkennbar; oder den Nutzer fragen.
  - **Nie aus „Node hat eine LUT" auf „Node wirkt" schließen.** `GetLUT()` liefert den LUT-Namen
    auch bei abgeschaltetem Node.
  - Gegenprobe am Bild: Kette einmal komplett vs. verdächtiger Node einzeln rendern — dabei den
    **Viewer-Cache beachten** (frisches TC anfahren, sonst kommt derselbe Frame zurück).
- ⭐ **Timeline-Ebenen-Grade schlägt NICHT durch verschachtelte Quell-Timelines durch** — im
  Schnitt bleibt der Clip Log. **Nur Clip-Ebenen-Grades propagieren ins Nesting.**
  Also immer auf Clip-Ebene graden (Color-Page-Umschalter „Clip", nicht „Timeline").
- **OFX per Bildschirmsteuerung anhängen ist unzuverlässig** (Doppelklick und Ziehen von
  „Color Space Transform" scheiterten wiederholt). Zuverlässig: LUT per Rechtsklick → „LUT auf
  aktuellen Node anwenden", und v. a. **per API `SetLUT`**.
- **`SetLUT` gibt `False`** für neue LUT-Dateien → vorher `project.RefreshLUTList()` (am PROJECT).
- **Sonys `Sony SLog3 to Rec709.ilut` macht rötliche Haut** — verworfen. Stattdessen
  ARRI-Emulation (eigene gebackene LUT, `generate_sony2arri_lut.py`).
  Gekauftes Sony2Alexa (Melara) ist **nicht für die FS7 II kalibriert** — bringt dort nichts.
- **ImpulZ-Filmemulation:** NICHT per CST nach LogC wandeln, sondern
  „Alexa Rec709 to LOG-C" verwenden (siehe Memory `impulz-filmemulation-kette`).
- **Neat Video / temporale OFX nie auf Anpassungsclips** legen — erzeugt Schwarz bei
  Wiedergabe und Rendern. Immer auf echte Clips.
- **Vor dem Eintippen von Lift/Gamma/Gain immer per Farbstreifen prüfen, welches Feld
  Master/R/G/B ist** (Master = weiß). Position nicht raten.
- **Geteilte Nodes sind gesperrt** — Änderung wirkt auf alle Clips der Gruppe.
- ⭐ **Kopierter Anpassungsclip mit keyframe-animierter OFX (z. B. Weichzeichner-„Balken" hinter
  Titeln) rechnet nach dem Einfügen 0 = unsichtbar** (dieselbe Keyframe-Falle wie bei den Titeln:
  Keyframes liegen bei den Quell-Zeiten, außerhalb des neuen Clip-Bereichs → Intensität bleibt auf
  0). Diagnose: Color-Seite → Anpassungsclip (02 im Clip-Streifen) wählen → OFX-Node → Inspector
  zeigt Intensität 0.000 mit gefüllter Keyframe-Raute `◆`. Der Grade-Body liegt in der DB (per
  `titel.grade_body_lesen`; entpacken mit `from compression import zstd`, Py 3.14) und enthält OFX
  `com.blackmagicdesign.resolvefx.gaussianblur` + Fenster-Rechteck-Koordinaten. **Fix (einfach &
  robust): im Inspector die Intensität auf einen festen Wart tippen** (~0.4–0.5, Original war
  HStrength≈0.4) → gilt konstant über die Cliplänge, Balken sichtbar. Wert hält stabil (mit TC-Sprung
  prüfen). Fall Projekt-G 24.07.

## Multicam

- ⛔⛔ **Beim DRT-Bau eines Multicam-Clips NIEMALS neue UUIDs vergeben** (27.07.2026, Projekt-B-2).
  Symptom: Der Import erzeugt zwar einen Multicam-Clip (`Type: Multicam`, richtiger Start-TC),
  aber mit **`Frames 0`** — die Timeline zeigt **schwarz**, und beim Re-Export der Timeline fehlt
  der Container mit `UserDefinedName>Angle 1` komplett. Ursache: Die Zuordnung *Multicam-Sequence
  → Definitionscontainer* steht **nicht** im Klartext-XML (dort findet man nur `<Sequence>`-Felder,
  die scheinbar passen), sondern **UTF-16-hex-kodiert in den zstd-`FieldsBlob`s von
  `MpFolder.xml`**. Ein selbst gewürfelter Container ist dort nirgends registriert und wird
  ignoriert. **Fix: `DbId` von Multicam-Element, `Sm2Sequence` und `Sm2SequenceContainer` aus dem
  Muster-DRT unverändert übernehmen** (Resolve vergibt beim Import ohnehin neue IDs).
  Diagnose-Reihenfolge, die zum Ziel führte: `GetClipProperty('Frames')` (0 = keine Angles) →
  Kontrollimport des unveränderten Musters (dort `Frames` > 0) → Feld-Bisektion → Re-Export der
  importierten Timeline (Container fehlt) → UUID-Suche **auch in UTF-16/zstd**, nicht nur im Klartext.
- ⭐ **Nach dem DRT-Import sind die Angles die `… import`-Kopien, nicht die Original-Quell-Timelines.**
  Auch wenn im DRT die Originale als `MediaRef` stehen: Der Import dupliziert alle enthaltenen
  Timelines und biegt die Referenzen auf die Duplikate um. **Grading gehört danach auf
  `… weit import` / `… seite import`** — nur das propagiert in den Multicam-Schnitt. Die
  Original-Timelines sind funktionslose Reste → in einen Bin „Originale (ungenutzt)" schieben
  (nicht löschen), sonst gradet der Nutzer versehentlich ins Leere. Gilt auch für den Hauptton
  (`… ton import` liegt auf A1).
- **Der `<Name>` im Angle-Container ist ein eingefrorener Text, keine Live-Referenz** — er ändert
  sich nicht mit, wenn Timelines umbenannt werden, und taugt daher NICHT als Nachweis, welche
  Timeline ein Angle speist. **Belastbar ist nur die `MediaRef`:** Timeline als DRT exportieren,
  `MediaRef` des Angle-Clips im `MpFolder.xml` nachschlagen und den dortigen `<Name>` lesen
  (der ist live). Ein Test über „Grade abschalten + Frame rendern" ist unbrauchbar — der Viewer
  liefert einen gecachten Frame (identische Helligkeit trotz abgeschalteter Nodes).
- **`Frames`/Dauer eines Multicam-Clips kommt aus den Angle-Tracks, nicht aus `MediaExtents`.**
  Ändert man nur `MediaExtents`, verschiebt sich der Start-TC, die Dauer ergibt sich weiter aus
  `max(Angle-Ende) − neuer Start` (im Test: 41575 → 41752 Frames). Nützlich als Prüfgröße.
- **`In` der Schnittclips ist die Multicam-Zeitbasis:** `In = ton-Frame − MC0`. Aus einem
  Nesting-Clip umgerechnet: `In_neu = In_alt + off_frames[kamera] − MC0`. Nimmt man versehentlich
  die Timeline-Position (`Start − MC_START`), zeigen alle Clips die falsche Stelle (erkennbar an
  einem negativen `GetLeftOffset()` beim ersten Clip).
- **Multicam-Winkel aus verschachtelten Timelines erzeugen sporadische ~4-s-Schwarzlöcher**
  (echt schwarz, auch im Render; Projekt-C: 92 betroffene Clips). Rohdatei und Quell-Timeline
  sind dabei fehlerfrei — es ist die Multicam-Verschachtelung.
  **Prävention: Winkel aus echten Medien-Clips bzw. je Kamera einer geflachten Datei bauen.**
  Reparatur falls doch passiert: betroffene Stücke als ProRes rendern und frame-genau auf V2
  legen (Look-Nodes auf Timeline-Ebene wirken mit) — Skripte bei Projekt-C.
- **Angle-Mapping ist projektabhängig** und muss ausgelesen werden (Projekt-B: 1=seite, 2=weit;
  Projekt-C: 1=seiteR, 2=nah, 3=weit, 4=seiteL). Im Projekt-Memory notieren.
- Perspektivensync des Multicam-Clips: **Timecode** (unsere Start-TC-Konvention macht das exakt).

## Titel-Vorspann (`titel.py`)

1. **Text steht in `Value` UND `Expression`** (`string.upper(...)`). Expression überschreibt den
   Value → beim Lesen Expression bevorzugen, beim Schreiben **beide** setzen.
2. **Comp-Zeiten normalisieren.** Exportierte Comps tragen absolute Zeiten des Quellprojekts;
   ohne Umrechnung liegen alle Keyframes außerhalb → Animation eingefroren, Titel unsichtbar
   (Symptom: schwarzes Bild, Key-Kanal weiß).
3. **`SetMarkInOut` erwartet RELATIVE Frames** (0 = Timeline-Anfang). Der Mark-Bereich bestimmt
   Einfügeposition **und** Dauer.
4. **Zielspur nur per Tastatur** (`Alt+<Nr>` auf der Edit-Seite, **Umschalter!**). Ohne das landen
   Inserts auf V1 und verschieben dort alles. Spur sperren blockiert den Insert ganz.
5. **Anpassungsclips liefern frisch eingefügt keinen Node-Graph** → Grade als `.drx` in die
   Galerie, der Nutzer klickt einmal. In der Projekt-DB heißt der Clip englisch
   `Adjustment Clip`, in API/Oberfläche deutsch „Anpassungsclip". **Zusatz (Projekt-A 21.07.):
   die Color-Seite lässt den ungegradeten Anpassungsclip auch per GUI kaum anwählen** (Clip-Strip
   listet ihn nicht, `GetCurrentVideoItem` liefert den darüberliegenden Titel/das Video darunter).
   Praktisch: Galerie-Grade vom Nutzer manuell doppelklicken lassen (Anpassungsclip auf der
   Color-Mini-Timeline-Lane wählen) — Automatisierung unzuverlässig.
8. ⭐ **„Simple White"-Titel haben oft ZWEI Schatten übereinander — nie stapeln.** Quelle 1: der
   **Text+-interne Schatten** (Shading-Element 3 im „Template"/TextPlus-Node: `Enabled3=1`,
   `Softness3=1`, Rest Default). Quelle 2: ein separater **DropShadow-OFX-Node „Schlagschatten1"**
   (`com.blackmagicdesign.resolvefx.dropshadow`, Params `shadowStrength`, `Strength`, `shadowBlur`,
   `ShadowDistance`, `shadowAngle`). Symptom: Nutzer reduziert EINEN Schatten in Fusion → im Bild
   ändert sich nichts, weil der andere voll bleibt („liegen da zwei Schatten übereinander?" → ja).
   **Bei weißem Text auf hellem Grund ist der Schatten lesbarkeitstragend** — nicht voll entfernen,
   nur abschwächen; Element 3 ganz abzuschalten macht den Text blass. Nutzer-Regel: **kein
   Doppelschatten**, nur eine Quelle pflegen. Comp per `ExportFusionComp`/Regex prüfen
   (`Enabled3`, `shadowStrength`), gezielt einen Wert patchen, `ImportFusionComp`.
9. ⭐ **Edit/Montage-Viewer cached den Fusion-Render:** Comp-Änderung (Schatten, Text) erscheint im
   Schnitt-Viewer erst nach **frischem Frame** (Abspielkopf auf ein noch nicht gerendertes Timecode
   bewegen) oder Cache-Leeren — sonst wirkt es, als hätte die Fusion-Änderung „nicht gegriffen".
   Immer auf einem frischen Frame verifizieren, nicht auf dem zuletzt gezeigten.

7. ⭐ **Titel aus Fremdprojekt mit ANDERER Framerate kopiert = unsichtbar (Keyframes außerhalb
   des Render-Fensters).** Beim Kopieren/Einfügen eines Fusion-Titels aus z. B. einem 29.97-fps-
   Projekt in eine 59.94-fps-Timeline rechnet Resolve den **Clip-Renderbereich** (GlobalIn/Out) auf
   die neue Framerate/Position um (z. B. −1164/−754 → −2328/−1507), lässt die **Keyframes** aber auf
   den alten Werten (−1124…−854) → sie liegen komplett hinter dem Clip-Ende → Animation friert auf
   Deckkraft 0 = Titel unsichtbar. **Symptom identisch** zu Punkt 2, aber `zeit_normalisieren(…,0)`
   ist hier FALSCH: GlobalIn/Out wird beim `ImportFusionComp` von Resolve aus der Clip-Position
   bestimmt (Import-Wert ignoriert) und bleibt −2328/−1507 — auf 0 normalisierte Keyframes lägen
   dann erst recht außerhalb. **Richtiger Fix (in-place, kein Rippeln):** nur die Keyframes linear
   aus der Quell-Zeitbasis in den Clip-Renderbereich mappen:
   `neu = gi_clip + (t − gi_quelle) * (span_clip/span_quelle)` (Quelle Projekt-C-Vorlage:
   gi=−1164, span=410). **ACHTUNG — die eigentliche Falle:** Die Abbildung muss auf ALLE
   Zeitkoordinaten wirken, nicht nur auf die Keyframe-Keys `[t] = {`, sondern auch auf die
   **Bézier-Anfasser** `LH = { t, v }` / `RH = { t, v }` (jeweils nur das ERSTE Element = Zeit;
   das zweite ist der Wert!). Verschiebt/skaliert man nur die Keys und lässt die Handles auf den
   alten Absolut-Zeiten stehen, zeigen die Tangenten seitwärts → **Splines wirken um ~90° gedreht /
   mit Schleifen** (genau das passiert bei `titel_fix2.py`, nicht verwenden). Korrekt:
   `titel_fix3.py` (Fall Projekt-G 24.07.) — eine affine Abbildung auf Keys, LH/RH, GlobalIn/Out,
   CurrentTime. Basis immer das PRISTINE Original nehmen (vor eigenen Fehlversuchen exportiert).
   Merke außerdem: `titel.py`/`titel_overlay.py` `zeit_verschieben` ändert **nur** `[t]={`, nicht
   die Handles → derselbe Verdreh-Bug bei jedem Shift; bei gleicher fps/kleinem Shift fällt es kaum
   auf, bei fps-Unterschied (Skala ≠ 1) wird es sichtbar. `titel.py apply`/`titel_overlay.py`
   skalieren zudem bei fps-Unterschied die **Dauer** (skala=fps/qfps) mit, die **Keyframes nicht**.

6. ⭐ **titel.py rippelt bei Timelines MIT Inhalt** (Multicam-Schnitt): `InsertFusionTitle`/
   `InsertGenerator` sind Ripple-Inserts und schieben ALLE ungesperrten Spuren → V1+A1 wandern
   um die Vorspann-Länge nach hinten, es entsteht eine schwarze Lücke (Titel enden früher als der
   längere Anpassungsclip). titel.py ist für Append/leere Köpfe gedacht. **Lösung für OVERLAY
   (Titel über vorhandenem Bild, kein Ripple): vor JEDEM Insert alle Spuren AUSSER der Zielspur
   sperren** (`SetTrackLock('video',v, v!=ziel)` + alle Audio sperren) — dann rippelt nur die
   leere Zielspur, V1/A1 bleiben bei 0. Zielspur weiter per Alt+Nr wählen (Resolve muss im
   Vordergrund sein, sonst landet der Insert auf V1). Reihenfolge Anpassungsclip(V2) dann
   Titel(V3). Fertiges Muster: `resolve-prep\Projekt-A\mcbuild\titel_overlay.py`.

## OFX per Skript setzen — GELÖST (20.07.2026), aber mit Fallen

**OFX-Transplantation funktioniert** (per `ApplyGradeFromDRX` mit selbstgebauter DRX, per
DB-Injektion und per `grade-copy`) — Details/Rezept in `api-werkzeuge.md`. Die Fallen, die
das Experiment fast scheitern ließen:

- ⭐ **Keyframe-Falle (DIE große Erkenntnis):** Ein transplantierter Grade, dessen OFX-Parameter
  im Quellclip **keyframe-animiert** war, wertet die Kurve im Ziel **außerhalb des
  Quell-Zeitbereichs** aus → Effekt rechnet mit Startwert (oft 0) = unsichtbar, obwohl er
  korrekt am Node hängt, gelistet wird und sein Power Window sogar maskiert. Sah aus wie
  „Aktivierung fehlt" — in Wahrheit stand die Blur-Stärke auf 0. **Vor dem Transplantieren
  Keyframe-Listen (f5-Einträge mit f3-Zeitstempeln) entfernen oder auf statische Werte plätten.**
- **Nur Nicht-Default-Werte werden serialisiert:** Ein OFX-Param auf Default (z. B. Blur 0.4)
  taucht im Body **gar nicht auf**. Zum Setzen ggf. Eintrag **hinzufügen**
  (`f5 = {f1: name, f2: {f2: double}}`), nicht nur suchen+patchen.
- **OFX per GUI anhängen:** Doppelklick im Effekte-Panel tut NICHTS (bestätigt). Zuverlässig
  ist **langsames Drag in Einzelschritten**: `mouse_down` auf Effekt → mehrere `mouse_move`
  Richtung Node → kurz warten → `mouse_up`. (`left_click_drag` am Stück scheitert.)
- `ApplyGradeFromDRX` **filtert unbekannte Corrector-Elemente heraus** (Windows-Einträge
  2/4/5/6/18 flogen bei Fremd-Bodies raus); die DRT-Import- und DB-Injektions-Wege übernehmen
  dagegen alles. Für volle Treue (inkl. Windows) DB-Injektion bei geschlossenem Projekt nutzen.
- **Gauß-Blur auf flacher Fläche/linearer Ramp ist mathematisch unsichtbar** — beim Testen von
  Blur-Effekten immer Bildbereiche mit Detail prüfen (Test sonst blind).
- **CDL-Trick zum Window-Sichtbarmachen:** Slope 2.0 auf den Node → die sich ändernde Region
  im Frame-Diff zeigt exakt die Maske.
- `Timeline.Export(pfad, resolve.EXPORT_DRT, resolve.EXPORT_NONE)` → DRT ist ein **ZIP** mit
  `project.xml` + `SeqContainer/*.xml` (dort die Grade-Bodies) + `MediaPool/`.
- **Geteilte Nodes** (FilmConvert/Osiris shared) liegen NICHT im Clip-Body, sondern in
  `ListMgt::LmPowerNode.NodeBA`.

## Grafik-Einblendungen / Overlays  (ausführlich: `grafik-einblendungen.md`)

- **Standbilder landen nur mit 5 s in der Timeline.** `AppendToTimeline` ignoriert bei PNG/JPG
  das `endFrame`; `SetClipProperty('Frames')` gibt `False`; es gibt **kein** Project-Setting für
  die Still-Dauer (nur App-Preference). → PNG per ffmpeg in **ProRes-MOV mit exakter
  Frameanzahl** wandeln (`vorlagen/overlay_tools.py mov`). Alpha-Overlays: **ProRes 4444**
  (`-pix_fmt yuva444p10le`), Resolve erkennt den Alphakanal automatisch.
- **⭐⭐ ffmpeg-`zoompan` ZITTERT sichtbar** (rundet die Position pro Frame auf ganze Pixel,
  auch mit Supersampling). Der Nutzer bemerkt es sofort. → **Zoom nie einbacken**, Grafik
  statisch liefern, Zoom in Resolve setzen lassen (subpixel-genau).
- **Keyframes/Dynamic Zoom im Inspector per Computer-Use sind unzuverlässig** (winzige
  Keyframe-Rauten, Klick setzt oft nichts). Nicht damit kämpfen — dem Nutzer überlassen.
- **⭐ Zoom-Sicherheit gilt für BILD, nicht nur für Text.** Ein 110 %-Zoom schneidet je Rand
  4,55 % ab; eine KI-Illustration, die bis an die Kante reicht, verliert Kopf und Füße.
  Prüfen mit `overlay_tools.py check`, reparieren mit `overlay_tools.py zoomsafe`.
- **⭐ Erzeuger-Skripte NIE mit fest verdrahtetem Ausgabenamen schreiben** (z. B. `"Instagram Kurz %s" % titel`
  → verwechselbar mit anderen Projekten). Immer `basis = os.path.splitext(quelle)[0]` und daraus
  `f"{basis} <Zusatz>.<ext>"` bilden — siehe [[dateinamen-konvention]], SKILL.md Punkt 14.
  Bereits vorhandene generische Namen auf Wunsch umbenennen (behalten, nicht löschen).
- **⭐ Titelbild: NIE Text über Kopf/Stirn/Gesicht der Hauptperson** (Hintergrundpersonen ok).
  Zweimal übersehen worden (#2, #4), obwohl Memory [[titelbild-kopf-freihalten]] es sagt — daher
  **vor dem Rendern des Titelbilds hier nachlesen** und das Ergebnis **immer ansehen**. `make_thumb`
  hat `KOPF_FREI_FRAC` (rechte Textkante als Breitenanteil): steht die Person mittig/links, auf den
  Kopf-Beginn verkleinern (der Kicker wird per `fit_track` mitverkleinert). Faustregel: lieber
  kleinere Schrift links als ein Buchstabe über der Schläfe.
- **Datei überschrieben → Resolve zeigt „Media Offline" bzw. die alte Version.** Einfachster Fix
  (verifiziert 3.8.2026): MediaPool-Item **relinken** — `mp.RelinkClips([clip], r"<ordner>")`;
  der Timeline-Clip aktualisiert sich sofort, kein Löschen/Neu-Importieren nötig. (Manchmal zeigt
  Resolve die neue Version auch ohne Zutun — erst per `rctl.py frame` prüfen.)
- **`rctl.py frame` zeigt Overlays oberer Spuren NICHT** (nur die Color-Ebene) — zum Prüfen
  den Resolve-Viewer per Screenshot ansehen.
- **libass:** beim Einbrennen von ASS-Untertiteln **kein `fontsdir`** angeben, sonst fällt es
  auf eine Ersatzschrift zurück (mit `fontsdir=.` + `Bold=-1` reproduzierbar falsch).
- **ffmpeg-Filter-Expressions:** keine Kommas und kein `pow()` benutzen (bricht die
  Filtergraph-Syntax) — Potenzen als Multiplikation ausschreiben.

## Sackgassen — nicht nochmal probieren

- Fusion-`ActionManager` (889 Actions) steuert **nur die Fusion-Seite**, nichts für Color/Edit.
- `GalleryStillAlbum.ExportStills` ist in R21 launisch (oft `False`).
- „ID-Swap" zum Kalibrieren von DRX-Parametern schlägt bei bereits vorhandenen IDs fehl
  (Duplikat ⇒ Regler wird ignoriert).
- ChatGPT als Teil-Ausführer spart nichts (nur per Bildschirmsteuerung erreichbar = teurer).

## Grafik-Einblendungen / Overlays

**`overlay_tools.py place` loeschte fremde Projekte per Namensgleichheit (29.07.2026):**
Symptom: Auf der Timeline von #3 zeigte das Fachbegriffe-Lower-Third ploetzlich
Inhalte von #4 (Schrägen). Ursache: `cmd_place` loeschte vor dem Import ALLE
Media-Pool-Clips mit demselben DATEINAMEN in Master-Root (`c.GetName()==name`),
egal aus welchem Projektordner. Da jede Folge dieselbe Konvention `g1_..., g2_...`
nutzt, hat eine SPAETERE Session (die #4-Grafiken baute) den GLEICHNAMIGEN
`g1_fachbegriffe.mov`-Clip von #3 geloescht und ihren eigenen unter demselben
Namen neu angelegt — Resolves automatisches Offline-Relink-per-Dateiname hat
daraufhin die #3-Timeline-Clips stillschweigend auf die #4-Datei umgebogen.
**Fix (schon eingebaut):** der Lösch-Check vergleicht jetzt den vollen Dateipfad,
nicht nur den Namen — UND `place` importiert seither automatisch in den
Projekt-Unterordner statt in Master-Root (Ordnername = Elternordner der Quelldatei),
inkl. Kurzhinweis im `Comments`-Feld per `--fuer` (Details in
`grafik-einblendungen.md` Abschnitt 5). Nach dem Bauen neuer Folgen (#5–#7)
trotzdem kurz gegenpruefen: `GetMediaPoolItem().GetClipProperty('File Path')` der
eigenen g1…g9-Clips, falls eine andere Session parallel dieselben Namen benutzt.

**ffmpeg-Befehle in Anweisungsdateien: Filterketten IMMER quoten (29.07.2026).**
`-vf crop=...,scale=...,subtitles=...` und `-af loudnorm=...` enthalten Kommas.
Der Nutzer arbeitet in **PowerShell**, und dort sind nackte Kommas
Array-Trenner — der kopierte Befehl bricht ab. In `instagram_kurz.py` wird
deshalb jedes Argument ausser den Schaltern (`-x`) in Anfuehrungszeichen
gesetzt. Gilt fuer jede Anweisungsdatei, die wir dem Nutzer hinlegen.
