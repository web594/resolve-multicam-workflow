# Grafik-Einblendungen & Social-Auslieferung (Schritt 9)

Für **Vortrags-/Interview-Videos**, bei denen der Referent Fakten nennt, die man bebildern
kann — und für die Auslieferung als YouTube-Langversion + Instagram-Kurzversion.
Erarbeitet an Reihe-R #1/#2 (Juli 2026), gilt für alle weiteren Folgen derselben Reihe.

---

## 1. Erst analysieren, dann bauen — NICHT sofort losbauen

Der Nutzer will **zuerst wissen, wo welche Grafik empfohlen wird**, bevor etwas entsteht.
Reihenfolge:

1. **Timeline auslesen** (Spuren, Clips, Marker) → Lang-/Kurz-Bereich und Look-Ebene finden.
   Der Look kann als **Timeline-Grade** ODER auf einem **durchgehenden Anpassungsclip**
   liegen — beides ist gültig, nicht „korrigieren".
2. **Transkript (VTT) lesen** und die Stellen mit **konkreten Bild-Ankern** sammeln:
   Zahlen/Statistiken, Fachbegriffe, Aufzählungen, benannte Objekte.
   Rein persönliche/werbliche Passagen (Familie, Kurse, Anliegen) **nicht** bebildern.
3. **Vorhandene Einblendungen des Nutzers respektieren** — er legt oft schon welche selbst.
   Nur verschieben, wenn es erzählerisch klar besser ist, und das begründen.
4. **Verteilungsplan als Tabelle vorlegen** (Zeit | Frames | Grafik | neu/vorhanden) und
   **freigeben lassen**. Erst dann bauen.

**Faustregel Dichte:** nie 3 Vollbild-Grafiken direkt hintereinander — zwischen den Blöcken
Redner-Pausen von ≥5 s lassen.

---

## 2. Stil vom Nutzer übernehmen, nicht neu erfinden

Vorhandene Grafiken des Nutzers ansehen und **dieselbe Sprache** verwenden.
Bei Reihe-R etabliert (2304×1296, 16:9):

| Element | Wert |
|---|---|
| Hintergrund | radialer Verlauf `#050d1a` (Rand) → `#10284a` (Mitte) |
| Akzent Gold | `#E9A83C`, hell `#F7C460` |
| Text hell | Cremeweiß `#F3EDDF` |
| Fließtext | `#C8D4E2`, gedämpft `#96A8BE` |
| Display-Schrift | **Bebas Neue** (`BebasNeue-Regular.otf`) mit Buchstabenabstand |
| Fließschrift | Segoe UI / Segoe UI Semilight |

**Grafiken größer als die Timeline anlegen** (2304×1296 auf 1920×1080 = 1,2× Reserve) —
dann bleibt ein späterer Resolve-Zoom scharf.

### Zwei Grafik-Typen — klare Arbeitsteilung

| Typ | Wer baut | Vorgehen |
|---|---|---|
| **Daten-/Typo-Grafik** (Statistik, Begriffe, Vergleich) | **Claude** komplett | Pillow-Skript, 2× Supersampling, dann auf Zielgröße runterskalieren |
| **Fotorealistische Illustration** (Körper, Objekte, Szenen) | **Nutzer** generiert per KI | Claude schreibt den Prompt, Nutzer erzeugt, Claude legt Text darüber |

**KI-Prompt-Regeln** (haben sich bewährt):
- Illustration **OHNE jeden Text** anfordern („no text, no captions, no watermark").
- **Ein Bilddrittel bewusst frei lassen** für die späteren Labels.
- Farbwelt + Hintergrund exakt vorgeben (Hex-Werte), Format 16:9 nennen.
- Prompt als `.txt` in den Projektordner legen, damit der Nutzer ihn direkt nutzen kann.

**Labels exakt an Anschlusslinien setzen:** Endpunkte der goldenen Linien **programmatisch
messen** statt schätzen — Goldmaske per numpy, rechte Bildhälfte, je Zeile das maximale x,
dann nach y clustern:

```python
gold=(r>120)&(g>70)&(b<100)&(r>b+60)      # Goldton
mask=gold.copy(); mask[:, :int(W*0.50)]=False
# je Bildzeile max. x -> Cluster mit y-Abstand < 30 = ein Linienende
```

---

## 3. ⭐ Zoom-Sicherheit — gilt für TEXT **und** BILD

Wenn die Grafik später (in Resolve) reingezoomt wird, schneidet ein 110 %-Zoom je Rand
**~4,55 %** ab. Alles Wichtige muss in den **mittleren ~86 %** liegen.

**Häufigster Fehler:** nur den Text prüfen. Bei einer KI-Illustration, die bis an die
Bildkante reicht, wurden Kopf und Füße abgeschnitten.

**Fix für fertige Bilder:** `py overlay_tools.py zoomsafe bild.png aus.png` — verkleinert den Inhalt auf 90 %,
ergänzt den Hintergrund als radialen Verlauf aus den **echten Randfarben** des Bildes und
blendet die Kanten weich ein (feather 26 px) → nahtlos.

**Immer verifizieren** (numpy-Bounding-Box des Inhalts gegen den sichtbaren Bereich):

```python
cut=int(H*0.0455); cutx=int(W*0.0455)
ok = ys.min()>=cut and ys.max()<=H-cut and xs.min()>=cutx and xs.max()<=W-cutx
```

---

## 4. ⭐⭐ Zoom NICHT in ffmpeg einbacken — er zittert

`zoompan` rundet die Bildposition pro Frame auf **ganze Pixel** → sichtbares Zittern
(auch mit 2× Supersampling). Der Nutzer sieht das sofort.

**→ Grafiken IMMER statisch liefern, den Zoom setzt der Nutzer in Resolve** (subpixel-genau).

Falls doch einmal ein gebackener Zoom gewünscht ist: **niemals linear**. Der Nutzer will
eine weiche S-Kurve (sanft anfahren, weich auslaufen) = **Smootherstep** `T³(T(6T−15)+10)`,
wobei `T` = `(on/<N−1>)`. In der ffmpeg-Expression **keine Kommas / kein `pow()`** benutzen
(bricht die Filter-Syntax) — nur Multiplikation. Prüfen durch Schrittweiten-Messung an einer
harten Kante: das Profil muss glockenförmig sein.

---

## 5. ⭐ Overlay-Dauer: PNG → ProRes-MOV (die Still-Falle)

`AppendToTimeline` platziert importierte **Standbilder** nur mit der Standard-Still-Dauer
(5 s) — `endFrame` wird **ignoriert**, `SetClipProperty('Frames')` geht nicht, und die
Still-Dauer ist nur eine App-Preference (kein Project-Setting).

**Lösung:** PNG per ffmpeg in ein ProRes-MOV mit **exakter Frameanzahl** wandeln, dann
respektiert `AppendToTimeline` das `endFrame`. Werkzeug: `vorlagen/overlay_tools.py`.

```bash
# Vollbild ohne Alpha (422 HQ)
ffmpeg -y -loop 1 -i bild.png -r 30000/1001 -frames:v 264 \
  -c:v prores_ks -profile:v 3 -pix_fmt yuv422p10le out.mov

# Mit Transparenz, z. B. Lower-Third (4444) — Resolve erkennt Alpha automatisch
ffmpeg -y -loop 1 -i bild.png -r 30000/1001 -frames:v 300 \
  -c:v prores_ks -profile:v 4444 -pix_fmt yuva444p10le out.mov
```

Platzieren:

```python
mp.AppendToTimeline([{'mediaPoolItem':it,'startFrame':0,'endFrame':N-1,
                      'trackIndex':4,'recordFrame':<Timeline-Frame>,'mediaType':1}])
```

**Datei ersetzt?** Resolve hält die alte Version im Cache → Timeline-Clip **und**
MediaPool-Item löschen, neu importieren, neu platzieren.

**⭐ Nie lose in Master-Root importieren — immer in den Projekt-Unterordner, mit
Kurzhinweis im Comments-Feld.** Erst per Hand (29.07.2026) aufgeräumt, weil sich
Grafiken aus #1–#4 alle unsortiert in Master-Root stapelten und `place`s
Namensabgleich (s. u.) prompt eine fremde Folge überschrieben hat. `overlay_tools.py
place` erledigt beides automatisch:
- **Zielordner** = Elternordner-Name der Quelldatei (z. B. `.../#3 Thema-Y/xxx.mov`
  → Mediathek-Unterordner „#3 Thema-Y"; wird angelegt, falls er fehlt).
- **`--fuer "kurzer Hinweis"`** schreibt ins `Comments`-Feld des Clips (in der
  Mediathek als Spalte einblendbar), z. B. `"#3 Thema-Y, ab 0:41 - Aufbau
  Thema-Y"`. Ohne Angabe wird automatisch `Timeline @ Frame X (Track Y)`
  eingetragen — besser als nichts, aber ein sprechender Hinweis ist klarer.

```bash
py overlay_tools.py place g3_aufbau_Thema-Y.mov --timeline 19 --track 4 --at 1433 \
  --frames 359 --fuer "#3 Thema-Y, ab 0:41 - Aufbau Thema-Y im Schnitt"
```

**⭐⭐ Falle (gefunden 29.07.2026):** Der Duplikat-Check vor dem Import darf **nur
denselben Dateipfad** treffen, nicht bloß denselben Dateinamen — sonst löscht eine
spätere Folge (die dieselbe `g1_…, g2_…`-Konvention nutzt) die gleichnamige Datei
einer ANDEREN Folge aus der Mediathek, und Resolves automatisches
Offline-Relink-per-Dateiname biegt die alte Timeline dann still auf die neue,
falsche Datei um. Ist in `overlay_tools.py` (Pfadvergleich statt Namensvergleich)
längst behoben — Details in `fallstricke.md`.

**Prüfen:** `rctl.py frame out.png` zeigt (Resolve 21.0.3, 29.07.2026 nachgemessen) das
**fertige Timeline-Bild inklusive der Overlays auf den oberen Spuren** — Vollbild-Grafiken
und Alpha-Lower-Thirds sind darauf zu sehen. Damit lässt sich die Platzierung ohne
Screenshot und ohne dem Nutzer den Fokus zu klauen kontrollieren: mehrere Zeitpunkte
exportieren und als Kontaktbogen zusammensetzen. (Frühere Fassung dieses Skills behauptete
das Gegenteil.)

---

## 6. Auslieferung

### Instagram-Kurzversion (9:16)

⭐ **Seit #3 (28.07.2026) macht das `vorlagen/instagram_kurz.py` komplett allein:**
Spalte nachmessen → Crop + Skalieren + ASS einbrennen → Musik-Check → −14 LUFS
zweistufig → `ffmpeg Anweisung …txt` mit den echten Messwerten schreiben.

```bash
py instagram_kurz.py "<hochf angez>.mp4" --ass kurz_sub.ass --titel "#3"
```

Es bricht mit klarer Meldung ab, wenn die Quelle gar keine weißen Balken hat (also
nicht die „hochf angez"-Fassung ist). Das Folgende ist die Handarbeit dahinter.

Bild-/Positionsanpassungen lassen sich **nicht** aus der 16:9-Timeline in eine vertikale
Timeline übernehmen. Deshalb: Kurzbereich aus der 16:9-Timeline als **„hochf angez"**
rendern (Hochformat mittig zwischen weißen Balken, 4K, bereits gegradet, Musik drin),
dann per ffmpeg die mittlere Spalte croppen.

**Crop immer nachmessen, nie Werte übernehmen** — weiße Balken per Zeilen-Scan finden:

```python
row=a[H//2]; white=(row[:,0]>235)&(row[:,1]>235)&(row[:,2]>235)
n=np.where(~white)[0]   # -> crop=<Breite>:<H>:<n.min()>:0
```

```bash
ffmpeg -y -i "<hochf angez>.mp4" \
 -vf "crop=1216:2160:1312:0,scale=1080:1920,subtitles=kurz_sub.ass" \
 -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p -c:a copy -movflags +faststart out.mp4
```

**Ist Musik schon in der Tonspur?** → `silencedetect=noise=-45dB:d=0.4`; **keine Treffer**
= durchgehender Ton = Musik drin → `-c:a copy`. Sonst Musik per `amix` zumischen
(`volume=-20dB` unter der Stimme).

### Untertitel (ASS)
Stil-Vorlage steht im Memory `Reihe-R-projekt` (Candara 68, weicher Schatten,
`\blur7\fad(200,150)` + Größerwerden 96→100 %). **Kein `fontsdir`** angeben — sonst fällt
libass auf eine Ersatzschrift zurück. Whisper-Fehler vor dem Einbrennen korrigieren
(z. B. „Route/Routengeher" → „Rute/Rutengeher"). Text **kürzen und zuspitzen**, nicht das
Roh-Transkript übernehmen.

### Lautheit −14 LUFS (immer als letzter Schritt, Bild verlustfrei)
Resolves „Audiopegel normalisieren" trifft die −14 nicht. Stattdessen **zweistufig**:

```bash
ffmpeg -i IN.mp4 -af "loudnorm=I=-14:TP=-1:LRA=11:print_format=json" -f null -
ffmpeg -y -i IN.mp4 -c:v copy -af "loudnorm=I=-14:TP=-1:LRA=11:measured_I=…:measured_TP=…:measured_LRA=…:measured_thresh=…:offset=…:linear=true" -c:a aac -b:a 320k -movflags +faststart OUT.mp4
```

**Zum Schluss eine `ffmpeg Anweisung …txt`** in den Projektordner legen — mit den
tatsächlich benutzten Befehlen und Messwerten, damit der Nutzer sie wiederholen kann.

---

## Checkliste vor „fertig"

**Ein Befehl deckt die halbe Liste ab** (seit 29.07.2026):

```bash
py vorlagen/verify_overlays.py --timeline 19 --ende 5962 --ref 12
```

Er findet automatisch: **Schwarzbild-Löcher** (frameweise über ALLE Videospuren —
Anpassungsclips zählen nicht als Bild; genau so wurde das 1-Frame-Loch vor der
Endkarte in #3 gefunden), Überlappungen, **echte** Offline-Clips (Datei fehlt —
Generatoren/Fusion-Clips ohne MediaPoolItem sind KEIN Offline), Ton-Deckung bis zum
Soll-Ende (ist die Endkarte stumm?) und mit `--ref` den **1-Frame-Sync-Versatz der
Sprachspur** nach einem eingefügten Kaltstart.

- [ ] `verify_overlays.py` läuft ohne `[!]`
- [ ] Verteilungsplan war freigegeben
- [ ] Overlay-Dauern stimmen (Frames nachzählen, nicht auf Still-Standard hereinfallen)
- [ ] Overlays im Bild geprüft — `rctl.py frame` zeigt die oberen Spuren mit (s. Abschnitt 5),
      mehrere Zeitpunkte als Kontaktbogen, ohne dem Nutzer den Fokus zu nehmen
- [ ] Grafiken **statisch** geliefert (Zoom macht der Nutzer in Resolve)
- [ ] Clips liegen im **Projekt-Unterordner** der Mediathek, mit `--fuer`-Hinweis
- [ ] Projekt gespeichert (`pm.SaveProject()`)
- [ ] Nicht mehr benötigte Zwischendateien **benennen, nicht ungefragt löschen**
- [ ] **Render-Bereiche genannt** (Lang mit/ohne Endkarte, Kurz) — der Nutzer rendert selbst

---

## 8. Das Auslieferungspaket — ungefragt mitliefern

Bei #3 hat der Nutzer jeden dieser Punkte einzeln nachgefordert. Sie sind bei jeder
Folge gleich, also von vornherein mitbauen (siehe SKILL.md, stehende Antwort 11):

| Teil | Wie |
|---|---|
| **Titelbild** | `make_thumb.py` als `make_thumb_<folge>.py` kopieren, Block EINSTELLUNGEN anpassen. Standbild per `rctl.py frame` aus der **gegradeten** Timeline an einer Stelle **ohne Overlay** ziehen; Motiv mit freier linker Bildhälfte und offenen Augen (mehrere Zeitpunkte als Kontaktbogen vergleichen). **⭐ KOPF IMMER FREIHALTEN — NIE Text über Kopf/Stirn/Gesicht der Hauptperson** (Hintergrundpersonen ok). Der Generator hat dafür `KOPF_FREI_FRAC` (rechte Textkante als Breitenanteil) — bei mittig/links stehender Person auf den Kopf-Beginn verkleinern (Kicker wird per `fit_track` mitverkleinert), das Ergebnis-Bild danach **immer ansehen und prüfen**, ob wirklich nichts den Kopf berührt. Siehe Memory [[titelbild-kopf-freihalten]]. |
| **YouTube-Texte** | `YouTube Beschreibung <folge>.txt`: 3 Titelvarianten (konkreter, im Video gedeckter Aspekt statt Parole), Kapitelmarken ab 0:00, Beschreibung, angehefteter Kommentar, Tags, Quellenliste der eingeblendeten Zahlen. |
| **Endkarte** | Letzte Grafik: Verweis auf die Vorgängerfolge + Angebot + Website. **Hinter** dem letzten O-Ton-Clip platzieren heißt: Renderbereich verlängern UND Musik drunterlegen, sonst läuft sie stumm — und die Blende muss das Bild **überlappen**, sonst schwarzes Loch. |
| **Cross-Link** | Kleines Alpha-Lower-Third „→ Teil N: <Thema>" an einer inhaltlich passenden Stelle. |
| **Kaltstart** | Nur Marker + Anleitung, siehe SKILL.md, stehende Antwort 12. |
| **ANLEITUNG-Datei** | Alle Frames, Zahlenquellen, nächste Schritte, Render-Bereiche. Bei mehreren Timeline-Fassungen die **Frame-Verschiebung** dazuschreiben. |

---

## 7. Vertikale Balance — seit #3 AUTOMATISCH, nicht mehr nachmessen

Beim Bauen entsteht sonst zu viel Luft **oben** und zu wenig **unten**: der Titel sitzt
auf fester Höhe, die Bildunterschrift wird ans Ende gesetzt. Bei #3 hatten sechs von
sieben Vollbild-Grafiken 147 px Rand oben, aber nur 68–102 px unten — der Nutzer sah es
sofort und musste zweimal nachfragen.

**⭐ Erledigt das Stil-Modul jetzt selbst** (`vorlagen/infografik/stil_modul.py`):
`save()` hat **`center=True` als Standard** — es misst die Inhalts-Bounding-Box gegen den
gerenderten Hintergrund und schiebt so, dass Rand oben == Rand unten. Verifiziert an allen
neun #3-Grafiken (Abweichung 0–1 px). Die Konsolenzeile nennt die Ränder zur Kontrolle.

```python
save(img, "g8_sorge_strahlung.png")                 # zentriert automatisch
save(img, "g1_fachbegriffe.png", alpha=True, lower_third=True)   # Panel bleibt unten
save(img, "g3_aufbau.png", center=False)            # nur wenn eigene DY-Konstanten drin
```

- **`lower_third=True`** für Alpha-Panels: kein Zentrieren (das Panel MUSS unten sitzen)
  und kein Zoom-Check (der Verlauf darf an die Kante).
- **`dy=`** nur noch für Feinkorrektur zusätzlich zum Zentrieren.
- **`center=False`** nur, wenn das Skript schon eigene Verschiebungs-Konstanten hat —
  sonst zieht beides gegeneinander.

**Reicht gleichmäßiges Zentrieren nicht**, weil zusätzlich ein Element klebt (bei #3
lagen zwischen Erdreich-Block und Bildunterschrift nur 9 px), dann getrennte
Verschiebungen als Konstanten oben ins Skript (`DYT` Titel, `DY` Hauptgrafik,
`DYC` Bildunterschrift), auf die Koordinaten addieren und `center=False` setzen.

**⭐ Austauschen ohne die Arbeit des Nutzers zu zerstören:** Wenn der Nutzer schon
weiche Blenden oder Fusion-Zooms auf die Clips gelegt hat, **NICHT** löschen und neu
platzieren — das nimmt die Übergänge mit. Stattdessen die neue Datei unter neuem
Namen bauen und am Media-Pool-Item ersetzen:

```python
mediaPoolItem.ReplaceClip(r"...\g8_sorge_strahlung_v2.mov")
```

Position, Dauer, Blenden, Fusion-Comp und Transform bleiben unangetastet, und alle
Timelines, die den Clip nutzen, werden gleichzeitig aktualisiert (verifiziert
29.07.2026, Resolve 21.0.3, 6 Grafiken auf zwei Timelines).
