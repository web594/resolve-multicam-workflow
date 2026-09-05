# -*- coding: utf-8 -*-
"""
tc_pruefen.py - Timecode-Sync gegenpruefen (AirGlu / Atomos Shogun Ultra)

Liest den eingebetteten Start-Timecode zweier oder mehrerer Clips und vergleicht
den daraus errechneten Versatz mit dem TATSAECHLICHEN Versatz aus dem Ton
(Kreuzkorrelation). Damit ist belegt, ob die Timecode-Synchronisation stimmt --
statt ihr blind zu vertrauen.

Aufruf:
    python tc_pruefen.py clipA.MOV clipB.MOV [clipC.MOV ...]

Der ERSTE Clip ist die Referenz, alle weiteren werden gegen ihn gemessen.

Bewertung:
    < 1 Frame Abweichung  -> Timecode-Sync ist gut, Multicam per TC bauen
    1-3 Frames            -> grenzwertig, bei langen Clips gegenmessen
    > 3 Frames            -> nicht verlassen, klassisch per sync.py arbeiten

Vorsicht bei der Aussagekraft:
- Leiser Ton (RMS < 50) macht die Korrelation unsicher. Guete = Spitze/Median;
  unter ~10 ist das Ergebnis nur ein Anhaltspunkt. Fuer einen harten Beleg
  einmal kraeftig klatschen.
- Kurze Clips zeigen keinen Drift. Bei mehrstuendigen Aufnahmen zusaetzlich
  einen Clip vom ENDE der Veranstaltung messen.
"""
import json
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

import numpy as np


def probe(pfad):
    """Start-Timecode (Frames), fps und Dauer eines Clips holen."""
    roh = subprocess.run(
        ["ffprobe", "-v", "error", "-print_format", "json",
         "-show_entries",
         "format=duration:format_tags=timecode:"
         "stream=index,codec_type,r_frame_rate:stream_tags=timecode",
         str(pfad)],
        capture_output=True, text=True, check=True).stdout
    d = json.loads(roh)

    tc = d.get("format", {}).get("tags", {}).get("timecode")
    fps = None
    for s in d.get("streams", []):
        if s.get("codec_type") == "video":
            num, den = s["r_frame_rate"].split("/")
            fps = int(num) / int(den)
        if tc is None:
            tc = s.get("tags", {}).get("timecode")
    if tc is None:
        raise SystemExit(f"FEHLER: {Path(pfad).name} hat KEINEN Timecode eingebettet.")
    if not fps:
        raise SystemExit(f"FEHLER: {Path(pfad).name} hat keine Videospur.")

    h, m, s_, f = (int(x) for x in tc.replace(";", ":").split(":"))
    sek = h * 3600 + m * 60 + s_ + f / fps
    return {"tc": tc, "tc_sek": sek, "fps": fps,
            "dauer": float(d["format"]["duration"]), "name": Path(pfad).name}


def ton(pfad, tmp, nr):
    """Mono-WAV 48 kHz extrahieren und als float-Array laden."""
    wav = Path(tmp) / f"tc_{nr}.wav"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(pfad),
                    "-map", "0:a:0", "-ac", "1", "-ar", "48000",
                    "-c:a", "pcm_s16le", str(wav)], check=True)
    w = wave.open(str(wav), "rb")
    d = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(np.float64)
    w.close()
    return d, 48000


def versatz(a, b, sr):
    """Wie viele Sekunden liegt b VOR a? (positiv = b startete frueher)"""
    a = a - a.mean()
    b = b - b.mean()
    n = 1 << int(np.ceil(np.log2(len(a) + len(b))))
    c = np.fft.irfft(np.fft.rfft(a, n) * np.conj(np.fft.rfft(b, n)), n)
    c = np.concatenate((c[-(len(b) - 1):], c[:len(a)]))
    lag = int(np.argmax(np.abs(c))) - (len(b) - 1)
    guete = np.abs(c).max() / np.median(np.abs(c))
    return -lag / sr, guete


def main():
    clips = sys.argv[1:]
    if len(clips) < 2:
        raise SystemExit(__doc__)

    with tempfile.TemporaryDirectory() as tmp:
        meta = [probe(c) for c in clips]
        toene = [ton(c, tmp, i) for i, c in enumerate(clips)]

        print("Eingebetteter Timecode")
        print("-" * 64)
        for m in meta:
            print(f"  {m['name']:<40s} {m['tc']}   {m['fps']:.3f} fps   {m['dauer']:.2f} s")

        fps_set = {round(m["fps"], 3) for m in meta}
        if len(fps_set) > 1:
            print(f"\n  ACHTUNG: gemischte Bildraten {sorted(fps_set)} -- "
                  f"Timecode-Sync ueber verschiedene fps driftet.")

        ref_m, (ref_a, sr) = meta[0], toene[0]
        rms = np.sqrt((ref_a ** 2).mean())
        print(f"\nReferenz: {ref_m['name']}   (Ton-RMS {rms:.0f})")
        if rms < 50:
            print("  Hinweis: sehr leiser Ton -- Messung nur ein Anhaltspunkt.")

        print("\nTimecode gegen Ton gemessen")
        print("-" * 64)
        schlecht = False
        for m, (a, _) in zip(meta[1:], toene[1:]):
            tc_off = ref_m["tc_sek"] - m["tc_sek"]      # positiv: dieser Clip frueher
            ton_off, guete = versatz(ref_a, a, sr)
            d = ton_off - tc_off
            frames = d * ref_m["fps"]
            note = ("gut" if abs(frames) < 1 else
                    "grenzwertig" if abs(frames) < 3 else "SCHLECHT")
            if abs(frames) >= 1:
                schlecht = True
            print(f"  {m['name']}")
            print(f"    Timecode sagt : {tc_off:+.4f} s")
            print(f"    Ton sagt      : {ton_off:+.4f} s   (Guete {guete:.1f})")
            print(f"    Abweichung    : {d * 1000:+.1f} ms = {frames:+.2f} Frames  -> {note}")
            if guete < 10:
                print("    Guete unter 10 -- Ton zu leise/gleichfoermig, Ergebnis unsicher.")

        print("\n" + "-" * 64)
        if schlecht:
            print("Nicht blind auf den Timecode verlassen -- Ursache suchen oder sync.py nehmen.")
        else:
            print("Timecode-Sync belegt. Multicam kann ueber Timecode gebaut werden.")


if __name__ == "__main__":
    main()
