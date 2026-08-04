# -*- coding: utf-8 -*-
"""Prueft die Schnitt-Timeline: Lueckenlosigkeit, Clipanzahl, Winkelverteilung, Tonlaenge."""
import os, sys, json
os.environ.setdefault("RESOLVE_SCRIPT_API", r"C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting")
os.environ.setdefault("RESOLVE_SCRIPT_LIB", r"C:\Program Files\Blackmagic Design\DaVinci Resolve\fusionscript.dll")
sys.path.append(os.path.join(os.environ["RESOLVE_SCRIPT_API"], "Modules"))
import DaVinciResolveScript as dvr
NAME="Projekt-B-1"; FPS=30000/1001
proj=dvr.scriptapp("Resolve").GetProjectManager().GetCurrentProject()
tl=None
for i in range(1,proj.GetTimelineCount()+1):
    t=proj.GetTimelineByIndex(i)
    if t.GetName()==f"{NAME} Schnitt": tl=t
v=tl.GetItemListInTrack("video",1); a=tl.GetItemListInTrack("audio",1)
gaps=0; overl=0; prev=None
from collections import Counter
cnt=Counter()
durs=[]
for it in v:
    nm=it.GetName()
    cam="weit" if " weit" in nm else ("seite" if " seite" in nm else "?")
    cnt[cam]+=1; durs.append(it.GetDuration())
    if prev is not None:
        d=it.GetStart()-prev
        if d>0: gaps+=1
        elif d<0: overl+=1
    prev=it.GetEnd()
print(f"Clips: {len(v)}  Winkel: {dict(cnt)}")
print(f"Luecken: {gaps}  Ueberlappungen: {overl}")
print(f"Video gesamt: {(v[-1].GetEnd()-v[0].GetStart())/FPS/60:.1f}min  Ton-Clips: {len(a)}, Tonlaenge {sum(x.GetDuration() for x in a)/FPS/60:.1f}min")
print(f"Einstellung: min {min(durs)/FPS:.1f}s  max {max(durs)/FPS:.1f}s  mittel {sum(durs)/len(durs)/FPS:.1f}s")
