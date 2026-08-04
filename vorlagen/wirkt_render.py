# -*- coding: utf-8 -*-
"""Belastbarer Test (umgeht den Viewer-Cache): 1 Sekunde rendern, Node umschalten, erneut
rendern, mittlere RGB-Werte der Renders vergleichen."""
import os, sys, time, subprocess, glob, shutil
os.environ.setdefault("RESOLVE_SCRIPT_API", r"C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting")
os.environ.setdefault("RESOLVE_SCRIPT_LIB", r"C:\Program Files\Blackmagic Design\DaVinci Resolve\fusionscript.dll")
sys.path.append(os.path.join(os.environ["RESOLVE_SCRIPT_API"], "Modules"))
import DaVinciResolveScript as dvr

OUT = r"C:\claude\resolve-prep\Projekt-B-2\rtest"
TL = "Projekt-B-2 weit import"
IN_TC, OUT_TC = "01:05:12:00", "01:05:12:20"

resolve = dvr.scriptapp("Resolve")
proj = resolve.GetProjectManager().GetCurrentProject()
def timeline(n):
    for i in range(1, proj.GetTimelineCount()+1):
        t = proj.GetTimelineByIndex(i)
        if t.GetName() == n: return t
t = timeline(TL); proj.SetCurrentTimeline(t)
g = (t.GetItemListInTrack("video", 1) or [])[0].GetNodeGraph()

def render(tag):
    d = os.path.join(OUT, tag)
    shutil.rmtree(d, ignore_errors=True); os.makedirs(d, exist_ok=True)
    proj.DeleteAllRenderJobs()
    proj.SetRenderSettings({"SelectAllFrames": False, "MarkIn": t.GetStartFrame() + 0,
                            "MarkOut": t.GetStartFrame() + 20,
                            "TargetDir": d, "CustomName": tag,
                            "FormatWidth": 640, "FormatHeight": 360})
    proj.SetCurrentRenderFormatAndCodec("mp4", "H264")
    job = proj.AddRenderJob()
    proj.StartRendering(job)
    while proj.IsRenderingInProgress():
        time.sleep(1)
    files = glob.glob(os.path.join(d, "*"))
    if not files: return None
    out = subprocess.run(["ffmpeg", "-v", "error", "-i", files[0], "-frames:v", "1",
                          "-vf", "scale=32:18", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         capture_output=True).stdout
    if not out: return None
    return tuple(round(sum(out[i::3]) / len(out[i::3]), 2) for i in range(3))

for n in (1, 2, 5, 6):
    g.SetNodeEnabled(n, True);  an = render(f"n{n}an")
    g.SetNodeEnabled(n, False); aus = render(f"n{n}aus")
    g.SetNodeEnabled(n, True)
    print(f"Node {n} [{g.GetLUT(n) or '-'}]  an={an}  aus={aus}  -> "
          f"{'WIRKT' if an != aus else 'KEINE WIRKUNG'}", flush=True)
shutil.rmtree(OUT, ignore_errors=True)
resolve.GetProjectManager().SaveProject()
