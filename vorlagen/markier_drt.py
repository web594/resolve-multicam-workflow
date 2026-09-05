# -*- coding: utf-8 -*-
"""Markierungs-Timeline: VOLLES Material als echte Multicam, nichts geschnitten,
nur an den Passagengrenzen unterteilt und farbig markiert.

Gruen  = Stueck geht in die Kurzversion
Blau   = Stueck geht in die Langversion
farblos= wird nicht verwendet (bleibt vollstaendig erhalten)

Zeitachse bleibt DECKUNGSGLEICH mit der Tonzeit (Timeline-Frame = 108000 + Ton-Frame),
damit man jede Fundstelle direkt im Transkript wiederfindet.
"""
import os, re, json, uuid, zipfile

BASE = r"C:\claude\resolve-prep\projekt-n"
NAME = "Projekt-N Projekt-N"
SRC  = os.path.join(BASE, "mcbuild", "mcs.drt")
ZIEL = os.path.join(BASE, "mcbuild", "markier.drt")
FPS  = 30000/1001
TCBASE = 108000
MCLEN = 75495                      # Laenge des Multicam-Clips in Frames

PLAN = json.load(open(os.path.join(BASE, "cut_plan.json"), encoding="utf-8"))

# --- Passagen -> Frames, sortiert ---
pas = []
for p in PLAN:
    pas.append({"s": int(round(p["start"]*FPS)), "e": int(round(p["end"]*FPS)),
                "angle": p["angle"], "version": p["version"], "farbe": p["farbe"]})
pas.sort(key=lambda x: x["s"])
for a, b in zip(pas, pas[1:]):
    assert a["e"] <= b["s"], "Passagen ueberlappen"

# --- lueckenlose Segmentliste ueber die volle Laenge ---
segs = []
cur = 0
kurz = lang = 0
for p in pas:
    if p["s"] > cur:
        segs.append({"s": cur, "e": p["s"], "angle": 1, "version": None, "farbe": None})
    if p["version"] == "Kurzversion": kurz += 1; nr = kurz
    else:                             lang += 1; nr = lang
    segs.append({**p, "nr": nr})
    cur = p["e"]
if cur < MCLEN:
    segs.append({"s": cur, "e": MCLEN, "angle": 1, "version": None, "farbe": None})

# --- Musterbloecke aus dem Hauptschnitt (FieldsBlob = Winkel) ---
z = zipfile.ZipFile(SRC)
files = {n: z.read(n) for n in z.namelist()}
CONT = max((n for n in files if n.startswith("SeqContainer/")),
           key=lambda n: files[n].count(b"<Sm2TiVideoClip DbId="))
cd = files[CONT].decode("utf-8")

blocks = []
for m in re.finditer(r"<Element>\s*<Sm2TiVideoClip DbId=", cd):
    s = m.start()
    e = cd.index("</Element>", cd.index("</Sm2TiVideoClip>", s)) + len("</Element>")
    blocks.append({"text": cd[s:e], "a": s, "b": e})
LIST_A, LIST_B = blocks[0]["a"], blocks[-1]["b"]
# Plan-Reihenfolge == Clip-Reihenfolge im Schnitt (durch In-Werte belegt)
MUSTER = {1: blocks[2]["text"], 2: blocks[3]["text"]}
print(f"Muster: Angle1 {len(MUSTER[1])} B, Angle2 {len(MUSTER[2])} B")

def neue_ids(t):
    for old in set(re.findall(r'DbId="([0-9a-f-]{36})"', t)):
        t = t.replace(old, str(uuid.uuid4()))
    return t

def setz(t, tag, val):
    return re.sub(rf"<{tag}>-?\d*</{tag}>", f"<{tag}>{val}</{tag}>", t, count=1)

out = []
for g in segs:
    t = neue_ids(MUSTER[g["angle"]])
    t = setz(t, "Start", TCBASE + g["s"])
    t = setz(t, "Duration", g["e"] - g["s"])
    t = setz(t, "In", g["s"])
    out.append(t)

neu = cd[:LIST_A] + "\r\n".join(out) + cd[LIST_B:]

# --- Tonspur des Musters leeren (Ton kommt danach durchgehend per API) ---
ai = neu.find("<AudioTrackVec>"); aj = neu.find("</AudioTrackVec>")
seg = neu[ai:aj]
first = seg.find("<Element>")
last  = seg.rfind("</Element>") + len("</Element>")
neu = neu[:ai+first] + neu[ai+last:]

with zipfile.ZipFile(ZIEL, "w", zipfile.ZIP_DEFLATED) as zo:
    for n, d in files.items():
        zo.writestr(n, neu.encode("utf-8") if n == CONT else d)

json.dump(segs, open(os.path.join(BASE, "markier_segs.json"), "w", encoding="utf-8"),
          indent=1, ensure_ascii=False)
mk = sum(1 for g in segs if g["version"] == "Kurzversion")
ml = sum(1 for g in segs if g["version"] == "Langversion")
fk = sum(g["e"]-g["s"] for g in segs if g["version"] == "Kurzversion")
fl = sum(g["e"]-g["s"] for g in segs if g["version"] == "Langversion")
print(f"{len(segs)} Segmente ueber {MCLEN} Frames = {MCLEN/FPS/60:.1f} min")
print(f"  Kurzversion: {mk} Stuecke, {fk/FPS:.1f} s (gruen)")
print(f"  Langversion: {ml} Stuecke, {fl/FPS:.1f} s (blau)")
print(f"  unmarkiert : {len(segs)-mk-ml} Stuecke, {(MCLEN-fk-fl)/FPS/60:.1f} min")
print("->", ZIEL)
