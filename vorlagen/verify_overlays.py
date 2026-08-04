# -*- coding: utf-8 -*-
"""
verify_overlays.py - die fertige Overlay-/Auslieferungs-Timeline in EINEM Rutsch
pruefen, statt die immer gleichen rctl-eval-Abfragen von Hand zu tippen.

Findet automatisch die Fehler, die in der #3-Session einzeln von Hand gesucht
wurden (29.07.2026):
  * Schwarzbild-Luecken auf der Hauptbild-Spur (z. B. Endkarte HINTER dem
    letzten O-Ton-Clip -> hartes Schwarz vor der Endkarte)
  * Ueberlappungen und Offline-Clips auf jeder Spur
  * 1-Frame-Sync-Versatz der Sprachspur nach einem eingefuegten Kaltstart
    (Vergleich der LeftOffsets gegen eine Referenz-Timeline)
  * Ton-/Musik-Deckung bis zum gewuenschten Ende (Endkarte nicht stumm?)

Aufruf:
  py verify_overlays.py --timeline 19
  py verify_overlays.py --timeline 19 --bildspur 1 --ende 5962
  py verify_overlays.py --timeline 19 --ref 12   # Sync gegen Referenz-Timeline

Ohne --timeline wird die aktuelle Timeline geprueft. --bildspur ist die
durchgehende Hauptbild-Spur (Default 1). "Weiche Blende"/Transition-Items
werden bei der Lueckenpruefung ignoriert.
"""
import argparse, os, sys

sys.path.insert(0, r"C:\claude\resolve-ctl")


def connect():
    import rctl
    if hasattr(rctl, "connect"):
        return rctl.connect()
    import DaVinciResolveScript as dvr
    return dvr.scriptapp("Resolve")


def echte_clips(tl, art, tr):
    """Clips einer Spur ohne Transition-/Blenden-Items, nach Start sortiert."""
    out = [c for c in (tl.GetItemListInTrack(art, tr) or [])
           if "Blende" not in c.GetName() and "Transition" not in c.GetName()]
    return sorted(out, key=lambda c: c.GetStart())


def luecken_und_overlaps(clips, sf, bis=None):
    luecken, overlaps = [], []
    vor_end = None
    for c in clips:
        s, e = c.GetStart()-sf, c.GetEnd()-sf
        if bis is not None and s >= bis:
            break
        if vor_end is not None:
            if s > vor_end:
                luecken.append((vor_end, s, s-vor_end))
            elif s < vor_end:
                overlaps.append((s, vor_end, vor_end-s))
        vor_end = max(vor_end, e) if vor_end is not None else e
    return luecken, overlaps


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--timeline", type=int, default=0)
    p.add_argument("--bildspur", type=int, default=1, help="durchgehende Hauptbild-Spur")
    p.add_argument("--ende", type=int, default=0, help="Soll-Ende in Frames (0 = Timeline-Ende)")
    p.add_argument("--ref", type=int, default=0, help="Referenz-Timeline-Index fuer Sync-Vergleich")
    a = p.parse_args()

    resolve = connect()
    proj = resolve.GetProjectManager().GetCurrentProject()
    tl = proj.GetTimelineByIndex(a.timeline) if a.timeline else proj.GetCurrentTimeline()
    sf = tl.GetStartFrame()
    fps = float(proj.GetSetting('timelineFrameRate') or 29.97)
    ende = a.ende or (tl.GetEndFrame()-sf)

    def tc(f):
        s = f/fps
        return "%d:%05.2f" % (int(s//60), s % 60)

    problem = 0
    print("== %s ==  Ende %d (%s)" % (tl.GetName(), ende, tc(ende)))

    # 1) ECHTE Schwarzbild-Pruefung: Frame fuer Frame ueber ALLE Videospuren.
    #    Nur V1 zu pruefen reicht nicht - eine Endkarte auf V4 deckt dort
    #    legitim ab. Umgekehrt war genau das der Fehler in #3: V1 endete bei
    #    5672, die Endkarte begann bei 5673 -> ein Frame ganz ohne Bild.
    #    Anpassungsclips zaehlen NICHT als Bild (sie modifizieren nur).
    deckung = bytearray(ende)
    for tr in range(1, tl.GetTrackCount('video')+1):
        for c in tl.GetItemListInTrack('video', tr) or []:
            n = c.GetName()
            if "Anpassungsclip" in n or "Adjustment" in n:
                continue
            s, e = max(0, c.GetStart()-sf), min(ende, c.GetEnd()-sf)
            for f in range(s, e):
                deckung[f] = 1
    loecher, lauf = [], None
    for f in range(ende):
        if not deckung[f] and lauf is None:
            lauf = f
        elif deckung[f] and lauf is not None:
            loecher.append((lauf, f, f-lauf)); lauf = None
    if lauf is not None:
        loecher.append((lauf, ende, ende-lauf))
    if loecher:
        problem += 1
        print("\n[!] SCHWARZBILD - keine Videospur liefert dort Bild:")
        for l0, l1, n in loecher:
            print("    Frame %d-%d  (%s - %s, %d f)  <- Clip verlaengern"
                  " oder Grafik/Endkarte frueher ansetzen" % (l0, l1, tc(l0), tc(l1), n))
    else:
        print("\n[ok] durchgehend Bild bis %s, kein Schwarzbild" % tc(ende))

    # 2) alle Videospuren: Overlaps + ECHTE Offline-Clips
    #    (Anpassungsclip/Fusion/Text+ haben NIE ein MediaPoolItem - das ist
    #     kein Offline. Offline = hat eine Datei-Referenz, aber die Datei fehlt.)
    for tr in range(1, tl.GetTrackCount('video')+1):
        cs = echte_clips(tl, 'video', tr)
        _, ov = luecken_und_overlaps(cs, sf, ende)
        off = []
        for c in cs:
            mpi = c.GetMediaPoolItem()
            if not mpi:
                continue  # Generator/Adjustment/Fusion - normal
            pfad = mpi.GetClipProperty('File Path')
            if pfad and not os.path.exists(pfad):
                off.append(c.GetName())
        if ov:
            problem += 1
            print("[!] V%d Ueberlappungen: %s" % (tr, [(tc(o[0]), tc(o[1])) for o in ov]))
        if off:
            problem += 1
            print("[!] V%d OFFLINE (Datei fehlt): %s" % (tr, off))

    # 3) Ton: deckt IRGENDEINE aktive Spur bis zum Ende? (Musik reicht -
    #    dass die Sprachspur vor dem Schluss endet, ist normal.)
    print()
    max_deckung = 0
    for tr in range(1, tl.GetTrackCount('audio')+1):
        aktiv = tl.GetIsTrackEnabled('audio', tr)
        cs = echte_clips(tl, 'audio', tr)
        letztes = max((c.GetEnd()-sf for c in cs if c.GetStart()-sf < ende), default=0)
        print("[%s] A%d %s bis %s" % ("i" if not aktiv else "ok", tr,
              "STUMM," if not aktiv else "aktiv,", tc(letztes)))
        if aktiv:
            max_deckung = max(max_deckung, letztes)
    if max_deckung < ende-2:
        problem += 1
        print("[!] KEINE aktive Tonspur deckt bis %s (letzte endet %s) -> Schluss stumm!"
              % (tc(ende), tc(max_deckung)))
    else:
        print("[ok] Ton deckt bis zum Soll-Ende (%s)" % tc(max_deckung))

    # 4) Sync gegen Referenz-Timeline: der ZWEITE Bild-Clip (der erste NACH
    #    einem evtl. Kaltstart ist der Original-Filmanfang) muss denselben
    #    Quell-Offset haben wie der erste Clip der Referenz. Weicht der Ton
    #    davon ab, liegt er nach dem Kaltstart-Einfuegen um X Frames schief.
    if a.ref:
        ref = proj.GetTimelineByIndex(a.ref)
        rsf = ref.GetStartFrame()
        print("\n== Sync-Vergleich Bild<->Ton gegen %s ==" % ref.GetName())
        vb = echte_clips(tl, 'video', a.bildspur)
        rb = echte_clips(ref, 'video', a.bildspur)
        # Filmanfang in beiden finden: gleicher LeftOffset wie Referenz-Clip 0
        ref_off = rb[0].GetLeftOffset() if rb else None
        anfang = next((c for c in vb if c.GetLeftOffset() == ref_off), None)
        if anfang and ref_off is not None:
            kaltstart = anfang.GetStart()-sf
            print("   Filmanfang (Bild) liegt bei Frame %d = Kaltstartlaenge" % kaltstart)
            # unterste (bereinigte) Sprachspur
            ta = tl.GetTrackCount('audio')
            spr = echte_clips(tl, 'audio', ta)
            haupt = next((c for c in spr if c.GetStart()-sf >= kaltstart-3), None)
            if haupt:
                versatz = (haupt.GetStart()-sf) - kaltstart
                if versatz == 0:
                    print("   [ok] Sprachspur startet exakt am Filmanfang - synchron.")
                else:
                    problem += 1
                    print("   [!] Sprachspur startet %+d Frame(s) zum Bild versetzt"
                          " -> Ton-Clip um %d nach %s schieben."
                          % (versatz, abs(versatz), "links" if versatz > 0 else "rechts"))
        else:
            print("   (kein gemeinsamer Anker gefunden - Sync manuell pruefen)")

    print("\n%s" % ("ALLES SAUBER." if problem == 0
                    else "%d Punkt(e) pruefen (siehe [!] oben)." % problem))
    return problem


if __name__ == "__main__":
    sys.exit(main())
