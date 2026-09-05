# -*- coding: utf-8 -*-
"""Kaltstart-Clip (staerkster Satz) VORNE in die Kurzvideo-Timeline einfuegen -
Bild UND Ton, per DRT-Duplikat mit Ripple-Verschiebung des Rests. Der Winkel des
duplizierten Bildabschnitts bleibt exakt wie im Original (FieldsBlob unveraendert,
nur frische DbIds fuer die neuen Objekte). Nichts geloescht, nur eingefuegt."""
import zipfile, re, json, os, uuid, sys

V = json.load(open("kaltstart_final.json", encoding="utf-8"))
NR = int(sys.argv[1])
video = next(v for v in V if v["nr"] == NR)
A = next(x for x in video["varianten"] if x["tag"] == "A")
F_IN, F_OUT = A["f_in"], A["f_out"]
print(f"#{NR} {video['kurz']}: Kaltstart Ton-Frame {F_IN}-{F_OUT} ({A['dauer']}s)")

SRC = f"drt2/kurz_{NR}_final.drt"
z = zipfile.ZipFile(SRC)
files = {n: z.read(n) for n in z.namelist()}
CONT = max((n for n in files if n.startswith("SeqContainer/")),
           key=lambda n: files[n].count(b"<Sm2TiVideoClip DbId="))
cd = files[CONT].decode("utf-8")

def bloecke(cd, tag):
    out = []
    for m in re.finditer(rf"<Element>\s*<Sm2Ti{tag}Clip DbId=", cd):
        s = m.start()
        e = cd.index("</Element>", cd.index(f"</Sm2Ti{tag}Clip>", s)) + len("</Element>")
        b = cd[s:e]
        out.append(dict(a=s, b=e, text=b,
            start=int(re.search(r"<Start>(-?\d+)</Start>", b).group(1)),
            dur=int(re.search(r"<Duration>(\d+)</Duration>", b).group(1)),
            inn=int(re.search(r"<In>(-?\d*)</In>", b).group(1) or 0)))
    return out

def neue_ids(text):
    for old in set(re.findall(r'DbId="([0-9a-f-]{36})"', text)):
        text = text.replace(old, str(uuid.uuid4()))
    return text

def setz(b, tag, val):
    return re.sub(rf"<{tag}>-?\d*</{tag}>", f"<{tag}>{val}</{tag}>", b, count=1)

def dupliziere(blocks, f_in, f_out):
    """Blocks mit In-Bereich, der [f_in,f_out) schneidet -> neue Blocktexte, chronologisch,
    mit rec ab 0 aufwaerts gerechnet; liefert (liste_neuer_texte, gesamtlaenge, betroffene_Originalstarts).
    WICHTIG: die vorn eingefuegte Kopie behaelt die URSPRUENGLICHEN DbIds (sie steht jetzt
    chronologisch als ERSTE) - frische IDs bekommt stattdessen die spaeter im Schnitt liegende
    zweite Kopie (siehe dort). Andernfalls verwirft der Resolve-Import den Clip stillschweigend
    (verifiziert 24.08.2026: Original-IDs muessen an der chronologisch ERSTEN Stelle bleiben,
    wie im Verfahren aus kurzvideo_drt.py)."""
    treffer = [c for c in blocks if c["inn"] < f_out and c["inn"] + c["dur"] > f_in]
    treffer.sort(key=lambda c: c["inn"])
    TCBASE = blocks[0]["start"] if blocks[0]["start"] >= 100000 else 108000
    out = []; rec = TCBASE; betroffen = set()
    for c in treffer:
        lo, hi = max(c["inn"], f_in), min(c["inn"] + c["dur"], f_out)
        t = c["text"]
        t = setz(t, "Start", rec)
        t = setz(t, "Duration", hi - lo)
        t = setz(t, "In", c["inn"] + (lo - c["inn"]))
        out.append(t)
        rec += hi - lo
        betroffen.add(c["a"])
    return out, rec - TCBASE, betroffen

VB = bloecke(cd, "Video")
AB = bloecke(cd, "AudioTrackVec" in cd and "Audio" or "Audio")
print(f"  Video-Clips im DRT: {len(VB)}  Audio-Clips: {len(AB)}")

vneu, vlen, v_betroffen = dupliziere(VB, F_IN, F_OUT)
aneu, alen, a_betroffen = dupliziere(AB, F_IN, F_OUT)
print(f"  Dupliziert: {len(vneu)} Video-Bloecke ({vlen}f), {len(aneu)} Audio-Bloecke ({alen}f)")
assert vlen == alen, f"Bild-/Tonlaenge weichen ab: {vlen} != {alen}"

# --- Video-Liste im Container ersetzen: neue Bloecke vorn, alte Start-Werte + vlen ---
LIST_A, LIST_B = VB[0]["a"], VB[-1]["b"]
alte_video_texte = []
for c in VB:
    t = neue_ids(c["text"]) if c["a"] in v_betroffen else c["text"]
    t = setz(t, "Start", c["start"] + vlen)
    alte_video_texte.append(t)
neu_video_block = "\r\n".join(vneu + alte_video_texte)
cd2 = cd[:LIST_A] + neu_video_block + cd[LIST_B:]
versatz = len(neu_video_block) - (LIST_B - LIST_A)

# --- Audio-Liste im Container ersetzen (Positionen im Originaltext + versatz) ---
AL_A, AL_B = AB[0]["a"] + versatz, AB[-1]["b"] + versatz
alte_audio_texte = []
for c in AB:
    t = neue_ids(c["text"]) if c["a"] in a_betroffen else c["text"]
    t = setz(t, "Start", c["start"] + alen)
    alte_audio_texte.append(t)
neu_audio_block = "\r\n".join(aneu + alte_audio_texte)
cd3 = cd2[:AL_A] + neu_audio_block + cd2[AL_B:]

ziel = os.path.abspath(f"drt2/kurz_{NR}_kaltstart.drt")
with zipfile.ZipFile(ziel, "w", zipfile.ZIP_DEFLATED) as zo:
    for n, d in files.items():
        zo.writestr(n, cd3.encode("utf-8") if n == CONT else d)
print(f"  geschrieben: {ziel}  (Kaltstart-Laenge {vlen} Frames = {vlen/(30000/1001):.2f}s)")
print(f"  KALTSTART_FRAMES={vlen}")
