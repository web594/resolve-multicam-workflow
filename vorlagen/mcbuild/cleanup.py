# -*- coding: utf-8 -*-
"""Fehlversuche der Multicam-Bauversuche entfernen und die gueltigen Objekte sauber benennen."""
import os, sys
os.environ.setdefault("RESOLVE_SCRIPT_API", r"C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting")
os.environ.setdefault("RESOLVE_SCRIPT_LIB", r"C:\Program Files\Blackmagic Design\DaVinci Resolve\fusionscript.dll")
sys.path.append(os.path.join(os.environ["RESOLVE_SCRIPT_API"], "Modules"))
import DaVinciResolveScript as dvr

NAME = "Projekt-B-2 Projekt-B"
KEEP_SUFFIX = {"Schnitt import 2": f"{NAME} Multicam Schnitt",
               "Multicam import 3": f"{NAME} Multicam",
               "weit import 4":     f"{NAME} weit import",
               "seite import 4":    f"{NAME} seite import",
               "ton import 4":      f"{NAME} ton import"}

proj = dvr.scriptapp("Resolve").GetProjectManager().GetCurrentProject()
mp = proj.GetMediaPool(); root = mp.GetRootFolder()

def walk(f):
    for c in f.GetClipList(): yield c
    for s in f.GetSubFolderList(): yield from walk(s)

def keep_name(n):
    for suf, neu in KEEP_SUFFIX.items():
        if n == f"{NAME} {suf}":
            return neu
    return None

# 1) Timelines: Fehlversuche loeschen
tls = [proj.GetTimelineByIndex(i) for i in range(1, proj.GetTimelineCount()+1)]
weg = []
for t in tls:
    n = t.GetName()
    if "import" in n and keep_name(n) is None:
        weg.append(t)
    if n.startswith("ZZ TEST"):
        weg.append(t)
if weg:
    print("loesche Timelines:", [t.GetName() for t in weg])
    mp.DeleteTimelines(weg)

# 2) MediaPool: verwaiste Multicam-Clips und Timeline-Clips der Fehlversuche
clips = list(walk(root))
weg_c = [c for c in clips
         if ("import" in c.GetName() or c.GetName().startswith("ZZ TEST"))
         and keep_name(c.GetName()) is None
         and c.GetClipProperty("Type") in ("Multicam", "Timeline")]
if weg_c:
    print("loesche MediaPool-Eintraege:", [c.GetName() for c in weg_c])
    mp.DeleteClips(weg_c)

# 3) gueltige Objekte umbenennen
for t in [proj.GetTimelineByIndex(i) for i in range(1, proj.GetTimelineCount()+1)]:
    neu = keep_name(t.GetName())
    if neu:
        print(f"Timeline umbenannt: {t.GetName()}  ->  {neu}")
        t.SetName(neu)
for c in walk(root):
    neu = keep_name(c.GetName())
    if neu:
        print(f"Clip umbenannt: {c.GetName()}  ->  {neu}")
        c.SetName(neu)

print("\n--- Stand ---")
for i in range(1, proj.GetTimelineCount()+1):
    t = proj.GetTimelineByIndex(i)
    print(f"  Timeline: {t.GetName()}")
for c in walk(root):
    if c.GetClipProperty("Type") in ("Multicam",):
        print(f"  Multicam: {c.GetName()} | Frames {c.GetClipProperty('Frames')}")
dvr.scriptapp("Resolve").GetProjectManager().SaveProject()
print("gespeichert.")
