# Historie dieses Skills

Kurz eintragen: Datum — was geändert — warum. Neueste oben.

## 2026-08-18 — Farbgebung ausgelagert: zwei eigene Look-Skills, Kamera-Prüfung Pflicht
Neue Datei `references/farbgebung.md` (Nutzer-Vorgabe vom 18.08.2026):
- **Standard ist `resolve-kino-look-nodekette`** (4-Node-Kette),
  **Ersatz ist `resolve-lut-look-kette`** (4 LUT-Nodes + 1 regelbarer Node). Beide liegen als
  eigene Skills und als öffentliche Repos vor.
- **In beiden Ketten zuerst die gekauften LUTs und Werkzeuge**; die freien Fassungen nur, wenn
  ein Werkzeug fehlt oder die Kamera kein Profil im Plugin hat.
- ⚠️ **Vor jedem Look prüfen, welche Kameras im Projekt liegen.** Log-Material (FS7 II, S-Log3)
  → Kette wie vorgesehen; **Rec.709-Consumer-Camcorder (Sony AX100, CX900E und ähnliche) →
  Filmemulation gar nicht oder nur ganz wenig %**, sonst werden die Farben unnatürlich.
- `SKILL.md` (Lesereihenfolge, Schritt 7, Punkt „Look") entsprechend umgestellt; die alte
  „Variante A/Variante B"-Formulierung ist damit erledigt.
- Das öffentliche Repo `resolve-multicam-workflow` stand seit 05.08. still — mit diesem Eintrag
  wird der ganze Zwischenstand (Fallstricke 12./13.08., Instagram-Kurz, SetCDL-Richtung)
  nachgezogen.

## 2026-08-04 (5) — Dateinamen: Zwischenprodukt-Namen nicht weiterschleppen (Nutzer-Auftrag)
Ergänzung zu Regel 14 (SKILL.md) und `fallstricke.md`: Ein Dateiname muss **erstens dem Projekt**
zuzuordnen sein, **dann** Details und Version tragen. Deshalb gilt jetzt beides:
- Quelle ist ein **fertiger Film mit gutem Namen** → Namen übernehmen, Zusatz hinten dran.
- Quelle ist ein **Zwischenprodukt mit kryptischem Namen** (Resolve-Standbild
  `Standbild 2026-08-03 170627 für tb 1_2.1.1.png`) → Namen **neu bilden**:
  `<Projekt/Folge> <Art> <Details> <Version>`, z. B. `Titelbild <Folge> v2_4K.jpg`.
  Beim Zwischenprodukt selbst ist ein Datums-/Zeitname noch okay, wenn es im zugehörigen
  `renderings`-Ordner liegt; bei Enddateien nicht.
Praktisch: `instagram_kurz.py` leitet den Namen aus der Quelle ab, `make_thumb_*.py` setzt
`OUTNAME` sprechend.

## 2026-08-04 (4) — Blenden als Alpha, 4K-Standbild, AppendToTimeline-Off-by-one
Aus der Nacharbeit an einer Folge (Grafik-Overlays + Auslieferung) in `fallstricke.md`
ergänzt bzw. korrigiert:
- **Weiche Blenden für Overlays per ffmpeg als Alpha einbacken** (ProRes 4444) statt
  Opacity-Keyframes zu klicken — spart die unzuverlässige Inspector-Arbeit, zittert nicht.
- **4K-Standbild aus einer 1080p-Timeline** über kurzzeitiges Umstellen der Timeline-Auflösung
  + `GrabStill`/`ExportStills` — für scharfe Titelbilder.
- **`AppendToTimeline`: `endFrame` ist die Dauer**, nicht Dauer−1 (war 1 Frame zu kurz).
- Zwei alte Notizen widerlegt: `rctl.py frame` zeigt Overlays oberer Spuren **doch**;
  `ExportStills` lief zuverlässig.
- Bestätigt: **Ripple-Einfügen (Kaltstart) bleibt beim Nutzer** — die Aufnahmezeiten liegen
  zstd-komprimiert in den DRT-Blobs, dafür gibt es keinen sicheren Skriptweg.

## 2026-08-04 (3) — öffentliches Repo aktualisiert
Der Skill ist als **öffentliches Repo** veröffentlicht:
`https://github.com/web594/resolve-multicam-workflow` (Arbeitskopie `C:\claude\resolve-multicam-repo`).
Stand vom 22.07. auf den heutigen gebracht (Multicam per DRT, Kino-Look-Rezept, Vorbild-Projekt,
Grafik-Einblendungen, neue Vorlagen).
- **Regel: keine Projekt-/Kunden-/Personendaten.** Anonymisierung per Skript
  (`scratchpad/anonymisieren.py`, Mapping: Projekt-A…H, Reihe-R, Thema-X/-Y/-Z, `JJMMTT`,
  Benutzername → `<benutzer>`). **Hinweise auf wunder-media.de sind ausdrücklich erlaubt.**
- ⚠️ Falle der ersten Veröffentlichung: naives Ersetzen ohne Wortgrenzen zerstörte Wörter
  („Ebene" → „Eprojekt-d", weil `Projekt-D` ersetzt wurde). Jetzt buchstabenbasierte Grenzen
  `(?<![A-Za-zÄÖÜäöüß])…(?![A-Za-zÄÖÜäöüß])`. Nach jeder Anonymisierung gegenprüfen.

## 2026-08-04 (2) — ⭐ Vorbild-Projekt festgehalten (Nutzer-Auftrag)
Der Nutzer hat den Stand von `Projekt-B-3 Projekt-B` (2 Kameras + Hauptton) ausdrücklich als
**Vorbild für Multicam-Projekte** freigegeben. Neu `references/vorbild-projekt.md`:
Plattenordner, **Soll-Zustand der Mediathek**, der bewährte Farb-Ablauf und vor allem die
**Grenze Claude ↔ Mensch**.
- **Neue Regel „Anlegen":** die nur beim Anlegen gebrauchten Zwischen-Timelines
  (`… mitte`, `… seite`, `… ton`, `… Schnitt`) räumt Claude zum Schluss selbst per
  `mp.MoveClips` in einen Bin **`Anlegen`**. Die `… import`-Timelines bleiben oben — sie
  tragen den Grade und sind die Multicam-Winkel. (Im Vorbildprojekt am 04.08. ausgeführt.)
- **Leitsatz der Arbeitsteilung:** nicht „kann Claude das?", sondern **„braucht Claude
  deutlich länger als ein Mensch?"** → dann macht es der Mensch (Qualifizierer/Power Window,
  Shared-Node-Verknüpfung, Beschriftung, tetraedrische LUT-Interpolation, Feinschnitt und
  Gestaltung in `… Multicam Auswahl`, Endrender).
- **Look-Varianten neu gewichtet:** Variante A (FilmConvert-5-Node-Kette) ist der **Standard**,
  ohne Rückfrage bauen. Variante B (ARRI → Filmstock → Kino-LUT) ist laut Nutzer eine
  ernstzunehmende zweite Möglichkeit, aber **noch nicht ausgereift** — nur auf ausdrücklichen
  Wunsch. SKILL.md Punkt 2 entsprechend umgeschrieben, Punkte 8a/8b neu.

## 2026-07-27 (Abschluss) — offene Fragen beantwortet, Endstand ausgewertet (Projekt-B-2)
Am **fertigen** Projekt abgelesen, was der Nutzer nach der Übergabe noch selbst machen musste —
das gehört künftig zur Lieferung (`ablauf.md` Schritt 8, `SKILL.md` Punkte 7–8):
Arbeitskopie `… Multicam auswahl` → Vorlauf am Anfang-Marker abtrennen → Einspieler →
Endmontage `… zus` (V1/A1 Render, A2 nachbearbeiteter Ton, V3 „Einfarbig", V4 Titel „Simple White").
- ⚠️ **Korrektur (Nutzer):** Titel **und Einspieler sind reihen-/kundenspezifisch** — bei anderen
  Videos ist es anders. Der Projekt-B-Titel (`DR. MAX MUSTERMANN` / `BERUFSBEZEICHNUNG`) ist ein
  **Beispiel**, kein Muster; Texte nie aus einem fremden Projekt übernehmen, sondern für die
  jeweilige Reihe erfragen oder aus einer früheren Folge derselben Reihe ablesen. Allgemein ist
  nur die Technik (`titel_overlay.py`, OVERLAY).
- **⭐ DRX allein überträgt einen Look NICHT vollständig** (Verdrahtung der Nebenzweige fehlt →
  nur der Hauptstrang wirkt, Bild bleibt flau). Nachgewiesen per Render-Messung (Quelle warm
  RGB 141/123/107, Ziel neutral 121/119/115). Richtiger Weg: **Galerie/PowerGrade-Still**, danach
  `CopyGrades`. Neue Vorlage `vorlagen/wirkt_render.py` misst die Wirkung einzelner Nodes per
  Render (der Viewer cached und taugt dafür nicht).
- **Referenz-Look Projekt-B (11 Nodes)** in `ablauf.md` dokumentiert — Ausgangspunkt für die vom
  Nutzer gewünschte Farbverbesserung beim nächsten Mal.
- **„Haut soll mehr Farbe":** eigener Node mit *Farbton-vs-Sättigung*-Kurve über einen
  **Hautton-Qualifizierer** (nicht global sättigen) — so hat der Nutzer es gelöst.

## 2026-07-27 — ⭐⭐ Multicam-Clip OHNE GUI + ruhigere Schnitte (Sitzung Projekt-B-2)
**Zwei ausdrückliche Nutzer-Anweisungen, beide „darf nicht vergessen werden".**

1. **Multicam wird komplett per Skript gebaut — nicht per Maus.** Die bisherige Behauptung
   „Multicam-Clip geht nur von Hand in der GUI" war falsch und wurde überall gestrichen
   (`SKILL.md`, `ablauf.md` Schritt 6, `api-werkzeuge.md`-Grenzentabelle). Verifiziert an
   Projekt-B-2 (Resolve 21.0.3): Multicam-Clip + 21 Winkel-Schnitte, **0 Winkelfehler**, ohne Klick.
   - Neu `vorlagen/mcbuild/build_mc_drt.py` (setzt `<Sm2MpMulticamClip>` + Definitionscontainer
     ins DRT), `import_mc2.py`, `cleanup.py`, `vorlagen/verify_mc.py`.
   - Format dokumentiert: `MediaExtents` = 2 LE-doubles [start_s, dauer_s], `MediaTimemapBA` =
     "02"+BE-double, Winkelziffer im Clip-`FieldsBlob` hinter `4b616d657261c2a0`,
     `In` = ton-Frame − MC0.
   - **Die teure Falle** (in `fallstricke.md`): Sequence→Container-Zuordnung steckt UTF-16-kodiert
     in den zstd-Blobs von `MpFolder.xml` → **keine neuen UUIDs würfeln**, sonst `Frames 0` und
     schwarzes Bild. Kostete mehrere Fehlversuche; Diagnoseweg ist dort mit festgehalten.
2. **Ausgeschaltete Nodes** (Nutzer-Hinweis am selben Tag): Beim Übernehmen eines Looks aus einem
   Altprojekt kommen deaktivierte Nodes stumm mit — sie gehören **nicht** ins neue Projekt, und
   Claude soll generell **mehr darauf achten, ob ein Node aus ist** (die API hat kein
   `GetNodeEnabled`, nur `SetNodeEnabled` → Node-Graph ansehen/nachfragen; „hat eine LUT" heißt
   nicht „wirkt"). Konkret waren bei Projekt-B `Projekt-B_Korrektur_v5` und `Projekt-B_Kino_mittel` aus.
   Steht in `fallstricke.md` (Grading, ganz oben) und `ablauf.md` Schritt 7.
3. **Schnitt geringfügig ruhiger** (nach Rückmeldung zu Projekt-A: „manche Schnitte zu früh"):
   `MIN_SHOT 6`, `CUT_MIN 6`, `CUT_MAX 11`, `PARA_GAP 1.2`, `MAX_STD 50`, **neu `CALM_GAP 12`**,
   mechanische Teilung 55/42/10; erster Span immer Leitkamera; keine Cutaways vor `ANFANG`.
   Ergebnis Projekt-B-2: ⌀ 23,6 s statt 21,5 s, kürzeste Einstellung 10,5 s statt 4 s.
   Werte in `vorlagen/make_cutplan.py` und in `SKILL.md`/`ablauf.md` Schritt 5.

## 2026-07-27 — Schritt 9: Grafik-Einblendungen + Auslieferung (Sitzung Reihe-R #2)
Bei einer Vortragsreihe mit demselben Referenten (7 Folgen) wiederholt sich nach dem Schnitt
immer dasselbe: Infografiken aus dem Transkript ableiten, als Overlay einbauen, dann
YouTube-Lang + Instagram-Kurz ausliefern. Das war bisher nirgends festgehalten.
- **Neu `references/grafik-einblendungen.md`** — kompletter Schritt 9: erst Verteilungsplan
  vorlegen und freigeben lassen (nicht sofort bauen), Stil des Nutzers übernehmen,
  Arbeitsteilung Daten-Grafik (Claude) vs. fotorealistisch (KI-Prompt → Nutzer generiert →
  Claude beschriftet), Zoom-Sicherheit, Instagram-Crop, ASS-Untertitel, −14 LUFS.
- **Neu `vorlagen/overlay_tools.py`** (getestet): `check` (Zoom-Beschnitt prüfen),
  `zoomsafe` (Inhalt 90 % + Hintergrund ergänzen), `mov` (PNG → ProRes mit exakter
  Frameanzahl, optional Alpha), `place` (importieren + platzieren, ersetzt Vorversion sauber).
- **`fallstricke.md`** um den Abschnitt „Grafik-Einblendungen / Overlays" ergänzt. Die drei
  teuersten: Standbilder bekommen nur 5 s; **ffmpeg-`zoompan` zittert** (Zoom gehört nach
  Resolve); Zoom-Sicherheit gilt auch fürs **Bild**, nicht nur für Text.
- `SKILL.md`: Schritt 9 in die Ablauf-Tabelle und in die Leseliste aufgenommen.

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
  `projekt-a-projekt`.

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
— Aktivierung liegt außerhalb der Projekt-DB. Details + verwertbare Nebenerkenntnisse
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

## 28.07.2026 — Grafik-Einblendungen #3 Thema-Y
- **Neu: `vorlagen/instagram_kurz.py`** — die ganze Instagram-Auslieferung in einem Aufruf
  (Spalte nachmessen, Crop+ASS, Musik-Check, −14 LUFS zweistufig, Anweisungs-TXT).
  Bei #2 war das noch Handarbeit in fünf Schritten. In `grafik-einblendungen.md` verlinkt.
- **Gemeinsames Stil-Modul bewährt:** ein `gr_style.py` (Hintergrund, Fonts, Titel, Donut,
  Glow, `save()` mit eingebautem Zoom-Check) + je Grafik ein kurzes Skript. Der Zoom-Check
  muss gegen den **gerenderten Hintergrund** vergleichen, nicht gegen die Eckfarbe —
  bei radialem Verlauf meldet die Eckfarben-Variante sonst immer „nicht zoomsicher".
- **Vortragsfolien als Datenquelle, nicht als Einblendung:** die Folien der Reihe sind
  handgezeichnet + Hochformat. Aber die *Zahlen* darauf (z. B. 4 m Rohr → 4 km Turm,
  Materialaufbau) ergeben die stärksten eigenen Grafiken. Immer erst die Folien zum Thema
  ansehen, bevor Zahlen gesucht werden.
- **Zahlen von außen belegen** (Bundesnetzagentur, BfS …) und die Quelle klein in die
  Grafik setzen — stützt die Aussage des Referenten, ohne ihm etwas zuzuschreiben.

## 29.07.2026 — Mediathek-Ordnung + Comments-Hinweis
- **`overlay_tools.py place` importiert jetzt automatisch in den passenden
  Projekt-Unterordner** (Elternordner-Name der Quelldatei), nie mehr lose in
  Master-Root — direkte Folge des Namenskollisions-Bugs vom selben Tag.
- **Neuer Parameter `--fuer "..."`**: schreibt einen Kurzhinweis ins
  `Comments`-Feld des Media-Pool-Clips (z. B. "#3 Thema-Y, ab 0:41 - Aufbau
  Thema-Y"). Ohne Angabe automatisch `Timeline @ Frame X (Track Y)`. Grund:
  bei vielen Folgen mit gleicher g1…g9-Namenskonvention war in der Mediathek
  nicht mehr erkennbar, welcher Clip zu welcher Timeline/Stelle gehört.
- Bestehende, schon unsortierte Master-Root-Clips aus #1–#4 einmalig per
  `mp.MoveClips(..., zielordner)` nachsortiert (Pfad-Praefix-Abgleich,
  Backslash im Python-Quelltext ueber `chr(92)` erzeugen — direkte
  Backslash-Literale gehen durch mehrere Shell-/rctl-eval-Schichten kaputt).

## 29.07.2026 (2) — #3 Thema-Y abgeschlossen: drei Automatisierungen
- **`vorlagen/infografik/`** neu: `stil_modul.py` (generisches Stil-Modul) + drei
  Beispielskripte (Datengrafik, Lower-Third, Schemazeichnung). `save()` **zentriert
  Vollbild-Grafiken jetzt automatisch vertikal** (`center=True`) und kennt
  `lower_third=True`. Grund: bei #3 waren 6 von 7 Grafiken unten zu eng (147 px
  oben / 68–102 px unten), der Nutzer musste zweimal nachfragen. An allen neun
  Grafiken verifiziert (Abweichung 0–1 px).
- **`vorlagen/verify_overlays.py`** neu: prüft die fertige Overlay-Timeline in einem
  Aufruf auf Schwarzbild-Löcher (frameweise über ALLE Videospuren, Anpassungsclips
  ausgenommen), Überlappungen, echte Offline-Clips, Ton-Deckung bis zum Soll-Ende und
  Sprachspur-Sync gegen eine Referenz-Timeline. Gegengetestet: findet das 1-Frame-Loch
  vor der Endkarte in der alten v1 und meldet die reparierte v2 sauber.
- **`instagram_kurz.py`**: Filterketten werden in der erzeugten Anweisungsdatei jetzt
  gequotet (PowerShell-Kommafalle), `overlay_tools.py place` importiert in den
  Projekt-Unterordner und schreibt `--fuer` ins Comments-Feld.
- **SKILL.md, stehende Antworten 9–13** ergänzt: kein „empfohlen/optional"-Splitting im
  Verteilungsplan, keine „Angabe <Referent>"-Zeile, Auslieferungspaket ungefragt
  mitliefern, Kaltstart nur als Marker + Anleitung (Grenzen aus Wort-Zeitstempeln),
  B-Roll darf dem Maßstab der Anleitung nicht widersprechen.

## 04.08.2026 — Grading-Kette als Rezept, eigener Skill `resolve-kino-look`
- Ein fertig gegradetes FS7-Projekt ausgelesen (Node-Graph, OFX-Parameter, LUT,
  Reglerwerte, Projekt-Farbeinstellungen). Ergebnis: **5-Node-Kette** FilmConvert
  Nitrate → Primärkorrektur → OSIRIS PRISMO (40 %) → Gesicht-Sekundär → Film Look
  Creator (Halation/Vignette), Projekt auf **DaVinci YRGB** (nicht Color Managed).
  Nur aktive Nodes — ausgeschaltete gehören ausdrücklich nicht ins Rezept.
- **⭐ Verifiziert:** Ein DRX überträgt die ganze Kette inkl. OFX-Plugins mit allen
  Parametern, LUT-Zuweisung und sämtlichen Reglerwerten **1:1 in 0,04 s je Clip**
  (Test im Wegwerf-Projekt, Werte danach bitgleich zurückgelesen). Damit ist die
  Kette **nie per Computer-Use nachzubauen** — das dauert über eine Stunde.
- Neu: `references/kino-look-nodekette.md` (Rezept + Tabelle „was macht Claude, was
  der Nutzer"), SKILL.md-Punkt 2 der stehenden Antworten auf **zwei Varianten**
  erweitert (A = neue FilmConvert-Kette, B = alte 3-LUT-Kette).
- Neuer eigenständiger Skill **`resolve-kino-look`** mit DRX-Vorlage,
  `apply_kino_look.py`, `drx_werte.py` (DRX offline auslesen) und
  `drx_anonymisieren.py`. Als privates Repo gesichert.
- Neue API-Grenzen belegt: **`SetNodeLabel` existiert nicht** (nur `GetNodeLabel`),
  LUT-Interpolation ist keine API-Einstellung, `grade-show` liest nur aus der
  Kalibrier-Projekt-DB → Reglerwerte stattdessen direkt aus dem DRX lesen.
- **Node-Container im DRX-Body: Feld 7 = 1 heißt aktiv** — so lassen sich
  ausgeschaltete Nodes ohne GUI erkennen.
- ⚠️ Eine DRX aus einem echten Projekt enthält `SrcHint` (Projekt-/Kundenname),
  `GalleryPath` (Benutzername) und **Vorschaubilder aus dem Dreh** (`Buffer`,
  `ClipThumbnails`) — vor jeder Weitergabe `drx_anonymisieren.py` laufen lassen.

## 05.08.2026 — Vorlagen synchronisiert + zwei Fallen ergänzt
- ⚠️ **`vorlagen/instagram_kurz.py` war veraltet** gegenüber der gepflegten
  Projekt-Fassung (`…\renderings\tools\instagram_kurz.py`, Stand 04.08.2026).
  Der Skill-Stand maß die weißen Balken nur an der Bildmittelzeile (weißer
  Restrand möglich) und benannte die Ausgabe „Instagram Kurz #N …" — ohne
  Quellname und ohne Projektdatum, also **gegen die Namenskonvention**.
  Beim Ausliefern von #7 hat das prompt eine falsch benannte Datei erzeugt.
  → Projekt-Fassung nach `vorlagen/` kopiert. **Merke: wenn ein Werkzeug auch
  im Projektordner liegt, ist die Projekt-Fassung meist die neuere — vor dem
  Benutzen kurz `diff`en oder gleich die aus `tools\` nehmen.**
- `fallstricke.md`: `overlay_tools.py place --frames N` legt nur N−1 Frames
  (`--frames N+1` übergeben), und `GetIsTrackEnabled` liefert für nicht aktive
  Timelines `False` → vor jeder Prüfung `SetCurrentTimeline` setzen.
- **12.08.2026 (Projekt-I Projekt-I):** `fallstricke.md` um vier Punkte ergänzt —
  stummer externer Recorder (Sync-Master wird dann der Kameraton), zwei Tonquellen nie über
  die `… ton`-Timeline nesten, Audio-Clips haben kein `Frames`-Property, und die **gemessene**
  Richtung von `SetCDL` (Power < 1 = heller; gegen Clipping wirkt nur `Slope`).
  Ausserdem in der alternierenden `make_cutplan`-Fassung zwei Schnittfehler behoben:
  zu lange Spans müssen in **ungerade** Stückzahl geteilt werden (sonst verschmilzt das letzte
  Teilstück wieder mit dem Nachbarspan), und `snap()` muss den Schnittpunkt klemmen, wenn keine
  Phrasengrenze in Reichweite liegt (sonst entstehen 4-Sekunden-Zuckungen).
  Referenzfassung: `C:\claude\resolve-prep\projekt-i\make_cutplan.py`.
- **13.08.2026 (Projekt-I Projekt-I):** `fallstricke.md` um die AVCHD-Halbbilddominanz
  ergänzt (CX900E/AX100 sind `tt` geflaggt, aber progressiv → Clipeigenschaften auf „Progressiv";
  per API NICHT setzbar, Mehrfachauswahl greift nicht). `kino-look-nodekette.md` um den Abschnitt
  „FilmConvert je nach Kamera dosieren" ergänzt (FS7 II gut, CX900E/AX100 auf Default unnatürlich)
  — inkl. der offenen Aufgabe, für Rec.709-Consumer-Camcorder eine eigene Look-Variante zu bauen.
- **13.08.2026:** `fallstricke.md`: Regel ergänzt, vor schreibenden/exportierenden API-Zugriffen
  `proj.IsRenderingInProgress()` zu prüfen — ein `Timeline.Export` während eines laufenden
  Renders zwang den Nutzer zum Resolve-Neustart.
- **16.08.2026 (Projekt-A Projekt-A):** `fallstricke.md` um den Render-Abbruch „Die Fusion
  Komposition bei <TC> konnte nicht verarbeitet werden" ergänzt. Echte Ursache steht nur im
  Resolve-Log (`No frame available for MediaOut1`): eine Fusion-Comp auf einem Anpassungsclip
  liefert am letzten Comp-Frame kein Bild. Fix = `MediaIn.SetInput('HoldLastFrame', 1.0)`.
  Mit dokumentiert: die Eingrenz-Technik über Einzelframe-Testrender per API, und was alles
  NICHT hilft (Comp-Range, PassThrough auf Blur/Maske/AudioDisplay, Spur deaktivieren).
- **16.08.2026 (Projekt-A Projekt-A, Fortsetzung):** `fallstricke.md` um zwei wiederverwendbare
  Techniken ergänzt: (1) **Clip trimmen ohne Maus** — Spuren sperren + `keys.py ctrl+b` +
  `tl.DeleteClips([item], False)`, inkl. der Falle, dass `SetCurrentTimecode` direkt nach
  `OpenPage` verschluckt wird; (2) **Wirkung eines Nodes messen, bevor man ihn abschaltet**
  (Frame-Differenz an mehreren Stellen statt `GetToolsInNode` zu vertrauen).
