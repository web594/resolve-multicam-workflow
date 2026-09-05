# -*- coding: utf-8 -*-
"""Wurde eine Kamera von den Gesichtern her zu hell aufgenommen?

Misst im ROHMATERIAL (S-Log3, ungegradet) an mehreren Zeitpunkten:
  * Hautton-Pixel (nur obere Bildhaelfte, damit der Holzboden nicht mitzaehlt)
  * wie hoch die Gesichter auf der Skala sitzen
  * ob ueberhaupt etwas anschlaegt (Clipping) - Fenster werden getrennt ausgewiesen
Ausgabe: Tabelle je Zeitpunkt und je Kamera."""
import os, subprocess, json
import numpy as np

BASE = r"C:\claude\resolve-prep\projekt-m"
ROOT = r"E:\Projekt-M Projekt-M"
FPS = 30000/1001
CAMDIR = {"nah": "k1 nah", "weit": "k2 weit", "seite": "k3 seite"}
OFFJ = json.load(open(os.path.join(BASE, "offsets_blocks.json"), encoding="utf-8"))["blocks"]
TON = os.path.join(ROOT, "t1 Hauptton")


def ffdur(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                 "-of", "csv=p=0", p], capture_output=True, text=True).stdout)


tondur = [ffdur(os.path.join(TON, f"00{i}_330715.wav")) for i in (1, 2, 3, 4)]
bstart = [0.0]
for d in tondur[:-1]:
    bstart.append(bstart[-1] + d)

# Teil-Dateien je Kamera/Block mit Laengen
teile = {}
for b in "1234":
    for cam, d in OFFJ[b]["kameras"].items():
        lst = []
        for n in d["teile"]:
            f = os.path.join(ROOT, CAMDIR[cam], n)
            lst.append((f, ffdur(f)))
        teile[(cam, b)] = (lst, d["offset_s"])


def quelle(cam, tsec):
    """Ton-Sekunde -> (Datei, Position in der Datei) fuer diese Kamera."""
    for bi, b in enumerate("1234"):
        b0 = bstart[bi]; b1 = b0 + tondur[bi]
        if not (b0 <= tsec < b1): continue
        lst, off = teile[(cam, b)]
        camzeit = (tsec - b0) - off          # off negativ = Kamera lief vorher
        if camzeit < 0: return None
        for f, dur in lst:
            if camzeit < dur: return f, camzeit
            camzeit -= dur
        return None
    return None


def frame(f, pos):
    q = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{pos:.3f}", "-i", f, "-frames:v", "1",
                        "-vf", "scale=640:360", "-pix_fmt", "rgb24", "-f", "rawvideo", "-"],
                       capture_output=True)
    if len(q.stdout) < 640*360*3: return None
    return np.frombuffer(q.stdout, dtype=np.uint8).astype(float).reshape(360, 640, 3)


ZEITEN = [1200, 2400, 3300, 4200, 5200, 6500, 7600, 8800, 9800, 11000, 12500,
          13900, 15200, 16300, 17500, 19200, 20500, 21300]

print("Rohmaterial (S-Log3, ungegradet). Werte 0-255.")
print(f"{'Ton-Zeit':>9} {'Kamera':<6} {'Haut n':>7} {'Haut-Median':>12} {'Haut-p90':>9} "
      f"{'Bild-p99':>9} {'>250 %':>7}")
sam = {c: [] for c in CAMDIR}
for t in ZEITEN:
    for cam in ("nah", "weit", "seite"):
        q = quelle(cam, t)
        if not q:
            print(f"{t:9d} {cam:<6}   (keine Aufnahme)"); continue
        im = frame(*q)
        if im is None:
            print(f"{t:9d} {cam:<6}   (Frame nicht lesbar)"); continue
        r, g, bl = im[..., 0], im[..., 1], im[..., 2]
        y = 0.2126*r + 0.7152*g + 0.0722*bl
        mx = im.max(2); mn = im.min(2)
        sat = (mx-mn)/np.maximum(mx, 1)
        oben = np.zeros_like(y, dtype=bool); oben[:int(360*0.55), :] = True
        haut = (r > g) & (g > bl) & (sat > 0.06) & (sat < 0.45) & (y > 30) & (y < 250) & oben
        n = int(haut.sum())
        if n < 200:
            print(f"{t:9d} {cam:<6} {n:7d}   (zu wenig Hautflaeche)"); continue
        med = float(np.median(y[haut])); p90 = float(np.percentile(y[haut], 90))
        p99 = float(np.percentile(y, 99)); clip = float((y > 250).mean()*100)
        sam[cam].append(med)
        print(f"{t:9d} {cam:<6} {n:7d} {med:12.1f} {p90:9.1f} {p99:9.1f} {clip:7.2f}")

print("\nZusammenfassung Hautton-Median im Rohmaterial:")
for cam in ("nah", "weit", "seite"):
    v = np.array(sam[cam])
    if len(v):
        print(f"  {cam:<6} n={len(v):2d}  Median {np.median(v):5.1f} "
              f"({np.median(v)/2.55:4.1f} %)  Spanne {v.min():.0f}-{v.max():.0f}")
