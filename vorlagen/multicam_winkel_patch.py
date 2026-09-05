# -*- coding: utf-8 -*-
"""Unscharfe Einstellungen auf einen anderen Multicam-Winkel umstellen - per DRT.
⭐ Der Winkel steht im FieldsBlob als EIN Hex-Byte hinter 'Kamera'+NBSP:
   4b616d657261c2a0 31|32|33  ->  Angle 1|2|3. Direkt patchbar, keine GUI noetig.
"""
import zipfile, re, json, os, sys
ANG={"nah":"31","weit":"32","seite":"33"}
def lade(drt):
    z=zipfile.ZipFile(drt); files={n:z.read(n) for n in z.namelist()}
    CONT=max((n for n in files if n.startswith("SeqContainer/")),
             key=lambda n: files[n].count(b"<Sm2TiVideoClip DbId="))
    return files, CONT, files[CONT].decode("utf-8")
def bloecke(cd):
    out=[]
    for m in re.finditer(r"<Element>\s*<Sm2TiVideoClip DbId=", cd):
        s=m.start(); e=cd.index("</Element>", cd.index("</Sm2TiVideoClip>", s))+len("</Element>")
        b=cd[s:e]
        out.append(dict(a=s,b=e,text=b,
            start=int(re.search(r"<Start>(-?\d+)</Start>",b).group(1)),
            dur=int(re.search(r"<Duration>(\d+)</Duration>",b).group(1)),
            inn=int(re.search(r"<In>(-?\d*)</In>",b).group(1) or 0),
            ang=re.search(r"4b616d657261c2a0(3\d)",b).group(1)))
    return out
def setz_winkel(text, ziel):
    return re.sub(r"(4b616d657261c2a0)3\d", r"\g<1>"+ziel, text, count=1)
def speichern(files, CONT, cd, ziel):
    with zipfile.ZipFile(ziel,"w",zipfile.ZIP_DEFLATED) as zo:
        for n,d in files.items():
            zo.writestr(n, cd.encode("utf-8") if n==CONT else d)

if __name__=="__main__":
    FIX=[r for r in json.load(open('qualitaet_final.json')) if r["k"]<60]
    for r in FIX:
        r["ziel"]=max(((c,v) for c,v in r["altk"].items() if v), key=lambda x:x[1])[0]
    files,CONT,cd=lade("drt2/Projekt-M_Projekt-M_Multicam_Schnitt.drt")
    B=bloecke(cd); print(len(B),"Clips im DRT")
    idx={b["inn"]: b for b in B}
    neu=cd; versatz=0; n=0
    for r in sorted(FIX,key=lambda x:x["s"]):
        b=idx.get(r["s"])
        if not b: print("  ! kein Clip mit In =",r["s"]); continue
        if b["dur"] != r["e"]-r["s"]: print(f"  ! Laenge weicht ab bei {r['s']}"); continue
        t2=setz_winkel(b["text"], ANG[r["ziel"]])
        assert t2!=b["text"]
        neu = neu[:b["a"]+versatz] + t2 + neu[b["b"]+versatz:]
        versatz += len(t2)-len(b["text"]); n+=1
        print(f"  In {r['s']:7d}  {r['a']} -> {r['ziel']}")
    print(n,"Clips umgestellt")
    from collections import Counter
    print("Winkel neu:", Counter(re.findall(r"4b616d657261c2a0(3\d)", neu)))
    speichern(files,CONT,neu,os.path.abspath("drt2/schnitt_winkelfix.drt"))
    print("geschrieben")
