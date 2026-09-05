# -*- coding: utf-8 -*-
"""Qualitaetspruefung Projekt-M Projekt-M: pro Cut-Segment den aktiven Winkel auf
Unschaerfe (Laplace-Varianz) und Wackeln (Frame-Differenz) messen - direkt aus den
Quelldateien (kein 6-h-Render noetig)."""
import json, subprocess, sys, numpy as np, os
FPS=30000/1001; W,H=480,270; N=6      # 6 Frames je Probe
MAP=json.load(open("quellmap.json",encoding="utf-8"))
CUT=json.load(open("cut_final.json",encoding="utf-8"))

def quelle(angle, frame):
    for c in MAP[angle]:
        if c["s"] <= frame < c["e"]:
            return c["f"], (c["off"] + frame - c["s"])/FPS
    return None, None

def probe(path, sek):
    cmd=["ffmpeg","-hide_banner","-loglevel","error","-ss",f"{max(sek,0):.3f}","-i",path,
         "-frames:v",str(N),"-vf",f"scale={W}:{H},format=gray","-f","rawvideo","-"]
    try:
        raw=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,timeout=120).stdout
    except subprocess.TimeoutExpired:
        return None
    n=len(raw)//(W*H)
    if n<2: return None
    f=np.frombuffer(raw[:n*W*H],dtype=np.uint8).astype(np.float32).reshape(n,H,W)
    lap=(f[:,1:-1,1:-1]*4 - f[:,:-2,1:-1]-f[:,2:,1:-1]-f[:,1:-1,:-2]-f[:,1:-1,2:])
    foc=float(np.median(lap.reshape(n,-1).var(axis=1)))
    mot=float(np.mean(np.abs(np.diff(f,axis=0)).mean(axis=(1,2))))
    hel=float(f.mean())
    return foc, mot, hel

def messen(angle, s, e, anteile=(0.3,0.7)):
    r=[]
    for a in anteile:
        fr=int(s+(e-s)*a)
        p,sek=quelle(angle,fr)
        if p is None: continue
        v=probe(p,sek)
        if v: r.append(v)
    if not r: return None
    return (float(np.median([x[0] for x in r])), float(np.max([x[1] for x in r])),
            float(np.mean([x[2] for x in r])))

if __name__=="__main__":
    res=[]
    for i,sp in enumerate(CUT):
        v=messen(sp["angle"], sp["s"], sp["e"])
        res.append(dict(i=i, a=sp["angle"], s=sp["s"], e=sp["e"],
                        foc=v[0] if v else None, mot=v[1] if v else None, hel=v[2] if v else None))
        if i%50==0:
            print(f"{i}/{len(CUT)}", flush=True)
    json.dump(res, open("qualitaet_roh.json","w"), indent=0)
    print("fertig")
