# -*- coding: utf-8 -*-
"""Transkribiert den Hauptton (16k mono) mit faster-whisper large-v3 auf CUDA.
Schreibt Segmente (start,end,text) + Woerter als JSON. Deutsch, VAD-gefiltert.
Basis fuer den automatischen Multicam-Schnitt (Pausen/Absaetze) und spaetere UT."""
import json, sys, time, os, glob
_nv = glob.glob(os.path.join(os.path.dirname(os.__file__), "site-packages", "nvidia", "*", "bin"))
os.environ["PATH"] = os.pathsep.join(_nv) + os.pathsep + os.environ.get("PATH", "")
for d in _nv:
    try: os.add_dll_directory(d)
    except Exception: pass
from faster_whisper import WhisperModel

WAV = r"C:\claude\resolve-prep\projekt-b\audio16k.wav"
OUT = r"C:\claude\resolve-prep\projekt-b"

t0 = time.time()
print("lade large-v3 auf CUDA...", flush=True)
model = WhisperModel("large-v3", device="cuda", compute_type="int8_float16")
print(f"Modell geladen ({time.time()-t0:.0f}s). Transkribiere...", flush=True)

segments, info = model.transcribe(
    WAV, language="de", word_timestamps=True, vad_filter=True,
    vad_parameters=dict(min_silence_duration_ms=500),
    condition_on_previous_text=False,
)
segs = []
words = []
for s in segments:
    segs.append({"i": len(segs), "start": round(s.start, 3), "end": round(s.end, 3),
                 "text": s.text.strip()})
    if s.words:
        for w in s.words:
            words.append({"start": round(w.start, 3), "end": round(w.end, 3),
                          "word": w.word, "prob": round(w.probability, 2)})
    if len(segs) % 50 == 0:
        print(f"  {len(segs)} Segmente, bis {s.end:.0f}s ({time.time()-t0:.0f}s)", flush=True)

json.dump(segs, open(OUT + r"\segments.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
json.dump(words, open(OUT + r"\words.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print(f"FERTIG: {len(segs)} Segmente, {len(words)} Woerter in {time.time()-t0:.0f}s", flush=True)
