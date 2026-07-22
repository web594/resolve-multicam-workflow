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
  noch Worteprojekt-d liefert dort Schnittpunkte → lange Spans **mechanisch unterteilen**.
- Anfang einer Aufnahme ist fast immer **Setup-Geplänkel** — Kopf später trimmen, den Nutzer
  fragen, ab wo der Film beginnen soll.

## Grading

- ⭐ **Timeline-Eprojekt-dn-Grade schlägt NICHT durch verschachtelte Quell-Timelines durch** — im
  Schnitt bleibt der Clip Log. **Nur Clip-Eprojekt-dn-Grades propagieren ins Nesting.**
  Also immer auf Clip-Eprojekt-d graden (Color-Page-Umschalter „Clip", nicht „Timeline").
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

## Multicam

- **Multicam-Winkel aus verschachtelten Timelines erzprojekt-c sporadische ~4-s-Schwarzlöcher**
  (echt schwarz, auch im Render; Projekt-C: 92 betroffene Clips). Rohdatei und Quell-Timeline
  sind dabei fehlerfrei — es ist die Multicam-Verschachtelung.
  **Prävention: Winkel aus echten Medien-Clips bzw. je Kamera einer geflachten Datei bauen.**
  Reparatur falls doch passiert: betroffene Stücke als ProRes rendern und frame-genau auf V2
  legen (Look-Nodes auf Timeline-Eprojekt-d wirken mit) — Skripte bei Projekt-C.
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

## Sackgassen — nicht nochmal probieren

- Fusion-`ActionManager` (889 Actions) steuert **nur die Fusion-Seite**, nichts für Color/Edit.
- `GalleryStillAlbum.ExportStills` ist in R21 launisch (oft `False`).
- „ID-Swap" zum Kalibrieren von DRX-Parametern schlägt bei bereits vorhandenen IDs fehl
  (Duplikat ⇒ Regler wird ignoriert).
- ChatGPT als Teil-Ausführer spart nichts (nur per Bildschirmsteuerung erreichbar = teurer).
