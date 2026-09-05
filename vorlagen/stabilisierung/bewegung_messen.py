# -*- coding: utf-8 -*-
"""Bildbewegung an statischer Struktur messen - schnelle Fassung.

ffmpeg liefert nur das Fenster um die Strukturen (statt 4K), innerhalb dessen eine Maske
die erlaubten Boxen freigibt. Getrackt wird gegen einen FESTEN Referenzframe (driftfrei),
mit Vorwaerts-Rueckwaerts-Pruefung und Ausreisserfilter.
"""
import subprocess, sys, json, time, numpy as np, cv2
FPS = 30000/1001
CLAHE = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
LK = dict(winSize=(41, 41), maxLevel=4,
          criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 40, 0.01))

def refbild(datei, f, fenster):
    fx, fy, fw, fh = fenster
    cmd = ["ffmpeg","-hide_banner","-loglevel","error","-ss",f"{f/FPS:.6f}","-i",datei,
           "-frames:v","1","-vf",f"crop={fw}:{fh}:{fx}:{fy},format=gray","-f","rawvideo","-"]
    b = subprocess.run(cmd, capture_output=True).stdout[:fw*fh]
    return CLAHE.apply(np.frombuffer(b, np.uint8).reshape(fh, fw))

def lauf(datei, start_f, anz, fenster, boxen, out, name="", ref_f=None):
    fx, fy, fw, fh = fenster
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error",
           "-ss", f"{start_f/FPS:.6f}", "-i", datei, "-frames:v", str(anz),
           "-vf", f"crop={fw}:{fh}:{fx}:{fy},format=gray", "-vsync", "0", "-f", "rawvideo", "-"]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=fw*fh*4)
    maske = np.zeros((fh, fw), np.uint8)
    for (x, y, w, h) in boxen:
        maske[max(0,y-fy):y-fy+h, max(0,x-fx):x-fx+w] = 255
    maske0 = None
    ref = p0 = None; res = []; n = 0; t0 = time.time()
    if ref_f is not None:
        ref = refbild(datei, ref_f, fenster)
    while True:
        b = p.stdout.read(fw*fh)
        if len(b) < fw*fh: break
        g = CLAHE.apply(np.frombuffer(b, np.uint8).reshape(fh, fw))
        if p0 is None:
            if ref is None: ref = g
            p0 = cv2.goodFeaturesToTrack(ref, 500, 0.01, 20, mask=maske, blockSize=7)
            print(f"   {name}: {len(p0)} Referenzpunkte", flush=True)
        if True:
            p1, st, _ = cv2.calcOpticalFlowPyrLK(ref, g, p0, None, **LK)
            pr, st2, _ = cv2.calcOpticalFlowPyrLK(g, ref, p1, None, **LK)
            ok = (st.ravel()==1)&(st2.ravel()==1)& \
                 (np.linalg.norm((pr-p0).reshape(-1,2),axis=1) < 0.5)
            d = (p1-p0).reshape(-1,2)[ok]
            if len(d) >= 8:
                med = np.median(d, axis=0)
                gut = np.linalg.norm(d-med, axis=1) < 2.0
                dd = d[gut] if gut.sum() >= 8 else d
                res.append((n, float(np.median(dd[:,0])), float(np.median(dd[:,1])), len(dd)))
            else:
                res.append((n, float('nan'), float('nan'), len(d)))
        n += 1
        if n % 2000 == 0:
            print(f"   {name}: {n}/{anz} ({n/(time.time()-t0):.1f} fps)", flush=True)
    p.stdout.close(); p.wait()
    json.dump({"datei": datei, "start": start_f, "anz": n,
               "werte": [[v[0], round(v[1],4), round(v[2],4), v[3]] for v in res]},
              open(out, "w"), indent=0)
    a = np.array([[v[1],v[2]] for v in res], float); m = ~np.isnan(a[:,0])
    print(f"   {name}: {n} Frames in {time.time()-t0:.0f}s | x-Spanne {np.ptp(a[m,0]):.2f} px, "
          f"y-Spanne {np.ptp(a[m,1]):.2f} px | ungueltig {(~m).sum()}", flush=True)

if __name__ == "__main__":
    for k in json.load(open(sys.argv[1], encoding="utf-8")):
        lauf(k["datei"], k["start"], k["anz"], k["fenster"], k["boxen"], k["out"], k["name"], k.get("ref_f"))
