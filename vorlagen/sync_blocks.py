# -*- coding: utf-8 -*-
"""Sync je AUFNAHMEBLOCK: 3 Kameras gegen den jeweiligen Hauptton-Teil.
Es gab Pausen; nach jeder Pause wurde neu gestartet -> pro Block eigener Offset.
Ausgabe: offsets_blocks.json (Sekunden + Frames @29.97)."""
import os, sys, json, subprocess, glob, re
import numpy as np

SR = 1600; BIN = 16; ENV_SR = SR // BIN; FPS = 30000/1001
ROOT = r"E:\Projekt-M Projekt-M"
CACHE = r"C:\claude\resolve-prep\projekt-m\cache"
OUT = r"C:\claude\resolve-prep\projekt-m\offsets_blocks.json"
os.makedirs(CACHE, exist_ok=True)

TON = os.path.join(ROOT, "t1 Hauptton")
# Block -> (Ton-wav, {kamera: T-Nummern in Reihenfolge})
BLOCKS = {
    1: ("001_330715.wav", {"nah": ["T006"], "weit": ["T009"], "seite": ["T009"]}),
    2: ("002_330715.wav", {"nah": ["T007"], "weit": ["T010"], "seite": ["T010"]}),
    3: ("003_330715.wav", {"nah": ["T008"], "weit": ["T012", "T011"], "seite": ["T011"]}),
    4: ("004_330715.wav", {"nah": ["T009"], "weit": ["T013"], "seite": ["T012"]}),
}
CAMDIR = {"nah": "k1 nah", "weit": "k2 weit", "seite": "k3 seite"}


def parts_for(cam, tnums):
    out = []
    for t in tnums:
        fs = sorted(glob.glob(os.path.join(ROOT, CAMDIR[cam], f"*_{t}_*.MOV")))
        out += fs
    return out


def decode(path):
    p = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vn", "-ac", "1",
                        "-ar", str(SR), "-f", "f32le", "-"], capture_output=True)
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
    e = np.abs(sig[:n]).reshape(-1, BIN).mean(axis=1).astype(np.float64)
    le = np.log1p(e/(e.mean()+1e-9)); w = 151; k = np.ones(w)/w
    return np.maximum(le-np.convolve(le, k, mode='same'), 0.0)


def nrm(x):
    x = x-x.mean(); s = x.std(); return x/s if s > 0 else x


def coarse(a, b):
    A = nrm(a); B = nrm(b); N = len(A)+len(B)-1; Nf = 1 << (N-1).bit_length()
    cc = np.fft.irfft(np.fft.rfft(A, Nf)*np.conj(np.fft.rfft(B, Nf)), Nf)
    full = np.concatenate((cc[-(len(B)-1):], cc[:len(A)])); k = int(np.argmax(full))
    return (k-(len(B)-1))/ENV_SR


def find(A, B):
    A = nrm(A); Bm = B-B.mean(); La, Lb = len(A), len(B)
    Nf = 1 << ((La+Lb-1)-1).bit_length()
    full = np.fft.irfft(np.fft.rfft(Bm, Nf)*np.fft.rfft(A[::-1], Nf), Nf)
    cc = full[La-1:Lb]; k = int(np.argmax(cc)); seg = B[k:k+La]; seg = seg-seg.mean()
    d = np.linalg.norm(A)*np.linalg.norm(seg)
    return k, (float(np.dot(A, seg)/d) if d > 0 else 0.0)


def verify(a, b, off_s, win_s=300, search_s=12, nwin=6):
    W = int(win_s*ENV_SR); pad = int(search_s*ENV_SR)
    cs = np.cumsum(np.concatenate(([0], a))); en = cs[W:]-cs[:-W]
    adur = len(a)/ENV_SR; bdur = len(b)/ENV_SR; lo = max(0, off_s); hi = min(adur, off_s+bdur)
    lo_i = int(lo*ENV_SR); hi_i = min(len(en), int(hi*ENV_SR)-W)
    if hi_i <= lo_i: return []
    order = np.argsort(en[lo_i:hi_i])[::-1]+lo_i; picks = []; out = []
    for c in order:
        if any(abs(c-p) < W for p in picks): continue
        picks.append(c); Awin = a[c:c+W]; ps = c-int(round(off_s*ENV_SR))
        if ps-pad < 0 or ps+W+pad > len(b): continue
        B = b[ps-pad:ps+W+pad]; k, pe = find(Awin, B)
        out.append((off_s+(k-pad)/ENV_SR, pe))
        if len(out) >= nwin: break
    return out


res = {}
only = sys.argv[1:] and [int(x) for x in sys.argv[1:]] or list(BLOCKS)
for b in only:
    wav, cams = BLOCKS[b]
    print(f"=== Block {b} ({wav}) ===", flush=True)
    ton = load_cached(f"b{b}_ton", [os.path.join(TON, wav)])
    a = onset(ton)
    res[str(b)] = {"ton": wav, "ton_dauer_s": round(len(ton)/SR, 3), "kameras": {}}
    for cam, tn in cams.items():
        parts = parts_for(cam, tn)
        sig = load_cached(f"b{b}_{cam}", parts)
        bb = onset(sig)
        off = coarse(a, bb); vs = verify(a, bb, off)
        if not vs:
            print(f"  {cam}: KEINE Fenster!"); continue
        offs = np.array([o for o, _ in vs]); pe = np.array([p for _, p in vs])
        med = float(np.median(offs)); spread = float(offs.max()-offs.min())
        ok = bool(np.median(pe) > 0.45 and spread < 0.5)
        print(f"  {cam:<6} off={med:8.3f}s  frames={med*FPS:7.0f}  "
              f"pearson={'/'.join(f'{p:.2f}' for p in pe)}  streu={spread:.2f}  {'OK' if ok else 'PRUEFEN'}",
              flush=True)
        res[str(b)]["kameras"][cam] = {
            "teile": [os.path.basename(p) for p in parts],
            "dauer_s": round(len(sig)/SR, 3),
            "offset_s": round(med, 3), "frames": round(med*FPS),
            "pearson_med": round(float(np.median(pe)), 3),
            "spread_s": round(spread, 3), "ok": ok}

old = {}
if os.path.exists(OUT):
    old = json.load(open(OUT, encoding="utf-8")).get("blocks", {})
old.update(res)
json.dump({"fps": FPS, "hinweis": "offset_s = Kamera-Start relativ zum Ton-Start des Blocks; "
                                  "positiv = Ton lief vor der Kamera",
           "blocks": old}, open(OUT, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print("\ngeschrieben:", OUT, flush=True)
