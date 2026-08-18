# -*- coding: utf-8 -*-
"""Sync-Offsets weit/seite gegen Hauptton dr10L (001_181212.wav) per Onset-Kreuzkorrelation.
Extrahiert Ton bei 1600 Hz mono (Kamera-Teile in Reihenfolge konkateniert), Grob-Offset
per FFT + Mehrfenster-Verifikation. Ausgabe: offsets.json (Sekunden + Frames @29.97 NDF)."""
import os, sys, json, subprocess
import numpy as np

SR = 1600; BIN = 16; ENV_SR = SR // BIN; FPS = 30000/1001
ROOT = r"E:\Projekt-B-1 Projekt-B"
CACHE = r"C:\claude\resolve-prep\projekt-b\cache"
os.makedirs(CACHE, exist_ok=True)

REF = os.path.join(ROOT, "dr10L", "001_181212.wav")
CAMS = {
    "weit":  [os.path.join(ROOT, "weit",  f"SHOGUNU_S001_S001_T019_0{i}.MOV") for i in range(2)],
    "seite": [os.path.join(ROOT, "seite", f"SHOGUNU_S001_S001_T019_0{i}.MOV") for i in range(2)],
}

def decode(path):
    """ein File -> float32 mono @SR (downmix aller Kanaele)."""
    p = subprocess.run(["ffmpeg","-v","error","-i",path,"-vn","-ac","1","-ar",str(SR),
                        "-f","f32le","-"], capture_output=True)
    return np.frombuffer(p.stdout, dtype=np.float32)

def load_cached(name, parts):
    f = os.path.join(CACHE, name + f".{SR}.npy")
    if os.path.exists(f):
        return np.load(f)
    print(f"  extrahiere {name} ({len(parts)} Teil(e))...", flush=True)
    sig = np.concatenate([decode(p) for p in parts]) if len(parts) > 1 else decode(parts[0])
    np.save(f, sig)
    return sig

def onset(sig):
    n = (len(sig)//BIN)*BIN
    e = np.abs(sig[:n]).reshape(-1,BIN).mean(axis=1).astype(np.float64)
    le = np.log1p(e/(e.mean()+1e-9)); w=151; k=np.ones(w)/w
    return np.maximum(le-np.convolve(le,k,mode='same'),0.0)

def nrm(x):
    x=x-x.mean(); s=x.std(); return x/s if s>0 else x

def coarse(a,b):
    A=nrm(a);B=nrm(b);N=len(A)+len(B)-1;Nf=1<<(N-1).bit_length()
    cc=np.fft.irfft(np.fft.rfft(A,Nf)*np.conj(np.fft.rfft(B,Nf)),Nf)
    full=np.concatenate((cc[-(len(B)-1):],cc[:len(A)]));k=int(np.argmax(full))
    return (k-(len(B)-1))/ENV_SR

def find(A,B):
    A=nrm(A); Bm=B-B.mean(); La,Lb=len(A),len(B)
    Nf=1<<((La+Lb-1)-1).bit_length()
    full=np.fft.irfft(np.fft.rfft(Bm,Nf)*np.fft.rfft(A[::-1],Nf),Nf)
    cc=full[La-1:Lb]; k=int(np.argmax(cc)); seg=B[k:k+La]; seg=seg-seg.mean()
    d=np.linalg.norm(A)*np.linalg.norm(seg)
    return k,(float(np.dot(A,seg)/d) if d>0 else 0.0)

def verify(a,b,off_s,win_s=300,search_s=12,nwin=6):
    W=int(win_s*ENV_SR);pad=int(search_s*ENV_SR)
    cs=np.cumsum(np.concatenate(([0],a)));en=cs[W:]-cs[:-W]
    adur=len(a)/ENV_SR;bdur=len(b)/ENV_SR;lo=max(0,off_s);hi=min(adur,off_s+bdur)
    lo_i=int(lo*ENV_SR);hi_i=min(len(en),int(hi*ENV_SR)-W)
    if hi_i<=lo_i:return []
    order=np.argsort(en[lo_i:hi_i])[::-1]+lo_i;picks=[];out=[]
    for c in order:
        if any(abs(c-p)<W for p in picks):continue
        picks.append(c);Awin=a[c:c+W];ps=c-int(round(off_s*ENV_SR))
        if ps-pad<0 or ps+W+pad>len(b):continue
        B=b[ps-pad:ps+W+pad];k,pe=find(Awin,B)
        out.append((off_s+(k-pad)/ENV_SR, pe))
        if len(out)>=nwin:break
    return out

print("=== Ton laden ===", flush=True)
sig = {"ton": load_cached("ton",[REF])}
for n,parts in CAMS.items():
    sig[n]=load_cached(n,parts)
on = {n: onset(s) for n,s in sig.items()}

# Selbst-Test
W=300*ENV_SR; A=on["ton"][5000:5000+W]; k,p=find(A,on["ton"][5000-1000:5000+W+1000])
print(f"Selbst-Test: shift={k-1000} (soll 0), Pearson={p:.3f}\n", flush=True)

res={}
print(f"{'Quelle':<8}{'Offset(s)':>12}{'Frames':>10}{'Pearson':>22}{'Streu':>8}")
for n in CAMS:
    off=coarse(on["ton"],on[n]); vs=verify(on["ton"],on[n],off)
    offs=np.array([o for o,_ in vs]); pe=np.array([p for _,p in vs])
    med=float(np.median(offs)); spread=float(offs.max()-offs.min())
    print(f"{n:<8}{med:>12.3f}{med*FPS:>10.0f}{'/'.join(f'{p:.2f}' for p in pe):>22}{spread:>8.2f}", flush=True)
    res[n]={"offset_s":round(med,3),"frames":round(med*FPS),
            "pearson_med":round(float(np.median(pe)),3),"spread_s":round(spread,3),
            "ok":bool(np.median(pe)>0.45 and spread<0.5)}

json.dump({"ref":"ton (001_181212.wav)","fps":FPS,"sources":res},
          open(r"C:\claude\resolve-prep\projekt-b\offsets.json","w",encoding="utf-8"),
          indent=2,ensure_ascii=False)
print("\nok:",{n:res[n]["ok"] for n in res}, flush=True)
