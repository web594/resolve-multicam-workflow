# -*- coding: utf-8 -*-
"""Setzt je Kurzvideo (und im Hauptschnitt) einen Marker MIT DAUER auf den
empfohlenen Kaltstart-Bereich. Nicht-destruktiv: es wird nur hinzugefuegt."""
import sys, json
sys.path.append(r"C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting\Modules")
import DaVinciResolveScript as dvr
FARBE="Fuchsia"
V=json.load(open("kaltstart_final.json",encoding="utf-8"))
proj=dvr.scriptapp("Resolve").GetProjectManager().GetCurrentProject()
TLS={}
for i in range(1,proj.GetTimelineCount()+1):
    t=proj.GetTimelineByIndex(i); TLS[t.GetName()]=t

def karte(t):
    st=t.GetStartFrame()
    return [(it.GetLeftOffset(), it.GetLeftOffset()+it.GetDuration(), it.GetStart()-st)
            for it in t.GetItemListInTrack("video",1)]

def ton2tl(k, f):
    for a,b,t0 in k:
        if a<=f<b: return t0+(f-a)
    return None

def setz(tname, f_in, f_out, name, note):
    t=TLS[tname]; k=karte(t)
    a=ton2tl(k,f_in); b=ton2tl(k,f_out)
    if a is None: print(f"  ! {tname}: Anfang liegt nicht in der Timeline"); return
    if b is None or b<=a: b=a+1
    vorhanden=t.GetMarkers() or {}
    while a in vorhanden: a+=1
    ok=t.AddMarker(a, FARBE, name, note, max(1,b-a))
    print(f"  {tname:38s} Frame {a:7d} Dauer {b-a:5d}  {'ok' if ok else 'FEHLER'}")

for v in V:
    A=[x for x in v["varianten"] if x["tag"]=="A"][0]
    note=(f"Empfohlener Kaltstart ({A['dauer']}s): \"{A['text']}\"  "
          f"| Tonzeit {A['t_in']:.2f}-{A['t_out']:.2f}s")
    print(f"\n#{v['nr']} {v['kurz']}")
    setz(v["timeline"], A["f_in"], A["f_out"], f"Kaltstart #{v['nr']}", note)
    setz("Projekt-M Projekt-M Multicam Schnitt", A["f_in"], A["f_out"], f"Kaltstart #{v['nr']} {v['kurz']}", note)
dvr.scriptapp("Resolve").GetProjectManager().SaveProject()
print("\ngespeichert")
