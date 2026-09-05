# -*- coding: utf-8 -*-
"""Prueft in jeder Kurzvideo-Timeline, ob Bild und Ton an JEDER Stelle dieselbe
Ton-Zeit zeigen.

Bild: der Multicam-Clip traegt in GetLeftOffset() den Multicam-Frame — und weil der
Multicam-Clip bei Ton-Frame 0 beginnt, IST das die Ton-Zeit des Bildes.
Ton:  aus Position und Anfang des jeweiligen Tonclips.
Beides muss an derselben Timeline-Position denselben Wert ergeben."""
import os, sys
os.environ.setdefault("RESOLVE_SCRIPT_API", r"C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting")
os.environ.setdefault("RESOLVE_SCRIPT_LIB", r"C:\Program Files\Blackmagic Design\DaVinci Resolve\fusionscript.dll")
sys.path.append(os.path.join(os.environ["RESOLVE_SCRIPT_API"], "Modules"))
import DaVinciResolveScript as dvr

FPS = 30000/1001
r = dvr.scriptapp("Resolve"); p = r.GetProjectManager().GetCurrentProject()

for i in range(1, p.GetTimelineCount()+1):
    tl = p.GetTimelineByIndex(i)
    n = tl.GetName()
    if " #" not in n and "Multicam Schnitt" not in n: continue
    v = tl.GetItemListInTrack("video", 1) or []
    a = tl.GetItemListInTrack("audio", 1) or []
    if not v or not a: continue
    # Tonspur: Liste (tl_start, tl_end, ton_start)
    aud = [(x.GetStart(), x.GetEnd(), x.GetLeftOffset()) for x in a]

    def ton_bei(pos):
        for s, e, off in aud:
            if s <= pos < e:
                return off + (pos - s)
        return None

    schlimm = 0; summe = 0; beispiele = []
    for it in v:
        pos = it.GetStart() + it.GetDuration()//2      # Mitte des Clips
        bild = it.GetLeftOffset() + it.GetDuration()//2
        ton = ton_bei(pos)
        if ton is None: continue
        d = bild - ton
        summe += 1
        if abs(d) > 2:
            schlimm += 1
            if len(beispiele) < 3:
                beispiele.append((round((pos-108000)/FPS, 1), round(d/FPS, 2)))
    marke = "OK" if schlimm == 0 else "VERSATZ"
    print(f"{n[13:]:26} {summe:5} Clips geprueft | abweichend {schlimm:5} | {marke}"
          + ("  Beispiele (Position s, Versatz s): " + str(beispiele) if beispiele else ""))
