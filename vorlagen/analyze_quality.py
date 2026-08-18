# -*- coding: utf-8 -*-
"""Schnitt-Render (mc_check.mp4) pro Cut-Segment auf Unschaerfe (Laplace-Varianz)
und Bewegung (Frame-Differenz) pruefen. Findet Segmente, deren aktiver Winkel
auffaellig schlechter ist als der Kamera-Normalwert."""
import subprocess, json, numpy as np, sys
MP4=r"C:\Users\<benutzer>\AppData\Local\Temp\claude\C--claude\d77fb14d-1b80-456d-9d02-6b368742b11b\scratchpad\mc_check.mp4"
PLAN=json.load(open(r"C:\claude\resolve-prep\projekt-a\cut_plan.json",encoding="utf-8"))
FPSs=4; W,H=480,270           # Sample-fps und Analyse-Groesse
CAMLEN={"nah":196207,"weit":196440}; FPS=30000/1001

cmd=["ffmpeg","-hide_banner","-loglevel","error","-i",MP4,
     "-vf",f"fps={FPSs},scale={W}:{H},format=gray","-f","rawvideo","-"]
p=subprocess.Popen(cmd,stdout=subprocess.PIPE)
fsz=W*H
foc=[]; mot=[]; prev=None
i=0
while True:
    buf=p.stdout.read(fsz)
    if len(buf)<fsz: break
    f=np.frombuffer(buf,dtype=np.uint8).astype(np.float32).reshape(H,W)
    lap=(f[1:-1,1:-1]*4 - f[:-2,1:-1]-f[2:,1:-1]-f[1:-1,:-2]-f[1:-1,2:])
    foc.append(float(lap.var()))
    mot.append(0.0 if prev is None else float(np.abs(f-prev).mean()))
    prev=f; i+=1
p.wait()
foc=np.array(foc); mot=np.array(mot); t=np.arange(len(foc))/FPSs
print(f"Frames analysiert: {len(foc)} ({t[-1]:.0f}s)")

# Segment-Aggregation (Boundary 0.4s ausschliessen wg. Schnitt-Sprung)
segs=[]
for sp in PLAN:
    a=sp["angle"]; s=sp["start"]; e=min(sp["end"], CAMLEN[a]/FPS)
    if e<=s: continue
    m=(t>=s+0.4)&(t<=e-0.4)
    if m.sum()<2: m=(t>=s)&(t<=e)
    if m.sum()<1: continue
    segs.append({"a":a,"s":s,"e":e,"dur":e-s,
                 "foc":float(np.median(foc[m])),
                 "mot":float(np.percentile(mot[m],80)),
                 "n":int(m.sum())})

for cam in ("nah","weit"):
    fv=np.array([g["foc"] for g in segs if g["a"]==cam])
    mv=np.array([g["mot"] for g in segs if g["a"]==cam])
    fmed=np.median(fv); mmed=np.median(mv)
    print(f"\n=== {cam}: Segmente {len(fv)}  Schaerfe-Median {fmed:.1f}  Bewegung-Median {mmed:.2f}")
    # unscharf: Schaerfe < 55% des Kamera-Medians ; wackelig: Bewegung > 2.2x Median
    for g in segs:
        if g["a"]!=cam: continue
        blur = g["foc"] < 0.55*fmed
        shake= g["mot"] > max(2.2*mmed, mmed+3)
        if blur or shake:
            tag=("UNSCHARF " if blur else "")+("WACKELT" if shake else "")
            mm=int(g["s"]//60); ss=int(g["s"]%60)
            print(f"  {mm:02d}:{ss:02d}  dur {g['dur']:4.1f}s  Schaerfe {g['foc']:5.1f} (Cam-Med {fmed:.0f})  Bew {g['mot']:4.1f}  -> {tag}")
