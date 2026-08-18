# Vorbild-Projekt: so soll ein fertiges Multicam-Projekt aussehen

Ausgelesen am **04.08.2026** am Projekt `Projekt-B-3 Projekt-B` (3. Folge derselben Reihe,
2 Kameras + separater Hauptton). Der Nutzer hat diesen Stand ausdrücklich als **Vorbild**
freigegeben: „dieser Farb-Ablauf ist ganz gut geworden".

**Zweck dieser Datei:** Claude legt ein neues Projekt bis genau zu diesem Stand **selbstständig**
an; ab da arbeitet ein **Mensch** weiter. Die Grenze verläuft nicht nach „kann Claude das?",
sondern nach **„braucht Claude dafür deutlich länger als ein Mensch?"** — dann macht es der Mensch.

---

## 0. Was am Vorbild allgemein gilt — und was pro Projekt anders ist

⚠️ **Nicht alle Projekte sind gleich** (Nutzer, 04.08.2026). Das Vorbild zeigt einen
**2-Kamera-Fall mit einer Tonquelle** — das ist der häufige, nicht der einzige.

| gleich bleibt (normalerweise) | variiert pro Projekt |
|---|---|
| **Das Multicam-Vorgehen als solches**: sichten → Ton-Sync → Quell-Timelines → Transkript → Schnittplan → Multicam-Clip + Schnitte per DRT → verifizieren → Grade auf die `… import`-Timelines → Marker → Arbeitskopie → `Anlegen` aufräumen | **Anzahl der Kameras** (2, 3, 4 …) und ihre Rollen |
| Die Arbeitsteilung Claude ↔ Mensch (Abschnitt 4) | **Anzahl und Art der Tonquellen** (Recorder, Funke, Kamera-Ton, Saal-Pult) |
| Der Farb-Ablauf A als Startpunkt | **Titel: Text, Gestaltung und Aufbau** |
| Nicht-destruktives Arbeiten (Marker statt Schnitt) | **Einspieler, Grafik-Einblendungen, Endkarten** — ob es sie gibt und welche |
| Die Namenskonventionen | Ob es eine **Reihe** ist (Folge N mit festem Muster) oder ein **Einzelprojekt** |

**Mehr Kameras:** `k1…k4`-Ordner, je Kamera eine Quell-Timeline und ein Angle. Im Schnittplan
eine **Leitkamera** + mehrere Cutaway-Kameras im Wechsel (welche mitspielen, beim Nutzer
erfragen; eine kann reine Reserve sein). Das DRT-Verfahren skaliert unverändert — pro Kamera
ein Track im Definitionscontainer. Angle 1 bleibt die Leitkamera.

**Mehr Tonquellen:** **eine** ist der Sync-Master (meist der externe Recorder), alle anderen
werden **gegen diese** synchronisiert und als eigene Audiospuren geführt (nicht mischen —
das macht der Mensch). Backup-Spuren (`_D`) nicht importieren. Stumme oder unbrauchbare
Kameratonspuren nur zum Sync verwenden, dann stummschalten.

### ⚠️ Titel und Einblendungen sind NIE ein Muster

Titel unterscheiden sich **von Projekt zu Projekt in Text UND Aufbau** — mal Lower-Third mit
Name/Funktion, mal Vorspann-Karte, mal gar keiner. Ebenso Einspieler, Grafiken, Endkarten.

- **Reihe** (wiederkehrender Referent/Kunde): Titelaufbau aus einer **früheren Folge derselben
  Reihe** ablesen und nur den Text der neuen Folge einsetzen.
- **Neues/einzelnes Projekt:** Aufbau und Text **erfragen** — nichts aus einem fremden Projekt
  übernehmen und nichts erfinden.
- Allgemein ist **nur die Technik**: `titel_overlay.py`, OVERLAY statt Ripple, Spuren sperren.

## 1. Ordner auf der Platte (Rohdaten)

```
E:\<JJMMTT Name>\
  k1 <kamera-rolle>\      z. B. „k1 seite“   — eine MOV je Kamera
  k2 <kamera-rolle>\      z. B. „k2 mitte“   (Leitkamera)
  dr10L\                  Hauptton-WAV (+ „_D“ = Backup, nicht importieren)
  Kameraeinstellungen\    Fotos der Kamera-/Rekordermenüs vom Dreh
  testaufnahmen …\        optionale Testclips
  renderings\             alles Erzeugte: Render, Ton-Extrakt, Transkript
                          (.wav/.vtt/.json/.html), Standbild + DRX fürs Titelbild,
                          Titelbild .png/.psd
  <Projektname>.odt       Textdokument des Nutzers (Titel-/Thumbnail-Varianten)
  <Analyse>.pdf           projektbezogene Analysen/Empfehlungen als PDF
```

Die `k…`/`t…`/`p…`-Konvention liest `prep.py` automatisch. Erzeugtes gehört **immer** nach
`renderings\`, nie neben die Rohdaten, und folgt der Dateinamen-Konvention
(Quellname vorne + Versionsnummer, siehe SKILL.md Punkt 14).

## 2. Mediathek in Resolve — Soll-Zustand bei der Übergabe

```
Master
  ├─ <NAME> Multicam Schnitt      ← das Ergebnis von Claude (unangetastet lassen)
  ├─ <NAME> mitte import          ← Quell-Timeline Leitkamera  = Angle 1  · TRÄGT DEN GRADE
  ├─ <NAME> seite import          ← Quell-Timeline Cutaway     = Angle 2  · TRÄGT DEN GRADE
  ├─ <NAME> ton import            ← Hauptton-Timeline
  ├─ <NAME> Multicam              ← der Multicam-Clip selbst
  ├─ (<NAME> Multicam Auswahl)    ← ⚠️ NICHT von Claude vorab anlegen — erst wenn der Nutzer
  │                                  den Multicam Schnitt als fertig bestätigt (06.08.2026)
  ├─ (Einspieler, bereinigter Ton, Musik … kommen beim Weiterarbeiten dazu)
  ├─ [mitte] [seite] [ton]        ← Bins mit den Quellclips
  └─ [Anlegen]                    ← ⭐ Bins für alles, was nur beim Anlegen gebraucht wurde
        <NAME> mitte · <NAME> seite · <NAME> ton · <NAME> Schnitt
```

### ⭐ Regel „Anlegen“ (Nutzer, 04.08.2026)

Die beim Anlegen entstandenen **Zwischen-Timelines** — `<NAME> mitte`, `<NAME> seite`,
`<NAME> ton` und die verschachtelte `<NAME> Schnitt` — sind für die Weiterarbeit **nicht im
Vordergrund**. Claude verschiebt sie am Ende **selbst** in einen Bin **`Anlegen`**, damit der
Master-Ordner nur noch das zeigt, womit ein Mensch weiterarbeitet. Löschen: nein — nur wegräumen.

```py
py C:\claude\resolve-ctl\rctl.py eval "
root = mp.GetRootFolder()
sub = {f.GetName(): f for f in root.GetSubFolderList()}
ziel = sub.get('Anlegen') or mp.AddSubFolder(root, 'Anlegen')
namen = ['<NAME> mitte','<NAME> seite','<NAME> ton','<NAME> Schnitt']
mp.MoveClips([c for c in root.GetClipList() if c.GetName() in namen], ziel)
"
```

⚠️ **Die `… import`-Timelines bleiben oben** — sie tragen den Grade und sind die Multicam-Winkel.
Ebenso `Multicam Schnitt` und `Multicam`. `Multicam Auswahl` kommt erst **später** dazu (s. o.).

## 3. Farb-Ablauf — der bewährte (Variante A)

**Das ist der Standard**, nicht mehr zur Auswahl stellen. Vollständiges Rezept mit allen
gemessenen Werten: `kino-look-nodekette.md` + Skill `resolve-kino-look`.

| Ebene | Inhalt |
|---|---|
| Projekt | **DaVinci YRGB** (nicht Color Managed), Timeline/Ausgabe **Rec.709 (Scene)**, LUT-Interpolation **tetraedrisch** |
| Grade liegt auf | den **Quell-Timelines `… import`** (je ein Clip) → propagiert durch den Multicam-Clip auf jeden Schnitt |
| Node 1 | **FilmConvert Nitrate** — *geteilt* („FilmConvert Shared Node") |
| Node 2 | **Primärkorrektur** „Belic Kontr WB" — *lokal*, pro Kamera eingemessen |
| Node 3 | **OSIRIS `PRISMO - Rec709.cube`**, Key-Gain **0,40** — *geteilt* |
| Node 4 | **„Gesicht einzeln"** (Qualifizierer + Power Window) — *lokal*, vom Menschen gezogen |
| Node 5 | **Film Look Creator** (Halation + Vignette) — *geteilt* |

Merksätze: Weißabgleich/Belichtung **vor** die kreative LUT. Alles außer den drei Look-Nodes
bleibt **regelbarer Node-Wert**, nie eine zusätzlich gebackene LUT. Gleiche Inhalte über die
Kameras hinweg = **geteilte Nodes**.

### Variante B (ARRI-Umweg) — noch nicht fertig

Aus früheren Projekten: S-Log3 → **ARRI LogC** wandeln → **Filmstock-Emulation** (ImpulZ /
Kodak Ektar) → **Kino-LUT** obendrauf, als geteilte Gruppen-Nodes (`build_group_look.py`,
Memory `impulz-filmemulation-kette`, `grading-look-kette-praeferenz`).
**Status (Nutzer, 04.08.2026): eine ernstzunehmende zweite Möglichkeit, aber noch nicht
ausgereift — muss erst genauer angesehen werden.** Also: **nicht** von sich aus für ein
Kundenprojekt wählen; nur auf ausdrücklichen Wunsch oder als Versuchsreihe neben Variante A.
Bekannte Schwachstelle: die steile Film-LUT reagiert empfindlich auf schwaches Quellmaterial
(8-Bit / niedrige Bitrate → wandernde Streifen; s. Banding-Analyse im Projektordner).

## 4. Was Claude liefert — und wo der Mensch übernimmt

**Faustregel: Claude macht alles, was Zahl, Pfad oder Struktur ist. Der Mensch macht alles,
was Zeigen, Beurteilen oder freies Gestalten ist.**

| Arbeit | Wer | Warum |
|---|---|---|
| Rohdaten sichten, ffprobe-Bericht (Bit-Tiefe, Bitrate, Log-Profil) | **Claude** | Sekunden |
| Ton-Sync per Kreuzkorrelation, Offsets + Pearson | **Claude** | exakter als Auge/Ohr |
| Projekt, Bins, Import, Quell-Timelines | **Claude** | `prep.py` |
| Transkript (faster-whisper) | **Claude** | |
| Schnittplan + **Multicam-Clip + Schnitte per DRT** | **Claude** | ohne einen Klick |
| Verifizieren (Lücken, Überlappungen, Winkel, Schwarzbild-Render) | **Claude** | Zahlen nennen |
| 5-Node-Look per DRX auf beide Kameras | **Claude** | 0,04 s statt >1 h Klicken |
| Node 2 einmessen (Gain/Offset/Temp/Tint) | **Claude** | Richtung bestätigt der Nutzer |
| Marker Anfang/Ende aus dem Transkript, Löschkandidaten gelb | **Claude** | nicht-destruktiv |
| Arbeitskopie `… Multicam Auswahl` anlegen, Vorlauf abtrennen | **Claude** | ⚠️ erst wenn `Multicam Schnitt` vom Nutzer als fertig bestätigt ist — nicht automatisch (06.08.2026) |
| Zwischen-Timelines nach `Anlegen` räumen | **Claude** | s. o. |
| Transkript-Ton, Titelbild-Standbild, Render-Bereiche, YouTube-Paket | **Claude** | |
| **Node 4: Qualifizierer/Power Window ziehen** | **Mensch** | motivabhängig, per Maus 1–3 min |
| **Nodes zu echten Shared Nodes verknüpfen, Nodes beschriften** | **Mensch** | keine API |
| **LUT-Interpolation auf tetraedrisch** | **Mensch** | 1 Klick, keine API |
| **„heller/dunkler?", Look-Urteil** | **Mensch** | subjektiv |
| **Feinschnitt in `… Multicam Auswahl`**: Winkel tauschen, Einspieler setzen, Ton bereinigen/Musik, Titel/Lower-Third | **Mensch** | Gestaltung; Claude liefert nur Marker + Anleitung |
| **Endrender** | **Mensch** | |

⛔ **Nicht per Computer-use nachbauen**, was es als Skriptweg gibt (Node-Ketten klicken,
Zahlen ins Panel tippen, Timelines von Hand bauen). Dauert Claude weit über eine Stunde
und ist fehleranfällig.

## 5. So sieht die Arbeitskopie nach dem Menschen aus (Vorbild)

`<NAME> Multicam Auswahl` im Vorbildprojekt — zur Orientierung, **nicht** von Claude zu bauen:

| Spur | Inhalt |
|---|---|
| V1 | Multicam-Schnitt (35 Clips) + eingesetzter **Einspieler**-Clip |
| V2 | „Einfarbig"-Balken (Generator) unter dem Titel |
| V3 | Titel „Simple White" (Lower-Third) |
| A1 | Original-Hauptton (`… ton import`) |
| A2 | **bereinigte Sprachspur** (Speech-Isolation) + **Musik/Atmo** mit Überblendungen |

Marker im Original bleiben stehen: **grün „Anfang"**, **rot „Ende"** (aus dem Transkript),
blaue Hilfsmarken. Geschnitten wird nur in der Kopie.
