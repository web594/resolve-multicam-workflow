# -*- coding: utf-8 -*-
"""Stabilisierte Fassung einer Kameradatei erzeugen (ausserhalb von Resolve).

Die gemessene Bewegung der statischen Hintergrundstruktur wird Frame fuer Frame
gegengerechnet - subpixelgenau, in 10 Bit, ohne Farbunterabtastung zu veraendern
(yuv422p10le rein wie raus). Ein winziger Zoom deckt die Raender ab.

Aufruf: py erzeugen.py <konfig.json>
"""
import os, sys, json, time, subprocess, numpy as np, cv2

BREITE, HOEHE = 3840, 2160
SPRUNG, MINABSCH, MAXPX = 2.5, 90, 6.0
ZOOM = 1.0035                      # deckt +-6 px Korrektur ab

def kurve(pfad):
    d = json.load(open(pfad))
    a = np.array([[v[1], v[2]] for v in d["werte"]], float)
    dx, dy = a[:, 0].copy(), a[:, 1].copy()
    for v in (dx, dy):
        m = np.isnan(v)
        if m.any(): v[m] = np.interp(np.flatnonzero(m), np.flatnonzero(~m), v[~m])
    spr = np.flatnonzero((np.abs(np.diff(dx)) > SPRUNG) | (np.abs(np.diff(dy)) > SPRUNG)) + 1
    g = [0]
    for x in [int(s) for s in spr] + [len(dx)]:
        if x - g[-1] < MINABSCH and x != len(dx): continue
        g.append(x)
    kx, ky = np.zeros(len(dx)), np.zeros(len(dy))
    for a0, b0 in zip(g, g[1:]):
        kx[a0:b0] = dx[a0:b0] - np.median(dx[a0:b0])
        ky[a0:b0] = dy[a0:b0] - np.median(dy[a0:b0])
    return np.clip(kx, -MAXPX, MAXPX), np.clip(ky, -MAXPX, MAXPX)

def lauf(quelle, mess, ziel, anz=None, start=0):
    kx, ky = kurve(mess)
    n_ges = anz or len(kx) - start
    yb, cb = BREITE*HOEHE*2, (BREITE//2)*HOEHE*2      # Bytes je Ebene (10 Bit in 16-Bit-Woertern)
    ein = ["ffmpeg", "-hide_banner", "-loglevel", "error"]
    if start: ein += ["-ss", f"{start/(30000/1001):.6f}"]
    ein += ["-i", quelle, "-frames:v", str(n_ges), "-f", "rawvideo",
            "-pix_fmt", "yuv422p10le", "-"]
    aus = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
           "-f", "rawvideo", "-pix_fmt", "yuv422p10le", "-s", f"{BREITE}x{HOEHE}",
           "-r", "30000/1001", "-i", "-"]
    if start: aus += ["-ss", f"{start/(30000/1001):.6f}"]
    aus += ["-i", quelle, "-map", "0:v", "-map", "1:a?", "-c:a", "copy",
            "-c:v", "prores_ks", "-profile:v", "2", "-vendor", "apl0",
            "-pix_fmt", "yuv422p10le", ziel]
    p_in = subprocess.Popen(ein, stdout=subprocess.PIPE, bufsize=yb*2)
    p_out = subprocess.Popen(aus, stdin=subprocess.PIPE, bufsize=yb*2)
    t0 = time.time(); n = 0
    while n < n_ges:
        by = p_in.stdout.read(yb)
        if len(by) < yb: break
        bu = p_in.stdout.read(cb); bv = p_in.stdout.read(cb)
        q = min(start + n, len(kx)-1)      # ausserhalb des Messbereichs: letzten Wert halten
        dx = float(kx[q]); dy = float(ky[q])
        Y = np.frombuffer(by, np.uint16).reshape(HOEHE, BREITE)
        U = np.frombuffer(bu, np.uint16).reshape(HOEHE, BREITE//2)
        V = np.frombuffer(bv, np.uint16).reshape(HOEHE, BREITE//2)
        # Zoom um die Bildmitte, danach die gemessene Bewegung gegenrechnen
        def M(w, h, fx):
            m = np.array([[ZOOM, 0, (1-ZOOM)*w/2 - dx*fx],
                          [0, ZOOM, (1-ZOOM)*h/2 - dy]], np.float32)
            return m
        Y2 = cv2.warpAffine(Y, M(BREITE, HOEHE, 1.0), (BREITE, HOEHE),
                            flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        U2 = cv2.warpAffine(U, M(BREITE//2, HOEHE, 0.5), (BREITE//2, HOEHE),
                            flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        V2 = cv2.warpAffine(V, M(BREITE//2, HOEHE, 0.5), (BREITE//2, HOEHE),
                            flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        p_out.stdin.write(Y2.tobytes()); p_out.stdin.write(U2.tobytes()); p_out.stdin.write(V2.tobytes())
        n += 1
        if n % 500 == 0:
            print(f"   {n}/{n_ges} ({n/(time.time()-t0):.1f} fps)", flush=True)
    p_in.stdout.close(); p_out.stdin.close(); p_in.wait(); p_out.wait()
    print(f"   fertig: {n} Frames in {(time.time()-t0)/60:.1f} min -> {ziel}", flush=True)

if __name__ == "__main__":
    for k in json.load(open(sys.argv[1], encoding="utf-8")):
        print(k["name"], flush=True)
        lauf(k["quelle"], k["mess"], k["ziel"], k.get("anz"), k.get("start", 0))
