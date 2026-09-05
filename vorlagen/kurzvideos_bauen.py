# -*- coding: utf-8 -*-
"""Baut je Kurzvideo eine eigene Timeline aus der fertigen 'Projekt-M Projekt-M Multicam Schnitt'.

Wichtig (Fallstrick Projekt-J): NICHT per ImportTimelineFromFile duplizieren — das
erzeugt einen zweiten Multicam-Unterbau ohne Grade. Stattdessen die vorhandenen
Multicam-Clips der Schnitt-Timeline per AppendToTimeline uebernehmen; damit bleiben
Grade UND Winkel erhalten und jeder Clip ist weiterhin auf eine andere Kamera umschaltbar.

Passagengrenzen werden auf die naechste Sprechpause eingerastet (words.json)."""
import os, sys, json
os.environ.setdefault("RESOLVE_SCRIPT_API", r"C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting")
os.environ.setdefault("RESOLVE_SCRIPT_LIB", r"C:\Program Files\Blackmagic Design\DaVinci Resolve\fusionscript.dll")
sys.path.append(os.path.join(os.environ["RESOLVE_SCRIPT_API"], "Modules"))
import DaVinciResolveScript as dvr

BASE = r"C:\claude\resolve-prep\projekt-m"
NAME = "Projekt-M Projekt-M"
QUELLE = f"{NAME} Multicam Schnitt"
FPS = 30000/1001
TCBASE = 108000
CFG = json.load(open(os.path.join(BASE, "videos.json"), encoding="utf-8"))
WORDS = json.load(open(os.path.join(BASE, "words.json"), encoding="utf-8"))
NUR = [int(x) for x in sys.argv[1:]] or None

# --- Sprechpausen: Liste (pause_start, pause_ende) ---
pausen = []
for a, b in zip(WORDS, WORDS[1:]):
    if b["start"] - a["end"] >= 0.35:
        pausen.append((a["end"], b["start"]))


def einrasten(t, richtung):
    """richtung=+1: Passagenanfang -> in die Pause DAVOR rutschen (Wortanfang nicht abschneiden)
       richtung=-1: Passagenende  -> in die Pause DANACH rutschen"""
    best, bd = t, 9e9
    for ps, pe in pausen:
        m = (ps + pe) / 2
        d = abs(m - t)
        if d < bd and d <= 6.0:
            bd = d; best = m
    return best


r = dvr.scriptapp("Resolve"); p = r.GetProjectManager().GetCurrentProject()
assert p.GetName() == NAME, p.GetName()
mp = p.GetMediaPool(); root = mp.GetRootFolder()

src = None
for i in range(1, p.GetTimelineCount()+1):
    if p.GetTimelineByIndex(i).GetName() == QUELLE: src = p.GetTimelineByIndex(i)
assert src, QUELLE
items = src.GetItemListInTrack("video", 1)
print(f"Quelle: {QUELLE}, {len(items)} Clips", flush=True)


def walk(f):
    for c in f.GetClipList(): yield c
    for s in f.GetSubFolderList(): yield from walk(s)


pool = {c.GetName(): c for c in walk(root)}
ton = pool[f"{NAME} ton"]

# Bin fuer die Kurzvideos
binf = None
for sf in root.GetSubFolderList():
    if sf.GetName() == "Kurzvideos": binf = sf
if binf is None:
    binf = mp.AddSubFolder(root, "Kurzvideos")

bericht = []
for v in CFG["videos"]:
    if NUR and v["nr"] not in NUR: continue
    tlname = v["name"]
    for i in range(p.GetTimelineCount(), 0, -1):
        t = p.GetTimelineByIndex(i)
        if t.GetName() == tlname: mp.DeleteTimelines([t])
    mp.SetCurrentFolder(binf)
    tl = mp.CreateEmptyTimeline(tlname)
    tl.SetStartTimecode("01:00:00:00")
    rec = TCBASE
    infos = []
    kapitel = []
    for a, b, txt in v["passagen"]:
        a2 = einrasten(float(a), +1); b2 = einrasten(float(b), -1)
        fa = TCBASE + int(round(a2*FPS)); fb = TCBASE + int(round(b2*FPS))
        kapitel.append((rec-TCBASE, txt, a2, b2))
        for it in items:
            s, e = it.GetStart(), it.GetEnd()
            if e <= fa or s >= fb: continue
            lo, hi = max(s, fa), min(e, fb)
            off = it.GetLeftOffset() + (lo - s)
            infos.append({"mediaPoolItem": it.GetMediaPoolItem(),
                          "startFrame": off, "endFrame": off + (hi-lo),
                          "mediaType": 1, "trackIndex": 1, "recordFrame": rec})
            rec += hi - lo
    # Ton laeuft synchron zum Bild mit -> wir nehmen den Hauptton passagenweise
    rec2 = TCBASE
    for a, b, txt in v["passagen"]:
        a2 = einrasten(float(a), +1); b2 = einrasten(float(b), -1)
        fa = int(round(a2*FPS)); fb = int(round(b2*FPS))
        infos.append({"mediaPoolItem": ton, "startFrame": fa, "endFrame": fb,
                      "mediaType": 2, "trackIndex": 1, "recordFrame": rec2})
        rec2 += fb - fa
    mp.AppendToTimeline(infos)
    vv = tl.GetItemListInTrack("video", 1) or []
    aa = tl.GetItemListInTrack("audio", 1) or []
    dauer = (vv[-1].GetEnd()-TCBASE) if vv else 0
    print(f"#{v['nr']} {tlname}: {len(vv)} Bildclips, {len(aa)} Tonclips, "
          f"{dauer/FPS/60:.1f} min", flush=True)
    bericht.append({"nr": v["nr"], "name": tlname, "titel": v["titel"],
                    "dauer_s": round(dauer/FPS, 1),
                    "kapitel": [{"pos_s": round(k[0]/FPS, 1), "text": k[1],
                                 "quelle_s": [round(k[2], 1), round(k[3], 1)]} for k in kapitel]})

json.dump(bericht, open(os.path.join(BASE, "kurzvideos_bericht.json"), "w", encoding="utf-8"),
          indent=1, ensure_ascii=False)
r.GetProjectManager().SaveProject()
print("gespeichert.")
