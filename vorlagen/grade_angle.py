# -*- coding: utf-8 -*-
"""Look-Kette auf eine Winkel-Quell-Timeline legen (aktuellen Teil bauen, auf alle kopieren).
6-Node-Struktur:  1=Sony->ARRI(LUT)  2=Korrektur WB/Helligkeit(leer,regelbar)
3=Rec709->LogC(LUT)  4=Filmstock FPE(LUT)  5=Kino(LUT)  6=Feinschliff(leer,regelbar)."""
import os, sys, time, subprocess
os.environ.setdefault("RESOLVE_SCRIPT_API", r"C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting")
os.environ.setdefault("RESOLVE_SCRIPT_LIB", r"C:\Program Files\Blackmagic Design\DaVinci Resolve\fusionscript.dll")
sys.path.append(os.path.join(os.environ["RESOLVE_SCRIPT_API"], "Modules"))
import DaVinciResolveScript as dvr

TLNAME = sys.argv[1] if len(sys.argv)>1 else "260626 Projekt-A weit import"
LUTS = {1:"Sony_SLog3_to_ARRI_Rec709.cube",
        3:"projekt-a/Alexa Rec709 to LOG-C_Impulz.cube",
        4:"projekt-a/Alexa_Kodak Vis3 500T 5219 (NEG)_FPE.cube",
        5:"projekt-a/Projekt-C_Kino_mittel.cube"}
NODES=6
resolve=dvr.scriptapp("Resolve"); proj=resolve.GetProjectManager().GetCurrentProject()
proj.RefreshLUTList()
byname={proj.GetTimelineByIndex(i).GetName():proj.GetTimelineByIndex(i) for i in range(1,proj.GetTimelineCount()+1)}
tl=byname[TLNAME]; proj.SetCurrentTimeline(tl); resolve.OpenPage("color"); time.sleep(0.5)
tl=proj.GetCurrentTimeline()
tl.SetCurrentTimecode(tl.GetStartTimecode()); time.sleep(0.3)
cur=tl.GetCurrentVideoItem()
print("Baue auf:",cur.GetName())
g=cur.GetNodeGraph()
# vorhandene Grades platt: erst reset (zurueck auf 1 Node)
g.ResetAllGrades(); time.sleep(0.2); g=cur.GetNodeGraph()
tries=0
while g.GetNumNodes()<NODES and tries<12:
    subprocess.run(["py", r"C:\claude\resolve-ctl\rctl.py","node-add","serial"], capture_output=True)
    time.sleep(0.4); g=cur.GetNodeGraph(); tries+=1
print("Nodes:",g.GetNumNodes())
for nidx,l in LUTS.items():
    print(" node",nidx,g.SetLUT(nidx,l),"->",g.GetLUT(nidx))
v=tl.GetItemListInTrack("video",1)
others=[it for it in v if it!=cur]
print("CopyGrades ->",cur.CopyGrades(others))
for it in v:
    print("  ",it.GetName(),"nodes",it.GetNodeGraph().GetNumNodes())
