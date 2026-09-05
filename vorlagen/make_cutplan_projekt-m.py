# -*- coding: utf-8 -*-
"""Automatischer Multicam-Schnittplan fuer 'Projekt-M Projekt-M' (Ton-Zeit = zusammenhaengender
Hauptton der 4 Bloecke). Leitkamera nah; Auflockerung abwechselnd weit und seite.
Beruecksichtigt, dass am Ende jedes Aufnahmeblocks einzelne Kameras schon gestoppt hatten
(dort steht die betreffende Kamera nicht zur Verfuegung).
Ausgabe: cut_plan.json = [{start,end,angle}] in Ton-Sekunden."""
import json, os, subprocess
from collections import Counter

BASE = r"C:\claude\resolve-prep\projekt-m"
WRD = os.path.join(BASE, "words.json")
OUTP = os.path.join(BASE, "cut_plan.json")
FPS = 30000/1001

# --- ruhiger Schnitt (Nutzer-Vorgabe 27.07.2026) ---
SMALL_GAP = 0.40
PARA_GAP = 1.20
CUT_MIN = 6.0
CUT_MAX = 11.0
MAX_STD = 50.0
MIN_SHOT = 6.0
CALM_GAP = 12.0
SPLIT_MAX = 55.0; HOLD = 42.0; CUT = 10.0
STD = "nah"
CUTAWAYS = ["weit", "seite"]
ANFANG = float(os.environ.get("PROJEKT-M_ANFANG", "0"))

# --- Verfuegbarkeit je Kamera aus den Sync-Daten -------------------------------
OFFJ = json.load(open(os.path.join(BASE, "offsets_blocks.json"), encoding="utf-8"))["blocks"]
TON = r"E:\Projekt-M Projekt-M\t1 Hauptton"


def ffdur(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                 "-of", "csv=p=0", p], capture_output=True, text=True).stdout)


tondur = [ffdur(os.path.join(TON, f"00{i}_330715.wav")) for i in (1, 2, 3, 4)]
bstart = [0.0]
for d in tondur[:-1]:
    bstart.append(bstart[-1] + d)
ENDE_TON = sum(tondur)

avail = {c: [] for c in ("nah", "weit", "seite")}
for bi, b in enumerate("1234"):
    for cam, d in OFFJ[b]["kameras"].items():
        off = d["offset_s"]
        s = bstart[bi] + max(0.0, off)
        e = bstart[bi] + off + d["dauer_s"]
        avail[cam].append((s, min(e, bstart[bi] + tondur[bi])))


def da(cam, t0, t1):
    """Ist cam im ganzen Bereich [t0,t1] vorhanden?"""
    return any(s <= t0 and t1 <= e for s, e in avail[cam])


words = [w for w in json.load(open(WRD, encoding="utf-8")) if w["end"] > w["start"]]
phr = []
cur = {"start": words[0]["start"], "end": words[0]["end"]}
for w in words[1:]:
    if w["start"] - cur["end"] >= SMALL_GAP:
        phr.append(cur); cur = {"start": w["start"], "end": w["end"]}
    else:
        cur["end"] = w["end"]
phr.append(cur)
END = round(phr[-1]["end"], 3)

angle = [STD] * len(phr)
last_cut_end = max(phr[0]["start"], ANFANG)
turn = 0
i = 0
while i < len(phr):
    s = phr[i]
    gap_before = s["start"] - phr[i-1]["end"] if i > 0 else 0.0
    trigger = (s["start"] >= ANFANG and
               ((gap_before >= PARA_GAP and s["start"] - last_cut_end >= CALM_GAP)
                or (s["start"] - last_cut_end >= MAX_STD)))
    if trigger:
        t0 = s["start"]; j = i
        while j < len(phr) and phr[j]["end"] - t0 <= CUT_MAX:
            j += 1
        if j == i: j += 1
        while j < len(phr) and phr[j-1]["end"] - t0 < CUT_MIN:
            j += 1
        t1 = phr[j-1]["end"]
        # abwechselnd; wenn die gewuenschte Kamera dort fehlt, die andere nehmen
        cam = None
        for k in range(len(CUTAWAYS)):
            c = CUTAWAYS[(turn + k) % len(CUTAWAYS)]
            if da(c, t0, t1): cam = c; break
        if cam is None:
            i = j; continue
        for x in range(i, j): angle[x] = cam
        turn += 1
        last_cut_end = t1
        i = j
    else:
        i += 1

# Leitkamera-Loecher schliessen: wo nah fehlt, auf weit bzw. seite
for idx, p in enumerate(phr):
    if angle[idx] == STD and not da(STD, p["start"], p["end"]):
        for c in CUTAWAYS + ["nah"]:
            if da(c, p["start"], p["end"]): angle[idx] = c; break


def boundary(i): return round((phr[i-1]["end"] + phr[i]["start"]) / 2, 3)


spans = []; curA = angle[0]; start = round(phr[0]["start"], 3)
for i in range(1, len(phr)):
    if angle[i] != curA:
        spans.append({"start": start, "end": boundary(i), "angle": curA})
        start = boundary(i); curA = angle[i]
spans.append({"start": start, "end": END, "angle": curA})

changed = True
while changed and len(spans) > 1:
    changed = False
    for i, sp in enumerate(spans):
        if sp["end"] - sp["start"] < MIN_SHOT:
            if i > 0: spans[i-1]["end"] = sp["end"]
            else: spans[i+1]["start"] = sp["start"]
            spans.pop(i); changed = True; break


def merge(sps):
    m = [sps[0]]
    for sp in sps[1:]:
        if sp["angle"] == m[-1]["angle"]: m[-1]["end"] = sp["end"]
        else: m.append(sp)
    return m


spans = merge(spans)

out = []
tog = 0
for sp in spans:
    dur = sp["end"] - sp["start"]
    if dur <= SPLIT_MAX:
        out.append(sp); continue
    t = sp["start"]; std_turn = True
    while t < sp["end"] - 1e-6:
        seg = HOLD if std_turn else CUT
        e = min(t + seg, sp["end"])
        if sp["end"] - e < MIN_SHOT: e = sp["end"]
        if std_turn:
            cam = sp["angle"]
        else:
            cam = None
            for k in range(len(CUTAWAYS)):
                c = CUTAWAYS[(tog + k) % len(CUTAWAYS)]
                if c != sp["angle"] and da(c, t, e): cam = c; break
            tog += 1
            if cam is None: cam = sp["angle"]
        out.append({"start": round(t, 3), "end": round(e, 3), "angle": cam})
        t = e; std_turn = not std_turn
spans = merge(out)

json.dump(spans, open(OUTP, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
cnt = Counter(s["angle"] for s in spans)
dur = {a: sum(s["end"]-s["start"] for s in spans if s["angle"] == a) for a in cnt}
print(f"Phrasen: {len(phr)}  Einstellungen: {len(spans)}  " +
      "  ".join(f"{a}:{cnt[a]}={dur[a]/60:.1f}min" for a in cnt))
tot = spans[-1]["end"] - spans[0]["start"]
print(f"Bereich {spans[0]['start']:.1f}..{END:.1f}s ({tot/60:.1f} min), "
      f"mittlere Einstellung {tot/len(spans):.1f}s")
lg = max(spans, key=lambda s: s['end']-s['start'])
print(f"laengste Einstellung: {lg['end']-lg['start']:.1f}s ({lg['angle']}) bei {lg['start']:.0f}s")
