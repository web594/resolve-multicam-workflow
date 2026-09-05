# -*- coding: utf-8 -*-
"""Kurzvideo-DRTs importieren, Ton passagenweise ergaenzen, Winkel verifizieren."""
import os, sys, json
os.environ.setdefault("RESOLVE_SCRIPT_API", r"C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting")
os.environ.setdefault("RESOLVE_SCRIPT_LIB", r"C:\Program Files\Blackmagic Design\DaVinci Resolve\fusionscript.dll")
sys.path.append(os.path.join(os.environ["RESOLVE_SCRIPT_API"], "Modules"))
import DaVinciResolveScript as dvr
from collections import Counter

BASE = r"C:\claude\resolve-prep\projekt-m"
NAME = "Projekt-M Projekt-M"
FPS = 30000/1001
TCBASE = 108000
NUR = [int(x) for x in sys.argv[1:]] or [1, 2, 3, 4, 5, 6]

r = dvr.scriptapp("Resolve"); p = r.GetProjectManager().GetCurrentProject()
mp = p.GetMediaPool(); root = mp.GetRootFolder()


def walk(f):
    for c in f.GetClipList(): yield c
    for s in f.GetSubFolderList(): yield from walk(s)


def bin_(name):
    for sf in root.GetSubFolderList():
        if sf.GetName() == name: return sf
    return mp.AddSubFolder(root, name)


kurzbin = bin_("Kurzvideos"); anlegen = bin_("Anlegen")
ton = {c.GetName(): c for c in walk(root)}[f"{NAME} ton"]

for nr in NUR:
    meta = json.load(open(os.path.join(BASE, "mcbuild", f"kurz_{nr}.json"), encoding="utf-8"))
    tlname = meta["name"]
    for i in range(p.GetTimelineCount(), 0, -1):
        t = p.GetTimelineByIndex(i)
        if t.GetName() == tlname:
            mp.DeleteTimelines([t]); print(f"  alte Timeline '{tlname}' entfernt")
    vorher = {c.GetName() for c in walk(root)}
    mp.SetCurrentFolder(kurzbin)
    tl = mp.ImportTimelineFromFile(os.path.join(BASE, "mcbuild", f"kurz_{nr}.drt"),
                                   {"timelineName": tlname})
    if not tl:
        print(f"#{nr} IMPORT FEHLGESCHLAGEN"); continue
    if tl.GetName() != tlname:
        tl.SetName(tlname)
    tl.SetStartTimecode("01:00:00:00")
    p.SetCurrentTimeline(tl)
    # Ton passagenweise auf A1
    infos = []; rec = TCBASE
    for fa, fb in meta["ton"]:
        infos.append({"mediaPoolItem": ton, "startFrame": fa, "endFrame": fb,
                      "mediaType": 2, "trackIndex": 1, "recordFrame": rec})
        rec += fb - fa
    mp.AppendToTimeline(infos)
    v = tl.GetItemListInTrack("video", 1) or []
    a = tl.GetItemListInTrack("audio", 1) or []
    ang = Counter(x.GetName().split("- ")[-1] for x in v)
    lue = ov = 0; prev = None
    for it in v:
        if prev is not None:
            if it.GetStart() < prev: ov += 1
            elif it.GetStart() > prev: lue += 1
        prev = it.GetEnd()
    vlen = v[-1].GetEnd()-TCBASE if v else 0
    alen = a[-1].GetEnd()-TCBASE if a else 0
    # Hilfstimelines wegraeumen
    neu = [c for c in walk(root) if c.GetName() not in vorher and c.GetName() != tlname]
    if neu: mp.MoveClips(neu, anlegen)
    print(f"#{nr} {tlname}: {len(v)} Clips, {vlen/FPS/60:.1f} min | Winkel {dict(ang)} | "
          f"Luecken {lue} Ueberl {ov} | Ton {len(a)} Clips, Laengendiff {vlen-alen} f | "
          f"weggeraeumt: {len(neu)}", flush=True)

r.GetProjectManager().SaveProject()
print("gespeichert.")
