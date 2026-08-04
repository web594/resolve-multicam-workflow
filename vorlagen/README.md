# Vorlagen-Skripte

Herkunft: Projekt **Projekt-B-1** (sauberstes, vollständigstes Projekt, 2 Kameras).
Alle Skripte sind lauffähig — sie brauchen nur die **Kopf-Konstanten** angepasst.

**Vorgehen:** ganzen Ordner nach `C:\claude\resolve-prep\<kurzname>\` kopieren, Konstanten
anpassen, in dieser Reihenfolge laufen lassen.

| Skript | Anzupassen | Ergebnis |
|---|---|---|
| `sync.py` | `ROOT`, `REF` (Hauptton-wav), `CAMS` (Teile in Reihenfolge), `CACHE` | `offsets.json` |
| `prep.py` | `ROOT`, `NAME`, `CAMS`, `HAUPTTON`, Pfad zu `offsets.json` | Projekt + Bins + Quell-Timelines |
| `transcribe.py` | Ton-Pfad, Ausgabepfade | `segments.json`, `words.json` |
| `make_cutplan.py` | **Leitkamera**, Cutaway-Kameras, Pausen-Schwellen, Zwangswechsel-Dauer | `cut_plan.json` |
| `apply_cut.py` | `NAME`, Timeline-Namen, Fallback-Kamera | Timeline `<NAME> Schnitt` (verschachtelt) |
| `verify_cut.py` | Timeline-Name | Prüfbericht: Clips je Winkel, Lücken, Überlappungen, Dauer |
| `mcbuild/build_scaffold_mc.py` → `patch_mc.py` → `import_mc.py` | Multicam-Clipname, **Angle-Mapping**, Start-TC | Timeline `<NAME> Multicam Schnitt` |

## Wichtig vor dem Anpassen

- **Offset-Vorzeichen** bestimmt, ob in `prep.py` der Ton oder die Kamera getrimmt wird.
  Die Vorlage ist für **positive** Offsets (Tascam lief vor den Kameras) gebaut.
- `mcbuild` setzt voraus, dass der **Multicam-Clip von Hand in der GUI** angelegt wurde
  (Perspektivensync = Timecode). Das **Angle-Mapping ist projektabhängig** und muss ausgelesen
  und in `patch_mc.py` eingetragen werden.
- Vergleichsmaterial: `C:\claude\resolve-prep\{Projekt-B,Projekt-C,Projekt-A}\` — dort stehen
  Varianten (negative Offsets bei Projekt-A, 4 Kameras + LUT-Generatoren + Schwarzloch-Reparatur
  bei Projekt-C).

## Wenn eine Vorlage besser wird

Verbesserte Fassung hierher zurückschreiben und in `../references/historie.md` vermerken.
