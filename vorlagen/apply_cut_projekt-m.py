# -*- coding: utf-8 -*-
"""Verschachtelte Schnitt-Timeline 'Projekt-M Projekt-M Schnitt' aus dem cut_plan.
Die Quell-Timelines sind TON-indiziert (StartTC 01:00:00:00 = Ton-Frame 0),
darum gilt: Ton-Frame == Quell-Timeline-Frame. Kein Offset noetig."""
import os, sys, json
os.environ.setdefault("RESOLVE_SCRIPT_API", r"C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting")
os.environ.setdefault("RESOLVE_SCRIPT_LIB", r"C:\Program Files\Blackmagic Design\DaVinci Resolve\fusionscript.dll")
sys.path.append(os.path.join(os.environ["RESOLVE_SCRIPT_API"], "Modules"))
import DaVinciResolveScript as dvr
from collections import Counter

NAME = "Projekt-M Projekt-M"
BASE = r"C:\claude\resolve-prep\projekt-m"
FPS = 30000/1001
CAMS = ("nah", "weit", "seite")
PLAN = json.load(open(os.path.join(BASE, "cut_plan.json"), encoding="utf-8"))

proj = dvr.scriptapp("Resolve").GetProjectManager().GetCurrentProject()
assert proj.GetName() == NAME, f"falsches Projekt offen: {proj.GetName()}"
mp = proj.GetMediaPool(); root = mp.GetRootFolder()


def walk(f):
    for c in f.GetClipList(): yield c
    for s in f.GetSubFolderList(): yield from walk(s)


items = {c.GetName(): c for c in walk(root)}
SRC = {a: items[f"{NAME} {a}"] for a in CAMS + ("ton",)}

# Verfuegbarkeitsfenster je Kamera (Ton-Frames) aus den Timeline-Clips
WIN = {}
for i in range(1, proj.GetTimelineCount()+1):
    t = proj.GetTimelineByIndex(i)
    for a in CAMS:
        if t.GetName() == f"{NAME} {a}":
            v = t.GetItemListInTrack("video", 1)
            WIN[a] = [(it.GetStart()-108000, it.GetEnd()-108000) for it in v]
TONLEN = None
for i in range(1, proj.GetTimelineCount()+1):
    t = proj.GetTimelineByIndex(i)
    if t.GetName() == f"{NAME} ton":
        a = t.GetItemListInTrack("audio", 1)
        TONLEN = a[-1].GetEnd()-108000
print("Tonlaenge:", TONLEN, "Frames")


def avail(a, s, e):
    return any(x <= s and e <= y for x, y in WIN[a])


for i in range(proj.GetTimelineCount(), 0, -1):
    t = proj.GetTimelineByIndex(i)
    if t.GetName() == f"{NAME} Schnitt":
        mp.DeleteTimelines([t])

raw = []
for sp in PLAN:
    s = int(round(sp["start"]*FPS)); e = int(round(sp["end"]*FPS))
    e = min(e, TONLEN)
    if e <= s: continue
    t = s
    while t < e:
        pref = sp["angle"] if avail(sp["angle"], t, t+1) else \
            next((c for c in CAMS if avail(c, t, t+1)), None)
        if pref is None:
            nxt = [x for c in CAMS for x, _ in WIN[c] if x > t]
            if not nxt: break
            t = min(nxt); continue
        seg_end = min(e, max(y for x, y in WIN[pref] if x <= t))
        raw.append([pref, t, seg_end]); t = seg_end

mrg = []
for a, s, e in raw:
    if mrg and mrg[-1][0] == a and s == mrg[-1][2]: mrg[-1][2] = e
    else: mrg.append([a, s, e])

tl = mp.CreateEmptyTimeline(f"{NAME} Schnitt")
tl.SetStartTimecode("01:00:00:00")
infos = []
rec = 108000
for a, s, e in mrg:
    infos.append({"mediaPoolItem": SRC[a], "startFrame": s, "endFrame": e,
                  "mediaType": 1, "trackIndex": 1, "recordFrame": rec})
    rec += e - s
# ⭐⭐ Der Ton MUSS genauso gestueckelt werden wie das Bild.
# Der Schnitt legt die Clips ohne Luecken hintereinander, ueberspringt aber Stellen
# ohne Bild (Blockgrenzen). Ein durchgehender Tonclip laeuft dadurch immer weiter
# weg — bei Projekt-M waren es am Ende 95 Sekunden.
ber = []
for a, s, e in mrg:
    if ber and ber[-1][1] == s:
        ber[-1][1] = e
    else:
        ber.append([s, e])
rec = 108000
for s, e in ber:
    infos.append({"mediaPoolItem": SRC["ton"], "startFrame": s, "endFrame": e,
                  "mediaType": 2, "trackIndex": 1, "recordFrame": rec})
    rec += e - s
print(f"Ton in {len(ber)} Stueck(en) passend zum Bild")
mp.AppendToTimeline(infos)

v = tl.GetItemListInTrack("video", 1) or []
cnt = Counter(a for a, _, _ in mrg)
print(f"Schnitt: {len(v)} Clips (geplant {len(mrg)}), {dict(cnt)}")
print(f"  Dauer {sum(e-s for _, s, e in mrg)/FPS/60:.1f} min")
json.dump([{"angle": a, "s": s, "e": e} for a, s, e in mrg],
          open(os.path.join(BASE, "cut_final.json"), "w", encoding="utf-8"), indent=1)
dvr.scriptapp("Resolve").GetProjectManager().SaveProject()
print("gespeichert.")
