# -*- coding: utf-8 -*-
"""Kachel-Schaerfe: robust gegen Bildinhalt. Ein scharfes Bild hat IRGENDWO
knackige Kanten; ein unscharfes nirgends. Metrik = 90%-Quantil der Kachelwerte."""
import json, subprocess, numpy as np, sys
import qual_projekt-m as q
W,H=960,540; TX,TY=12,9
def kachel(path, sek, n=2):
    cmd=["ffmpeg","-hide_banner","-loglevel","error","-ss",f"{max(sek,0):.3f}","-i",path,
         "-frames:v",str(n),"-vf",f"scale={W}:{H},format=gray","-f","rawvideo","-"]
    raw=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,timeout=180).stdout
    m=len(raw)//(W*H)
    if m<1: return None
    f=np.frombuffer(raw[:m*W*H],dtype=np.uint8).astype(np.float32).reshape(m,H,W)
    h,w=H//TY, W//TX; best=0.0
    for k in range(m):
        v=[]
        for i in range(TY):
            for j in range(TX):
                t=f[k, i*h:(i+1)*h, j*w:(j+1)*w]
                lap=(t[1:-1,1:-1]*4 - t[:-2,1:-1]-t[2:,1:-1]-t[1:-1,:-2]-t[1:-1,2:])
                v.append(lap.var())
        best=max(best, float(np.percentile(np.array(v),90)))
    return best
def segment(angle, s, e, anteile=(0.25,0.5,0.75)):
    r=[]
    for a in anteile:
        fr=int(s+(e-s)*a); p,sek=q.quelle(angle,fr)
        if p is None: continue
        v=kachel(p,sek)
        if v is not None: r.append(v)
    return None if not r else float(np.median(r))
if __name__=="__main__":
    A=json.load(open('qualitaet_alt.json'))
    for i,r in enumerate(A):
        r["k"]=segment(r["a"], r["s"], r["e"])
        if i%10==0: print(i,flush=True)
    json.dump(A, open('qualitaet_kachel.json','w'), indent=0)
    print("fertig")
