# -*- coding: utf-8 -*-
"""Patcht die Winkel im DRT: pro Clip (Timeline-Reihenfolge) das Kamera-Byte im
FieldsBlob setzen. Mapping aus der Definitionssequenz: Angle 1 = seite ('1'/0x31),
Angle 2 = weit ('2'/0x32). Nur die eine Timeline-XML wird ersetzt, Rest 1:1.
Ausgabe: patched.drt + Verifikation der Ziffernverteilung."""
import zipfile, re, json, os

SRC = r"C:\claude\resolve-prep\Projekt-B\mcbuild\scaffold.drt"
OUT = r"C:\claude\resolve-prep\Projekt-B\mcbuild\patched.drt"
SEQ = json.load(open(r"C:\claude\resolve-prep\Projekt-B\mcbuild\schnitt_seq.json", encoding="utf-8"))
cams = SEQ["cams"]
PAT = "4b616d657261c2a0"                 # 'Kamera' + NBSP
DIGIT = {"seite": "31", "weit": "32"}    # Angle 1 = seite, Angle 2 = weit

zin = zipfile.ZipFile(SRC)
# Timeline-XML = die mit den meisten Multicam-Treffern
tl_name = None; tl_text = None
for n in zin.namelist():
    if n.startswith("SeqContainer"):
        d = zin.read(n).decode("utf-8", errors="replace")
        if d.count("Multicam") >= 40:
            tl_name, tl_text = n, d; break
assert tl_name, "Timeline-XML nicht gefunden"

# alle FieldsBlobs in Reihenfolge; die mit PAT bekommen der Reihe nach die Wunsch-Ziffer
blob_iter = list(re.finditer(r"<FieldsBlob>([0-9a-fA-F]*)</FieldsBlob>", tl_text))
targets = [m for m in blob_iter if PAT in m.group(1)]
assert len(targets) == len(cams), f"Blob/Clip-Mismatch: {len(targets)} vs {len(cams)}"

# von hinten nach vorn ersetzen (Positionen bleiben gueltig)
new_text = tl_text
for m, cam in reversed(list(zip(targets, cams))):
    hexs = m.group(1)
    i = hexs.find(PAT) + len(PAT)
    patched = hexs[:i] + DIGIT[cam] + hexs[i+2:]
    new_text = new_text[:m.start(1)] + patched + new_text[m.end(1):]

# neues Zip schreiben (nur tl_name ersetzen)
with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as zout:
    for n in zin.namelist():
        data = new_text.encode("utf-8") if n == tl_name else zin.read(n)
        zout.writestr(n, data)
zin.close()

# Verifikation
z = zipfile.ZipFile(OUT); d = z.read(tl_name).decode("utf-8", errors="replace")
digs = [bytes.fromhex(b[b.find(PAT)+16:b.find(PAT)+18]).decode("latin1")
        for b in re.findall(r"<FieldsBlob>([0-9a-fA-F]*)</FieldsBlob>", d) if PAT in b]
from collections import Counter
exp = "".join("1" if c=="seite" else "2" for c in cams)
got = "".join(digs)
print("patched.drt geschrieben:", os.path.getsize(OUT), "bytes")
print("Ziffern erwartet:", Counter(exp), " bekommen:", Counter(got))
print("Reihenfolge korrekt:", exp == got)
print("erste 30:", got[:30])
