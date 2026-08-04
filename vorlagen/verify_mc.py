# -*- coding: utf-8 -*-
"""Multicam-Schnitt-Timeline verifizieren: Clipanzahl, Luecken/Ueberlappungen,
Winkel gegen cut_plan.json, Tonspur."""
import os, sys, json, re
os.environ.setdefault("RESOLVE_SCRIPT_API", r"C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting")
os.environ.setdefault("RESOLVE_SCRIPT_LIB", r"C:\Program Files\Blackmagic Design\DaVinci Resolve\fusionscript.dll")
sys.path.append(os.path.join(os.environ["RESOLVE_SCRIPT_API"], "Modules"))
import DaVinciResolveScript as dvr

B = r"C:\claude\resolve-prep\Projekt-B-2"
NAME = "Projekt-B-2"
TLNAME = f"{NAME} Multicam Schnitt"
FPS = 30000/1001
SEQ = json.load(open(B + r"\mcbuild\schnitt_seq.json", encoding="utf-8"))
cams, MC0 = SEQ["cams"], SEQ["MC0"]
ANGLE = SEQ["angle"]                      # {'weit':1,'seite':2}
A2C = {v: k for k, v in ANGLE.items()}

proj = dvr.scriptapp("Resolve").GetProjectManager().GetCurrentProject()
tl = None
for i in range(1, proj.GetTimelineCount()+1):
    t = proj.GetTimelineByIndex(i)
    if t.GetName() == TLNAME:
        tl = t
assert tl, f"{TLNAME} nicht gefunden"
proj.SetCurrentTimeline(tl)

v = tl.GetItemListInTrack("video", 1) or []
a = tl.GetItemListInTrack("audio", 1) or []
print(f"Timeline: {tl.GetName()}")
print(f"  Videoclips: {len(v)} (Plan {len(cams)})")
print(f"  Audioclips A1: {len(a)}")
print(f"  Dauer: {(tl.GetEndFrame()-tl.GetStartFrame())} f = {(tl.GetEndFrame()-tl.GetStartFrame())/FPS/60:.2f} min")

luecken = ueberlapp = 0
for x, y in zip(v, v[1:]):
    d = y.GetStart() - x.GetEnd()
    if d > 0: luecken += 1
    if d < 0: ueberlapp += 1
print(f"  Luecken: {luecken}   Ueberlappungen: {ueberlapp}")

falsch = []
for k, (it, soll) in enumerate(zip(v, cams)):
    m = re.search(r"Angle\s*(\d+)", it.GetName())
    ist = A2C.get(int(m.group(1))) if m else "?"
    if ist != soll:
        falsch.append((k+1, soll, ist, it.GetName()))
print(f"  Winkelfehler ggue. Plan: {len(falsch)} / {len(cams)}")
for f in falsch[:8]:
    print("    Clip", f)

from collections import Counter
verteilung = Counter(re.search(r"Angle\s*(\d+)", it.GetName()).group(1)
                     if re.search(r"Angle\s*(\d+)", it.GetName()) else "?" for it in v)
print("  Winkelverteilung:", {A2C.get(int(k), k): n for k, n in verteilung.items()})

dauern = [(it.GetEnd()-it.GetStart())/FPS for it in v]
print(f"  Einstellungen: kuerzeste {min(dauern):.1f}s, laengste {max(dauern):.1f}s, "
      f"Mittel {sum(dauern)/len(dauern):.1f}s")
