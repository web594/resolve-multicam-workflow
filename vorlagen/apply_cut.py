# -*- coding: utf-8 -*-
"""Schnitt-Timeline aus VERSCHACHTELTEN Quell-Timelines (weit/seite).
Quell-Timelines kamera-indiziert (Frame 0 = Kamerastart), daher
Ton-Zeit t -> Quell-Frame = round(t*FPS) - off_frames[a]. Wo die gewuenschte
Kamera nicht verfuegbar ist (z.B. weit startet erst bei 67 s), automatisch die
andere Kamera. Hauptton durchgehend auf A1 ab erstem verwendeten Moment."""
import os, sys, json
os.environ.setdefault("RESOLVE_SCRIPT_API", r"C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting")
os.environ.setdefault("RESOLVE_SCRIPT_LIB", r"C:\Program Files\Blackmagic Design\DaVinci Resolve\fusionscript.dll")
sys.path.append(os.path.join(os.environ["RESOLVE_SCRIPT_API"], "Modules"))
import DaVinciResolveScript as dvr

NAME = "Projekt-B-1"
FPS = 30000/1001
OFF  = json.load(open(r"C:\claude\resolve-prep\Projekt-B\offsets.json", encoding="utf-8"))["sources"]
PLAN = json.load(open(r"C:\claude\resolve-prep\Projekt-B\cut_plan.json", encoding="utf-8"))
CAMS = ("weit", "seite")
FOFF = {a: OFF[a]["frames"] for a in CAMS}

proj = dvr.scriptapp("Resolve").GetProjectManager().GetCurrentProject()
mp = proj.GetMediaPool(); root = mp.GetRootFolder()

def walk(f):
    for c in f.GetClipList(): yield c
    for s in f.GetSubFolderList(): yield from walk(s)
items = {c.GetName(): c for c in walk(root)}
SRC = {a: items[f"{NAME} {a}"] for a in CAMS + ("ton",)}

def cam_vidlen(name):
    for i in range(1, proj.GetTimelineCount()+1):
        t = proj.GetTimelineByIndex(i)
        if t.GetName()==name:
            v = t.GetItemListInTrack("video",1)
            return v[-1].GetEnd() - t.GetStartFrame()
    return None
CAMLEN = {a: cam_vidlen(f"{NAME} {a}") for a in CAMS}
WIN = {a: (FOFF[a], FOFF[a] + CAMLEN[a]) for a in CAMS}     # Verfuegbarkeit in ton-Frames
print("Kamera-Videolaenge (Frames):", CAMLEN)
print("Verfuegbar (ton-Frames):", WIN)

def other(a): return "seite" if a == "weit" else "weit"
def avail(a, s, e): return WIN[a][0] <= s and e <= WIN[a][1]

# alte Schnitt-Timeline weg
for i in range(proj.GetTimelineCount(),0,-1):
    t=proj.GetTimelineByIndex(i)
    if t.GetName()==f"{NAME} Schnitt": mp.DeleteTimelines([t])

# Plan -> (angle,s,e) in ton-Frames, mit Verfuegbarkeits-Fallback (an Fenstergrenzen splitten)
raw = []
for sp in PLAN:
    s = int(round(sp["start"]*FPS)); e = int(round(sp["end"]*FPS))
    a = sp["angle"]
    # gesamten Bereich auf Union der beiden Fenster klemmen
    lo = min(WIN[c][0] for c in CAMS); hi = max(WIN[c][1] for c in CAMS)
    s = max(s, lo); e = min(e, hi)
    if e <= s: continue
    # innerhalb [s,e] Stueck fuer Stueck die verfuegbare Kamera waehlen (bevorzugt a)
    t = s
    while t < e:
        pref = a if avail(a, t, t+1) else other(a)
        if not avail(pref, t, t+1):        # keine Kamera -> ueberspringen bis naechster Start
            nexts = [WIN[c][0] for c in CAMS if WIN[c][0] > t]
            if not nexts: break
            t = min(nexts); continue
        # bis wohin bleibt pref verfuegbar und a-Wunsch unveraendert -> bis e oder pref-Fensterende
        seg_end = min(e, WIN[pref][1])
        # falls pref = Ersatz (nicht a) und a spaeter verfuegbar wird, dort umschalten
        if pref != a and WIN[a][0] > t:
            seg_end = min(seg_end, WIN[a][0])
        raw.append([pref, t, seg_end]); t = seg_end

# benachbarte gleiche Winkel mergen
mrg = []
for a,s,e in raw:
    if mrg and mrg[-1][0]==a and s==mrg[-1][2]: mrg[-1][2]=e
    else: mrg.append([a,s,e])

tl = mp.CreateEmptyTimeline(f"{NAME} Schnitt")
tl.SetStartTimecode("01:00:00:00")
first_t = mrg[0][1]; last_t = mrg[-1][2]; nclip=0
for a,s,e in mrg:
    s0 = max(0, s - FOFF[a]); e0 = min(CAMLEN[a], e - FOFF[a])
    if e0 <= s0: continue
    mp.AppendToTimeline([{"mediaPoolItem":SRC[a],"startFrame":s0,"endFrame":e0,"mediaType":1}])
    nclip+=1
mp.AppendToTimeline([{"mediaPoolItem":SRC["ton"],"startFrame":first_t,"endFrame":last_t,"mediaType":2}])

from collections import Counter
cnt = Counter(a for a,_,_ in mrg)
print(f"Schnitt: {nclip} genestete Clips, {dict(cnt)}")
print(f"  Video-Dauer {sum(e-s for _,s,e in mrg)}f = {sum(e-s for _,s,e in mrg)/FPS/60:.1f}min")
print(f"  ton-Zeitbereich {first_t/FPS:.1f}..{last_t/FPS:.1f}s")
dvr.scriptapp("Resolve").GetProjectManager().SaveProject()
print("gespeichert.")
