# -*- coding: utf-8 -*-
"""Kurzvideos als ECHTE Multicam-Timelines bauen — mit den Kamerawinkeln aus dem Hauptschnitt.

Warum nicht per AppendToTimeline: dabei landen zwar Multicam-Clips in der neuen Timeline,
aber ALLE auf Angle 1 — die Winkelwahl des Hauptschnitts geht verloren. Die Winkelziffer
steht nur im FieldsBlob des Clips (hinter 'Kamera'+NBSP) und ist ueber die Skript-
Schnittstelle nicht setzbar. Also: den Hauptschnitt als DRT exportieren, die Clips der
gewuenschten Passagen daraus uebernehmen (FieldsBlob unveraendert = Winkel bleibt),
Start/Duration/In neu rechnen und als eigene Timeline importieren.

Aufruf:  py kurzvideo_drt.py [nr ...]
"""
import os, sys, json, re, zipfile, uuid

BASE = r"C:\claude\resolve-prep\projekt-m"
NAME = "Projekt-M Projekt-M"
SRC_DRT = os.path.join(BASE, "mcbuild", "mcs.drt")
FPS = 30000/1001
TCBASE = 108000
CFG = json.load(open(os.path.join(BASE, "videos.json"), encoding="utf-8"))
WORDS = json.load(open(os.path.join(BASE, "words.json"), encoding="utf-8"))
NUR = [int(x) for x in sys.argv[1:]] or None

pausen = [((a["end"]+b["start"])/2) for a, b in zip(WORDS, WORDS[1:])
          if b["start"] - a["end"] >= 0.35]

# ⭐ Der Hauptschnitt ist gegenueber der Tonzeit GESTAUCHT: er beginnt bei Ton-Frame 49,
# und an den Blockgrenzen wurden Bereiche ohne Bild uebersprungen (25 s / 59 s / 10 s).
# Timeline-Frame = 108000 + kumulierte Laenge davor + (ton - Segmentanfang).
# Ohne diese Abbildung laufen im Kurzvideo Bild und Ton auseinander (bis 95 s!).
CUT = json.load(open(os.path.join(BASE, "cut_final.json"), encoding="utf-8"))
SEG = []          # (ton_s, ton_e, tl_start)
_acc = 0
for _x in CUT:
    SEG.append((_x["s"], _x["e"], TCBASE + _acc))
    _acc += _x["e"] - _x["s"]


def ton_bereiche(pa, pb):
    """Ton-Frame-Bereich -> Liste (ton_a, ton_b, tl_a, tl_b), Luecken ausgelassen."""
    out = []
    for s, e, t0 in SEG:
        if e <= pa or s >= pb: continue
        a, b = max(s, pa), min(e, pb)
        out.append((a, b, t0 + (a - s), t0 + (b - s)))
    # benachbarte zusammenfassen
    m = []
    for a, b, ta, tb in out:
        if m and m[-1][1] == a and m[-1][3] == ta:
            m[-1] = (m[-1][0], b, m[-1][2], tb)
        else:
            m.append((a, b, ta, tb))
    return m


def einrasten(t):
    best, bd = t, 9e9
    for m in pausen:
        d = abs(m - t)
        if d < bd and d <= 6.0:
            bd = d; best = m
    return best


z = zipfile.ZipFile(SRC_DRT)
files = {n: z.read(n) for n in z.namelist()}
CONT = max((n for n in files if n.startswith("SeqContainer/")),
           key=lambda n: files[n].count(b"<Sm2TiVideoClip DbId="))
cd = files[CONT].decode("utf-8")
print(f"Quelle: {CONT.split('/')[1][:8]}, {cd.count('<Sm2TiVideoClip DbId=')} Clips")

# --- Clipbloecke (jeweils <Element>…</Element>) einlesen ---
blocks = []
for m in re.finditer(r"<Element>\s*<Sm2TiVideoClip DbId=", cd):
    s = m.start()
    e = cd.index("</Element>", cd.index("</Sm2TiVideoClip>", s)) + len("</Element>")
    b = cd[s:e]
    blocks.append({
        "text": b,
        "start": int(re.search(r"<Start>(-?\d+)</Start>", b).group(1)),
        "dur": int(re.search(r"<Duration>(\d+)</Duration>", b).group(1)),
        "in": int(re.search(r"<In>(-?\d*)</In>", b).group(1) or 0),
        "a": s, "b": e,
    })
LIST_A, LIST_B = blocks[0]["a"], blocks[-1]["b"]
print(f"Clipliste im Container: Zeichen {LIST_A}..{LIST_B}")

# Audioclip aus dem AudioTrackVec entfernen (Ton kommt spaeter passagenweise per API)
ai = cd.find("<AudioTrackVec>")
aj = cd.find("</AudioTrackVec>")
aseg = cd[ai:aj]
am = re.search(r"<Element>\s*<Sm2TiAudioClip DbId=", aseg)
if am:
    s = am.start()
    e = aseg.index("</Element>", aseg.index("</Sm2TiAudioClip>", s)) + len("</Element>")
    AUD_A, AUD_B = ai + s, ai + e
else:
    AUD_A = AUD_B = None


def neue_ids(text):
    """alle DbIds in einem Block durch frische ersetzen (nur fuer doppelt genutzte Clips)"""
    ids = set(re.findall(r'DbId="([0-9a-f-]{36})"', text))
    for old in ids:
        text = text.replace(old, str(uuid.uuid4()))
    return text


def setz(b, tag, val):
    return re.sub(rf"<{tag}>-?\d*</{tag}>", f"<{tag}>{val}</{tag}>", b, count=1)


for v in CFG["videos"]:
    if NUR and v["nr"] not in NUR: continue
    rec = TCBASE
    out = []
    gesehen = set()
    kapitel = []
    tonstuecke = []
    for a, bs, txt in v["passagen"]:
        a2 = einrasten(float(a)); b2 = einrasten(float(bs))
        pa = int(round(a2*FPS)); pb = int(round(b2*FPS))
        kapitel.append((rec - TCBASE, txt, a2, b2))
        for ton_a, ton_b, fa, fb in ton_bereiche(pa, pb):
            tonstuecke.append((ton_a, ton_b))
            for c in blocks:
                cs, ce = c["start"], c["start"] + c["dur"]
                if ce <= fa or cs >= fb: continue
                lo, hi = max(cs, fa), min(ce, fb)
                t = c["text"]
                if c["start"] in gesehen:
                    t = neue_ids(t)
                gesehen.add(c["start"])
                t = setz(t, "Start", rec)
                t = setz(t, "Duration", hi - lo)
                t = setz(t, "In", c["in"] + (lo - cs))
                out.append(t)
                rec += hi - lo
    neu = cd[:LIST_A] + "\r\n".join(out) + cd[LIST_B:]
    if AUD_A is not None:
        d0 = len("\r\n".join(out)) - (LIST_B - LIST_A)
        neu = neu[:AUD_A + d0] + neu[AUD_B + d0:]
    ziel = os.path.join(BASE, "mcbuild", f"kurz_{v['nr']}.drt")
    with zipfile.ZipFile(ziel, "w", zipfile.ZIP_DEFLATED) as zo:
        for n, d in files.items():
            zo.writestr(n, neu.encode("utf-8") if n == CONT else d)
    json.dump({"nr": v["nr"], "name": v["name"], "titel": v["titel"],
               "dauer_f": rec - TCBASE, "ton": tonstuecke,
               "kapitel": [[round(k[0]/FPS, 1), k[1], round(k[2], 1), round(k[3], 1)]
                           for k in kapitel]},
              open(os.path.join(BASE, "mcbuild", f"kurz_{v['nr']}.json"), "w",
                   encoding="utf-8"), indent=1, ensure_ascii=False)
    print(f"#{v['nr']} {v['name']}: {len(out)} Clips, {(rec-TCBASE)/FPS/60:.1f} min -> {ziel}")
