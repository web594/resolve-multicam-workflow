# -*- coding: utf-8 -*-
"""
overlay_tools.py — Grafik-Einblendungen für Resolve vorbereiten und platzieren.

Löst die drei wiederkehrenden Probleme (siehe references/grafik-einblendungen.md):
  1. Standbilder landen in der Timeline nur mit 5 s Standard-Dauer  -> PNG in ProRes-MOV
     mit exakter Frameanzahl wandeln.
  2. Ein späterer Zoom schneidet Ränder ab                          -> zoomsafe / check
  3. Overlays brauchen Alpha                                        -> ProRes 4444

Aufrufe
-------
  py overlay_tools.py check     bild.png [--zoom 1.10]
  py overlay_tools.py zoomsafe  bild.png ausgabe.png [--scale 0.90]
  py overlay_tools.py mov       bild.png ausgabe.mov --frames 264 [--fps 30000/1001] [--alpha]
  py overlay_tools.py place     ausgabe.mov --timeline 7 --track 4 --at 2676 --frames 264 \
                                 --fuer "#N Thema-Y, ab 0:41 - Aufbau Thema-Y"

`place` importiert automatisch in den Mediathek-Unterordner, der dem
Elternordner der Datei entspricht (z. B. ".../#N Thema-Y/xxx.mov" ->
Ordner "#N Thema-Y"; wird angelegt, falls er fehlt) - NIE lose in
Master-Root. `--fuer` schreibt einen Kurzhinweis ins Comments-Feld des
Clips (Spalte in der Mediathek einblendbar), damit bei vielen Dateien
erkennbar bleibt, fuer welche Timeline/Stelle sie gedacht sind. Ohne
`--fuer` wird automatisch "Timeline @ Frame X (Track Y)" eingetragen.

Hinweis: Zoom NICHT einbacken (ffmpeg zoompan zittert) — statisch liefern,
Zoom setzt der Nutzer in Resolve.
"""
import argparse, math, os, subprocess, sys, glob

FFMPEG = None
def ffmpeg():
    global FFMPEG
    if FFMPEG: return FFMPEG
    for c in (["ffmpeg"], glob.glob(os.path.expandvars(
            r"%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg*\ffmpeg*\bin\ffmpeg.exe"))):
        c = c if isinstance(c, list) else [c]
        for p in c:
            try:
                subprocess.run([p, "-version"], capture_output=True, check=True)
                FFMPEG = p; return p
            except Exception:
                pass
    sys.exit("ffmpeg nicht gefunden")


def _content_bbox(path):
    """Bounding-Box des sichtbaren Inhalts (alles deutlich heller als der Hintergrund)."""
    from PIL import Image
    import numpy as np
    a = np.asarray(Image.open(path).convert("RGB")).astype(int)
    H, W, _ = a.shape
    bg = np.percentile(a.reshape(-1, 3).sum(axis=1), 25)
    inhalt = a.sum(axis=2) > bg + 90
    ys, xs = np.where(inhalt)
    return (W, H, xs.min(), xs.max(), ys.min(), ys.max())


def cmd_check(args):
    """Prüft, ob beim Reinzoomen nichts abgeschnitten wird (Text UND Bild)."""
    W, H, x0, x1, y0, y1 = _content_bbox(args.bild)
    m = (1 - 1 / args.zoom) / 2                       # Beschnitt je Rand
    cx, cy = int(W * m), int(H * m)
    ok = x0 >= cx and x1 <= W - cx and y0 >= cy and y1 <= H - cy
    print(f"Bild {W}x{H} | Inhalt x {x0}-{x1}  y {y0}-{y1}")
    print(f"bei {args.zoom:.0%} sichtbar: x {cx}-{W-cx}  y {cy}-{H-cy}  (je Rand {m:.2%})")
    print("ALLES DRIN" if ok else
          f"!! ABGESCHNITTEN: links {max(0,cx-x0)} rechts {max(0,x1-(W-cx))} "
          f"oben {max(0,cy-y0)} unten {max(0,y1-(H-cy))} px  -> 'zoomsafe' benutzen")
    return 0 if ok else 1


def cmd_zoomsafe(args):
    """Inhalt verkleinern, Hintergrund aus den echten Randfarben ergänzen, Kanten weich."""
    from PIL import Image, ImageDraw, ImageFilter
    import numpy as np
    src = Image.open(args.bild).convert("RGB")
    W, H = src.size
    a = np.asarray(src).astype(int)
    edge = np.concatenate([a[0:6].reshape(-1, 3), a[-6:].reshape(-1, 3),
                           a[:, 0:6].reshape(-1, 3), a[:, -6:].reshape(-1, 3)])
    outer = tuple(int(v) for v in np.percentile(edge, 20, axis=0))
    inner = tuple(int(v) for v in np.percentile(edge, 85, axis=0))

    sw, sh = W // 8, H // 8
    small = Image.new("RGB", (sw, sh)); sp = small.load()
    cx, cy = sw * 0.5, sh * 0.45
    maxd = math.hypot(sw * 0.62, sh * 0.62)
    for y in range(sh):
        for x in range(sw):
            t = min(1.0, math.hypot(x - cx, y - cy) / maxd) ** 2
            sp[x, y] = tuple(int(inner[i] + (outer[i] - inner[i]) * t) for i in range(3))
    bg = small.resize((W, H), Image.BILINEAR)

    nw, nh = int(W * args.scale), int(H * args.scale)
    content = src.resize((nw, nh), Image.LANCZOS)
    f = 26
    mask = Image.new("L", (nw, nh), 0)
    ImageDraw.Draw(mask).rectangle([f, f, nw - f, nh - f], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(f / 2))
    bg.paste(content, ((W - nw) // 2, (H - nh) // 2), mask)
    bg.save(args.ausgabe)
    print(f"{args.ausgabe}  Inhalt {args.scale:.0%}  bg {outer}->{inner}")


def cmd_mov(args):
    """PNG -> ProRes-MOV mit exakter Frameanzahl (sonst nimmt Resolve 5 s Still-Dauer)."""
    prof, pix = ("4444", "yuva444p10le") if args.alpha else ("3", "yuv422p10le")
    cmd = [ffmpeg(), "-y", "-loop", "1", "-i", args.bild, "-r", args.fps,
           "-frames:v", str(args.frames), "-c:v", "prores_ks",
           "-profile:v", prof, "-pix_fmt", pix, args.ausgabe]
    subprocess.run(cmd, check=True, capture_output=True)
    sec = args.frames / (30000 / 1001 if args.fps == "30000/1001" else float(args.fps))
    print(f"{args.ausgabe}  {args.frames} Frames = {sec:.2f}s  "
          f"ProRes {'4444 (Alpha)' if args.alpha else '422 HQ'}")


def _finde_oder_erstelle_ordner(mp, root, name):
    """Direkten Unterordner von Master mit diesem Namen finden, sonst anlegen.
    Grafiken/Fotos landen NIE lose in Master-Root -> sonst nicht mehr
    zuordenbar, sobald mehrere Projekte/Folgen dieselbe g1/g2/...-Konvention
    benutzen (siehe fallstricke.md, Fund 29.07.2026)."""
    for sf in root.GetSubFolderList():
        if sf.GetName() == name:
            return sf
    return mp.AddSubFolder(root, name)


def _alle_clips(folder):
    """Rekursiv ALLE Clips unterhalb eines Ordners (fuer den Pfad-Abgleich unten)."""
    treffer = list(folder.GetClipList())
    for sf in folder.GetSubFolderList():
        treffer += _alle_clips(sf)
    return treffer


def cmd_place(args):
    """Importiert das MOV in den zur Quelldatei passenden Projekt-Unterordner
    (Name des Elternordners der Datei, z. B. ".../#N Thema-Y/xxx.mov" ->
    Mediathek-Unterordner "#N Thema-Y") und legt es an die gewünschte
    Timeline-Position. Ersetzt eine gleichnamige Vorversion sauber (Resolve
    cacht sonst die alte Datei) UND schreibt ins Comments-Feld, für welche
    Timeline/Stelle die Grafik gedacht ist - sonst ist das bei vielen
    Dateien in der Mediathek nicht mehr auseinanderzuhalten."""
    sys.path.insert(0, r"C:\claude\resolve-ctl")
    import rctl  # nutzt die vorhandene Verbindung
    resolve = rctl.connect() if hasattr(rctl, "connect") else None
    if resolve is None:
        import DaVinciResolveScript as dvr
        resolve = dvr.scriptapp("Resolve")
    proj = resolve.GetProjectManager().GetCurrentProject()
    mp = proj.GetMediaPool(); root = mp.GetRootFolder()
    tl = proj.GetTimelineByIndex(args.timeline) if args.timeline else proj.GetCurrentTimeline()
    proj.SetCurrentTimeline(tl)
    name = os.path.basename(args.mov)
    ziel = os.path.abspath(args.mov)

    alt = [i for i in tl.GetItemListInTrack('video', args.track) if i.GetName() == name]
    if alt: tl.DeleteClips(alt)

    # NUR Klone DERSELBEN Datei loeschen (Pfad-Vergleich!) - nicht per Name.
    # Andere Projekte nutzen dieselbe g1/g2/...-Namenskonvention; ein reiner
    # Namensvergleich hat schon einmal das g1_fachbegriffe.mov eines ANDEREN
    # Projekts geloescht und die eigene Timeline stillschweigend darauf
    # umgelinkt (Fund 29.07.2026, Projekt Reihe-R-alexander).
    def gleiche_datei(c):
        try:
            p = c.GetClipProperty('File Path')
        except Exception:
            return False
        return p and os.path.abspath(p) == ziel
    mp.DeleteClips([c for c in _alle_clips(root) if gleiche_datei(c)])

    ordnername = os.path.basename(os.path.dirname(ziel))  # z.B. "#N Thema-Y"
    zielordner = _finde_oder_erstelle_ordner(mp, root, ordnername)
    mp.SetCurrentFolder(zielordner)
    item = mp.ImportMedia([ziel])[0]

    hinweis = args.fuer or ("%s @ Frame %d (Track %d)" % (tl.GetName(), args.at, args.track))
    item.SetClipProperty("Comments", hinweis)

    mp.AppendToTimeline([{'mediaPoolItem': item, 'startFrame': 0,
                          'endFrame': args.frames - 1, 'trackIndex': args.track,
                          'recordFrame': args.at, 'mediaType': 1}])
    fps = float(proj.GetSetting('timelineFrameRate') or 29.97)
    for it in tl.GetItemListInTrack('video', args.track):
        s = it.GetStart() / fps
        print(f"  {int(s//60)}:{s%60:05.2f}  ({it.GetEnd()-it.GetStart()}f)  {it.GetName()[:44]}")
    print('Ordner:', ordnername, '| Comments:', hinweis)
    print('gespeichert' if resolve.GetProjectManager().SaveProject() else 'SPEICHERN FEHLGESCHLAGEN')


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("check");    c.add_argument("bild"); c.add_argument("--zoom", type=float, default=1.10); c.set_defaults(f=cmd_check)
    z = sub.add_parser("zoomsafe"); z.add_argument("bild"); z.add_argument("ausgabe"); z.add_argument("--scale", type=float, default=0.90); z.set_defaults(f=cmd_zoomsafe)
    m = sub.add_parser("mov");      m.add_argument("bild"); m.add_argument("ausgabe"); m.add_argument("--frames", type=int, required=True); m.add_argument("--fps", default="30000/1001"); m.add_argument("--alpha", action="store_true"); m.set_defaults(f=cmd_mov)
    l = sub.add_parser("place");    l.add_argument("mov"); l.add_argument("--timeline", type=int, default=0); l.add_argument("--track", type=int, default=4); l.add_argument("--at", type=int, required=True); l.add_argument("--frames", type=int, required=True); l.add_argument("--fuer", default="", help='Kurzer Hinweis fuers Comments-Feld, z.B. "#N Thema-Y, ab 0:41 - Aufbau Thema-Y". Ohne Angabe wird Timeline+Frame automatisch eingetragen.'); l.set_defaults(f=cmd_place)

    a = p.parse_args()
    sys.exit(a.f(a) or 0)


if __name__ == "__main__":
    main()
