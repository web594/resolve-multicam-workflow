# -*- coding: utf-8 -*-
"""Look als GETEILTE Nodes via Color Group (Projekt-A).
Group Pre-Clip (geteilt): Sony->ARRI. Clip-Eprojekt-d (pro Kamera): Korrektur.
Group Post-Clip (geteilt): Rec709->LogC, Filmstock, Kino.
Schritt 1 hier: Gruppe anlegen, alle 12 Quell-Clips zuordnen, Clip-Grades platten,
Pre-Clip-LUT setzen. Post-Clip-Nodes (3) werden per GUI ergaenzt, dann LUTs gesetzt."""
import os, sys, time
os.environ.setdefault("RESOLVE_SCRIPT_API", r"C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting")
os.environ.setdefault("RESOLVE_SCRIPT_LIB", r"C:\Program Files\Blackmagic Design\DaVinci Resolve\fusionscript.dll")
sys.path.append(os.path.join(os.environ["RESOLVE_SCRIPT_API"], "Modules"))
import DaVinciResolveScript as dvr
resolve=dvr.scriptapp("Resolve"); proj=resolve.GetProjectManager().GetCurrentProject()
proj.RefreshLUTList()
GRP="Look Projekt-A"
byname={proj.GetTimelineByIndex(i).GetName():proj.GetTimelineByIndex(i) for i in range(1,proj.GetTimelineCount()+1)}

# vorhandene gleichnamige Gruppe entfernen
for g in proj.GetColorGroupsList():
    if g.GetName()==GRP: proj.DeleteColorGroup(g)
grp=proj.AddColorGroup(GRP)
print("Gruppe:", grp.GetName())

clips=[]
for tln in ("260626 Projekt-A nah import","260626 Projekt-A weit import"):
    t=byname[tln]
    for it in t.GetItemListInTrack("video",1):
        clips.append(it)
print("Quell-Clips:", len(clips))

for it in clips:
    it.GetNodeGraph().ResetAllGrades()        # Clip-Eprojekt-d platten (Look kommt in die Gruppe)
    ok=it.AssignToColorGroup(grp)
print("zugeordnet + Clip-Grades geplattet")

# Pre-Clip (geteilt): Sony->ARRI
pre=grp.GetPreClipNodeGraph()
print("Pre-Clip nodes:", pre.GetNumNodes(), "SetLUT:", pre.SetLUT(1,"Sony_SLog3_to_ARRI_Rec709.cube"), "->", pre.GetLUT(1))
post=grp.GetPostClipNodeGraph()
print("Post-Clip nodes (soll 1, brauchen 3):", post.GetNumNodes())
proj.GetMediaPool()  # noop
print("verify group clips:", len(grp.GetClipsInTimeline()))
