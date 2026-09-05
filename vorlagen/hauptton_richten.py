# -*- coding: utf-8 -*-
"""Tonspur des Hauptschnitts an die Stauchung des Bildes anpassen.

Der Auto-Schnitt legt die Clips ohne Luecken hintereinander, ueberspringt aber die
Stellen ohne Bild (Blockgrenzen). Ein DURCHGEHENDER Tonclip laeuft dadurch immer
weiter weg (hier 1,6 s am Anfang, danach 26 s / 85 s / 95 s). Der Ton muss in
genauso viele Stuecke zerlegt werden wie das Bild Segmente hat."""
import os, sys, json
os.environ.setdefault("RESOLVE_SCRIPT_API", r"C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting")
os.environ.setdefault("RESOLVE_SCRIPT_LIB", r"C:\Program Files\Blackmagic Design\DaVinci Resolve\fusionscript.dll")
sys.path.append(os.path.join(os.environ["RESOLVE_SCRIPT_API"], "Modules"))
import DaVinciResolveScript as dvr

BASE = r"C:\claude\resolve-prep\projekt-m"
NAME = "Projekt-M Projekt-M"
TL = f"{NAME} Multicam Schnitt"
FPS = 30000/1001
TCBASE = 108000

CUT = json.load(open(os.path.join(BASE, "cut_final.json"), encoding="utf-8"))
# zusammenhaengende Bereiche der Ton-Zeit bilden
ber = []
for x in CUT:
    if ber and ber[-1][1] == x["s"]:
        ber[-1][1] = x["e"]
    else:
        ber.append([x["s"], x["e"]])
print(f"{len(ber)} zusammenhaengende Bereiche:")
acc = 0
stuecke = []
for a, b in ber:
    stuecke.append((a, b, TCBASE + acc))
    print(f"   ton {a:7}-{b:7} ({(b-a)/FPS/60:6.1f} min) -> Timeline {TCBASE+acc}")
    acc += b - a

r = dvr.scriptapp("Resolve"); p = r.GetProjectManager().GetCurrentProject()
mp = p.GetMediaPool()
tl = next(p.GetTimelineByIndex(i) for i in range(1, p.GetTimelineCount()+1)
          if p.GetTimelineByIndex(i).GetName() == TL)
p.SetCurrentTimeline(tl)


def walk(f):
    for c in f.GetClipList(): yield c
    for s in f.GetSubFolderList(): yield from walk(s)


ton = {c.GetName(): c for c in walk(mp.GetRootFolder())}[f"{NAME} ton"]
alt = tl.GetItemListInTrack("audio", 1) or []
if alt:
    print("alte Tonspur entfernen:", tl.DeleteClips(alt, False))
mp.AppendToTimeline([{"mediaPoolItem": ton, "startFrame": a, "endFrame": b,
                      "mediaType": 2, "trackIndex": 1, "recordFrame": t0}
                     for a, b, t0 in stuecke])
a = tl.GetItemListInTrack("audio", 1) or []
v = tl.GetItemListInTrack("video", 1) or []
print(f"neue Tonspur: {len(a)} Stuecke, Ende {a[-1].GetEnd()} (Bild endet {v[-1].GetEnd()})")
r.GetProjectManager().SaveProject()
print("gespeichert.")
