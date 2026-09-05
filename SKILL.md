---
name: resolve-projekt
description: DaVinci-Resolve-Filmprojekt für wunder-media anlegen und bearbeiten — Rohdaten sichten, Ton-Sync per Kreuzkorrelation oder Timecode (Atomos AirGlu), Projekt/Bins/Quell-Timelines per Python-API, Auto-Multicam-Schnitt aus Whisper-Transkript, Grading-Kette. Nutzen bei "neues Projekt anlegen", "Kameras synchronisieren", "Timecode einrichten", "AirGlu", "Schnitt vorbereiten", "Multicam bauen", sowie generell wenn Resolve per Skript statt per Maus gesteuert werden soll (rctl.py, grade-set, Nodes, LUTs, Titel-Vorspann).
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
4. ⭐ `references/farbgebung.md` — **welcher Look-Skill genommen wird**: Standard ist
   `resolve-kino-look-nodekette`, Ersatz ist `resolve-lut-look-kette`; gekaufte LUTs/Werkzeuge
   zuerst; und die **Kamera-Prüfung** (Rec.709-Consumer-Camcorder → Filmemulation gar nicht oder
   nur ganz wenig %). **Vor jedem Grading lesen.**
   Danach `references/kino-look-nodekette.md` — dieselbe Kette als Rezept mit allen gemessenen
   Werten und der DRX-Vorlage (**ganze Kette in 0,04 s statt einer Stunde Klicken**).
5. ⭐ `references/vorbild-projekt.md` — **das Vorbild für Multicam-Projekte**: Ordnerbau,
   Soll-Zustand der Mediathek (inkl. Bin **`Anlegen`**), der bewährte Farb-Ablauf und die
   **Grenze Claude ↔ Mensch**. Bei jedem Multicam-Projekt lesen — beschreibt genau den
   Stand, bis zu dem Claude selbstständig anlegt.
6. `references/timecode-sync.md` — **Variante zu Schritt 2**: Kameras laufen über
   Atomos **AirGlu** mit gemeinsamem Timecode → Offsets direkt aus den Dateien statt
   Kreuzkorrelation. Enthält die Geräte-Einrichtung (Server/Client, Region **Europe**,
   die Falle „Source hängt auf HDMI") und die Pflicht-Gegenprobe `vorlagen/tc_pruefen.py`.
   Lesen, wenn die Rohdaten von Shogun/Ninja Ultra kommen und Timecode tragen.
7. `references/grafik-einblendungen.md` — **Schritt 9**: Infografiken/Overlays einbauen und
   das Video ausliefern (YouTube-Lang + Instagram-Kurz). Bei Vortrags-/Interview-Reihen
   mit wiederkehrendem Referenten immer lesen, bevor Grafiken gebaut werden.
8. `vorlagen/` — lauffähige Vorlagen-Skripte (aus Projekt-B, dem saubersten Projekt).
   Kopieren nach `C:\claude\resolve-prep\<kurzname>\`, Kopf-Konstanten anpassen, laufen lassen.
   `overlay_tools.py` läuft direkt (check / zoomsafe / mov / place).

## Kurzfassung des Ablaufs

| # | Schritt | Werkzeug |
|---|---------|----------|
| 1 | Rohdaten sichten (ffprobe: Kameras, Teile, fps, Ton-Kanäle, Log/Rec709) | `references/ablauf.md` |
| 2 | Ton-Sync gegen Hauptton (Tascam/dr10L), Offsets als JSON | `vorlagen/sync.py` |
| 2b | **Bei Atomos-Rekordern mit AirGlu: Offsets direkt aus dem Timecode** statt Kreuzkorrelation — vorher mit `tc_pruefen.py` belegen | `references/timecode-sync.md`, `vorlagen/tc_pruefen.py` |
| 3 | Projekt + Bins + Import + Quell-Timeline je Kamera | `vorlagen/prep.py` |
| 4 | Transkript (faster-whisper large-v3, CUDA) | `vorlagen/transcribe.py` |
| 5 | Auto-Schnittplan aus Sprechpausen (**ruhige Parameter, s. u.**) | `vorlagen/make_cutplan.py` |
| 6 | Schnitt-Timeline. **Bei ≥2 Kameras IMMER Multicam-mit-Schnitten — Multicam-Clip per DRT-Bau, NICHT per GUI** | `vorlagen/mcbuild/build_mc_drt.py` |
| 6b | **Bild-Ton-Probe (Pflicht):** die Schnitt-Timeline ist gegenueber der Tonzeit GESTAUCHT (uebersprungene Stellen ohne Bild) - Ton stueckeln, dann messen | vorlagen/sync_pruefen.py |
| 7 | Verifizieren (Lücken, Überlappungen, Winkel, **Schwarzbild-Render**), dann Grading (Skill `resolve-kino-look-nodekette`, **geteilte Nodes**) | `vorlagen/verify_cut.py`, `references/farbgebung.md` |
| 8 | Nachbearbeiten: **richtigen Anfang finden, Organisatorisches raus, verwackelte/unscharfe Winkel tauschen**; Titel-Vorspann (Overlay) | `references/ablauf.md` |
| 8b | **Aufräumen + Übergabe:** Zwischen-Timelines in den Bin **`Anlegen`**, Soll-Zustand gegen das Vorbild prüfen | `references/vorbild-projekt.md` |
| 9 | **Grafik-Einblendungen + Auslieferung** (Infografiken aus dem Transkript, Instagram-Kurz 9:16, Untertitel, −14 LUFS) | `references/grafik-einblendungen.md`, `vorlagen/overlay_tools.py`, `vorlagen/infografik/`, `vorlagen/verify_overlays.py`, `vorlagen/instagram_kurz.py` |

**Voraussetzung immer:** Resolve läuft, Einstellungen → System → Allgemein →
„Externes Scripting" = **Lokal**. Bei `scriptapp("Resolve") is None` → Resolve komplett neu starten.

## ⛔ NICHT VERGESSEN: Multicam entsteht KOMPLETT per Skript — nie per Maus

**Nutzer-Anweisung (27.07.2026, ausdrücklich): Dieses Wissen darf nicht wieder verloren gehen,
und es ist SO durchzuführen, nicht anders.** Frühere Fassungen dieses Skills behaupteten,
der Multicam-**Clip** ginge „nur von Hand in der GUI". **Das ist falsch.** Er wird gebaut mit
`vorlagen/mcbuild/build_mc_drt.py` → `import_mc2.py` → `verify_mc.py` (verifiziert 27.07.2026,
Resolve 21.0.3: Multicam-Clip + 21 geschnittene Winkel ohne einen einzigen Klick).

Kurzfassung des Verfahrens (Details in `references/ablauf.md` Schritt 6):
1. Verschachtelte Schnitt-Timeline bauen (`apply_cut.py`) und als **DRT exportieren** (`Timeline.Export(pfad, 1)`).
2. Aus einem **beliebigen älteren Projekt mit Multicam** ein DRT als **Muster** exportieren.
3. `build_mc_drt.py` setzt in das neue DRT ein `<Sm2MpMulticamClip>`-Element + einen
   Definitions-`SeqContainer` (pro Kamera ein Track, `UserDefinedName` = „Angle N",
   `MediaRef` = DbId der Quell-Timeline) und biegt die Schnittclips auf den Multicam um.
4. `ImportTimelineFromFile` → fertige Multicam-Schnitt-Timeline.

⭐⭐ **Die eine Falle, an der es scheitert:** Die Zuordnung *Multicam-Sequence → Definitions-
container* steht **nicht** im Klartext-XML, sondern **UTF-16-kodiert in den zstd-`FieldsBlob`s
von `MpFolder.xml``**. Deshalb **niemals neue UUIDs würfeln** — die `DbId`s von Multicam-Element,
Sequence und Container aus dem Muster **unverändert übernehmen** (Resolve vergibt beim Import
ohnehin frische IDs). Sonst entsteht ein Multicam-Clip **ohne Angles: `Frames 0`, schwarzes Bild**.

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
0. **Schnitt-Tempo: geringfügig ruhiger als früher** (Nutzer, 27.07.2026). Bei Projekt-A kamen
   manche Schnitte zu früh: nach einem Schnitt braucht der Zuschauer ein paar Sekunden, um sich
   auf das neue Bild einzustellen — folgt dann gleich wieder eine kurze Gegen-Einstellung, wirkt
   es hektisch. Wenige Sekunden mehr pro Einstellung genügen. Werte in `make_cutplan.py`:
   `MIN_SHOT 6.0`, `CUT_MIN 6.0`, `CUT_MAX 11.0`, `PARA_GAP 1.2`, `MAX_STD 50`, **`CALM_GAP 12.0`**
   (Beruhigungspause: so lange nach einem Cutaway kein neuer), mechanische Teilung 55/42/10.
   Außerdem: **erster Span immer Leitkamera** und **keine Cutaways vor dem inhaltlichen Anfang**
   (`ANFANG`), sonst fällt direkt hinter dem Filmanfang ein Schnitt.
1. **≥2 Kameras → IMMER die geschnittene Multicam liefern** (echter Multicam-Clip per DRT-Bau,
   `vorlagen/mcbuild/`), damit der Nutzer beim Bearbeiten jeden Clip auf eine andere Kamera umschalten
   kann. Nicht mehr fragen „Nesting oder Multicam".
   ⭐⭐ **Das gilt auch für JEDES abgeleitete Video** — Kurzfassung, Ausschnitt, Arbeitskopie,
   Instagram-Fassung (Nutzer, 23.08.2026, ausdrücklich): Sie müssen **echte Multicam-Timelines mit
   den Winkeln des Hauptschnitts** sein, sonst kann der Nutzer beim Feinschnitt keine Einstellung
   mehr austauschen. ⛔ **`AppendToTimeline` mit dem Multicam-Clip reicht NICHT** — dabei landen zwar
   Multicam-Clips in der Zieltimeline, aber **alle auf Angle 1**; die Winkelwahl ist weg. Der Winkel
   steht nur im `FieldsBlob` des Clips und ist per API nicht setzbar. Richtiger Weg:
   `vorlagen/kurzvideo_drt.py` + `vorlagen/kurzvideo_import.py` (Hauptschnitt als DRT exportieren,
   Clips der gewünschten Passagen mit **unverändertem FieldsBlob** übernehmen, `Start`/`Duration`/`In`
   neu rechnen, importieren; Ton danach passagenweise per API auf A1). Der Grade kommt im DRT mit.
1b. ⭐⭐ **Wiedergabe-Framerate = Timeline-Framerate — SOFORT beim Anlegen setzen** (Nutzer,
   23.08.2026). `proj.SetSetting("timelinePlaybackFrameRate", "<fps>")` gehört in denselben
   Einstellungsblock wie `timelineFrameRate`, **bevor** die erste Timeline entsteht. Steht sie falsch
   (Standard oft **24**), klingt der Ton beim Abspielen schlecht — und **sobald eine Timeline im
   Projekt liegt, verweigert `SetSetting` die Änderung** (`False`, auch auf Timeline-Ebene). In der
   Oberfläche geht es dann noch: Zahnrad unten rechts → Haupteinstellungen → Timeline-Format →
   „Wiedergabe-Framerate" eintippen → Speichern. Beim Anlegen mitsetzen erspart diesen Umweg.
2. **Look — der Standard steht fest, Richtung NICHT erfragen, einfach bauen** (Nutzer,
   18.08.2026). Einzelheiten und die Kamera-Prüfung: `references/farbgebung.md`.
   - ⭐ **Standard: Skill `resolve-kino-look-nodekette`** — die 4-Node-Kette
     Filmemulation → Weißabgleich+Helligkeit (regelbar) → Finish-LUT (40 %) →
     Film-Look-Erzeuger (Halation/Vignette). Komplett per DRX übertragbar (**0,04 s**).
     Braucht Projekt auf **DaVinci YRGB** (nicht Color Managed).
   - **Ersatz: Skill `resolve-lut-look-kette`** — dieselbe Idee als reine LUT-Kette
     (Log→ARRI Rec.709 · regelbarer Node · Rec.709→ARRI LogC · Filmemulation · Kino-Look).
     Nehmen, wenn Plugins fehlen/nicht zur Kamera passen, eine Reihe schon darauf aufgebaut ist
     oder der Nutzer es wünscht.
   - **In beiden Ketten zuerst die GEKAUFTEN LUTs und Werkzeuge**; die freien Fassungen nur,
     wenn ein Werkzeug fehlt oder die Kamera kein Profil im Plugin hat.
   - ⚠️ **Vor dem Bauen prüfen, welche Kameras im Projekt liegen.** Log-Material (FS7 II,
     S-Log3) → Kette wie vorgesehen. **Rec.709-Consumer-Camcorder (Sony AX100, CX900E und
     ähnliche) → Filmemulation gar nicht oder nur ganz wenig %**, sonst werden die Farben
     unnatürlich; Filmcharakter über die übrigen Nodes holen.
   → **Immer die Nodekette bauen**, ohne Rückfrage. Nur die Feinhelligkeit bestätigen lassen.
3. **LUTs NUR für diese drei Look-Schritte.** Jede Korrektur (Weißabgleich, Helligkeit, Farbstich/
   Magenta/Blau, Sättigung, Kontrast) als **regelbarer Resolve-Node-Wert**, nie als zusätzliche
   gebackene LUT — damit nachvollziehbar bleibt, was vom Original abweicht, und einzelne Werte
   zurückstellbar sind.
4. **⭐ Gleiche Node-Inhalte über Kameras hinweg = GETEILTE Nodes** (Shared Nodes): die identischen
   Look-Nodes (ARRI-Wandlung, Filmstock, Kino) als geteilte Nodes anlegen, damit eine Änderung auf
   ALLE Clips/Kameras wirkt. Nur kamera-spezifische Korrekturen (z. B. Angleich weit→nah) bleiben
   lokal. Details in `references/ablauf.md`/`fallstricke.md`.
4b. ⭐⭐ **Weißabgleich-Node: pro Winkel EIN geteilter Node — immer so anlegen** (Nutzer,
   24.08.2026, ausdrücklich „bitte für immer merken"). Der regelbare Node 2
   („Weissabgleich + Helligkeit") wird **je Winkel** zu einem **geteilten Node**, der auf
   **allen Clips dieses Winkels** sitzt — dann ändert eine Korrektur den ganzen Winkel auf einmal.
   Winkel-übergreifend wird er **nicht** geteilt (jeder Winkel hat eigene Werte).
   Die Look-Nodes 1/3/4 sind ohnehin geteilt.
   **Rezept (verifiziert 24.08.2026 an Projekt-M Projekt-M, 3 Winkel × 21/22 Clips):**
   1. In der `… import`-Timeline des Winkels auf einen Referenzclip fahren
      (`SetCurrentTimeline` + `SetCurrentTimecode`, `OpenPage("color")`).
   2. **Ein einziger Computer-use-Klick:** Rechtsklick auf Node 2 →
      **„Als geteilten Node speichern"**. (Die API kann das nicht; ein Klick ist zumutbar.)
   3. Alles Weitere per Skript: `refItem.CopyGrades(alle_anderen_Clips_des_Winkels)` —
      `CopyGrades` überträgt geteilte Nodes als **dasselbe** Objekt, das Label wird überall
      `… Shared Node <n>`. Das gilt auch **timeline-übergreifend**: die Kopien der
      Winkel-Timelines, die beim DRT-Import der Kurzvideos entstehen
      (`… nah import 1…12`), im selben Zug mitversorgen, sonst hängen die Kurzvideos an
      einem alten, nicht mitgeführten Grade.
   4. Prüfen: Node-Labels auslesen (alle gleich?) und je Winkel einen Frame messen.
   5. **Gleich mit erledigen:** LUT-Interpolation auf **tetraedrisch** stellen — Shift+9 →
      Color Management → „Look-up-Tables" → „3D-LUT-Interpolation" → Speichern (kein API-Schlüssel).

4c. ⭐ **Unbenutzte Shared-Node-Kopien am Ende wieder löschen** (Nutzer, 27.08.2026, für immer).
   Jedes Anwenden einer DRX/Look-Kette, die geteilte Nodes enthält, legt in der Shared-Node-Liste
   einen **neuen** Eintrag an, statt den vorhandenen zu benutzen — bei clipweisem Anwenden also
   eine Kopie **pro Clip** (Projekt-M Projekt-M: 198 Einträge, davon nur 12 benutzt, 186 Karteileichen,
   alle byte-identisch). Bild bleibt richtig, aber die Liste wird unbrauchbar und die Projekt-DB
   wächst.
   - **Vermeiden:** Kette einmal anlegen und die Clips per `CopyGrades`/Farbgruppe anhängen
     (Rezept 4b), statt die DRX auf jeden Clip einzeln anzuwenden.
   - **Aufräumen (ohne Rückfrage einplanen, aber vorher messen):**
     1. Benutzte Namen sammeln: über **alle** Timelines je Clip
        `item.GetNodeGraph().GetNodeLabel(i)` — das Label ist der Name des geteilten Nodes.
     2. Registry lesen: Tabelle `ListMgt::LmPowerNode` in der Projekt-DB
        (`…\Resolve Project Library\…\Projects\<name>\Project.db`, WAL-Dateien mitkopieren).
     3. Alles, was in 1. nicht vorkommt, ist Karteileiche → in der GUI über die Shared-Node-Liste
        löschen (Rechtsklick). **Benutzte niemals löschen** — sonst bricht der Grade.

5. **Andere Kameras an die Leitkamera angleichen** (per Korrektur-Node-Werten, nicht per LUT).
6. **Titeltext** aus Ordnername ableiten (Name + Bezeichnung; Datum + Ort, meist „München") und nur
   **inhaltlich gegenprüfen** lassen — nicht die ganze Titel-Prozedur erfragen.

7. ⚠️ **Titel und Einspieler sind KEIN allgemeines Muster** (Nutzer, 27.07.2026): Sie sind
   **pro Reihe/Kunde verschieden** — was bei Projekt-B gilt, gilt bei anderen Videos nicht.
   Also **nie einen Titeltext aus einem anderen Projekt übernehmen**, sondern für die jeweilige
   Reihe erfragen (bzw. aus einer früheren Folge **derselben** Reihe ablesen). Nur die
   *Technik* ist allgemein (`titel_overlay.py`, OVERLAY statt Ripple).
8. ⚠️ **Arbeitskopie „… Multicam Auswahl" NICHT automatisch/vorzeitig anlegen** (Nutzer,
   06.08.2026, nach Projekt-J): Claude baute sie bisher direkt im Zuge der Pipeline mit —
   das ist **falsch**. Der Sinn der „Auswahl" ist, dass **aus ihr** hinterher das rausgenommen
   wird, was nicht in den fertigen Film soll (Organisatorisches, verworfene Winkel, der
   Vorlauf) — übrig bleibt am Ende **die Auswahl**. Legt Claude diese Kopie schon an, **bevor**
   der `… Multicam Schnitt` durch die Nachbearbeitung (Schritt 8 unten: richtiger Anfang,
   Qualitätscheck, ggf. weitere Korrekturen) wirklich fertig ist, spiegelt die Kopie einen
   Zwischenstand — spätere Änderungen am `Schnitt` laufen an ihr vorbei. **Regel: die
   Arbeitskopie erst anlegen, wenn der Nutzer den `Multicam Schnitt` als fertig bestätigt hat**
   (explizit fragen, nicht von selbst loslegen). Erst dann: Vorlauf am Anfang-Marker abtrennen
   (in der KOPIE schneiden ist erlaubt — das Original bleibt unangetastet), danach ggf. die
   **„… zus"-Endmontage**. Titel/Einspieler dort nur einbauen, wenn Text bzw. Material für
   dieses Projekt bekannt sind. Bauweise der Kopie (kein Re-Import!): `ablauf.md` Schritt 8.1.
8a. ⭐ **Mediathek aufräumen — Bin `Anlegen`** (Nutzer, 04.08.2026). Zum Schluss verschiebt Claude
   die nur beim Anlegen gebrauchten Zwischen-Timelines — `<NAME> mitte`, `<NAME> seite`,
   `<NAME> ton`, `<NAME> Schnitt` — per `mp.MoveClips` in einen Bin **`Anlegen`**. Nicht löschen,
   nur wegräumen. **Oben bleiben** die `… import`-Timelines (tragen den Grade, sind die
   Multicam-Winkel), `Multicam Schnitt`, der `Multicam`-Clip und `Multicam Auswahl`.
   Befehl + Soll-Zustand der Mediathek: `references/vorbild-projekt.md`.
8a-2. ⭐⭐⭐ **In Master steht von jedem Namen (auch von technischen Zwischen-Objekten)
   IMMER nur EIN Eintrag — nicht „alle, die gerade aktiv gebraucht werden".**
   (Nutzer, 24.08.2026, nach dreimaliger Korrektur ausdrücklich „für immer merken".)
   Erste Fassung dieser Regel war zu lasch: sie ließ *alle* aktuell benutzten Kopien
   (z. B. sieben verschiedene `… weit import <N>`, je eine pro Kurzvideo + Hauptschnitt)
   in Master stehen, weil sie ja „alle gerade gebraucht" werden. **Das war falsch.**
   Bin-Ort und Funktion sind unabhängig: `mp.MoveClips` ändert nichts an der internen
   Verknüpfung (Multicam-Referenzen laufen über DbId, nicht über den Bin-Pfad) — deshalb
   darf und soll in Master **grundsätzlich nur die EINE Kopie sichtbar bleiben, die zum
   Hauptschnitt (`Multicam Schnitt`) gehört** (die unnumerierte: `nah/weit/seite/ton
   import`, `Multicam import`). **Jede numerierte Kopie** (`… import 10`, `… import 23`
   usw.) — auch wenn sie von einem der sechs Kurzvideos aktiv gebraucht wird — gehört in
   den Unterordner `Alte Versionen`. Die Kurzvideos funktionieren danach unverändert
   weiter (verifiziert: Clip-/Markeranzahl unverändert, Bildprobe scharf und korrekt
   gegradet) — nur eben nicht mehr sichtbar in Master.
   **Praktisch:** nach jedem DRT-Reimport (Winkel-Korrektur, Kaltstart, künftige
   Änderungen) per Namensmuster `^Projekt-M Projekt-M (Multicam import|nah import|weit
   import|seite import|ton import) \d+$` **alles mit einer Zahl am Ende** aus Master in
   den Unterordner verschieben — ausnahmslos, unabhängig davon, ob es technisch noch
   gebraucht wird.
   ⚠️ **Dabei nicht nur die Wurzel von Master durchsuchen, sondern REKURSIV alle
   Unterordner** (`Kurzvideos`, `Anlegen`, …) — dort können sich weitere alte Kopien
   desselben Namens verstecken, die beim Aufräumen sonst übersehen werden.
   ⭐ Falls man wissen will, welche Winkel-Timeline ein bestimmter Multicam-Clip benutzt
   (z. B. zum gezielten Nachbearbeiten): Media Pool → Multicam-Clip → Rechtsklick →
   **„In Timeline öffnen"** (sicher, kein Absturzrisiko) → auf der **Edit-Seite** (nicht
   Farbe-Seite!) zeigt jede Spur den Namen ihrer Quell-Winkel-Timeline im Clip-Label.
8b. **Grenze Claude ↔ Mensch** (Nutzer, 04.08.2026): Claude zieht alles durch, was per Skript
   geht — aber **Arbeiten, für die Claude deutlich länger braucht als ein Mensch, macht der
   Mensch** (Qualifizierer/Power Window, Shared-Node-Verknüpfung, Node-Beschriftung,
   LUT-Interpolation, Feinschnitt/Gestaltung in `… Multicam Auswahl`, Endrender).
   Tabelle in `references/vorbild-projekt.md` Abschnitt 4.
8c. ⚠️ **Nicht alle Projekte sind gleich** (Nutzer, 04.08.2026). Gleich bleibt normalerweise nur
   das **Multicam-Vorgehen selbst**. Verschieden sind: **Anzahl der Kameras** (2, 3, 4 … — je
   Kamera ein Angle, Leitkamera = Angle 1), **Anzahl/Art der Tonquellen** (eine ist Sync-Master,
   der Rest wird dagegen synchronisiert und als eigene Spur geführt, nicht mischen), und vor
   allem **Titel, Einspieler und Grafik-Einblendungen** — die sind in **Text UND Aufbau** pro
   Projekt/Reihe verschieden. Bei einer **Reihe** den Aufbau aus einer früheren Folge
   **derselben** Reihe ablesen; bei einem **Einzelprojekt erfragen**. Nie aus einem fremden
   Projekt übernehmen. Details: `references/vorbild-projekt.md` Abschnitt 0.

### Stehende Antworten für Grafik-Folgen einer Reihe (aus #3 Thema-Y, 29.07.2026)

9. **„Sonst bitte alles umsetzen" ist die Regel, nicht die Ausnahme.** Beim Verteilungsplan
   NICHT in „empfohlen / optional" aufteilen und dann auf eine Auswahl warten — der Nutzer
   nimmt ohnehin alles. Plan vorlegen, Freigabe abwarten, dann **den kompletten Plan** bauen.
10. ⛔ **Keine „Angabe <Referent>"-Zeile** unter Aussagen des Referenten (Nutzer, 29.07.2026).
    Nicht erneut anbieten. **Fremde** Zahlen (Bundesnetzagentur, BfS, Statista) bekommen
    dagegen eine kleine neutrale Quellenzeile — die stützt ihn, statt ihn zu relativieren.
11. **Das Auslieferungspaket immer ungefragt mitliefern** (der Nutzer hat es bei #3 einzeln
    nachgefordert, es ist jedes Mal dasselbe):
    Titelbild (`make_thumb_<folge>.py` als Kopie, gegradetes Standbild per `rctl.py frame`)
    · `YouTube Beschreibung <folge>.txt` mit 3 Titelvarianten, Kapitelmarken, Beschreibung,
    angeheftetem Kommentar, Tags · **Endkarte** als letzte Grafik · **Cross-Link-Lower-Third**
    auf die Vorgängerfolge · **Kaltstart-Vorschlag** (stärkster Satz nach vorn, siehe 12)
    · `ANLEITUNG <folge>.txt` mit allen Frames + Render-Bereichen.
12. **Kaltstart nicht selbst schneiden — nur Marker + Anleitung.** Frame-genaue Grenzen aus den
    **Wort-Zeitstempeln** der Whisper-JSON (`seg['timestamps']`) holen, nicht aus den VTT-Cues;
    In-Punkt in die Sprechpause legen. Drei Längen-Varianten anbieten, den empfohlenen Bereich
    als Marker **mit Dauer** setzen (dann ist er im Lineal als Balken sichtbar), und in eine
    Textdatei schreiben, was wohin kopiert wird (inkl. „Marker wandern beim Ripple nicht mit").
13. **B-Roll-Fotos dürfen dem Maßstab der Anleitung nicht widersprechen.** Bei #3 lag ein
    30-m-Steinturm über „so einen Thema-Y baut ihr im Garten" — der Zuschauer denkt dann,
    er müsse das bauen. Faustregel: Ein Foto nur dort, wo der Ton es **deckt**; wenn keine
    Passage passt, das Bild **weglassen** und für die Folge aufheben, in der er darüber spricht.
14. **⭐ Dateinamen-Konvention — sechs feste Regeln, ausnahmslos für alle Projekte**
    (Nutzer, 3./4.8.2026, nach mehrfachem Verstoß bei `instagram_kurz.py` und `make_thumb_*.py`).
    Leitfrage: **Erkennt ein Kollege allein am Dateinamen, zu welchem Projekt/welcher Folge die
    Datei gehört und welcher Stand sie ist?**

    (a) **Projekt-/Folgenzuordnung muss im Namen stehen.** Ein Film für ein anderes Projekt oder
    eine andere Folge MUSS anders heißen. „Instagram Kurz #4" reicht NICHT (könnte alles sein).

    (b) ⭐ **FILME tragen vorne das Projektdatum.** Der sechsstellige Projektcode `JJMMTT` aus dem
    Projektordner (z. B. `Reihe-R …`) steht **am Anfang** des Dateinamens — daran findet man den
    Film beim Suchen wieder:
    `Reihe-R #5 <Folge>, Kurz 1.1 15t Instagram (Text, Musik, -14 LUFS).mp4`. Fehlt er in der
    Quelle, wird er vorangestellt; `instagram_kurz.py` macht das automatisch (Projektcode per
    Regex `[\\/](\d{6})[ _-]` aus dem Pfad).

    (c) **Guten Quellnamen übernehmen, Zusatz hinten anhängen** — nichts ersetzen:
    `<Quellname unveraendert> <Zusatz>.<ext>`, z. B. `#4 Thema-X, Kurz 1.1 15t.mp4` →
    `#4 Thema-X, Kurz 1.1 15t Instagram (Text, Musik, -14 LUFS).mp4`.

    (d) **Immer eine Versionsnummer/-kennung**, damit ein alter Stand nicht mit einem neuen
    verwechselt wird — steckt schon eine in der Quelle, reicht die, sonst `v1`/`v2` anhängen.

    (e) ⭐ **Kryptische Zwischenprodukt-Namen NICHT weiterschleppen.** Ein Resolve-Standbild heißt
    z. B. `Standbild 2026-08-03 170627 für tb 1_2.1.1.png` — daraus darf **kein** Titelbildname
    werden. **Enddateien** (Titelbilder, Grafiken, Videos, Texte) bekommen einen **neu gebildeten**
    Namen: `<Projektname/Folge> <Art der Datei> <Details> <Version>`, z. B.
    `Titelbild #5 Thema-Z v3_4K.jpg`. Beim **Zwischenprodukt selbst** ist ein Datums-/Zeitname
    noch in Ordnung, solange es im zugehörigen `renderings`-Ordner liegt (dann ist die Zuordnung
    aus dem Ordner erschließbar) — bei Enddateien nicht.

    (f) ⛔ **Nur EIGENE Dateien umbenennen.** Die Regeln gelten für Dateien, die Claude selbst
    erzeugt — dort **gleich beim Anlegen** einen guten Namen vergeben. **Vom Nutzer erzeugte
    Dateien** (Renderings, Standbilder, KI-Bilder) **nicht umbenennen**, auch nicht „aufräumend"
    oder um einen Tippfehler zu beheben — nur auf ausdrückliche Bitte. Ist ein Quellname schlecht:
    die eigene Ergebnisdatei gut benennen und die Quelle in Ruhe lassen. Solche Quellen im Skript
    per **Namensfragment** suchen statt hart eintippen — Resolve-Standbilder enthalten z. B. ein
    **geschütztes Leerzeichen (Zeichen 160)**, ein getippter Pfad scheitert daran.

    **Praktisch in den Skripten:** `instagram_kurz.py` (Quelle = fertiger Film) leitet den
    Ausgabenamen aus der Quelle ab (`os.path.splitext(quelle)[0] + " <Zusatz>"`) und stellt das
    Projektdatum voran; `make_thumb_*.py` (Quelle = Standbild) setzt `OUTNAME` als sprechenden
    Namen und sucht die Quelle über ein `MATCH`-Fragment.
    Details/Beispiele im Memory `dateinamen-konvention`.

**Nur das noch beim Nutzer lassen:**
- Die **subjektive Helligkeits-/Richtungsfeinheit**: Mitte-Frame zeigen, kurz „heller/dunkler?".
- **Zerstörerische Eingriffe an bereits vorhandener Nutzer-Arbeit** (fremde Timelines/Grades
  löschen/überschreiben). Das reine Anlegen der Pipeline auf einem neuen/leeren Projekt ist frei.
- **Den Verteilungsplan der Grafiken freigeben** (einmal, als Tabelle) — danach durchziehen.
- **Rendern** macht der Nutzer selbst; wir liefern die exakten **Frame-Bereiche**.

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
  `C:\Users\<benutzer>\.claude\projects\C--claude\memory\` anlegen/aktualisieren (Muster:
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
