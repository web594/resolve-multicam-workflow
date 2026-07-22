# -*- coding: utf-8 -*-
"""Projekt '260709 Projekt-B' anlegen: Import, Bins, und pro Kamera eine
Quell-Timeline. Wie Projekt-C: Tascab lief VOR den Kameras (Offsets positiv),
daher Video ab Frame 0 (kein Trim) und Hauptton am Kopf um offset getrimmt, damit
Ton auf der Quell-Timeline zum Bild passt. Start-TC = 01:00:00:00 + offset (gemeinsame
Referenz 01:00:00:00 = Ton-Start). 1920x1080, 29.97. 2 Kameras: weit + seite."""
import os, sys, json
os.environ.setdefault("RESOLVE_SCRIPT_API", r"C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting")
os.environ.setdefault("RESOLVE_SCRIPT_LIB", r"C:\Program Files\Blackmagic Design\DaVinci Resolve\fusionscript.dll")
sys.path.append(os.path.join(os.environ["RESOLVE_SCRIPT_API"], "Modules"))
import DaVinciResolveScript as dvr

ROOT = r"E:\260709 Projekt-B"
NAME = "260709 Projekt-B"
OFF  = json.load(open(r"C:\claude\resolve-prep\projekt-b\offsets.json", encoding="utf-8"))["sources"]

CAMS = {
    "weit":  [os.path.join(ROOT, "weit",  f"SHOGUNU_S001_S001_T019_0{i}.MOV") for i in range(2)],
    "seite": [os.path.join(ROOT, "seite", f"SHOGUNU_S001_S001_T019_0{i}.MOV") for i in range(2)],
}
HAUPTTON = os.path.join(ROOT, "dr10L", "001_181212.wav")
START_TC = "01:00:00:00"; TCBASE = 108000  # 01:00:00:00 @30fps NDF

def frames_to_tc(total):
    ff=total%30; s=total//30%60; m=total//1800%60; h=total//108000
    return f"{h:02d}:{m:02d}:{s:02d}:{ff:02d}"

resolve = dvr.scriptapp("Resolve")
pm = resolve.GetProjectManager()

existing = pm.GetProjectListInCurrentFolder()
target = NAME
if target in existing:
    n = 2
    while f"{NAME} ({n})" in existing: n += 1
    target = f"{NAME} ({n})"
    print(f"HINWEIS: '{NAME}' existiert -> lege '{target}' an.")
proj = pm.CreateProject(target)
assert proj, "Projekt konnte nicht erstellt werden"
print("Projekt:", target)
for k, v in {"timelineFrameRate":"29.97","timelineResolutionWidth":"1920",
             "timelineResolutionHeight":"1080","videoMonitorFormat":"HD 1080p 29.97"}.items():
    proj.SetSetting(k, v)

mp = proj.GetMediaPool(); root = mp.GetRootFolder()

def bin_import(bin_name, files):
    binf = mp.AddSubFolder(root, bin_name)
    if binf is None:
        for sf in root.GetSubFolderList():
            if sf.GetName() == bin_name: binf = sf; break
    mp.SetCurrentFolder(binf)
    items = mp.ImportMedia(files) or []
    print(f"  Bin '{bin_name}': {len(items)}/{len(files)} importiert")
    by = {}
    for it in items:
        try: by[os.path.normcase(it.GetClipProperty("File Path"))] = it
        except Exception: pass
    return [by[os.path.normcase(f)] for f in files if os.path.normcase(f) in by]

print("-- Import --")
cam_items = {c: bin_import(c, CAMS[c]) for c in CAMS}
ton_item = bin_import("ton", [HAUPTTON])[0]

def make_cam_tl(cam):
    off_f = OFF[cam]["frames"]                     # positiv: Kamera startet off_f nach Ton
    tl = mp.CreateEmptyTimeline(f"{NAME} {cam}")
    tl.SetStartTimecode(frames_to_tc(TCBASE + off_f))
    parts = cam_items[cam]
    clips = [{"mediaPoolItem": p, "mediaType": 1} for p in parts]   # Video ganz, kein Trim
    mp.AppendToTimeline(clips)
    mp.AppendToTimeline([{"mediaPoolItem": ton_item, "startFrame": off_f, "mediaType": 2}])  # Ton passend getrimmt
    v = tl.GetItemListInTrack("video", 1)
    print(f"  '{NAME} {cam}': off {off_f}f, {len(parts)} Videoteile ({v[-1].GetEnd()-tl.GetStartFrame()}f) + Ton, StartTC {tl.GetStartTimecode()}")
    return tl

def make_ton_tl():
    tl = mp.CreateEmptyTimeline(f"{NAME} ton")
    tl.SetStartTimecode(START_TC)
    mp.AppendToTimeline([{"mediaPoolItem": ton_item, "mediaType": 2}])
    print(f"  '{NAME} ton': nur Hauptton, StartTC {tl.GetStartTimecode()}")

print("-- Quell-Timelines --")
mp.SetCurrentFolder(root)
for c in CAMS: make_cam_tl(c)
make_ton_tl()

proj.SetSetting("useCustomSettings", "1")
pm.SaveProject()
print("Gespeichert. Naechster Schritt: make_cutplan + apply_cut_nested + Multicam.")
