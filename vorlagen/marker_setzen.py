# -*- coding: utf-8 -*-
"""Marker in 'Projekt-M Projekt-M Multicam Schnitt':
  * je Heilungsarbeit ein Balken (Dauer-Marker) mit Anfang, dazu ein Marker am Ende
  * je Kurzvideo eine eigene Farbe fuer alle Passagen, die dort verwendet wurden
Alle Zeiten in Ton-Sekunden (= Timeline-Position, 01:00:00:00 = 0)."""
import os, sys, json
os.environ.setdefault("RESOLVE_SCRIPT_API", r"C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting")
os.environ.setdefault("RESOLVE_SCRIPT_LIB", r"C:\Program Files\Blackmagic Design\DaVinci Resolve\fusionscript.dll")
sys.path.append(os.path.join(os.environ["RESOLVE_SCRIPT_API"], "Modules"))
import DaVinciResolveScript as dvr

BASE = r"C:\claude\resolve-prep\projekt-m"
TL = "Projekt-M Projekt-M Multicam Schnitt"
FPS = 30000/1001

# --- Heilungsarbeiten (Ton-Sekunden) ---
HA = [
    (3099, 9045, "1 Christine",
     "Wunsch: wieder gehen koennen. Brust-OP, Selbstabwertung, der Brief vom Vater im "
     "Schlafzimmer. Kommt bei 0:56 nach vorne, Fortsetzung nach der Mittagspause ab 1:37. "
     "Ergebnis: Koerpercheck rund, Ehrenrunde durch den Raum."),
    (6180, 6870, "1a Einschub Antje",
     "Nebenarbeit waehrend Christines Sitzung: der Enkel als Spiegel - was mich am anderen "
     "stoert, gehoert mir. Vergeben, danken, um Entschuldigung bitten."),
    (9053, 11280, "2 Schmerzbehandlung mit sechs Teilnehmern",
     "Sechs Melder mit Schmerzen, sechs Heiler hinter den Stuehlen. Gefuehrte Anwendung, "
     "danach die Rueckmelderunde. Thomas: 'Es hat sich nichts geaendert' - seine Nachmeldung "
     "kommt bei 5:11."),
    (12242, 12750, "3 Maria, Hautflecken",
     "Marias erster Punkt: Flecken links unter der Brust. Trennungskonflikt (erste Hautschicht) "
     "und Besudelungskonflikt (zweite Schicht). Ihre eigentliche Behandlung folgt bei 5:14."),
    (13603, 16440, "4 Annett",
     "Wunsch: durchschlafen koennen. Herzrhythmus nicht rund, Schnappfinger auf dem "
     "Allergie-Meridian, ein fehlendes Geschwister in der Reihe. Arbeit an Opa Manfred, "
     "an Christian und an sich selbst."),
    (18675, 18845, "2b Nachmeldung Thomas",
     "Rund drei Stunden nach der Schmerzbehandlung: die Steifigkeit im Ruecken ist weniger "
     "geworden, die Zehen nicht mehr taub, die Fuesse nicht mehr kalt - und die Angst, vor "
     "einer Gruppe zu sprechen, ist auch weg."),
    (18851, 21470, "5 Maria, Milchallergie",
     "Milchtest vor der Behandlung negativ. Spur in die Zeit im Mutterleib: die Mutter, der "
     "Autounfall, die gesuchte Schwester (Nina). Behandlung mit Rueckwaertszaehlen. Danach "
     "Milchtest positiv: 'fuer mich ist gruenes Licht'."),
]
HA_FARBE = "Cream"
V_FARBE = {1: "Cyan", 2: "Green", 3: "Yellow", 4: "Red", 5: "Purple", 6: "Sky"}
V_KURZ = {1: "Christine", 2: "Annett", 3: "Maria Milch", 4: "Schmerz", 5: "Entzuendung",
          6: "Schaukeltest"}

# ⭐ Der Auto-Schnitt ist gegenueber der Tonzeit GESTAUCHT (Beginn bei Ton-Frame 49,
# an den Blockgrenzen fehlen 25/59/10 s Bild). Marker muessen daher ueber diese
# Abbildung gesetzt werden, sonst sitzen sie bis zu 95 s daneben.
CUT = json.load(open(os.path.join(BASE, "cut_final.json"), encoding="utf-8"))
SEG = []
_acc = 0
for _x in CUT:
    SEG.append((_x["s"], _x["e"], _acc))
    _acc += _x["e"] - _x["s"]
LETZTES = _acc


def ton2tl(tonframe):
    """Ton-Frame -> Position in der Schnitt-Timeline (0 = erster Frame)."""
    for s, e, t0 in SEG:
        if s <= tonframe < e:
            return t0 + (tonframe - s)
    if tonframe < SEG[0][0]: return 0
    return LETZTES - 1


r = dvr.scriptapp("Resolve"); p = r.GetProjectManager().GetCurrentProject()
tl = next(p.GetTimelineByIndex(i) for i in range(1, p.GetTimelineCount()+1)
          if p.GetTimelineByIndex(i).GetName() == TL)
p.SetCurrentTimeline(tl)

alt = tl.GetMarkers() or {}
if alt:
    print(f"{len(alt)} vorhandene Marker werden entfernt")
    for f in list(alt):
        tl.DeleteMarkerAtFrame(f)

belegt = set()


def frei(f):
    while f in belegt:
        f += 1
    belegt.add(f)
    return f


def setz(sec, farbe, name, note, bis_sec=None):
    f = frei(ton2tl(int(round(sec*FPS))))
    d = 1
    if bis_sec:
        d = max(1, ton2tl(int(round(bis_sec*FPS))) - f)
    ok = tl.AddMarker(f, farbe, name, note, d)
    if not ok:
        print(f"  FEHLER bei {name} @ {f}")
    return ok


def tc(s):
    return f"{int(s//3600)}:{int(s//60)%60:02d}:{int(s%60):02d}"


n = 0
for a, b, name, note in HA:
    n += setz(a, HA_FARBE, f"HEILUNGSARBEIT {name}", note, b)
    n += setz(b, HA_FARBE, f"ENDE Heilungsarbeit {name}", f"Beginn war bei {tc(a)}.")
print(f"Heilungsarbeiten: {n} Marker")

m = 0
for nr in range(1, 7):
    meta = json.load(open(os.path.join(BASE, "mcbuild", f"kurz_{nr}.json"), encoding="utf-8"))
    for i, (pos, text, q0, q1) in enumerate(meta["kapitel"], 1):
        ok = setz(q0, V_FARBE[nr],
                  f"V{nr} {V_KURZ[nr]} - Teil {i}/{len(meta['kapitel'])}: {text}",
                  f"Kurzvideo #{nr} '{meta['name']}'\nliegt dort bei {tc(pos)}.\n"
                  f"Quelle in Tonzeit {tc(q0)} - {tc(q1)} ({q1-q0:.0f} s)", q1)
        m += ok
    print(f"  V{nr} ({V_FARBE[nr]}): {len(meta['kapitel'])} Passagen")
print(f"Kurzvideo-Passagen: {m} Marker")

mk = tl.GetMarkers() or {}
from collections import Counter
print(f"\nGesamt in der Timeline: {len(mk)} Marker")
print("nach Farbe:", dict(Counter(v["color"] for v in mk.values())))
r.GetProjectManager().SaveProject()
print("gespeichert.")
