# -*- coding: utf-8 -*-
"""Kaltstart-Vorschlaege: staerkster Satz je Kurzvideo, framegenau aus den Wort-
Zeitstempeln, mit In-/Out-Punkt in der Sprechpause. Setzt Marker MIT DAUER."""
import json, re, sys
FPS = 30000/1001
W = json.load(open("words.json", encoding="utf-8"))
def norm(s): return re.sub(r"[^a-zäöüß0-9]", "", s.lower())
NW = [norm(w["word"]) for w in W]

def finde(phrase, um_sek, fenster=200):
    """Erstes Vorkommen der Phrase in der Naehe von um_sek -> (i_start, i_end)."""
    ziel = [norm(x) for x in phrase.split() if norm(x)]
    best=None
    for i,w in enumerate(W):
        if abs(w["start"]-um_sek) > fenster: continue
        if NW[i:i+len(ziel)] == ziel:
            d=abs(w["start"]-um_sek)
            if best is None or d<best[0]: best=(d,i,i+len(ziel)-1)
    if not best: raise SystemExit(f"Phrase nicht gefunden: {phrase!r} um {um_sek}")
    return best[1], best[2]

def grenzen(i0, i1, luft=0.25, max_luft=0.6):
    """In-/Out-Punkt in die Sprechpause legen."""
    a = W[i0]["start"]; b = W[i1]["end"]
    vor = W[i0-1]["end"] if i0>0 else a-2
    nach = W[i1+1]["start"] if i1+1 < len(W) else b+2
    inp  = max(vor + 0.08, a - min(max((a-vor)/2, 0), max_luft), a-max_luft)
    outp = min(nach - 0.08, b + min(max((nach-b)/2, 0), max_luft), b+max_luft)
    return inp, outp, a-vor, nach-b

def tc(fr):
    fr=int(round(fr)); f=fr%30; s=fr//30; m=s//60; s%=60; h=m//60; m%=60
    return f"{h+1:02d}:{m:02d}:{s:02d}:{f:02d}"

if __name__ == "__main__":
    VORSCHLAEGE = json.load(open("kaltstart_saetze.json", encoding="utf-8"))
    out=[]
    for v in VORSCHLAEGE:
        for var in v["varianten"]:
            i0,_ = finde(var["von"], var["um"])
            _,i1 = finde(var["bis"], var["um"])
            inp,outp,pv,pn = grenzen(i0,i1)
            txt=" ".join(w["word"].strip() for w in W[i0:i1+1])
            var.update(dict(t_in=inp, t_out=outp, f_in=int(round(inp*FPS)), f_out=int(round(outp*FPS)),
                            dauer=round(outp-inp,2), pause_vor=round(pv,2), pause_nach=round(pn,2), text=txt))
        out.append(v)
    json.dump(out, open("kaltstart_final.json","w",encoding="utf-8"), ensure_ascii=False, indent=1)
    for v in out:
        print(f"\n=== #{v['nr']} {v['kurz']}")
        for var in v["varianten"]:
            print(f"  [{var['tag']}] Ton {var['t_in']:.2f}-{var['t_out']:.2f}s  {var['dauer']}s  "
                  f"Pause vor {var['pause_vor']}s / nach {var['pause_nach']}s")
            print(f"      {var['text'][:160]}")
