# -*- coding: utf-8 -*-
"""mc_ready.drt importieren, Hauptton auf A1, Verifikation der Winkel."""
import os, sys, json, re
os.environ.setdefault("RESOLVE_SCRIPT_API", r"C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting")
os.environ.setdefault("RESOLVE_SCRIPT_LIB", r"C:\Program Files\Blackmagic Design\DaVinci Resolve\fusionscript.dll")
sys.path.append(os.path.join(os.environ["RESOLVE_SCRIPT_API"], "Modules"))
import DaVinciResolveScript as dvr

B = r"C:\claude\resolve-prep\projekt-b2"
NAME = "Projekt-B-2 Projekt-B"
TLNAME = f"{NAME} Multicam Schnitt"
DRT = B + r"\mcbuild\mc_ready.drt"
SEQ = json.load(open(B + r"\mcbuild\schnitt_seq.json", encoding="utf-8"))
cams = SEQ["cams"]; MC0 = SEQ["MC0"]
FPS = 30000/1001
PLAN = json.load(open(B + r"\cut_plan.json", encoding="utf-8"))

proj = dvr.scriptapp("Resolve").GetProjectManager().GetCurrentProject()
mp = proj.GetMediaPool(); root = mp.GetRootFolder()
print("Projekt:", proj.GetName())

def walk(f):
    for c in f.GetClipList(): yield c
    for s in f.GetSubFolderList(): yield from walk(s)

before = {c.GetName() for c in walk(root)}

for i in range(proj.GetTimelineCount(), 0, -1):
    t = proj.GetTimelineByIndex(i)
    if t.GetName() == TLNAME:
        mp.DeleteTimelines([t]); print("alte Timeline entfernt")

mp.SetCurrentFolder(root)
tl = mp.ImportTimelineFromFile(DRT, {"timelineName": TLNAME})
if not tl:
    raise SystemExit("Import fehlgeschlagen")
v = tl.GetItemListInTrack("video", 1) or []
print("Importiert:", tl.GetName(), "| Videoclips:", len(v))
print("Clipnamen (erste 5):", [c.GetName() for c in v[:5]])

neu = [c for c in walk(root) if c.GetName() not in before]
print("neue MediaPool-Eintraege:", [(c.GetName(), c.GetClipProperty("Type")) for c in neu])

# Hauptton auf A1
items = {c.GetName(): c for c in walk(root)}
if f"{NAME} ton" in items and not (tl.GetItemListInTrack("audio", 1) or []):
    first_t = int(round(PLAN[0]["start"]*FPS)); last_t = int(round(PLAN[-1]["end"]*FPS))
    proj.SetCurrentTimeline(tl)
    mp.AppendToTimeline([{"mediaPoolItem": items[f"{NAME} ton"],
                          "startFrame": first_t, "endFrame": last_t, "mediaType": 2}])
    print("Hauptton auf A1 ergaenzt")

dvr.scriptapp("Resolve").GetProjectManager().SaveProject()
print("gespeichert.")
