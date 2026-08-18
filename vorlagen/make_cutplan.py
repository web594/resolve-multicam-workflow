# -*- coding: utf-8 -*-
"""Automatischer Multicam-Schnittplan aus dem Transkript (Ton-Zeit) auf WORTEBENE.
Whisper liefert teils sehr lange Segmente (hier eines mit 223 s) -> Schnitte wuerden
dort nie fallen. Daher Phrasen an Wortpausen (>= SMALL_GAP) bilden und darueber schneiden.
Standard 'weit' (Leitkamera). Cutaways mit 'seite' an Absatz-Pausen + Zwang nach MAX_STD.
Schnittgrenzen liegen in den Wortpausen (Stille). Ausgabe: cut_plan.json = [{start,end,angle}]."""
import json

WRD  = r"C:\claude\resolve-prep\projekt-b2\words.json"
OUTP = r"C:\claude\resolve-prep\projekt-b2\cut_plan.json"

# --- RUHIGER SCHNITT (Nutzer-Vorgabe 27.07.2026) -------------------------------
# Beim Projekt-A-Schnitt kamen manche Schnitte zu frueh: nach einem Schnitt braucht der
# Zuschauer ein paar Sekunden, um sich auf das neue Bild einzustellen; folgte dann gleich
# wieder eine kurze Gegen-Einstellung, wirkte es hektisch. Daher: laengere Mindest-
# standzeiten, laengere Cutaways und eine Beruhigungspause nach jedem Cutaway.
SMALL_GAP = 0.40   # Wortpause -> erlaubter Schnittpunkt / Phrasengrenze
PARA_GAP  = 1.20   # groessere Pause -> Absatz -> Cutaway ausloesen   (war 1.00)
CUT_MIN   = 6.0    # Mindestdauer eines Cutaways (s)                  (war 4.0)
CUT_MAX   = 11.0   # Cutaway max (s)                                  (war 8.0)
MAX_STD   = 50.0   # nach so langer weit-Strecke Cutaway erzwingen    (war 40.0)
MIN_SHOT  = 6.0    # kuerzere Einstellungen mit Nachbar verschmelzen  (war 4.0)
CALM_GAP  = 12.0   # NEU: so lange nach einem Cutaway keinen neuen ausloesen
ANFANG    = 192.4  # inhaltlicher Einstieg ("Gruess Gott, meine Damen und Herren"); davor
                   # nur Setup-Gepla_nkel -> dort keine Cutaways, damit der Film frontal startet
STD       = "weit"
CUTAWAY   = "seite"

words = [w for w in json.load(open(WRD, encoding="utf-8")) if w["end"] > w["start"]]

# --- Phrasen an Wortpausen bilden ---
phr = []
cur = {"start": words[0]["start"], "end": words[0]["end"]}
for w in words[1:]:
    if w["start"] - cur["end"] >= SMALL_GAP:
        phr.append(cur); cur = {"start": w["start"], "end": w["end"]}
    else:
        cur["end"] = w["end"]
phr.append(cur)
END = round(phr[-1]["end"], 3)

# 1) Cutaways markieren
angle = [STD] * len(phr)
last_cut_end = max(phr[0]["start"], ANFANG)   # ab inhaltlichem Einstieg zaehlen
i = 0
while i < len(phr):
    s = phr[i]
    # i == 0: kein Trigger -> der Film startet immer auf der Leitkamera (sonst faellt
    # direkt hinter dem Anfang ein Schnitt, was unruhig wirkt).
    gap_before = s["start"] - phr[i-1]["end"] if i > 0 else 0.0
    # Absatz-Trigger erst wieder, wenn der letzte Cutaway CALM_GAP zurueckliegt (ruhiger);
    # der Zwangswechsel nach MAX_STD bleibt davon unberuehrt.
    trigger = (s["start"] >= ANFANG and
               ((gap_before >= PARA_GAP and s["start"] - last_cut_end >= CALM_GAP)
                or (s["start"] - last_cut_end >= MAX_STD)))
    if trigger:
        t0 = s["start"]; j = i
        while j < len(phr) and phr[j]["end"] - t0 <= CUT_MAX:
            angle[j] = CUTAWAY; j += 1
        if j == i:
            angle[j] = CUTAWAY; j += 1
        while j < len(phr) and phr[j-1]["end"] - t0 < CUT_MIN:
            angle[j] = CUTAWAY; j += 1
        last_cut_end = phr[j-1]["end"]
        i = j
    else:
        i += 1

# 2) Spans, Schnittgrenze = Mitte der Wortpause
def boundary(i): return round((phr[i-1]["end"] + phr[i]["start"]) / 2, 3)
spans = []; curA = angle[0]; start = round(phr[0]["start"], 3)
for i in range(1, len(phr)):
    if angle[i] != curA:
        spans.append({"start": start, "end": boundary(i), "angle": curA})
        start = boundary(i); curA = angle[i]
spans.append({"start": start, "end": END, "angle": curA})

# 3) zu kurze Spans verschmelzen, gleiche Nachbarn mergen
changed = True
while changed and len(spans) > 1:
    changed = False
    for i, sp in enumerate(spans):
        if sp["end"] - sp["start"] < MIN_SHOT:
            if i > 0: spans[i-1]["end"] = sp["end"]
            else: spans[i+1]["start"] = sp["start"]
            spans.pop(i); changed = True; break
merged = [spans[0]]
for sp in spans[1:]:
    if sp["angle"] == merged[-1]["angle"]: merged[-1]["end"] = sp["end"]
    else: merged.append(sp)
spans = merged

# 4) lange Spans (Whisper ohne verlaessliche Wortpausen) mechanisch unterteilen:
#    weit-gefuehrtes Muster HOLD s weit + CUT s seite, damit keine Einstellung > SPLIT_MAX steht.
SPLIT_MAX = 55.0; HOLD = 42.0; CUT = 10.0   # ruhiger (war 45/34/7)
out = []
for sp in spans:
    dur = sp["end"] - sp["start"]
    if dur <= SPLIT_MAX:
        out.append(sp); continue
    t = sp["start"]; toggle = STD
    while t < sp["end"] - 1e-6:
        seg = HOLD if toggle == STD else CUT
        e = min(t + seg, sp["end"])
        if sp["end"] - e < MIN_SHOT:      # Rest zu kurz -> anhaengen
            e = sp["end"]
        out.append({"start": round(t, 3), "end": round(e, 3), "angle": toggle})
        t = e; toggle = CUTAWAY if toggle == STD else STD
spans = out
# gleiche Nachbarn erneut mergen
merged = [spans[0]]
for sp in spans[1:]:
    if sp["angle"] == merged[-1]["angle"]: merged[-1]["end"] = sp["end"]
    else: merged.append(sp)
spans = merged

json.dump(spans, open(OUTP, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
from collections import Counter
cnt = Counter(s["angle"] for s in spans)
dur = {a: sum(s["end"]-s["start"] for s in spans if s["angle"]==a) for a in cnt}
print(f"Phrasen: {len(phr)}  Spans: {len(spans)}  " + "  ".join(f"{a}:{cnt[a]}={dur[a]/60:.1f}min" for a in cnt))
print(f"Bereich {spans[0]['start']:.1f}..{END:.1f}s ({(END-spans[0]['start'])/60:.1f}min), mittlere Einstellung {(END-spans[0]['start'])/len(spans):.1f}s")
longest = max(spans, key=lambda s: s['end']-s['start'])
print(f"laengste Einstellung: {longest['end']-longest['start']:.1f}s ({longest['angle']})")
for s in spans[:16]:
    print(f"  {s['start']:7.1f}-{s['end']:7.1f} ({s['end']-s['start']:5.1f}s) {s['angle']}")
