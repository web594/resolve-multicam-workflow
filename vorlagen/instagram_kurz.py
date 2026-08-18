# -*- coding: utf-8 -*-
"""
Instagram-Kurzversion (9:16) aus einer "hochf angez"-Renderdatei bauen.

Macht in einem Rutsch:
  1. Hochformat-Spalte zwischen den weissen Balken NACHMESSEN (nie Werte raten)
  2. Crop + Skalieren auf 1080x1920 + Untertitel (ASS) einbrennen
  3. Pruefen, ob Musik schon in der Tonspur ist (silencedetect)
  4. Lautheit zweistufig auf -14 LUFS (Bild verlustfrei)
  5. Eine "ffmpeg Anweisung ...txt" mit den tatsaechlich benutzten Befehlen schreiben

Aufruf:
  py instagram_kurz.py "<Quelle hochf angez.mp4>" --ass kurz_sub.ass --titel "#3"

Erstellt fuer die Reihe Reihe-R (#1, #2 ... ), Stand 28.07.2026.
"""
import argparse, json, os, re, subprocess, sys, glob

FF_DIR = glob.glob(r"C:\Users\<benutzer>\AppData\Local\Microsoft\WinGet\Packages"
                   r"\Gyan.FFmpeg*\ffmpeg*\bin")
FFMPEG = os.path.join(FF_DIR[0], "ffmpeg.exe") if FF_DIR else "ffmpeg"
FFPROBE = os.path.join(FF_DIR[0], "ffprobe.exe") if FF_DIR else "ffprobe"


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                          errors="replace", **kw)


def probe(pfad):
    r = run([FFPROBE, "-v", "error", "-select_streams", "v:0", "-show_entries",
             "stream=width,height,r_frame_rate,duration", "-of", "json", pfad])
    s = json.loads(r.stdout)["streams"][0]
    num, den = s["r_frame_rate"].split("/")
    return int(s["width"]), int(s["height"]), int(num)/int(den), float(s.get("duration", 0))


def spalte_messen(pfad, W, H, dauer):
    """Weisse Balken robust finden -> crop-Werte (ohne weissen Restrand).

    Statt nur die Bildmittelzeile zu pruefen, wird JEDE Spalte ueber die
    GANZE Bildhoehe bewertet: eine Spalte gilt nur dann als Balken, wenn sie
    fast durchgehend hell ist. So wird heller Bildinhalt (Wand, Hemd) nicht
    faelschlich als Balken gewertet, und weiche/interpolierte Kanten nach dem
    Rendern fuehren nicht mehr zu einem uebrig bleibenden weissen Streifen.
    Zusaetzlich ein kleiner Sicherheitsabstand nach innen.
    """
    import numpy as np
    from PIL import Image
    SAFE = 4               # px Sicherheitsabstand pro Seite (frisst Weichkanten)
    tmp = os.path.join(os.environ.get("TEMP", "."), "_hochf_probe.png")
    x0s, x1s = [], []
    for t in (dauer*0.2, dauer*0.4, dauer*0.6, dauer*0.8):
        run([FFMPEG, "-y", "-v", "error", "-ss", "%.2f" % t, "-i", pfad,
             "-frames:v", "1", tmp])
        a = np.array(Image.open(tmp).convert("RGB")).astype(int)
        hell = (a > 232).all(axis=2)          # helle Pixel
        anteil = hell.mean(axis=0)            # je Spalte: Anteil heller Zeilen
        inhalt = np.where(anteil < 0.97)[0]   # Spalten mit echtem Bildinhalt
        if len(inhalt):
            x0s.append(int(inhalt.min()))
            x1s.append(int(inhalt.max()))
    if not x0s:
        raise SystemExit("Keine Hochformat-Spalte gefunden - ist das wirklich die "
                         "'hochf angez'-Fassung mit weissen Balken?")
    x0 = max(x0s) + SAFE                       # engste gemeinsame Innenkante
    x1 = min(x1s) - SAFE
    breite = x1 - x0 + 1
    breite -= breite % 2
    if breite > W*0.9:
        raise SystemExit(
            "Keine weissen Balken gefunden (gemessene Spalte %d von %d Pixel).\n"
            "Das ist offenbar NICHT die 'hochf angez'-Fassung, sondern ein normales\n"
            "16:9-Bild. Erst die Kurzfassung als Hochformat-zwischen-weissen-Balken\n"
            "rendern, dann dieses Skript darauf anwenden." % (breite, W))
    return x0, breite


def musik_drin(pfad):
    r = run([FFMPEG, "-i", pfad, "-af", "silencedetect=noise=-45dB:d=0.4",
             "-f", "null", "-"])
    return "silence_start" not in (r.stderr or "")


def loudnorm_messen(pfad):
    r = run([FFMPEG, "-i", pfad, "-af",
             "loudnorm=I=-14:TP=-1:LRA=11:print_format=json", "-f", "null", "-"])
    m = re.findall(r"\{[^{}]*input_i[^{}]*\}", r.stderr, re.S)
    if not m:
        raise SystemExit("loudnorm-Messung fehlgeschlagen:\n" + r.stderr[-1500:])
    return json.loads(m[-1])


def lautheit_pruefen(pfad):
    r = run([FFMPEG, "-i", pfad, "-af", "ebur128=peak=true:framelog=verbose",
             "-f", "null", "-"])
    i = re.findall(r"I:\s*(-?\d+\.\d+) LUFS", r.stderr)
    tp = re.findall(r"Peak:\s*(-?\d+\.\d+) dBFS", r.stderr)
    return (float(i[-1]) if i else float("nan"),
            float(tp[-1]) if tp else float("nan"))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("quelle")
    p.add_argument("--ass", default="kurz_sub.ass")
    p.add_argument("--titel", default=None,
                   help='veraltet/optional, nur noch fuer den Kopf der ffmpeg-'
                        'Anweisungsdatei; der Dateiname wird IMMER aus der '
                        'Quelldatei abgeleitet (Namenskonvention).')
    a = p.parse_args()

    ordner = os.path.dirname(os.path.abspath(a.quelle)) or "."
    os.chdir(ordner)
    quelle = os.path.basename(a.quelle)
    if not os.path.exists(quelle):
        raise SystemExit("Quelle nicht gefunden: " + quelle)
    if not os.path.exists(a.ass):
        raise SystemExit("ASS-Datei nicht gefunden: " + a.ass)

    # Namenskonvention (siehe Skill/Memory "dateinamen-konvention"): der
    # Ergebnis-Dateiname MUSS mit dem Namen der Quelldatei beginnen (inkl.
    # deren Versionsnummer/-kennung) - "Instagram Kurz #4 ..." allein reicht
    # NICHT, weil daraus nicht hervorgeht, zu welchem Film/Projekt es gehoert.
    basis = os.path.splitext(quelle)[0]

    # ... und bei FILMEN steht vorne das PROJEKTDATUM (JJMMTT), damit die Datei
    # beim Suchen wieder dem Projekt zuzuordnen ist (Nutzer, 04.08.2026).
    # Wird aus dem Projektordner im Pfad gelesen (z. B. "...\Reihe-R <projekt>\...").
    md = re.search(r"[\\/](\d{6})[ _-]", os.path.abspath(quelle))
    if md and not basis.startswith(md.group(1)):
        basis = "%s %s" % (md.group(1), basis)
        print("Projektdatum vorangestellt:", md.group(1))

    W, H, fps, dauer = probe(quelle)
    print("Quelle : %s  %dx%d  %.2f fps  %.2f s" % (quelle, W, H, fps, dauer))

    x0, breite = spalte_messen(quelle, W, H, dauer)
    crop = "crop=%d:%d:%d:0" % (breite, H, x0)
    print("Gemessen: Hochformat-Spalte x = %d .. %d  ->  %s" % (x0, x0+breite-1, crop))

    ton_copy = musik_drin(quelle)
    print("Ton    : %s" % ("durchgehend -> Musik ist drin, -c:a copy"
                           if ton_copy else "Stille gefunden -> Musik fehlt evtl.!"))

    out1 = "%s Instagram (Text, Musik).mp4" % basis
    vf = "%s,scale=1080:1920,subtitles=%s" % (crop, a.ass)
    cmd1 = [FFMPEG, "-y", "-i", quelle, "-vf", vf,
            "-c:v", "libx264", "-preset", "slow", "-crf", "18",
            "-pix_fmt", "yuv420p"] + \
           (["-c:a", "copy"] if ton_copy else ["-c:a", "aac", "-b:a", "320k"]) + \
           ["-movflags", "+faststart", out1]
    print("\n[1/2] Crop + Untertitel ...")
    r = run(cmd1)
    if not os.path.exists(out1):
        raise SystemExit(r.stderr[-2000:])

    print("[2/2] Lautheit -14 LUFS (zweistufig) ...")
    m = loudnorm_messen(out1)
    out2 = "%s Instagram (Text, Musik, -14 LUFS).mp4" % basis
    af = ("loudnorm=I=-14:TP=-1:LRA=11:measured_I=%s:measured_TP=%s:measured_LRA=%s"
          ":measured_thresh=%s:offset=%s:linear=true"
          % (m["input_i"], m["input_tp"], m["input_lra"], m["input_thresh"],
             m["target_offset"]))
    cmd2 = [FFMPEG, "-y", "-i", out1, "-c:v", "copy", "-af", af,
            "-c:a", "aac", "-b:a", "320k", "-movflags", "+faststart", out2]
    r = run(cmd2)
    if not os.path.exists(out2):
        raise SystemExit(r.stderr[-2000:])
    lufs, tp = lautheit_pruefen(out2)
    print("\nFERTIG: %s\n        %.2f LUFS / %.2f dBTP" % (out2, lufs, tp))

    def zeile(c):
        # ALLES ausser den Schaltern in Anfuehrungszeichen: die Filterketten
        # (-vf/-af) enthalten Kommas, und PowerShell liest nackte Kommas als
        # Array-Trenner -> der kopierte Befehl bricht sonst ab.
        return " ".join(x if x.startswith("-") and len(x) <= 12 else '"%s"' % x
                        for x in c[1:])
    txt = os.path.join(ordner, "%s ffmpeg Anweisung (Instagram Kurz + Lautheit).txt" % basis)
    kennung = a.titel or basis
    with open(txt, "w", encoding="utf-8") as f:
        f.write("Instagram-Kurzversion %s - automatisch erzeugt von instagram_kurz.py\n" % kennung)
        f.write("="*72 + "\n\n")
        f.write("Quelle: %s (%dx%d, %.2f s)\n" % (quelle, W, H, dauer))
        f.write("Gemessene Hochformat-Spalte: x %d .. %d  ->  %s\n" % (x0, x0+breite-1, crop))
        f.write("Ton: %s\n\n" % ("Musik bereits enthalten (-c:a copy)" if ton_copy
                                 else "Stille gefunden - Musik pruefen!"))
        f.write("Schritt 1 - Crop + Skalieren + Untertitel:\nffmpeg %s\n\n" % zeile(cmd1))
        f.write("Schritt 2 - Lautheit (Messwerte aus Pass 1: I=%s TP=%s LRA=%s thresh=%s offset=%s):\n"
                % (m["input_i"], m["input_tp"], m["input_lra"], m["input_thresh"], m["target_offset"]))
        f.write("ffmpeg %s\n\n" % zeile(cmd2))
        f.write("Ergebnis: %.2f LUFS / %.2f dBTP\n" % (lufs, tp))
        f.write("\nHinweis: KEIN fontsdir angeben - libass findet Candara sonst nicht.\n")
    print("Anweisung geschrieben: %s" % txt)


if __name__ == "__main__":
    main()
