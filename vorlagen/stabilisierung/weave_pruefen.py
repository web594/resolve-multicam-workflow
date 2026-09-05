# -*- coding: utf-8 -*-
"""Prueft in der Projekt-DB, ob im ResolveFX „Film-Look-Erzeuger" der Effekt
„Bildfenster-Weave" (gateWeave) noch aktiv ist — der erzeugt ein seitliches
Schwanken des ganzen Bildes und ist ab Werk EINGESCHALTET.

Gesucht wird an zwei Stellen:
  * geteilte Nodes  -> Tabelle ListMgt::LmPowerNode, Spalte NodeBA
    (Parameter stehen dort als ASCII-Hex einer UTF-16-Struktur:
     <name> 0000 0001 00XX ...  mit XX = 01 (an) / 00 (aus);
     fehlt der Name ganz, gilt der Vorgabewert = AN)
  * clip-eigene Grades -> Tabelle ListMgt::LmVersion, Spalte Body
    (0x81 + zstd + Protobuf, Parametername im Klartext)

Aufruf: py weave_pruefen.py ["<Projektname>"]
"""
import os, re, shutil, sqlite3, sys, tempfile
from compression import zstd

PROJ = sys.argv[1] if len(sys.argv) > 1 else "Projekt-N Projekt-N"
BASE = os.path.join(os.environ["APPDATA"], "Blackmagic Design", "DaVinci Resolve",
                    "Support", "Resolve Project Library", "Resolve Projects",
                    "Users", "guest", "Projects", PROJ)
DB = os.path.join(BASE, "Project.db")
if not os.path.exists(DB):
    print("Projekt-DB nicht gefunden:", DB); sys.exit(1)

tmp = tempfile.mkdtemp()
for suf in ("", "-wal", "-shm"):
    if os.path.exists(DB + suf):
        shutil.copy(DB + suf, os.path.join(tmp, "Project.db" + suf))
con = sqlite3.connect(os.path.join(tmp, "Project.db"))


def u16hex(s):
    return "".join("00%02x" % ord(c) for c in s).encode()


NAMEN = {"Bildfenster-Weave": u16hex("gateWeaveIsEnable"),
         "Flimmern": u16hex("flickerIsEnable")}
print("Projekt:", PROJ)
print()
print("Geteilte Nodes (wirken auf alle Clips, die sie benutzen):")
gefunden = False
for name, ba in con.execute('SELECT Name, NodeBA FROM "ListMgt::LmPowerNode"'):
    if not isinstance(ba, (bytes, bytearray)) or u16hex("resolvefx.filmlook") not in ba \
            and b"filmlook" not in ba:
        continue
    gefunden = True
    teile = []
    for bez, NAME in NAMEN.items():
        i = ba.find(NAME)
        if i < 0:
            zustand = "AN (Vorgabewert, nicht gespeichert)"
        else:
            # nach dem Namen: 0000 0001 00XX
            rest = ba[i + len(NAME):i + len(NAME) + 16].decode("latin-1")
            zustand = "AUS" if rest[8:12] == "0000" else "AN"
        teile.append(f"{bez} {zustand}")
    print(f"   {name!r}: " + " | ".join(teile))
if not gefunden:
    print("   (kein geteilter Node mit Film-Look-Erzeuger)")

print()
print("Clip-eigene Grades:")
an = aus = 0
for (b,) in con.execute('SELECT Body FROM "ListMgt::LmVersion" WHERE Body IS NOT NULL'):
    raw = b if isinstance(b, (bytes, bytearray)) else bytes.fromhex(b)
    if not raw or raw[0] != 0x81:
        continue
    try:
        d = zstd.decompress(raw[1:])
    except Exception:
        continue
    if b"resolvefx.filmlook" not in d:
        continue
    m = re.search(rb"gateWeaveIsEnable\x12\x02\x18(.)", d)
    if m is None or m.group(1) != b"\x00":
        an += 1
    else:
        aus += 1
print(f"   Grades mit eigenem Film-Look-Erzeuger: {an + aus}  (Weave AN {an} / AUS {aus})")
