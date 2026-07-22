# -*- coding: utf-8 -*-
"""Importiert patched.drt als Multicam-Schnitt-Timeline (Projekt-A), ergaenzt den
Hauptton auf A1 (first_t..last_t), schiebt Import-Duplikate in einen Backup-Bin und
verifiziert pro Clip den Winkel gegen schnitt_seq.json. Angle 1 = nah, Angle 2 = weit."""
import os, sys, json, re
from collections import Counter
os.environ.setdefault("RESOLVE_SCRIPT_API", r"C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting")
os.environ.setdefault("RESOLVE_SCRIPT_LIB", r"C:\Program Files\Blackmagic Design\DaVinci Resolve\fusionscript.dll")
sys.path.append(os.path.join(os.environ["RESOLVE_SCRIPT_API"], "Modules"))
import DaVinciResolveScript as dvr

NAME = "260626 Projekt-A"
DRT  = r"C:\claude\resolve-prep\projekt-a\mcbuild\patched.drt"
SEQ  = json.load(open(r"C:\claude\resolve-prep\projekt-a\mcbuild\schnitt_seq.json", encoding="utf-8"))
cams = SEQ["cams"]; first_t = SEQ["first_t"]; last_t = SEQ["last_t"]
TLNAME = f"{NAME} Multicam Schnitt"
ANGLE2CAM = {"1": "nah", "2": "weit"}

proj = dvr.scriptapp("Resolve").GetProjectManager().GetCurrentProject()
mp = proj.GetMediaPool(); root = mp.GetRootFolder()
def walk(f):
    for c in f.GetClipList(): yield c
    for s in f.GetSubFolderList(): yield from walk(s)
def tl_names():
    return {proj.GetTimelineByIndex(i).GetName() for i in range(1, proj.GetTimelineCount()+1)}

before_clips = {c.GetName() for c in walk(root)}

for i in range(proj.GetTimelineCount(),0,-1):
    t=proj.GetTimelineByIndex(i)
    if t.GetName()==TLNAME: mp.DeleteTimelines([t])

mp.SetCurrentFolder(root)
tl = mp.ImportTimelineFromFile(DRT, {"timelineName": TLNAME})
assert tl, "Import fehlgeschlagen"
print("Importiert:", tl.GetName(), "Clips:", len(tl.GetItemListInTrack("video",1)))

items = {c.GetName(): c for c in walk(root)}
ton = items[f"{NAME} ton"]
proj.SetCurrentTimeline(tl)
mp.AppendToTimeline([{"mediaPoolItem": ton, "startFrame": first_t, "endFrame": last_t, "mediaType": 2}])

new_clips = [c for c in walk(root) if c.GetName() not in before_clips]
dupes = [c for c in new_clips if c.GetClipProperty("Type") in ("Multicam","Timeline") or "Multicam" in c.GetName()]
if dupes:
    bk = mp.AddSubFolder(root, "Multicam Import (Backup)")
    if bk is None:
        for sf in root.GetSubFolderList():
            if sf.GetName()=="Multicam Import (Backup)": bk=sf
    mp.MoveClips(dupes, bk)
    print("Backup-Bin:", [c.GetName() for c in dupes])

v = tl.GetItemListInTrack("video",1)
bad=0; got=[]
for idx,it in enumerate(v):
    m = re.search(r"Angle\s*([0-9])", it.GetName())
    cam = ANGLE2CAM.get(m.group(1)) if m else "?"
    got.append(cam)
    if idx < len(cams) and cam != cams[idx]: bad+=1
print("Clips:", len(v), "Ton-Clips A1:", len(tl.GetItemListInTrack("audio",1)))
print("Winkelverteilung:", dict(Counter(got)))
print("Fehler ggue Plan:", bad, "/", len(cams))
print("Beispielnamen:", [v[i].GetName() for i in range(min(3,len(v)))])
dvr.scriptapp("Resolve").GetProjectManager().SaveProject()
print("gespeichert.")
