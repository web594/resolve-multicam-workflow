# Resolve per Skript steuern — was geht

Stand 20.07.2026, DaVinci Resolve Studio 21.0.2, Windows 11, Python via `py` (3.14).
Werkzeugkasten: **`C:\claude\resolve-ctl\`** — dessen `README.md` ist die ausführliche Referenz
und sollte bei Detailfragen gelesen werden. Hier die Kurzfassung.

Voraussetzung: Resolve läuft; Einstellungen → System → Allgemein → „Externes Scripting" = **Lokal**.
`scriptapp("Resolve")` liefert `None` → **Resolve komplett neu starten** (typisch nach Updates).

## Ebene 1 — offizielle API als CLI: `rctl.py`

```
py C:\claude\resolve-ctl\rctl.py            # Hilfe, alle Befehle
py C:\claude\resolve-ctl\rctl.py status     # Verbindung + Überblick
```

Befehle: `status timelines timeline clips page goto goto-clip frame nodes node-add node-enable
lut cdl grade-set grade-show grade-save grade-apply grade-copy render key eval`

- `goto-clip N --mitte` + `frame C:\tmp\f.png` → Frame ansehen und beurteilen
  (**bei mehrteiligen/flackernden Stücken immer am Mittel-Frame beurteilen**).
- `eval "..."` für freies Skripten; Objekte: `resolve, pm, proj, mp, tl, item, graph`.
- Introspektion nach Updates: `py probe_api.py` (`dir()` funktioniert auf den Remote-Objekten).

Direkt in eigenen Skripten:
```python
os.environ.setdefault("RESOLVE_SCRIPT_API", r"C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting")
os.environ.setdefault("RESOLVE_SCRIPT_LIB", r"C:\Program Files\Blackmagic Design\DaVinci Resolve\fusionscript.dll")
sys.path.append(os.path.join(os.environ["RESOLVE_SCRIPT_API"], "Modules"))
import DaVinciResolveScript as dvr
resolve = dvr.scriptapp("Resolve")
```

## ★ Ebene 2 — Grading-Werte nativ setzen und lesen

Der Durchbruch vom 19.07.2026: Claude schreibt in **alle Zahlenfelder des Primaries-Panels**
(Werte stehen danach sichtbar drin) und liest sie zurück.

```
py rctl.py grade-set gammaM=0.06 gainR=1.12 liftM=-0.02 temp=-320 saett=53
py rctl.py grade-show     # alle Regler + Abweichung vom Neutralwert
```
Regler (Anzeige-Skala wie im Panel): `lift/gamma/gain` je `M R G B`, `offsetR/G/B`,
`temp toenung kontrast drehpunkt md colorboost schatten lichter saett farbton lummix`.

Technik: DRX-Body patchen (`drxlib.py`) → `Graph.ApplyGradeFromDRX`; Lesen aus der Projekt-DB
(SQLite, WAL-Dateien mitkopieren). IDs+Skalen in `calibration_map.json`.

⚠️ `grade-set` **ersetzt den ganzen Node-Baum** → vorher `grade-save sicherung.drx`, dann
`grade-set --base sicherung.drx …`.
⚠️ **Gamma/Power nicht per DRX patchen** (wirkungslos) → `rctl cdl N --power`.
⚠️ Eine Param-ID darf im Body nur EINMAL stehen — Duplikat ⇒ Regler wird komplett ignoriert.

Nach Resolve-Updates neu kalibrieren: `calibrate_drx.py` / `refine_cal.py`
im Testprojekt „zz claude api-probe (loeschbar)", Timeline `cal-tl` mit `cal_ramp.mp4`.

## Ebene 3 — Nodes und Tastatur

- **Color-Nodes anlegen UND verbinden:** `rctl node-add serial|parallel|layer|outside`
  (Alt+S/P/L/O; Mixer entstehen automatisch). Einfügepunkt = aktuell gewählter Node,
  neue Nodes wählen sich selbst → **Bäume in Anlege-Reihenfolge bauen**.
- **Node-Baum übertragen:** `rctl grade-copy` (= `TimelineItem.CopyGrades`) kopiert den
  kompletten Baum inkl. Mixer, auch timeline-übergreifend. Zuverlässiger als der DRX-Weg.
- **Vorlagen-Trick:** Struktur einmal auf einem Vorlagen-Clip bauen, per `grade-copy` verteilen,
  dann Nodes per Index füllen (`cdl`, `lut`, `grade-set`).
- **LUT setzen:** `project.RefreshLUTList()` zuerst (Methode am PROJECT!), dann
  `timelineItem.SetLUT(1, "name.cube")` — sonst kommt `False` zurück.
- Tastatur: `rctl key alt+s`, `py keys.py --text "1.05"` (fokussiert das Fenster zuverlässig).

## Fusion-Seite — volle Node-Kontrolle

```python
resolve.OpenPage("fusion"); comp = resolve.Fusion().GetCurrentComp()
comp.Lock(); t = comp.AddTool("Blur", -32768, -32768); t.Input = anderer.Output; comp.Unlock()
```
Anlegen ✅, verbinden ✅, Parameter ✅, `GetToolList()`, `t.Delete()`. 522 Tools
(IDs in `action_ids.txt`). Fusion-`ActionManager` hat 889 Actions — aber **nur Fusion-Seite**.

## Titel-Vorspann als Vorlage (`titel.py`)

Sichert einen fertigen Vorspann inkl. **aller Animationen/Keyframes** und baut ihn in einem
anderen Projekt mit neuem Text auf. Vorlage aus Projekt-C liegt in
`C:\claude\resolve-ctl\titelvorlage\`.
```
py titel.py apply C:\claude\resolve-ctl\titelvorlage --timeline "zus" \
    --text1 "Name\nBezeichnung" --text2 "Datum\nOrt"
```
Fallstricke dazu in `fallstricke.md` (Expression vs. Value, Comp-Zeiten, Mark relativ, Zielspur).

## Prozent-Zähler / animierte Zahlen

0 %→100 %-Zähler per **Text+ StyledText-Ausdruck in der Fusion-Konsole** (Makros gehen nicht).
Clip framegenau trimmen und verifizieren. Siehe Memory `fusion-prozent-zaehler-technik`.

## ★ OFX auf Nodes setzen + Parameter patchen (gelöst 20.07.2026)

Drei funktionierende Wege, alle render-verifiziert:
1. **`grade-copy`** (`TimelineItem.CopyGrades`) — kopiert funktionierende OFX mit, auch
   timeline-übergreifend. Der Standardweg: 1 Vorlagen-Clip → auf alle verteilen.
2. **DRX mit OFX-Body** — Grade-Body (aus Projekt-DB `LmVersion.Body`: 0x81+zstd+Protobuf)
   in ein DRX-Skelett setzen → `ApplyGradeFromDRX` bei **offenem** Projekt. Vorlagen in
   `C:\claude\resolve-ctl\drx\ofx\` (gaussblur_body.bin, gaussblur_st10.drx,
   beispiel_param_patch.py). OFX-Params stehen im Body **mit Klartextnamen**
   (`f5 = {f1: "HStrength", f2: {f2: double}}`) → numerisch patchbar/hinzufügbar.
3. **DB-Injektion** (Projekt geschlossen): `LmVersion.Body` der aktiven Version direkt
   ersetzen — vollste Treue (auch Power Windows, die ApplyGradeFromDRX herausfiltert).

⚠️ Die zwei Fallen dabei (Keyframes! Default-Werte fehlen im Body!) → `fallstricke.md`.
Neue OFX-Vorlage gewinnen: Effekt einmal per GUI anlegen (langsamer Einzelschritt-Drag,
siehe `fallstricke.md`) → `pm.SaveProject()` → Body aus der DB ziehen.

## Harte API-Grenzen (Resolve 21, verifiziert)

| Nicht per API | Ersatzweg |
|---|---|
| Multicam-Clip erzeugen (kein `CreateMultiCamClip` in der API) | ⭐ **GELÖST 27.07.2026 — per DRT-Bau, ohne GUI:** `vorlagen/mcbuild/build_mc_drt.py` schreibt `<Sm2MpMulticamClip>` + Definitionscontainer (ein Track je Kamera, `UserDefinedName`=„Angle N", `MediaRef`=DbId der Quell-Timeline) ins DRT → `ImportTimelineFromFile`. **UUIDs des Musters beibehalten** (Container-Zuordnung steckt UTF-16-kodiert in den zstd-Blobs von `MpFolder.xml`), sonst `Frames 0`. Details: `ablauf.md` Schritt 6 |
| Multicam-Winkel schalten | Bulk-Bau: Winkelziffer im `FieldsBlob` der Schnittclips (hinter `4b616d657261c2a0`, `31`/`32`) — erledigt `build_mc_drt.py` gleich mit. Einzeln nachträglich: Edit-Seite Clip anwählen → Rechtsklick → „Multicam-Perspektive wechseln" → Angle N (GUI, nicht-destruktiv) |
| Audio-Sync / „Sound-Sync" | eigene ffmpeg-Kreuzkorrelation (`vorlagen/sync.py`) |
| Bestimmten vorhandenen Color-Node auswählen | Computer-Use |
| Sonderverdrahtung (Key-Ausgang → Maske) | Computer-Use |
| Grade auf frisch eingefügtem Anpassungsclip | `.drx` in Galerie legen, Nutzer klickt 1× |
| Kurven ziehen, Color-Slice-Scrub | Computer-Use |

Weitere Quirks:
- `AppendToTimeline` kann **keine Timeline** als Clip nesten (nur echte Medien-Clips).
- `endFrame` ist **exklusiv** (Frameanzahl = endFrame − startFrame).
- ProRes nur mit `SetCurrentRenderFormatAndCodec("mov","ProRes422HQ")` (sonst fällt es auf H264).
- `GalleryStillAlbum.ExportStills` liefert oft `False` (launisch) — `ExportCurrentFrameAsStill`
  geht zuverlässig, aber nur auf der Color-Seite.
- `SaveProject` auf einem unbenannten Projekt öffnet einen **blockierenden Dialog**.
- `SetProperty` = nur Transform (Pan/Tilt/Zoom/Opacity/Crop), **kein** Grading.
- Undokumentiert vorhanden: `TimelineItem.GetProperty/SetProperty`, `Timeline.DetectSceneCuts`,
  `Timeline.ImportIntoTimeline`, `resolve.OpenPage/Quit`, `Project.RenderWithQuickExport`.

## Weitere eigene Werkzeuge

- `C:\claude\resolve-prep\prepare_project.py "<Projektordner>"` (`--dry-run`) — generische
  Auto-Vorbereitung aus der k-/t-/p-Ordnerkonvention.
- `C:\claude\resolve-farbberater\` — Grading-Ratgeber (Frame-Analyse → Resolve-Werte,
  Referenzvergleich, WB-Pipette, CDL anwenden).
- `C:\claude\BeautySmoothOFX\` — eigenes Hautglättungs-Plugin (DCTL + OFX).
