# -*- coding: utf-8 -*-
"""Transkribiert den 6-Stunden-Hauptton in 10-Minuten-Stuecken (robust, mit
Fortschritt und Wiederaufnahme). Ergebnis in der ZUSAMMENHAENGENDEN Tonzeit
(Bloecke 001..004 hintereinander) = dieselbe Zeitbasis wie die Resolve-Timelines.
Schreibt segments.json + words.json."""
import json, os, sys, time, glob, subprocess
_nv = glob.glob(os.path.join(os.path.dirname(os.__file__), "site-packages", "nvidia", "*", "bin"))
os.environ["PATH"] = os.pathsep.join(_nv) + os.pathsep + os.environ.get("PATH", "")
for d in _nv:
    try: os.add_dll_directory(d)
    except Exception: pass
from faster_whisper import WhisperModel

BASE = r"C:\claude\resolve-prep\projekt-m"
WAV = os.path.join(BASE, "audio16k.wav")
TMP = os.path.join(BASE, "chunks"); os.makedirs(TMP, exist_ok=True)
CHUNK = 600.0
DUR = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                            "-of", "csv=p=0", WAV], capture_output=True, text=True).stdout)
N = int(DUR // CHUNK) + 1
print(f"Gesamt {DUR:.0f}s -> {N} Stuecke a {CHUNK:.0f}s", flush=True)

model = WhisperModel("large-v3", device="cuda", compute_type="int8_float16")
print("Modell geladen", flush=True)

t0 = time.time()
for i in range(N):
    out = os.path.join(TMP, f"seg_{i:03d}.json")
    if os.path.exists(out):
        continue
    ss = i * CHUNK
    piece = os.path.join(TMP, "piece.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(ss), "-t", str(CHUNK),
                    "-i", WAV, piece], check=True)
    segs, words = [], []
    s_it, _ = model.transcribe(piece, language="de", word_timestamps=True,
                               vad_filter=True, vad_parameters=dict(min_silence_duration_ms=500),
                               condition_on_previous_text=False)
    for s in s_it:
        segs.append({"start": round(ss + s.start, 3), "end": round(ss + s.end, 3),
                     "text": s.text.strip()})
        for w in (s.words or []):
            words.append({"start": round(ss + w.start, 3), "end": round(ss + w.end, 3),
                          "word": w.word, "prob": round(w.probability, 2)})
    json.dump({"segments": segs, "words": words}, open(out, "w", encoding="utf-8"),
              ensure_ascii=False)
    el = time.time() - t0
    print(f"  {i+1}/{N}  bis {ss+CHUNK:.0f}s  {len(segs)} Segmente  "
          f"({el/60:.1f} min, Rest ca. {el/(i+1)*(N-i-1)/60:.0f} min)", flush=True)

allseg, allw = [], []
for i in range(N):
    f = os.path.join(TMP, f"seg_{i:03d}.json")
    if not os.path.exists(f): continue
    d = json.load(open(f, encoding="utf-8"))
    allseg += d["segments"]; allw += d["words"]
for i, s in enumerate(allseg): s["i"] = i
json.dump(allseg, open(os.path.join(BASE, "segments.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
json.dump(allw, open(os.path.join(BASE, "words.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print(f"FERTIG: {len(allseg)} Segmente, {len(allw)} Woerter", flush=True)
