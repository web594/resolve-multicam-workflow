# -*- coding: utf-8 -*-
"""Scaffold-Timeline fuer den Multicam-Schnitt (Projekt-A) bauen und als DRT exportieren.
Identische Segmente wie apply_cut_nested.py (pro Span s=round(start*FPS),
e=min(round(end*FPS),CAMLEN[cam])), aber mit dem MULTICAM-Clip (Default-Winkel).
Start-TC des Multicam-Clips = 01:00:00:00 = Ton-Frame 0  ->  MC0 = 0.
Danach: DRT-Export -> Winkel patchen -> reimportieren."""
import os, sys, json, collections
os.environ.setdefault("RESOLVE_SCRIPT_API", r"C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting")
os.environ.setdefault("RESOLVE_SCRIPT_LIB", r"C:\Program Files\Blackmagic Design\DaVinci Resolve\fusionscript.dll")
sys.path.append(os.path.join(os.environ["RESOLVE_SCRIPT_API"], "Modules"))
import DaVinciResolveScript as dvr

NAME = "Projekt-A Projekt-A"
FPS  = 30000/1001
MC0  = 0                         # Multicam-Frame 0 == Ton-Frame 0 (Start-TC 01:00:00:00)
PLAN = json.load(open(r"C:\claude\resolve-prep\projekt-a\cut_plan.json", encoding="utf-8"))
DRT  = r"C:\claude\resolve-prep\projekt-a\mcbuild\scaffold.drt"
SEQ  = r"C:\claude\resolve-prep\projekt-a\mcbuild\schnitt_seq.json"

proj = dvr.scriptapp("Resolve").GetProjectManager().GetCurrentProject()
mp = proj.GetMediaPool(); root = mp.GetRootFolder()
def walk(f):
    for c in f.GetClipList(): yield c
    for s in f.GetSubFolderList(): yield from walk(s)
items = {c.GetName(): c for c in walk(root)}
MC = items[f"{NAME} Multicam"]

def vid_len(name):
    for i in range(1, proj.GetTimelineCount()+1):
        t = proj.GetTimelineByIndex(i)
        if t.GetName()==name:
            v = t.GetItemListInTrack("video",1); return v[-1].GetEnd() - t.GetStartFrame()
    return None
CAMLEN = {c: vid_len(f"{NAME} {c}") for c in ("nah","weit")}
print("Video-Contentlaenge:", CAMLEN)

# Segmente exakt wie apply_cut_nested.py
segs = []
for sp in PLAN:
    a = sp["angle"]
    s = int(round(sp["start"]*FPS)); e = int(round(sp["end"]*FPS))
    e = min(e, CAMLEN[a])
    if e <= s: continue
    segs.append([a, s, e])
first_t = segs[0][1]; last_t = segs[-1][2]

# alte Scaffold-Timeline weg
for i in range(proj.GetTimelineCount(),0,-1):
    t=proj.GetTimelineByIndex(i)
    if t.GetName()==f"{NAME} MC-Scaffold": mp.DeleteTimelines([t])
tl = mp.CreateEmptyTimeline(f"{NAME} MC-Scaffold")
tl.SetStartTimecode("01:00:00:00")
proj.SetCurrentTimeline(tl)

seq = []
for a,s,e in segs:
    ms = s - MC0; me = e - MC0
    if me <= ms: continue
    mp.AppendToTimeline([{"mediaPoolItem":MC,"startFrame":ms,"endFrame":me,"mediaType":1}])
    seq.append(a)
json.dump({"MC0":MC0, "first_t":first_t, "last_t":last_t, "cams":seq},
          open(SEQ,"w",encoding="utf-8"), indent=1, ensure_ascii=False)
v = tl.GetItemListInTrack("video",1)
print(f"Scaffold: {len(v)} Clips (Plan {len(seq)}), Kameras {dict(collections.Counter(seq))}")

ok = tl.Export(DRT, 1)
print("Export DRT:", ok, "->", DRT, "exists", os.path.exists(DRT), os.path.getsize(DRT) if os.path.exists(DRT) else "-")
