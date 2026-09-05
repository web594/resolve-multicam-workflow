# -*- coding: utf-8 -*-
"""Markierungs-Timeline importieren, Ton durchgehend anlegen, Clips faerben, Marker setzen."""
import os, sys, json
os.environ.setdefault("RESOLVE_SCRIPT_API", r"C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting")
os.environ.setdefault("RESOLVE_SCRIPT_LIB", r"C:\Program Files\Blackmagic Design\DaVinci Resolve\fusionscript.dll")
sys.path.append(os.path.join(os.environ["RESOLVE_SCRIPT_API"], "Modules"))
import DaVinciResolveScript as dvr

BASE = r"C:\claude\resolve-prep\projekt-n"
NAME = "Projekt-N Projekt-N"
ZIEL = f"{NAME} Multicam Markierung"
FPS  = 30000/1001
TCBASE = 108000
MCLEN = 75495
TONFILES = ["000_200731.wav", "001_200731.wav", "002_200731.wav"]

SEGS = json.load(open(os.path.join(BASE, "markier_segs.json"), encoding="utf-8"))
LAY  = json.load(open(os.path.join(BASE, "layout.json"), encoding="utf-8"))
TONSTART = LAY["tonstart"]; TONGES = 76116
TONLEN = [(TONSTART[i+1] if i+1 < len(TONSTART) else TONGES) - TONSTART[i]
          for i in range(len(TONSTART))]

res = dvr.scriptapp("Resolve"); pm = res.GetProjectManager()
proj = pm.GetCurrentProject(); assert proj.GetName() == NAME, proj.GetName()
mp = proj.GetMediaPool(); root = mp.GetRootFolder()

def walk(f):
    for c in f.GetClipList(): yield c
    for s in f.GetSubFolderList(): yield from walk(s)
items = {}
for c in walk(root): items.setdefault(c.GetName(), c)
TONI = [items[t] for t in TONFILES]

# alte Fassung entfernen
for i in range(proj.GetTimelineCount(), 0, -1):
    t = proj.GetTimelineByIndex(i)
    if t.GetName().startswith(ZIEL):
        mp.DeleteTimelines([t]); print("alte Fassung geloescht")

mp.SetCurrentFolder(root)
tl = mp.ImportTimelineFromFile(os.path.join(BASE, "mcbuild", "markier.drt"),
                               {"timelineName": ZIEL, "importSourceClips": False})
assert tl, "Import fehlgeschlagen"
proj.SetCurrentTimeline(tl)
v = tl.GetItemListInTrack("video", 1)
print(f"importiert: {tl.GetName()} | {len(v)} Videoclips | {tl.GetEndFrame()-TCBASE} Frames")

# --- Ton durchgehend (drei Tascam-Teile), am Bildende gekappt ---
for i, ti in enumerate(TONI):
    a = 0
    b = min(TONLEN[i], MCLEN - TONSTART[i])
    if b <= 0: continue
    mp.AppendToTimeline([{"mediaPoolItem": ti, "startFrame": a, "endFrame": b,
                          "mediaType": 2, "trackIndex": 1,
                          "recordFrame": TCBASE + TONSTART[i]}])
au = tl.GetItemListInTrack("audio", 1)
print(f"Ton: {len(au)} Stuecke, Ende {au[-1].GetEnd()-TCBASE} Frames")

# --- Clipfarben + Marker ---
ok = 0
for it, g in zip(v, SEGS):
    assert it.GetStart() == TCBASE + g["s"], (it.GetStart(), TCBASE+g["s"])
    if g["farbe"]:
        it.SetClipColor(g["farbe"]); ok += 1
        kurz = g["version"] == "Kurzversion"
        it.SetName(f"{'KURZ' if kurz else 'LANG'} {g['nr']:02d}")
        tl.AddMarker(g["s"], "Green" if kurz else "Blue",
                     f"{'Kurzversion' if kurz else 'Langversion'} {g['nr']}",
                     f"Winkel k{g['angle']} | {g['s']/FPS:.1f}-{g['e']/FPS:.1f} s "
                     f"({(g['e']-g['s'])/FPS:.1f} s)", g["e"]-g["s"])
print(f"{ok} Clips gefaerbt, {len(tl.GetMarkers())} Marker gesetzt")

# --- Marker an den Bild-Luecken zwischen den Aufnahmebloecken ---
for cam in ("k1", "k2"):
    bl = LAY["layout"][cam]
    for a, b in zip(bl, bl[1:]):
        if b[2] > a[3]:
            tl.AddMarker(a[3], "Yellow", f"kein Bild {cam}",
                         f"Aufnahmepause {a[0]}->{b[0]}", b[2]-a[3])
pm.SaveProject(); print("gespeichert.")
