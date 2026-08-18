# Farbgebung: welcher Look-Skill wird genommen

**Stehende Antwort (Nutzer, 18.08.2026) — nicht mehr erfragen:**

| Rolle | Skill / Repo | Was es ist |
|---|---|---|
| ⭐ **Standard** | `resolve-kino-look-nodekette`<br>https://github.com/web594/resolve-kino-look-nodekette | Kino-Look als **4 Nodes**: Filmemulation · Weißabgleich+Helligkeit (regelbar) · Finish-LUT bei 40 % · Film-Look-Erzeuger (Halation/Vignette) |
| **Ersatz** | `resolve-lut-look-kette`<br>https://github.com/web594/resolve-lut-look-kette | Film-Look als **4 LUT-Nodes + 1 regelbarer Node**: Log→ARRI Rec.709 · Weißabgleich+Helligkeit · Rec.709→ARRI LogC · Filmemulation · Kino-Look |

**Immer zuerst die Nodekette bauen.** Die LUT-Kette ist die Rückfallmöglichkeit — sie wird
genommen, wenn einer dieser Fälle eintritt:

- die nötigen **OFX-Plugins fehlen** oder passen nicht zur Kamera (s. u.),
- ein **Vorgängerprojekt derselben Reihe** ist bereits auf der LUT-Kette aufgebaut
  (Folgen einer Reihe bleiben untereinander gleich),
- der **Nutzer wünscht sie ausdrücklich**, oder der Nodeketten-Look überzeugt am Bild nicht.

## Gekauft vor frei

Beide Ketten gibt es in einer **gekauften** und einer **freien** Fassung. **Zuerst immer die
gekauften LUTs und Werkzeuge verwenden** (Filmemulations-Plugin mit Kameraprofil,
gekaufte Finish-/Filmstock-LUTs) — sie sind aus echten Filmscans gemessen und in den Farben
feiner. Die freien Fassungen (`look_anwenden.py --frei` bzw. die selbst gerechneten LUTs) sind
kein Qualitätsziel, sondern der Weg, wenn ein Werkzeug auf dem Rechner fehlt, die Lizenz nicht
greift **oder die Kamera kein Profil im Plugin hat**. Beim Wechsel auf frei kurz sagen, warum.

## ⚠️ Vor jedem Look: prüfen, welche Kameras im Projekt liegen

Die Kette ist **nicht kameraunabhängig.** Die Filmemulation (FilmConvert Nitrate) rechnet gegen
ein **Kameraprofil**; ohne echtes Profil passt die Farbtransformation nicht zum Material und die
Farben werden unnatürlich (Nutzer-Erkenntnis 13.08.2026 an einem Rec.709-Camcorder-Dreh).

Die Kamera steht schon aus **Schritt 1** fest (ffprobe-Sichtung). Falls nicht, reicht:

```bash
ffprobe -v error -show_entries format_tags -show_entries stream=codec_name,pix_fmt,color_transfer -of default <datei>
```

| Material | Kamera (Beispiele) | Entscheidung |
|---|---|---|
| **Log**, XAVC/ProRes, S-Log3/S-Gamut3.Cine | Sony FS7 II (auch über Rekorder) | ✅ **Nodekette wie vorgesehen**, Filmemulation mit echtem Kameraprofil (Make Sony / Model FS7 / Profile S-Log3), volle Stärke |
| **Rec.709**, AVCHD/MTS oder XAVC S, Consumer-Camcorder | Sony AX100, CX900E **und ähnliche** | ⚠️ **Filmemulation gar nicht oder nur ganz wenig %** — Plugin auf „Default/Standard sRGB" verfälscht die Farben |
| **Rec.709**, andere Fremdkameras ohne Profil im Plugin | — | wie Zeile 2 behandeln |

**Regel für Rec.709-Consumer-Kameras:** Node 1 entweder **ganz weglassen** oder die Intensität
**stark herunterdrehen** (einstellige bis niedrig-zweistellige Prozent). Den Filmcharakter dann
über die übrigen Kettenglieder holen: Finish-LUT, Film-Look-Erzeuger (Halation/Vignette) und
Node 2. Die freie **Rec.709-Filmemulations-LUT** aus `resolve-kino-look-nodekette`
(`Filmemulation_Rec709_zu_Rec709.cube`) ist für solche Kameras oft die **bessere Wahl als das
Plugin** — sie braucht kein Kameraprofil. Alternativ auf die **LUT-Kette** wechseln.

⛔ **Look nie ungeprüft aus einem Projekt mit anderer Kamera übernehmen.** Liegen im selben
Projekt **verschiedene Kamera-Arten**, bekommt jede Kamera-Art ihre eigene Dosierung von Node 1;
gemeinsam bleiben nur die Nodes, die unabhängig vom Aufnahmeformat sind.

**Ergebnis immer am gerenderten Frame prüfen, nie am Viewer** (der cached).

## Was Claude macht, was der Nutzer macht

- **Claude:** Kamera-Art feststellen, Kette bauen und auf alle Kameras verteilen (per DRX in
  Sekundenbruchteilen), Projekt-Farbeinstellungen setzen (DaVinci YRGB, nicht Color Managed),
  Node 2 je Kamera **vorschlagen** und numerisch setzen, Frames messen.
- **Nutzer:** Richtung bei Helligkeit/Farbe („heller/dunkler?"), Qualifizierer und Power Windows,
  echtes Verknüpfen geteilter Nodes, LUT-Interpolation auf **tetraedrisch** (1 Klick, einmalig).

Beurteilt wird am **repräsentativen Frame aus der Mitte** eines Stücks, nicht am Anfang.

## Was bleibt in diesem Skill

`references/kino-look-nodekette.md` beschreibt die ältere **5-Node-Fassung mit Gesicht-Sekundär**
mit allen gemessenen Werten — sie ist die Herkunft der heutigen 4-Node-Kette und weiterhin die
genaueste Quelle für Parameterwerte, Projekt-Farbeinstellungen und die DRX-Technik.
Für die Look-Arbeit selbst den Standard-Skill oben aufrufen.
