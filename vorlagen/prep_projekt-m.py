# -*- coding: utf-8 -*-
"""Projekt 'Projekt-M Projekt-M' anlegen: Import, Bins, pro Kamera EINE Quell-Timeline
ueber alle 4 Aufnahmebloecke.

Zeitbasis = der zusammenhaengend gelegte Hauptton (001..004 hintereinander).
01:00:00:00 = Ton-Frame 0. Je Block hat jede Kamera einen eigenen Offset
(Kameras liefen vor dem Rekorder -> Offsets negativ -> Kamera-Kopf trimmen).
"""
import os, sys, json, glob, re
os.environ.setdefault("RESOLVE_SCRIPT_API", r"C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting")
os.environ.setdefault("RESOLVE_SCRIPT_LIB", r"C:\Program Files\Blackmagic Design\DaVinci Resolve\fusionscript.dll")
sys.path.append(os.path.join(os.environ["RESOLVE_SCRIPT_API"], "Modules"))
import DaVinciResolveScript as dvr

ROOT = r"E:\Projekt-M Projekt-M"
NAME = "Projekt-M Projekt-M"
PREP = r"C:\claude\resolve-prep\projekt-m"
OFFJ = json.load(open(os.path.join(PREP, "offsets_blocks.json"), encoding="utf-8"))
BL = OFFJ["blocks"]
FPS = 30000/1001
TCBASE = 108000

CAMDIR = {"nah": "k1 nah", "weit": "k2 weit", "seite": "k3 seite"}
TONDIR = os.path.join(ROOT, "t1 Hauptton")
TONFILES = [os.path.join(TONDIR, f"00{i}_330715.wav") for i in (1, 2, 3, 4)]


def frames_to_tc(total):
    ff = total % 30; s = total//30 % 60; m = total//1800 % 60; h = total//108000
    return f"{h:02d}:{m:02d}:{s:02d}:{ff:02d}"


resolve = dvr.scriptapp("Resolve")
assert resolve, "Resolve nicht erreichbar - Resolve starten, Scripting=Lokal"
pm = resolve.GetProjectManager()
existing = pm.GetProjectListInCurrentFolder()
if NAME in existing and "--neu" in sys.argv:
    pm.CloseProject(pm.GetCurrentProject())
    print("loesche vorherigen (leeren) Anlauf:", pm.DeleteProject(NAME))
    existing = pm.GetProjectListInCurrentFolder()
target = NAME
if target in existing:
    n = 2
    while f"{NAME} ({n})" in existing: n += 1
    target = f"{NAME} ({n})"
    print(f"HINWEIS: '{NAME}' existiert -> lege '{target}' an.")
proj = pm.CreateProject(target)
assert proj, "Projekt konnte nicht erstellt werden"
print("Projekt:", target, flush=True)
for k, v in {"timelineFrameRate": "29.97", "timelinePlaybackFrameRate": "29.97",
             "timelineResolutionWidth": "1920",
             "timelineResolutionHeight": "1080", "videoMonitorFormat": "HD 1080p 29.97",
             "colorScienceMode": "davinciYRGB"}.items():
    proj.SetSetting(k, v)

mp = proj.GetMediaPool(); root = mp.GetRootFolder()


def bin_import(bin_name, files):
    binf = mp.AddSubFolder(root, bin_name)
    if binf is None:
        for sf in root.GetSubFolderList():
            if sf.GetName() == bin_name: binf = sf; break
    mp.SetCurrentFolder(binf)
    items = mp.ImportMedia(files) or []
    print(f"  Bin '{bin_name}': {len(items)}/{len(files)} importiert", flush=True)
    by = {}
    for it in items:
        try: by[os.path.normcase(it.GetClipProperty("File Path"))] = it
        except Exception: pass
    return [by[os.path.normcase(f)] for f in files if os.path.normcase(f) in by]


# --- Dateien je Kamera/Block aus offsets_blocks.json (Reihenfolge steht dort) ---
cam_block_files = {c: {} for c in CAMDIR}
for b in ("1", "2", "3", "4"):
    for cam, d in BL[b]["kameras"].items():
        cam_block_files[cam][b] = [os.path.join(ROOT, CAMDIR[cam], n) for n in d["teile"]]

print("-- Import --", flush=True)
cam_items = {}
for cam in CAMDIR:
    allf = [f for b in ("1", "2", "3", "4") for f in cam_block_files[cam][b]]
    got = bin_import(cam, allf)
    cam_items[cam] = {os.path.normcase(i.GetClipProperty("File Path")): i for i in got}
ton_items = bin_import("ton", TONFILES)
assert len(ton_items) == 4, "Ton unvollstaendig"

# --- Blockstarts in Frames = kumulierte Ton-Laengen ---
import subprocess
def ffdur(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                 "-of", "csv=p=0", p], capture_output=True, text=True).stdout)
ton_frames = [int(round(ffdur(p) * FPS)) for p in TONFILES]
bstart = [0]
for f in ton_frames[:-1]:
    bstart.append(bstart[-1] + f)
print("Blockstarts (Frames):", bstart, " Gesamt:", sum(ton_frames), flush=True)

mp.SetCurrentFolder(root)


def make_cam_tl(cam):
    tl = mp.CreateEmptyTimeline(f"{NAME} {cam}")
    tl.SetStartTimecode(frames_to_tc(TCBASE))
    infos = []
    log = []
    for bi, b in enumerate(("1", "2", "3", "4")):
        off_f = int(round(BL[b]["kameras"][cam]["offset_s"] * FPS))
        # off_f < 0: Kamera lief vorher -> Kopf um -off_f trimmen, Start = Blockanfang
        trim = -off_f if off_f < 0 else 0
        rec = bstart[bi] + (off_f if off_f > 0 else 0) + TCBASE
        for p in cam_block_files[cam][b]:
            it = cam_items[cam][os.path.normcase(p)]
            n = int(it.GetClipProperty("Frames"))
            if trim >= n:            # ganzer Teil liegt vor dem Ton-Start
                trim -= n; continue
            # endFrame ist EXKLUSIV -> n, nicht n-1 (sonst 1 Frame Luecke je Teil)
            infos.append({"mediaPoolItem": it, "startFrame": trim, "endFrame": n,
                          "mediaType": 1, "trackIndex": 1, "recordFrame": rec})
            rec += n - trim
            trim = 0
        log.append(f"B{b}:off {off_f}f")
    infos += [{"mediaPoolItem": it, "mediaType": 2, "trackIndex": 1,
               "recordFrame": TCBASE + bstart[i]} for i, it in enumerate(ton_items)]
    mp.AppendToTimeline(infos)
    v = tl.GetItemListInTrack("video", 1) or []
    print(f"  '{NAME} {cam}': {len(v)} Clips, {', '.join(log)}, "
          f"Ende {v[-1].GetEnd()-TCBASE if v else 0}f", flush=True)
    return tl


def make_ton_tl():
    tl = mp.CreateEmptyTimeline(f"{NAME} ton")
    tl.SetStartTimecode(frames_to_tc(TCBASE))
    mp.AppendToTimeline([{"mediaPoolItem": it, "mediaType": 2, "trackIndex": 1,
                          "recordFrame": TCBASE + bstart[i]} for i, it in enumerate(ton_items)])
    a = tl.GetItemListInTrack("audio", 1) or []
    print(f"  '{NAME} ton': {len(a)} Tonteile, Ende {a[-1].GetEnd()-TCBASE if a else 0}f", flush=True)


print("-- Quell-Timelines --", flush=True)
for c in ("nah", "weit", "seite"):
    make_cam_tl(c)
make_ton_tl()

proj.SetSetting("useCustomSettings", "1")
pm.SaveProject()
print("Gespeichert.", flush=True)
