# Timecode-Sync statt Kreuzkorrelation (Atomos AirGlu)

**Variante zu Schritt 2.** Wenn die Kameras ueber Atomos-Rekorder mit **AirGlu** laufen,
tragen die Clips einen gemeinsamen Timecode. Dann entfaellt die Kreuzkorrelation fuer
diese Kameras -- die Offsets stehen direkt in den Dateien.

**Gilt nur fuer die Atomos-Rekorder.** Der Tonrekorder (dr10L/Tascam) kann kein AirGlu RF
und bleibt bei `sync.py`. Ebenso die parallelen internen Kamera-Aufnahmen (XDCAM-MXF) --
die tragen den Kamera-Timecode, nicht den des Netzes.

## Einrichtung an den Geraeten

Ein Geraet ist **Server**, alle anderen sind **Client**. Menue: `Sync Config`.

| Feld | Server | Client |
|---|---|---|
| Network Role | Server | Client |
| Start/Join Network | an | an |
| Region | **Europe** | **Europe** |
| RF Channel | frei waehlbar (z. B. 7) | **gleiche Zahl wie Server** |
| Record Control | an = REC am Server startet alle | -- |

Danach je Geraet `Timecode` -> `Source` -> **AirGlu SYNC**.

⭐ **Die Falle:** `AirGlu SYNC` erscheint in der Source-Liste **erst, wenn das Geraet im Netz
ist**. Vorher haengt Source auf `HDMI` fest und laesst sich nicht umstellen. Das wirkt wie eine
Sperre, ist aber nur die Reihenfolge: **erst Sync Config beitreten, dann Timecode-Source setzen.**

Weitere Punkte:
- **Region ab Werk „North America"** -- in Deutschland umstellen. Clients finden das Netz sonst nicht.
- **AirGlu BT** (`Pair`, „Free Pairs Available") ist etwas anderes -- Bluetooth. Die
  Shogun-zu-Shogun-Strecke laeuft ueber AirGlu **RF**, nicht BT.

## UltraSync BLUE als Bruecke zum Tonrekorder

⭐ **Der UltraSync BLUE hat sehr wohl ein RF-Modul** (Displayzeile `RF-Client`) -- er tritt dem
RF-Netz genauso bei wie ein Shogun-Client. Er muss **nicht** ueber Bluetooth an den Shogun
gekoppelt werden; das BT-Menue des BLUE ist fuer die andere Seite da.

Damit entsteht die Bruecke in die Tonwelt:

```
Shogun-Server --RF Kanal 7--+-- SHOGUN2 / SHOGUN3 / SHOGUN4
                            +-- UltraSync BLUE --BT--> Tonrekorder (Tascam FR-AV2)
```

Einstellen am BLUE: **Role `RF-Client`**, **Region CE**, **RF Channel = der des Servers**.
Die Displayzeile unten rechts codiert beides: `CE02` = Region CE, Kanal 02.

⭐ **Der haeufige Fehler:** BLUE ab Werk auf **Kanal 02**, Netz auf 07 -- er findet nichts und
zeigt eine frei laufende Eigenzeit. Sieht aus wie ein Kopplungsproblem, ist ein Kanalproblem.
Nicht im BT-Menue suchen. Haengt danach noch eine alte Kopplung quer: `Clear Pairings` + Neustart.

Erfolgskontrolle: der BLUE erscheint im Reiter `Sync Network` am Server als eigene Zeile
(24.08.2026: `Blue6785`, ID 4, Signal 98 %).

**Vor dem Dreh laden.** Der BLUE taucht in der Netzliste mit Akkustand auf -- steht dort 0 %,
faellt im Betrieb der Taktgeber fuer den Ton aus. Ebenfalls pruefen, ob im BLUE-Menue eine
Framerate einstellbar ist; sie muss zur Network FPS passen (in der Netzliste bleibt seine
FPS-Spalte leer, er hat keinen Videoeingang).

**Erst der Tonrekorder wird per Bluetooth gekoppelt** -- am `BLUETOOTH`-Menue des BLUE
(`Searching`), nicht am Shogun. Voraussetzung: der Recorder kann BLE-Timecode. Der
**Tascam FR-AV2** kann es; ein einfacher DR-10L ohne „Pro" nicht -- dort bliebe nur, den
Timecode als Tonsignal auf eine Spur zu legen.
- **Network FPS** gibt der Server vor. Kameras mit abweichender Bildrate synchronisieren nicht sauber.
- **Use Drop Frame**: auf allen Geraeten gleich. Gemischt ist der einzige Fall, der in Resolve
  wirklich Aerger macht. Standard: aus (Non-Drop).
- **Set Device Name** je Geraet vergeben (`nah`, `weit`, `seiteL`, `seiteR`). Sonst heissen alle
  „SHOGUNU", man sieht in der Netzliste nicht, welches abgerissen ist, und der Dateiname
  ist beim Einlesen nicht zuzuordnen.
- **Kontrolle waehrend des Drehs:** Reiter `Sync Network` am Server listet alle Clients mit
  FPS, Signal und Akku. Faellt ein Geraet aus, verschwindet die Zeile.

## Gegenprobe: `vorlagen/tc_pruefen.py`

Dem Timecode nicht blind vertrauen -- er wird gemessen, bevor darauf geschnitten wird.
Das Skript liest den eingebetteten Start-TC und vergleicht den daraus errechneten Versatz
mit dem tatsaechlichen Versatz aus dem Ton.

```
python tc_pruefen.py nah_T001.MOV weit_T001.MOV seiteL_T001.MOV
```

Erster Clip = Referenz, alle weiteren werden dagegen gemessen. Bewertung:

| Abweichung | Folge |
|---|---|
| < 1 Frame | Timecode-Sync belegt, Multicam per TC bauen |
| 1--3 Frames | grenzwertig, bei langen Aufnahmen gegenmessen |
| > 3 Frames | nicht verlassen, klassisch `sync.py` |

**Grenzen der Messung** -- beide gemessen am 24.08.2026:
- **Leiser Ton macht sie unsicher.** Guete = Spitze/Median der Korrelation; unter ~10 ist das
  Ergebnis nur ein Anhaltspunkt. Fuer einen harten Beleg beim Test einmal kraeftig klatschen.
- **Kurze Clips zeigen keinen Drift.** Bei mehrstuendigen Veranstaltungen zusaetzlich ein
  Clip-Paar vom **Ende** messen, nicht nur vom Anfang.

## Verwendung im Ablauf

`probe()` in `tc_pruefen.py` liefert `tc_sek` je Clip. Daraus die Offsets fuer Schritt 3
statt aus `offsets.json`:

```
off_sek = tc_sek[kamera] - tc_sek[leitkamera]
off_frames = round(off_sek * fps)
```

Vorzeichenregel wie gehabt (`ablauf.md` Schritt 3): positiver Offset = diese Quelle lief
spaeter los, ihr Kopf bleibt stehen und die Leitquelle wird getrimmt.

**Der Tonrekorder bleibt Zeitreferenz.** Er hat keinen gemeinsamen Timecode, also weiterhin
`sync.py` fuer ihn -- und damit gilt `TC - 108000 = Ton-Frame` unveraendert.

## Belegter Stand

24.08.2026, zwei Shogun Ultra (Server + Client, RF Channel 7, Region Europe, 29.97):
Timecode-Versatz +2,4004 s, per Ton gemessen +2,4152 s -> **Abweichung 14,8 ms = 0,44 Frames**.
Ton war sehr leise (RMS 10, Guete 18), 13-Sekunden-Clips -- also belegt fuer den Startversatz,
nicht fuer Drift ueber Stunden.
