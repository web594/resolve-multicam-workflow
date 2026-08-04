---
name: resolve-projekt
description: DaVinci-Resolve-Filmprojekt für wunder-media anlegen und bearbeiten — Rohdaten sichten, Ton-Sync per Kreuzkorrelation, Projekt/Bins/Quell-Timelines per Python-API, Auto-Multicam-Schnitt aus Whisper-Transkript, Grading-Kette. Nutzen bei "neues Projekt anlegen", "Kameras synchronisieren", "Schnitt vorbereiten", "Multicam bauen", sowie generell wenn Resolve per Skript statt per Maus gesteuert werden soll (rctl.py, grade-set, Nodes, LUTs, Titel-Vorspann).
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
4. `references/kino-look-nodekette.md` — **die Grading-Kette als Rezept** (FilmConvert →
   Primär → OSIRIS-LUT → Gesicht → Film Look Creator), mit gemessenen Werten, der
   DRX-Vorlage (**ganze Kette in 0,04 s statt einer Stunde Klicken**) und der Tabelle
   „was macht Claude, was der Nutzer". Vor jedem Grading lesen.
5. ⭐ `references/vorbild-projekt.md` — **das Vorbild für Multicam-Projekte**: Ordnerbau,
   Soll-Zustand der Mediathek (inkl. Bin **`Anlegen`**), der bewährte Farb-Ablauf und die
   **Grenze Claude ↔ Mensch**. Bei jedem Multicam-Projekt lesen — beschreibt genau den
   Stand, bis zu dem Claude selbstständig anlegt.
6. `references/grafik-einblendungen.md` — **Schritt 9**: Infografiken/Overlays einbauen und
   das Video ausliefern (YouTube-Lang + Instagram-Kurz). Bei Vortrags-/Interview-Reihen
   mit wiederkehrendem Referenten immer lesen, bevor Grafiken gebaut werden.
7. `vorlagen/` — lauffähige Vorlagen-Skripte (aus Projekt-B, dem saubersten Projekt).
   Kopieren nach `C:\claude\resolve-prep\<kurzname>\`, Kopf-Konstanten anpassen, laufen lassen.
   `overlay_tools.py` läuft direkt (check / zoomsafe / mov / place).

## Kurzfassung des Ablaufs

| # | Schritt | Werkzeug |
|---|---------|----------|
| 1 | Rohdaten sichten (ffprobe: Kameras, Teile, fps, Ton-Kanäle, Log/Rec709) | `references/ablauf.md` |
| 2 | Ton-Sync gegen Hauptton (Tascam/dr10L), Offsets als JSON | `vorlagen/sync.py` |
| 3 | Projekt + Bins + Import + Quell-Timeline je Kamera | `vorlagen/prep.py` |
| 4 | Transkript (faster-whisper large-v3, CUDA) | `vorlagen/transcribe.py` |
| 5 | Auto-Schnittplan aus Sprechpausen (**ruhige Parameter, s. u.**) | `vorlagen/make_cutplan.py` |
| 6 | Schnitt-Timeline. **Bei ≥2 Kameras IMMER Multicam-mit-Schnitten — Multicam-Clip per DRT-Bau, NICHT per GUI** | `vorlagen/mcbuild/build_mc_drt.py` |
| 7 | Verifizieren (Lücken, Überlappungen, Winkel, **Schwarzbild-Render**), dann Grading (3-LUT-Kette, **geteilte Nodes**) | `vorlagen/verify_cut.py` |
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
2. **Look — Variante A ist der Standard, Richtung NICHT erfragen, einfach bauen:**
   - ⭐ **Variante A — der bewährte Farb-Ablauf** (Nutzer, 04.08.2026 am Vorbildprojekt:
     „ist ganz gut geworden"): die 5-Node-Kette
     FilmConvert Nitrate → Primärkorrektur → OSIRIS-Finish-LUT (35–45 %) → Gesicht-Sekundär →
     Film Look Creator (Halation/Vignette). Komplett per DRX übertragbar (**0,04 s**).
     Rezept + Werte + Vorlage: `references/kino-look-nodekette.md`, `vorlagen/kino_look/`.
     Braucht Projekt auf **DaVinci YRGB** (nicht Color Managed).
   - **Variante B (ARRI-Umweg) — NOCH NICHT FERTIG:** 1) auf **ARRI** wandeln → 2) **Filmstock**-
     Emulation → 3) **Kino-LUT** obendrauf. LUT-Pfade/Details im Memory
     `grading-look-kette-praeferenz`. **Status (Nutzer, 04.08.2026): eine ernstzunehmende zweite
     Möglichkeit, die aber erst noch genauer angesehen werden muss.** Deshalb **nicht** von sich
     aus für ein Kundenprojekt wählen — nur auf ausdrücklichen Wunsch.
   → **Immer Variante A bauen**, ohne Rückfrage. Nur die Feinhelligkeit bestätigen lassen.
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

7. ⚠️ **Titel und Einspieler sind KEIN allgemeines Muster** (Nutzer, 27.07.2026): Sie sind
   **pro Reihe/Kunde verschieden** — was bei Projekt-B gilt, gilt bei anderen Videos nicht.
   Also **nie einen Titeltext aus einem anderen Projekt übernehmen**, sondern für die jeweilige
   Reihe erfragen (bzw. aus einer früheren Folge **derselben** Reihe ablesen). Nur die
   *Technik* ist allgemein (`titel_overlay.py`, OVERLAY statt Ripple).
8. **Nach dem Multicam-Schnitt selbst mitliefern** (das musste der Nutzer bei Projekt-B-2 noch von
   Hand machen — siehe `ablauf.md` Schritt 8): eine **Arbeitskopie „… Multicam auswahl"**, darin
   den **Vorlauf am Anfang-Marker abtrennen** (in der KOPIE schneiden ist erlaubt — das Original
   bleibt unangetastet), und die **„… zus"-Endmontage** anlegen. Titel/Einspieler dort nur
   einbauen, wenn Text bzw. Material für dieses Projekt bekannt sind.
8a. ⭐ **Mediathek aufräumen — Bin `Anlegen`** (Nutzer, 04.08.2026). Zum Schluss verschiebt Claude
   die nur beim Anlegen gebrauchten Zwischen-Timelines — `<NAME> mitte`, `<NAME> seite`,
   `<NAME> ton`, `<NAME> Schnitt` — per `mp.MoveClips` in einen Bin **`Anlegen`**. Nicht löschen,
   nur wegräumen. **Oben bleiben** die `… import`-Timelines (tragen den Grade, sind die
   Multicam-Winkel), `Multicam Schnitt`, der `Multicam`-Clip und `Multicam Auswahl`.
   Befehl + Soll-Zustand der Mediathek: `references/vorbild-projekt.md`.
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
14. **⭐ Dateinamen erzeugter Dateien — drei feste Regeln, ausnahmslos für alle Projekte**
    (Nutzer, 3.8.2026, nach mehrfachem Verstoß bei `instagram_kurz.py`):
    (a) Aus dem Namen muss hervorgehen, zu **welchem Film/Projekt** die Datei gehört — ein Film
    für ein anderes Projekt/eine andere Folge MUSS anders heißen. „Instagram Kurz #4" reicht
    NICHT (könnte alles sein).
    (b) **Hat die Quelldatei einen GUTEN Namen, wird er übernommen** — Claudes Zusatz kommt
    HINTEN dran, nichts wird ersetzt: `<Quellname unveraendert> <Zusatz>.<ext>`, z. B.
    `#4 Thema-X, Kurz 1.1 15t.mp4` → `#4 Thema-X, Kurz 1.1 15t Instagram (Text, Musik, -14 LUFS).mp4`.
    (c) **Immer eine Versionsnummer/-kennung**, damit ein alter Stand nicht mit einem neuen
    verwechselt wird — steckt schon eine in der Quelle, reicht die, sonst `v1`/`v2` anhängen.
    (c2) ⭐ **FILME tragen vorne das Projektdatum** (Nutzer, 4.8.2026): der sechsstellige
    Projektcode `JJMMTT` aus dem Projektordner steht **am Anfang** des Dateinamens, damit der
    Film beim Suchen wieder dem Projekt zuzuordnen ist:
    `JJMMTT #5 Thema-Y, Kurz 1.1 15t Instagram (Text, Musik, -14 LUFS).mp4`. Fehlt er in der
    Quelle, wird er vorangestellt — `instagram_kurz.py` macht das automatisch (Projektcode per
    Regex `[\\/](\d{6})[ _-]` aus dem Pfad).
    (d) ⭐ **Kryptische Zwischenprodukt-Namen NICHT weiterschleppen** (Nutzer, 4.8.2026).
    Ein Resolve-Standbild heißt z. B. `Standbild 2026-08-03 170627 für tb 1_2.1.1.png` — daraus
    darf **kein** Titelbildname werden. Für **Enddateien** (Titelbilder, Grafiken, Videos, Texte)
    den Namen **neu bilden**: `<Projektname/Folge> <Art der Datei> <Details> <Version>`, z. B.
    `Titelbild #5 Thema-Y v2_4K.jpg`. Für das **Zwischenprodukt selbst** ist ein Datums-/Zeitname
    noch in Ordnung, solange es im zugehörigen `renderings`-Ordner liegt (dann ist die Zuordnung
    aus dem Ordner erschließbar) — für Enddateien nicht.
    Regel im Zweifel: Erkennt ein Kollege **allein am Dateinamen** Projekt/Folge und Stand?
    → Also in `instagram_kurz.py` (Quelle = fertiger Film) den Ausgabenamen aus der Quelle
    ableiten (`os.path.splitext(quelle)[0] + " <Zusatz>"`), in `make_thumb_*.py`
    (Quelle = Standbild) dagegen `OUTNAME` als sprechenden Namen setzen — nie fest verdrahtete
    generische Namen, aber auch nie den kryptischen Standbildnamen übernehmen.

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
  `Projekt-B-projekt.md`) und in `MEMORY.md` verlinken.

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
