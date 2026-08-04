# Kino-Look als 5-Node-Kette (FilmConvert-Variante)

Ausgelesen am 04.08.2026 aus einem fertig gegradeten FS7-II-/Shogun-Projekt (S-Log3,
S-Gamut3.Cine, Cine EI). **Nur die aktiven Nodes** — ausgeschaltete Nodes aus früheren
Versuchen sind bewusst nicht Teil des Rezepts (ausdrückliche Nutzer-Anweisung).

Diese Kette ist der **empfohlene Startpunkt** für Vortrags-/Interview-Material aus der FS7.
Sie ersetzt die ältere 3-LUT-Kette (ARRI-Wandlung → Filmstock-LUT → Kino-LUT) nicht generell,
ist aber die neuere und in der Praxis bevorzugte Variante — welche gilt, im Zweifel einmal
beim Nutzer bestätigen lassen.

## Projekt-Voraussetzung

| Einstellung | Wert | per API? |
|---|---|---|
| `colorScienceMode` | `davinciYRGB` (**nicht** Color Managed) | ✅ `proj.SetSetting` |
| `colorSpaceTimeline` | `Rec.709 (Scene)` | ✅ |
| `colorSpaceOutput` | `Rec.709 (Scene)` | ✅ |
| `colorSpaceInput` | `Rec.709 Gamma 2.4` | ✅ |
| `inputDRT` / `outputDRT` | `None` | ✅ |
| LUT-Interpolation | **Tetraedrisch** (Banding-Gegenmaßnahme) | ❌ nur GUI |

⚠️ Wichtig für Node 1: FilmConvert erwartet **unveränderte native Log-Pixel**. Deshalb muss
das Projekt auf DaVinci YRGB stehen — unter Color Management würde Resolve das Bild vorher
transformieren und Nitrate bekäme kein Log mehr.

## Die Kette

| # | Node | Art | Aufgabe |
|---|---|---|---|
| 1 | **FilmConvert Nitrate** | OFX, geteilt | Log-Dekodierung + Filmstock + Korn in einem |
| 2 | **Belic Kontr WB** | Primär, lokal | Belichtung, Kontrast, Weißabgleich — das technische Fundament |
| 3 | **OSIRIS-Finish-LUT** | LUT, geteilt | kreativer Finish, in der Wirkung heruntergeregelt |
| 4 | **Gesicht einzeln** | Sekundär, lokal | einzelne überstrahlte Bildpartie zurücknehmen |
| 5 | **Film Look Creator** | OFX, geteilt | Lichthof (Halation) + Vignette |

Reihenfolge ist nicht beliebig: **Weißabgleich und Grundbelichtung stehen VOR der kreativen
LUT** (Node 2 vor Node 3), sonst verstärkt die LUT einen vorhandenen Farbstich mit.

### Node 1 — FilmConvert Nitrate (`com.rubbermonkey:filmconvertnitrate`)

Gemessene Parameter (Indizes so, wie sie im Grade-Body stehen):

```
Make               = 34        (Kamerahersteller)
Model              = 46        (Kameramodell)
Profile            = 4         (Log-Profil der Kamera)
ProfileID          = 1306
Film Stock         = 2         (Tungsten-Emulsion)
Grain Strength     = 15.0      Grain Size      = 1.0
Grain Shadows      = 1.54      Grain Midtones  = 16.3
Grain Mid Shadows  = 13.9      Grain Mid Highl = 10.5
Grain Highlights   = 1.05
OSC Grain Curve    = "0.0154|0.139|0.163|0.105|0.0105"
```

Exposure/Temp/Tint bleiben in Nitrate auf 0 — die Feinkorrektur passiert bewusst erst in Node 2.
Halation wird in Nitrate **nicht** genutzt (kostenpflichtig) → kommt kostenlos aus Node 5.

### Node 2 — „Belic Kontr WB" (Primärkorrektur, lokal, pro Dreh neu)

Gemessene Werte des Beispielprojekts (Anzeige-Skala wie im Panel):

```
gainM   = 0.9317      offsetR/G/B = 11.30  (neutral 25.0 → Schwarz heruntergezogen)
temp    = +60.76      toenung     = -19.05
```

Diese Zahlen sind **motivabhängig** und müssen pro Dreh neu bestimmt werden — sie stehen hier
nur als Größenordnung. Setzen per `rctl.py grade-set` (siehe unten).

Ziele: Schatten mit leichter „Bodenschwelle" (nicht auf 0 crushen), Lichter dürfen einzeln
anstoßen, aber keine Fläche flächig clippen. Hauttöne im Vectorscope auf die Skin-Tone-Linie.

### Node 3 — OSIRIS-Finish-LUT (geteilt)

```
LUT             = "VisionColor OSIRIS - Rec709 LUTs\PRISMO - Rec709.cube"
Key-Ausgabe-Gain = 0.40      (Param-ID 0x0c30001d)
```

Rec709-Variante der LUT, weil das Bild ab Node 1 bereits in Rec.709 vorliegt.
Bei 100 % Wirkung entsättigt die LUT deutlich zu stark („faded" statt „muted but rich") —
**35–45 % ist der bewährte Bereich**, hier 40 %.

### Node 4 — „Gesicht einzeln" (Sekundär, lokal) ⚠️ der einzige Handgriff

3D-Qualifizierer auf die überstrahlte Hautpartie + weiche Ellipsen-Maske (Power Window),
Kanten deutlich weichgezeichnet. Korrektur bewusst minimal:

```
gammaM = -0.0264     gainM = 0.9723     Key-Ausgabe-Gain = 0.141
```

**Nicht per Skript reproduzierbar** — Qualifizierer und Fensterposition hängen davon ab, wo
das Gesicht im Bild steht. Ein kopiertes Fenster landet bei anderem Motiv falsch.

### Node 5 — Film Look Creator (`com.blackmagicdesign.resolvefx.filmlook`, geteilt)

```
colourBlend      = 0.1705    filmLookBlend = 0.1705   effectsBlend = 1.0
halationIsEnable = 1         halationHue   = 0.5      halationSat  = 0.7054
vignetteIsEnable = 1
flPreSat = 0.7 · lumVsSat = 0.85 · satVsSat = 0.9 · flSplitToneBlend = 0.5
globalPreset = "GlobalPresetCustom"
```

Intensität/Radius von Lichthof und Vignette stehen **nicht** im Body → sie sind auf
Plugin-Standard. (Merksatz: im Grade-Body stehen **nur Nicht-Default-Werte**.)

Zwei getrennte Regler: „Farbüberblendung" steuert Film-Look/Farbe/Teiltonung,
„Effektüberblendung" steuert Vignette/Lichthof/Bloom/Korn — dadurch lässt sich gezielt nur
eine Gruppe wirken lassen.

## ⭐ Übertragen: die ganze Kette in einem Aufruf

**Verifiziert am 04.08.2026** (Resolve 21, Wegwerf-Projekt): Ein DRX überträgt Struktur,
**OFX-Plugins mit allen Parametern**, LUT-Zuweisung und sämtliche Reglerwerte 1:1 —
Laufzeit **0,04 s**.

```
# einmal sichern (aus dem fertigen Vorlagen-Clip)
py C:\claude\resolve-ctl\rctl.py grade-save kino_look.drx

# in ein anderes Projekt / auf andere Clips bringen
py C:\claude\resolve-ctl\rctl.py grade-apply <pfad>\kino_look.drx --clip 1
```

Fertige Vorlage + Anwendungsskript liegen im **eigenen Skill `resolve-kino-look`**
(`vorlagen/kino_look_fs7_v1.drx`, `apply_kino_look.py`, `drx_werte.py`).
Für Grading-Arbeit diesen Skill aufrufen — dort stehen auch alle gemessenen Parameterwerte.

Beobachtungen aus dem Test:
- Die geteilten Nodes kommen als `Shared Node 1/2/3` zurück — Struktur und Inhalt stimmen,
  die **Beschriftung** geht verloren. ⚠️ `SetNodeLabel` gibt es in der API **nicht**
  (nur `GetNodeLabel`) → Umbenennen geht nur in der GUI. Kosmetik, kein Bildunterschied.
- Node 3 hatte den LUT-Pfad danach korrekt gesetzt (`GetLUT` bestätigt).
- Node 4 kommt mit, aber Qualifizierer/Fenster passen nur zum Ursprungsmotiv → nach dem
  Übertragen neu ziehen lassen.

## Wer macht was — Aufwandsabschätzung

Faustregel: **Claude macht alles, was Zahl, Pfad oder Struktur ist. Der Nutzer macht alles,
was Zeigen oder Beurteilen ist.**

| Aufgabe | Claude per Skript | Mensch per Maus | Wer |
|---|---|---|---|
| Komplette 5-Node-Kette inkl. OFX/LUT/Werte anlegen | **0,04 s**, 1 Aufruf | 5–15 min je Clip | ✅ **Claude** |
| Kette auf alle Kameras/Clips verteilen | Schleife, Sekunden | ×N | ✅ **Claude** |
| Primärwerte setzen (Gain/Offset/Temp/Tint) | `grade-set`, exakt, Sekunden | Räder ziehen | ✅ **Claude** (Richtung vom Nutzer) |
| LUT tauschen, Wirkung/Key-Gain ändern | `rctl lut` + DRX-Param | schnell | ✅ Claude, exakter |
| OFX-Parameter ändern (Stock, Korn, Halation) | DRX-Param-Patch | Panel durchklicken | ✅ **Claude** |
| Projekt-Farbeinstellungen setzen | `SetSetting`, Sekunden | Dialog | ✅ **Claude** |
| Frame prüfen/vergleichen, Messwerte liefern | `rctl frame` + Analyse | Auge | ✅ **Claude** |
| **Node 4: Qualifizierer + Power Window + Tracking** | Computer-use: langsam, ungenau, motivabhängig | 1–3 min | ❌ **Mensch** |
| Nodes zu echten Shared Nodes verknüpfen | offen | Rechtsklick ×3 | ❌ **Mensch** |
| Nodes beschriften | `SetNodeLabel` existiert nicht | Doppelklick + tippen | ❌ **Mensch**, Kosmetik |
| LUT-Interpolation auf tetraedrisch | nicht in der API | 1 Klick | ❌ **Mensch**, einmalig |
| „Heller/dunkler? Look richtig?" | — | — | ❌ **Mensch** |

⛔ **Nicht per Computer-use nachbauen.** Die Kette per Maus zu klicken (OFX ziehen, Panels
durchsteppen, Zahlen tippen) dauert Claude weit über eine Stunde und ist fehleranfällig —
der DRX-Weg erledigt dasselbe in Sekundenbruchteilen. Computer-use nur dort, wo es keinen
Skriptweg gibt: **Node 4 und die Shared-Node-Verknüpfung** — und selbst die besser vom Nutzer.

## Ablauf für ein neues Projekt

1. Projekt-Farbeinstellungen setzen (Tabelle oben) — Claude, Sekunden.
2. LUT-Ordner prüfen, `proj.RefreshLUTList()` — Claude.
3. `apply_kino_look.py` auf die Quell-Timeline-Clips jeder Kamera — Claude, Sekunden.
4. Node 2 pro Kamera einmessen (Frame ziehen, Werte vorschlagen, `grade-set`) — Claude,
   **Richtung vom Nutzer bestätigen lassen** (Mitte-Frame, „heller/dunkler?").
5. Node 4 vom Nutzer ziehen lassen (Qualifizierer + Fenster), danach kann Claude die
   Korrekturwerte wieder numerisch setzen.
6. LUT-Interpolation auf tetraedrisch — Nutzer, 1 Klick.
7. Verifizieren: Frame rendern, Kameras gegeneinander messen (Bücherwand/neutrale Fläche).
