# -*- coding: utf-8 -*-
"""Titel-Vorspann OVERLAY (ohne Ripple) auf eine Timeline mit vorhandenem Inhalt.
Pro Element werden alle Spuren AUSSER der Zielspur gesperrt -> der Ripple-Insert
verschiebt nur die (leere) Zielspur, V1/A1 bleiben stehen. Nutzt titel.py-Helfer.
Aufruf:  py titel_overlay.py <vorlagen-ordner> <timeline-fragment> \
             --text1 "..." --text2 "..."  [--nur-test]
"""
import os, sys, time, json, argparse
sys.path.append(r"C:\claude\resolve-ctl")
os.environ.setdefault("RESOLVE_SCRIPT_API", r"C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting")
os.environ.setdefault("RESOLVE_SCRIPT_LIB", r"C:\Program Files\Blackmagic Design\DaVinci Resolve\fusionscript.dll")
import titel as T
from titellib import patch_text, zeit_normalisieren
import keys

def lock_except(tl, keep_v):
    for v in range(1, tl.GetTrackCount("video")+1):
        tl.SetTrackLock("video", v, v != keep_v)
    for a in range(1, tl.GetTrackCount("audio")+1):
        tl.SetTrackLock("audio", a, True)

def unlock_all(tl):
    for v in range(1, tl.GetTrackCount("video")+1):
        tl.SetTrackLock("video", v, False)
    for a in range(1, tl.GetTrackCount("audio")+1):
        tl.SetTrackLock("audio", a, False)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ordner"); ap.add_argument("timeline")
    ap.add_argument("--text1"); ap.add_argument("--text2"); ap.add_argument("--text3")
    ap.add_argument("--nur-test", action="store_true")
    ap.add_argument("--nur-titel", action="store_true")
    a = ap.parse_args()
    texte = [t for t in (a.text1, a.text2, a.text3) if t is not None]

    resolve = T.verbinde(); proj = resolve.GetProjectManager().GetCurrentProject()
    tl = T.hole_timeline(proj, a.timeline); proj.SetCurrentTimeline(tl)
    resolve.OpenPage("edit"); time.sleep(0.8)
    fps = float(tl.GetSetting("timelineFrameRate") or 25)
    start = T.timeline_start(tl, fps)
    v = json.load(open(os.path.join(a.ordner, "vorlage.json"), encoding="utf-8"))
    qfps = float(v["quelle"].get("fps") or fps); skala = fps/qfps if qfps else 1.0

    def v1_start():
        it = tl.GetItemListInTrack("video",1)[0]; return it.GetStart()-start

    elemente = [e for e in v["elemente"] if e.get("typ") in ("titel","anpassungsclip")]
    if a.nur_test:
        elemente = [e for e in elemente if e.get("typ")=="anpassungsclip"]
    if a.nur_titel:
        elemente = [e for e in elemente if e.get("typ")=="titel"]
    print("V1[0] vor Einbau:", v1_start())

    ti = 0
    for e in elemente:
        typ = e["typ"]; ziel = int(e.get("spur",2))
        rel = int(e["start_frame"]*skala); dauer = max(1,int(e["dauer"]*skala))
        while tl.GetTrackCount("video") < ziel: tl.AddTrack("video")
        lock_except(tl, ziel)
        # Zielspur waehlen (Alt+Nr; Resolve muss im Vordergrund sein)
        keys.chord(f"alt+{ziel}"); time.sleep(0.35)
        tl.SetCurrentTimecode(T.frames_zu_tc(start+rel, fps))
        try: tl.SetMarkInOut(rel, rel+dauer-1, "all")
        except Exception: pass
        if typ == "titel":
            s = open(os.path.join(a.ordner, e["setting"]), encoding="utf-8").read()
            roh = texte[ti] if ti < len(texte) else None
            if roh: s,_ = patch_text(s, roh.replace("\\n","\n"))
            s = zeit_normalisieren(s, 0)
            use = os.path.join(a.ordner, f"_ov_{ti}.setting"); open(use,"w",encoding="utf-8").write(s)
            it = tl.InsertFusionTitleIntoTimeline("Text+")
            if it is None:  # Zielspur evtl. abgewaehlt -> nochmal togglen
                keys.chord(f"alt+{ziel}"); time.sleep(0.35); it = tl.InsertFusionTitleIntoTimeline("Text+")
            if it: it.ImportFusionComp(use); ti += 1
        else:
            it = tl.InsertGeneratorIntoTimeline("Adjustment Clip")
            if it is None:
                keys.chord(f"alt+{ziel}"); time.sleep(0.35); it = tl.InsertGeneratorIntoTimeline("Adjustment Clip")
        spur = "?"
        try:
            tt = it.GetTrackTypeAndIndex(); spur = tt[1] if tt else "?"
        except Exception: pass
        try: tl.ClearMarkInOut("all")
        except Exception: pass
        print(f"  {typ}: -> V{spur}  V1[0] jetzt {v1_start()}  (Ziel-Spur {ziel})")
        # Zielspur wieder freigeben fuer den naechsten Schritt
        keys.chord(f"alt+{ziel}"); time.sleep(0.2)
    unlock_all(tl)
    print("V1[0] nach Einbau:", v1_start(), "| Vtracks", tl.GetTrackCount("video"))
    resolve.GetProjectManager().SaveProject(); print("gespeichert.")

main()
