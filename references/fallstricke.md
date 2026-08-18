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

- ⭐ **Arbeitskopie einer Multicam-Timeline NICHT per `ImportTimelineFromFile` duplizieren**
  (Projekt-J 06.08.2026): erzeugt einen kompletten zweiten Multicam-Unterbau (neuer
  Multicam-Clip + neue „…import 1"-Winkel-Kopien) **ohne** den vorhandenen Grade — die Kopie
  sieht ungegradet aus. Fix: `AppendToTimeline` auf eine neue leere Timeline, `mediaPoolItem`
  = der bestehende (gegradete) Multicam-Clip, `startFrame/endFrame` je Clip aus
  `GetLeftOffset()`/`+GetDuration()` der Originaltimeline. Details `ablauf.md` Schritt 8.1.
- ⭐ **Kino-Look-DRX ist auf Log-Kameras kalibriert (FilmConvert Make/Model/Profile) — auf
  Rec.709-Consumer-Kameras (kein Log-Bildprofil) macht sie das Bild crushed/zu dunkel**
  (Projekt-J 06.08.2026: zwei Rec.709-Camcorder statt der sonst üblichen FS7/S-Log3).
  FilmConvert Nitrate wendet sonst einen Log-Dekode-Schritt auf bereits fertiges Rec.709-Bild
  an. **Vorher prüfen:** `ffmpeg -vf signalstats` auf einen Frame — YMIN nahe 0 UND YMAX=255
  → Rec.709 (nicht Log; S-Log3 hätte YMIN ~40-70 und würde nicht auf 255 clippen). Bei
  Rec.709-Material im FilmConvert-Node **Make/Model auf „Default/Default", Profile auf
  „Standard sRGB"** umstellen (nur per GUI-Dropdown, keine bekannte API dafür) — danach den
  korrigierten Clip per `grade-save` neu als Vorlage sichern und auf die übrigen Clips
  verteilen, statt die Original-DRX blind zu übernehmen.

## Multicam

- ⭐ **Skripte aus einem ALTEN Projektordner kopieren = Fixes fehlen** (09.08.2026, projekt-b4).
  Verlockend, weil dort schon die passende Variante steht (z. B. `TLOFF=0` bei negativen Offsets,
  die `<In/>`-Regex). Aber diese Fassungen sind eingefroren: `build_mc_drt.py` aus projekt-b3 hatte
  den **FrameRate-Fix nicht** (der kam erst mit Projekt-J in `vorlagen/`). **Regel: aus dem
  Projektordner kopieren ist ok, danach aber gegen `vorlagen/` diffen und fehlende Fixes
  nachziehen.** Ebenso Kopf-Konstanten prüfen — verify_mc.py aus projekt-b3 zeigte auf `B=…projekt-b2`
  und verglich gegen einen fremden Schnittplan („Plan 21", Winkel 'weit') statt zu scheitern.
- ⚠️ **Bash-Heredocs (`py - <<'EOF'`) zum Patchen von Skripten mit Windows-Pfaden vermeiden** —
  `\\c`/`\\2` kommen halbiert an (`\260…` wird zur Oktal-Escape), Ersetzungen greifen still nicht
  oder zerstören Pfade. Stattdessen das Edit-Werkzeug oder PowerShell `[IO.File]::ReadAllText` +
  `-replace` nehmen. (Auch `Get-Content` ist unsicher, wenn schon ein `\r` in der Zeile steckt —
  es splittet dort.)

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

- ⭐⭐ **Multicam-Clip bricht ab einer bestimmten Position mitten in der Timeline SCHWARZ ab
  (nicht am Anfang, nicht sporadisch wie die ~4s-Löcher weiter unten, sondern ab einem festen
  Punkt bis zum Ende)** — Ursache: `build_mc_drt.py` übernimmt das Multicam-Element aus einer
  Muster-DRT (`alt_mc.drt`) eines ANDEREN, älteren Projekts. Dessen `<FrameRate>`-Feld (8-Byte
  little-endian Double + 8 Nullbytes, hex-codiert) bleibt beim Kopieren unverändert stehen —
  auch wenn das neue Projekt eine andere FPS hat (z. B. 25 statt 29.97). Resolve berechnet die
  nutzbare Länge der Multicam-**Sequence** intern mit dieser geerbten FPS, nicht mit der
  Projekt-FPS: die Sequence wird dadurch effektiv verkürzt (verifiziert Projekt-J
  06.08.2026: Muster war 29.97fps, Projekt 25fps → Multicam-Clip brach bei ≈654 s statt der
  echten 1510 s ab; `GetClipProperty('FPS')` zeigte weiterhin 29.97, `Frames`/`End` passten
  nicht zur tatsächlichen Winkel-Geometrie). Sowohl im Live-Viewer als auch im Render schwarz.
  **Fix:** `<FrameRate>` im Multicam-Element IMMER auf die eigene Projekt-FPS umschreiben
  (`struct.pack("<d", FPS) + b"\x00"*8`), unabhängig davon, ob sie zufällig mit dem Muster
  übereinstimmt — im Skript `build_mc_drt.py` (Vorlage) bereits eingebaut, s. Kommentar dort.
  **Diagnose-Weg, der hinführte:** Schwarzbild zuerst per `blackdetect` im Render gefunden →
  Rohdatei am selben Content-Zeitpunkt geprüft (fehlerfrei) → nested (nicht-Multicam)
  Schnitt-Timeline an derselben Stelle geprüft (fehlerfrei) → „…weit import"-Quelltimeline
  direkt an der absoluten Multicam-Frame-Position geprüft (fehlerfrei) → erst der Vergleich
  `mcclip.GetClipProperty(['Duration','FPS','Frames'])` zeigte den Widerspruch (Duration
  00:10:53:14 bei angeblich 29.97 fps ≈ genau der Abbruchpunkt).

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
   Titel(V3). Fertiges Muster: `resolve-prep\projekt-a\mcbuild\titel_overlay.py`.

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

- **⭐ `overlay_tools.py place --frames N` legt nur N−1 Frames** (`endFrame = frames-1`, aber
  Resolve rechnet `Dauer = endFrame − startFrame`). → **immer `--frames N+1` übergeben**, wenn
  das Overlay N Frames lang sein soll, und die Dauer in der Ausgabe nachzählen. Gleiche Regel
  bei eigenem `AppendToTimeline`: `endFrame = startFrame + gewünschte Dauer`.
  (Gefunden 05.08.2026 an #7 Thema-W; deckt sich mit dem #5-Befund.)
- **⭐ `GetIsTrackEnabled` liefert für NICHT aktive Timelines `False`.** `verify_overlays.py`
  meldet dann fälschlich „A2 STUMM … Schluss stumm!". → Vor jeder Prüfung
  `proj.SetCurrentTimeline(tl)` setzen (das Werkzeug macht es nicht selbst), sonst jagt man
  einem Phantom hinterher.
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
- **⭐ Erzeuger-Skripte NIE mit fest verdrahtetem GENERISCHEM Ausgabenamen schreiben** (z. B.
  `"Instagram Kurz %s" % titel` → verwechselbar mit anderen Projekten). Ist die Quelle ein
  fertiger Film, `basis = os.path.splitext(quelle)[0]` nehmen und daraus `f"{basis} <Zusatz>.<ext>"`
  bilden — siehe [[dateinamen-konvention]], SKILL.md Punkt 14.
  Bereits vorhandene generische Namen auf Wunsch umbenennen (behalten, nicht löschen).
- **⭐ Umgekehrter Fall: kryptische Standbildnamen NICHT in den Titelbildnamen übernehmen**
  (Nutzer, 4.8.2026). `Standbild 2026-08-03 170627 für tb 1_2.1.1.png` ist als Quelle in Ordnung,
  als Titelbildname nicht. Enddateien (Titelbilder, Grafiken, Videos, Texte) heißen
  `<Projekt/Folge> <Art> <Details> <Version>` — in `make_thumb_*.py` also `OUTNAME` sprechend
  setzen (`"Titelbild #5 Thema-Z v2"`), nicht aus dem Standbildnamen ableiten. Kurz:
  Quelle = guter Name → übernehmen; Quelle = Zwischenprodukt → Namen neu bilden.
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
- **`rctl.py frame` zeigt Overlays oberer Spuren DOCH** (verifiziert 4.8.2026 an #5: Endkarte auf V4
  und Lower-Third waren im PNG drin, inkl. Alpha-Blende) — Platzierungen und Blenden lassen sich
  damit prüfen, ohne dem Nutzer den Bildschirmfokus zu nehmen. (Ältere Notiz „zeigt Overlays nicht"
  war falsch.)
- **⭐ Weiche Blenden für Overlays als ALPHA einbacken** statt Opacity-Keyframes zu klicken
  (4.8.2026, #5): `ffmpeg -i g.mov -vf "format=yuva444p10le,fade=t=in:st=0:d=<s>:alpha=1,
  fade=t=out:st=<dauer-aus>:d=<s>:alpha=1" -c:v prores_ks -profile:v 4444 -pix_fmt yuva444p10le`.
  Wirkt auch bei Vollbild-Grafiken als echte Überblendung auf das darunterliegende Bild.
  Anders als `zoompan` zittert das nicht — Blenden einbacken ist erlaubt, Zoom nicht.
  Prüfen: Frame per Frame den Alpha-Mittelwert messen (Pillow, `im.split()[3]`).
- **⭐ `AppendToTimeline`: `endFrame` = gewünschte Dauer, NICHT Dauer−1** (4.8.2026 gemessen).
  Mit `startFrame: 0, endFrame: 268` entsteht ein 268-Frame-Clip; für 269 Frames `endFrame: 269`.
  Nach dem Setzen immer `GetStart/GetEnd/GetDuration` gegenprüfen.
- **⭐ 4K-Standbild aus einer 1080p-Timeline** (4.8.2026, für Titelbilder): Timeline kurz
  umstellen — `tl.SetSetting("useCustomSettings","1")`, `timelineResolutionWidth/Height` auf
  3840/2160 —, dann `resolve.OpenPage("color")`, `tl.GrabStill()`,
  `proj.GetGallery().GetCurrentStillAlbum().ExportStills([still], ordner, name, "png")`,
  Still löschen und die Auflösung zurückstellen. Liefert echte 4K-Schärfe, weil das Quellmaterial
  4K ist. (`ExportStills` lief dabei zuverlässig — die alte Notiz „launisch in R21" traf hier nicht.)
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

## Ton- und Grading-Fallen aus Projekt-I (Projekt-I)

**Der externe Recorder kann streckenweise TOT sein — vor dem Sync prüfen (12.08.2026).**
Bei Projekt-I lieferte der Zoom die ersten 18:20 min **digitale Stille** (−90 dB) und endete
2 min vor den Kameras. Symptom im Standard-`sync.py`: Pearson-Reihe wie `0.49/0.70/0.00/0.11/0.00`
und **Streuung 22 s** — die Verifikationsfenster liegen im stummen Bereich. **Fix:** vor dem Sync
den Pegelverlauf der Tonquelle in Stufen prüfen
(`ffmpeg -ss T -t 20 -i ton.wav -af volumedetect -f null -`, ohne `-v error`, sonst wird die
Ausgabe verschluckt), und wenn nur ein Teil Signal trägt:
1. **Sync-Master wird der Kameraton der Leitkamera** (Teile vorher zu EINER WAV zusammenfügen),
2. der Recorder wird **nur über seinen nicht-stummen Bereich** gegen diese Referenz korreliert
   (Muster: `sync_ton.py` im Projektordner projekt-i).

**Eine `… ton`-Timeline mit ZWEI Tonquellen darf nicht als Ton in den Schnitt genestet werden.**
Beide Spuren summieren sich sonst (Kammfilter). Stattdessen die Tonquellen **einzeln aus dem
Medienpool** auf getrennte Spuren legen (A1 Recorder, A2 Kameraton) — `AppendToTimeline` mit
`trackIndex` und `recordFrame`. ⚠️ `recordFrame` ist **timeline-absolut**: Timeline-Frame 0
entspricht dem ersten geschnittenen Bild, nicht dem Nullpunkt der Sync-Referenz.

**Audio-Clips haben kein `Frames`-Property** (leerer String) — Länge aus `Duration` (Timecode)
rechnen: `((h*60+m)*60+s)*fps + f`.

**⭐ Richtung von `SetCDL` gemessen (12.08.2026): `Power` < 1 macht HELLER, > 1 dunkler.**
(Im Memory `projekt-j-projekt` stand es umgekehrt beschrieben.) Und: **Power bewegt die
Spitzlichter kaum** — gegen ausgefressene Lichter ist `Slope` (Gain) der wirksame Hebel.
Gemessen an einem überstrahlten Rec.709-Clip: Slope 1,00 → 1,9 % geclippt; Slope 0,90 → 0 %;
Slope 0,85 → Median 209 → 177 bei sauberen Lichtern.

**Frame-Messungen: erst Timeline UND Clip zusammenbringen.** `rctl.py frame` exportiert das,
worauf der Playhead steht. Wer `SetCDL` auf Clip-Index 1 setzt, während der Playhead auf Clip 0
steht, misst viermal denselben Wert und hält es für „CDL wirkt nicht". Also immer
`SetCurrentTimeline` + `goto` in den Bereich **des Clips**, den man gerade ändert.

**⭐ AVCHD von Sony-Camcordern (CX900E / AX100): Halbbilddominanz auf „Progressiv" stellen
(Nutzer-Vorgabe, 13.08.2026).** Die MTS-Dateien sind im Container als **`tt` (oberes Halbbild
zuerst)** geflaggt, obwohl der Inhalt 25p **progressiv** ist (`ffmpeg -vf idet` meldet
Progressive, 0 TFF/BFF). Resolve übernimmt das Flag als „Automatisch – Oberes Halbbild" und
deinterlact — Detailverlust und Kammartefakte bei Bewegung. Also bei JEDEM AVCHD-Projekt:
Clip in der Mediathek → Rechtsklick → **Clipeigenschaften → Video → Halbbilddominanz =
Progressiv** (setzt zugleich `Enable Deinterlacing` auf 0).
Prüfen vorab: `ffprobe -show_entries stream=field_order` (zeigt `tt`) und
`ffmpeg -ss T -t 8 -i x.MTS -vf idet -f null -` (zeigt „Progressive: 200").

⛔ **Zwei Fallen dabei:**
1. **Per API nicht setzbar:** `MediaPoolItem.SetClipProperty('Field Dominance', …)` gibt für
   dieses Feld **immer `None` zurück und ändert nichts** — egal welcher Wert. Nur der Dialog
   geht (Bildschirmsteuerung). **Lesen** geht dagegen: `GetClipProperty('Field Dominance')`
   liefert `'Auto'` / `'Upper Field'` / `'Progressive'`.
2. **Mehrfachauswahl greift nicht zuverlässig:** Klick + Shift-Klick auf beide Clips und dann
   der Dialog stellte nur den **zuletzt angeklickten** Clip um. Also **je Clip einzeln** machen
   und hinterher **per API gegenprüfen**, dass wirklich alle auf `'Progressive'` stehen.

**⛔ Während eines laufenden Renders NICHT ins Projekt greifen (13.08.2026).**
Der Nutzer rendert oft parallel, während Claude per API arbeitet. `Timeline.Export`,
`grade-save`/`ExportStills`, `SaveProject`, das Anlegen/Löschen von Timelines und
Media-Pool-Operationen können Resolve dabei aus dem Tritt bringen (bei Projekt-I musste der
Nutzer Resolve neu starten). **Vor jedem schreibenden oder exportierenden Zugriff prüfen:**

```python
if proj.IsRenderingInProgress():
    ...  # warten oder den Schritt verschieben, NICHT ausführen
```

Reines Lesen (`GetClipProperty`, Clip-/Timeline-Listen) ist unkritisch. Und: **für eine
Nebensächlichkeit gar nicht erst zugreifen** — im konkreten Fall ging es nur darum, einen
OFX-Wert auszulesen; das hätte warten können.

**⛔⛔ Render bricht an EINEM Frame ab: „Die Fusion Komposition bei <TC> konnte nicht
verarbeitet werden" (16.08.2026, Projekt-A).**
Symptom: Der Deliver-Render läuft an und scheitert reproduzierbar an genau einem Timecode.
Im Resolve-Log (`%APPDATA%\Blackmagic Design\DaVinci Resolve\Support\logs\davinci_resolve.log`)
steht dazu die eigentliche Ursache:
`GPU.SingleBoardMgr | ERROR | Exception caught while executing Fusion algorithms:
No frame available for MediaOut1`.

**Ursache:** Ein Clip mit Fusion-Composition (im Fall: ein **Anpassungsclip** mit
Fusion-`Blur`) liefert am **allerletzten Frame der Comp** kein Bild — `MediaIn1` hat dort
nichts mehr zu liefern, `MediaOut1` bleibt leer, der Render bricht ab. Betroffen ist nur der
eine Frame; alles davor und danach rendert.

**Lösung (per API, eine Zeile):** am `MediaIn` der Comp **HoldLastFrame** einschalten —
Fusion hält dann den letzten vorhandenen Frame, statt ins Leere zu greifen:
```python
it = tl.GetItemListInTrack('video', 2)[0]          # der Clip mit der Comp
c  = it.GetFusionCompByIndex(1)
mi = [v for v in c.GetToolList().values() if v.ID == 'MediaIn'][0]
mi.SetInput('HoldLastFrame', 1.0)                  # setzt auch TOOLI_Clip_ExtendLast = 1
```
In der GUI: Fusion-Seite → `MediaIn1` → Inspector → **Hold Last Frame** = 1.

**Was NICHT hilft** (alles durchgetestet, damit es niemand nochmal probiert):
Comp-Range verlängern (`COMPN_GlobalEnd`/`COMPN_RenderEnd` +1), den Blur-Node auf
`PassThrough`, die Maske auf `PassThrough`, die `AudioDisplay`-Tools abschalten, **oder die
ganze Videospur deaktivieren** — der Fehler kommt jedes Mal identisch wieder.

**Vorgehen zum Eingrenzen** (schnell, ohne den vollen Film zu rendern): kleine Testrender per
API auf einzelne Frames legen, den Job danach wieder löschen:
```python
proj.SetRenderSettings({'MarkIn': F, 'MarkOut': F, 'TargetDir': scratch, 'CustomName': 'test'})
jid = proj.AddRenderJob(); proj.StartRendering([jid], isInteractiveMode=False)
# pollen bis JobStatus in ('Abgeschlossen','Fehlgeschlagen'), dann proj.DeleteRenderJob(jid)
```
So ist der Schuldige in ein paar Minuten auf **einen** Frame eingegrenzt. Achtung:
`SetRenderSettings` verändert die sichtbaren Deliver-Einstellungen — hinterher auf den
echten Zielordner/Bereich zurückstellen. **`proj.SaveProject()` gibt es nicht** —
es heißt `pm.SaveProject()`.

**Nach dem Fix:** Die bereits fehlgeschlagenen Aufträge in der Renderliste stehen weiter auf
„Fehlgeschlagen" und starten nicht von selbst neu — der Nutzer muss sie in der Deliver-Seite
per **Rechtsklick → „Renderauftrag zurücksetzen"** zurücksetzen (per API nicht möglich).

**⭐ Clip trimmen, obwohl die API kein Trimmen kann (16.08.2026, Projekt-A).**
`TimelineItem` hat kein `SetStart`/`SetEnd`/`SetDuration` — einen Clip zu kürzen geht scheinbar
nur von Hand. **Doch: Blade per Tastatur + Löschen per API** funktioniert sauber und
frame-genau, ohne Ripple und ohne Maus:

```python
# 1. alle Spuren AUSSER der Zielspur sperren -> der Blade trifft nur diese eine
for t in ('video','audio'):
    for n in range(1, tl.GetTrackCount(t)+1):
        if not (t == 'video' and n == ZIEL): tl.SetTrackLock(t, n, True)
resolve.OpenPage('edit')
tl.SetCurrentTimecode('01:00:13:21')        # exakt der Schnittpunkt
# 2. Blade:  py keys.py ctrl+b
# 3. hinteren Teil per API loeschen, rippleDelete=False -> nichts verschiebt sich
hinten = [i for i in tl.GetItemListInTrack('video', ZIEL) if i.GetStart() == SCHNITT][0]
tl.DeleteClips([hinten], False)
# 4. Spuren wieder entsperren
```

⚠️ **Zwei Details:** (a) `tl.SetCurrentTimecode` direkt nach `resolve.OpenPage()` wird
**verschluckt** — kurz warten und den Timecode danach **gegenlesen**, sonst schneidet der Blade
an der alten Position. (b) Hat der Clip eine **Fusion-Comp**, zieht deren Range beim Trimmen
automatisch mit (`COMPN_GlobalEnd`), die Keyframes bleiben in Comp-Zeit stehen — danach am
**neuen** letzten Frame einen Testrender fahren (siehe „No frame available for MediaOut1").
Vorher zur Sicherheit `tl.Export(pfad, resolve.EXPORT_DRT)` in den Scratchpad.

**⭐ Bevor ein Node/Effekt abgeschaltet wird: seine Wirkung MESSEN (16.08.2026).**
`GetToolsInNode(n)` sagt nur, *welche* Werkzeuge im Node stecken — nicht, ob sie etwas tun,
und `GetNodeEnabled` gibt es gar nicht. Ob im selben Node noch etwas Gewolltes sitzt (eine
Verdunkelung, eine Korrektur), zeigt nur der Bildvergleich: Frame exportieren, `SetNodeEnabled`
umschalten, zweiten Frame exportieren, Differenz rechnen — an mehreren Stellen des Clips, weil
Power Windows und Keyframes zeitlich begrenzt wirken können.

```python
d = np.abs(a - b).mean(axis=2)      # a/b = Frames mit Node an/aus
print(d.mean(), d.max(), (d > 3).sum())
```
Im konkreten Fall war die Abweichung an allen fünf Messpunkten **exakt 0** — der OFX-Node war
wirkungslos und konnte gefahrlos aus. Ohne die Messung wäre das Abschalten ein Blindflug.
