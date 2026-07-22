# -*- coding: utf-8 -*-
"""Scaffold-Timeline fuer den Multicam-Schnitt bauen und als DRT exportieren.
Verwendet denselben Schnittplan wie die verschachtelte Schnitt-Timeline
(identische Span-Grenzen in ton-Frames), platziert aber den MULTICAM-Clip
(alle als Default-Winkel). Multicam-Frame = ton-Frame - MC0 (MC0 = 829, Start-TC
01:00:27:19). Danach: DRT-Export -> Winkel patchen -> reimportieren.
Schreibt schnitt_seq.json = Wunschkamera je Clip in Timeline-Reihenfolge."""
import os, sys, json
os.environ.setdefault("RESOLVE_SCRIPT_API", r"C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting")
os.environ.setdefault("RESOLVE_SCRIPT_LIB", r"C:\Program Files\Blackmagic Design\DaVinci Resolve\fusionscript.dll")
sys.path.append(os.path.join(os.environ["RESOLVE_SCRIPT_API"], "Modules"))
import DaVinciResolveScript as dvr

NAME = "260709 Projekt-B"
FPS = 30000/1001
MC0 = 829                       # Multicam-Frame 0 == ton-Frame 829 (Start-TC 01:00:27:19)
OFF  = json.load(open(r"C:\claude\resolve-prep\projekt-b\offsets.json", encoding="utf-8"))["sources"]
PLAN = json.load(open(r"C:\claude\resolve-prep\projekt-b\cut_plan.json", encoding="utf-8"))
CAMS = ("weit", "seite"); FOFF = {a: OFF[a]["frames"] for a in CAMS}
DRT  = r"C:\claude\resolve-prep\projekt-b\mcbuild\scaffold.drt"
SEQ  = r"C:\claude\resolve-prep\projekt-b\mcbuild\schnitt_seq.json"

proj = dvr.scriptapp("Resolve").GetProjectManager().GetCurrentProject()
mp = proj.GetMediaPool(); root = mp.GetRootFolder()
def walk(f):
    for c in f.GetClipList(): yield c
    for s in f.GetSubFolderList(): yield from walk(s)
items = {c.GetName(): c for c in walk(root)}
MC = items[f"{NAME} Multicam"]

def cam_vidlen(name):
    for i in range(1, proj.GetTimelineCount()+1):
        t = proj.GetTimelineByIndex(i)
        if t.GetName()==name:
            v = t.GetItemListInTrack("video",1); return v[-1].GetEnd() - t.GetStartFrame()
    return None
CAMLEN = {a: cam_vidlen(f"{NAME} {a}") for a in CAMS}
WIN = {a: (FOFF[a], FOFF[a] + CAMLEN[a]) for a in CAMS}

# --- identische mrg-Liste wie apply_cut_projekt-b.py ---
def other(a): return "seite" if a == "weit" else "weit"
def avail(a, s, e): return WIN[a][0] <= s and e <= WIN[a][1]
raw = []
lo = min(WIN[c][0] for c in CAMS); hi = max(WIN[c][1] for c in CAMS)
for sp in PLAN:
    s = int(round(sp["start"]*FPS)); e = int(round(sp["end"]*FPS)); a = sp["angle"]
    s = max(s, lo); e = min(e, hi)
    if e <= s: continue
    t = s
    while t < e:
        pref = a if avail(a, t, t+1) else other(a)
        if not avail(pref, t, t+1):
            nexts = [WIN[c][0] for c in CAMS if WIN[c][0] > t]
            if not nexts: break
            t = min(nexts); continue
        seg_end = min(e, WIN[pref][1])
        if pref != a and WIN[a][0] > t: seg_end = min(seg_end, WIN[a][0])
        raw.append([pref, t, seg_end]); t = seg_end
mrg = []
for a,s,e in raw:
    if mrg and mrg[-1][0]==a and s==mrg[-1][2]: mrg[-1][2]=e
    else: mrg.append([a,s,e])

# --- Scaffold-Timeline: Multicam-Clip video-only in Spans (mc-Frames) ---
for i in range(proj.GetTimelineCount(),0,-1):
    t=proj.GetTimelineByIndex(i)
    if t.GetName()==f"{NAME} MC-Scaffold": mp.DeleteTimelines([t])
tl = mp.CreateEmptyTimeline(f"{NAME} MC-Scaffold")
tl.SetStartTimecode("01:00:00:00")
seq = []
for a,s,e in mrg:
    ms = s - MC0; me = e - MC0
    if me <= ms: continue
    ok = mp.AppendToTimeline([{"mediaPoolItem":MC,"startFrame":ms,"endFrame":me,"mediaType":1}])
    seq.append(a)
json.dump({"MC0":MC0, "first_t":mrg[0][1], "last_t":mrg[-1][2], "cams":seq},
          open(SEQ,"w",encoding="utf-8"), indent=1, ensure_ascii=False)
v = tl.GetItemListInTrack("video",1)
print(f"Scaffold: {len(v)} Clips (Plan {len(seq)}), Kameras {dict(__import__('collections').Counter(seq))}")

# --- Export als DRT (Typ 1) ---
proj.SetCurrentTimeline(tl)
ok = tl.Export(DRT, 1)
print("Export DRT:", ok, "->", DRT, "exists", os.path.exists(DRT), os.path.getsize(DRT) if os.path.exists(DRT) else "-")
