# -*- coding: utf-8 -*-
"""★ Multicam-Clip OHNE GUI erzeugen — komplett per DRT-Bau (Projekt-B2, 27.07.2026).

Bisher galt: "Multicam-Clip erzeugen geht nur von Hand in der GUI". Das stimmt nicht.
Ein Multicam-Clip ist im DRT nichts weiter als
  * ein <Sm2MpMulticamClip>-Element im MediaPool (MpFolder.xml) mit einer eigenen Sequence, und
  * ein SeqContainer, in dem pro Kamera EIN Track liegt (UserDefinedName "Angle 1", "Angle 2", …),
    dessen Clip per <MediaRef> auf die Quell-Timeline zeigt.
Beides laesst sich erzeugen; die Schnitt-Clips der Timeline verweisen dann per <MediaRef> auf
den Multicam-Clip und tragen die Winkel-Ziffer in ihrem FieldsBlob ("Kamera<NBSP>1"/"2").

Zahlenformate (reverse-engineered):
  MediaExtents      = 2 little-endian doubles, hex: [start_s, dauer_s]
  MediaTimemapBA    = "02" + big-endian double (Dauer des Quellmediums in Sekunden)
  MediaStartTime    = Start-TC der Quelle in Sekunden (Frames/FPS)
  Start/Duration/In = Frames (Start = Timeline-Position inkl. 108000 = 01:00:00:00)

Eingang : neu_basis.drt  (Export der verschachtelten Schnitt-Timeline des NEUEN Projekts)
          alt_mc.drt     (Export einer Multicam-Timeline als Muster-Lieferant)
Ausgang : mc_ready.drt   (Multicam-Clip + geschnittene Multicam-Timeline)
"""
import zipfile, re, json, os, uuid, struct, binascii

B      = r"C:\claude\resolve-prep\projekt-b2"
BASIS  = B + r"\mcbuild\neu_basis.drt"
MUSTER = B + r"\mcbuild\alt_mc.drt"
OUT    = B + r"\mcbuild\mc_ready.drt"
SEQOUT = B + r"\mcbuild\schnitt_seq.json"

NAME = "Projekt-B-2 Projekt-B"
MCNAME = f"{NAME} Multicam"
FPS = 30000 / 1001
TCBASE = 108000
CAMS = ("weit", "seite")          # Angle 1 = weit (Leitkamera), Angle 2 = seite
ANGLE = {c: i + 1 for i, c in enumerate(CAMS)}

OFF  = json.load(open(B + r"\offsets.json", encoding="utf-8"))["sources"]
PLAN = json.load(open(B + r"\cut_plan.json", encoding="utf-8"))

# ---------------------------------------------------------------- Hilfen
def uid():
    return str(uuid.uuid4())

def extents(start_s, dur_s):
    return (struct.pack("<d", start_s) + struct.pack("<d", dur_s)).hex()

def timemap(dur_s):
    return "02" + struct.pack(">d", dur_s).hex()

def el(tag, text=""):
    return f"<{tag}>{text}</{tag}>"

def get(z, n):
    return z.read(n).decode("utf-8", "replace")

zb = zipfile.ZipFile(BASIS)
zm = zipfile.ZipFile(MUSTER)
basis = {n: get(zb, n) for n in zb.namelist()}

# ---------------------------------------------------------------- 1. Quell-Timelines im Basis-DRT finden
mpf = basis["MediaPool/Master/MpFolder.xml"]
tl_items = {}      # name -> (DbId, SeqDbId)
for m in re.finditer(r"<Sm2MpTimelineClip DbId=\"([0-9a-f-]+)\">", mpf):
    seg = mpf[m.start():m.start() + 30000]
    nm = re.search(r"<Name>([^<]*)</Name>", seg).group(1)
    sq = re.search(r"<Sm2Sequence DbId=\"([0-9a-f-]+)\">", seg).group(1)
    tl_items[nm] = (m.group(1), sq)
print("Quell-Timelines im DRT:", {k: v[0][:8] for k, v in tl_items.items()})

master_folder = re.search(r"<Sm2MpFolder DbId=\"([0-9a-f-]+)\">", mpf).group(1)

# Container der Schnitt-Timeline (der mit den meisten Videoclips)
schnitt_container = max(
    (n for n in basis if n.startswith("SeqContainer/")),
    key=lambda n: basis[n].count("<Sm2TiVideoClip DbId="))
print("Schnitt-Container:", schnitt_container.split("/")[1][:8],
      "Clips:", basis[schnitt_container].count("<Sm2TiVideoClip DbId="))

# Start/Dauer der Angle-Quell-Timelines (aus deren Clips im jeweiligen Container)
def tl_geom(cam):
    """Start-Frame (inkl. 108000) und Dauer in Frames der Quell-Timeline <NAME cam>."""
    dbid, seq = tl_items[f"{NAME} {cam}"]
    for n, d in basis.items():
        if n.startswith("SeqContainer/") and f"<Sequence>{seq}</Sequence>" in d:
            starts, ends = [], []
            for mm in re.finditer(r"<Start>(-?\d+)</Start>\s*<Duration>(\d+)</Duration>", d):
                s, du = int(mm.group(1)), int(mm.group(2))
                starts.append(s); ends.append(s + du)
            return min(starts), max(ends) - min(starts)
    raise SystemExit(f"Container fuer {cam} nicht gefunden")

GEO = {c: tl_geom(c) for c in CAMS}
print("Angle-Geometrie (Start-Frame, Dauer):", GEO)

MC_START = min(GEO[c][0] for c in CAMS)                       # frueheste Kamera
MC_END   = max(GEO[c][0] + GEO[c][1] for c in CAMS)
MC_DUR   = MC_END - MC_START
MC0      = MC_START - TCBASE                                   # Multicam-Frame 0 == ton-Frame MC0
print(f"Multicam: Start {MC_START} (ton-Frame {MC0}), Dauer {MC_DUR} f = {MC_DUR/FPS:.1f}s")

# ---------------------------------------------------------------- 2. Muster aus alt_mc.drt holen
mm_mpf = get(zm, "MediaPool/Master/MpFolder.xml")
i = mm_mpf.index("<Sm2MpMulticamClip DbId=")
j = mm_mpf.index("</Sm2MpMulticamClip>") + len("</Sm2MpMulticamClip>")
MC_MUSTER = mm_mpf[i:j]

# Definitionscontainer (der mit UserDefinedName "Angle 1")
def_name = next(n for n in zm.namelist()
                if n.startswith("SeqContainer/") and "Angle 1" in get(zm, n))
DEF_MUSTER = get(zm, def_name)

# ein Multicam-Clip-Element aus der alten Schnitt-Timeline (Winkel-FieldsBlob!)
alt_schnitt = max((n for n in zm.namelist() if n.startswith("SeqContainer/")),
                  key=lambda n: get(zm, n).count("<Sm2TiVideoClip DbId="))
d_alt = get(zm, alt_schnitt)
k = d_alt.index("<Sm2TiVideoClip DbId=")
MCCLIP_MUSTER = d_alt[k:d_alt.index("</Sm2TiVideoClip>", k) + len("</Sm2TiVideoClip>")]
MC_FIELDS = re.search(r"<FieldsBlob>([0-9a-f]*)</FieldsBlob>", MCCLIP_MUSTER).group(1)
MC_SELIDX = re.search(r"<CurrentSelectorIdx>(-?\d+)</CurrentSelectorIdx>", MCCLIP_MUSTER).group(1)
PAT = "4b616d657261c2a0"                      # 'Kamera' + NBSP  -> danach die Winkel-Ziffer
assert PAT in MC_FIELDS, "Winkel-Muster im FieldsBlob nicht gefunden"
print("Muster geladen: Multicam-Element, Definitionscontainer, Clip-FieldsBlob")

# ---------------------------------------------------------------- 3. Multicam-Element bauen
# ⭐⭐ WICHTIG: KEINE neuen UUIDs wuerfeln!
# Die Zuordnung "Multicam-Sequence -> Definitionscontainer" steht NICHT im Klartext-XML,
# sondern UTF-16-kodiert INNERHALB der zstd-FieldsBlobs von MpFolder.xml. Wer dem Multicam
# eine neue Sequence-/Container-UUID gibt, ohne diese Blobs zu patchen, bekommt einen
# Multicam-Clip OHNE Angles (Frames 0, schwarzes Bild). Deshalb die IDs des Musters
# uebernehmen — beim Import vergibt Resolve ohnehin frische DbIds.
MC_DBID   = re.search(r'<Sm2MpMulticamClip DbId="([0-9a-f-]+)">', MC_MUSTER).group(1)
MC_SEQ    = re.search(r'<Sm2Sequence DbId="([0-9a-f-]+)">', MC_MUSTER).group(1)
MC_MPITEM = re.search(r"<UniqueMediaPoolItemId>([0-9a-f-]+)</UniqueMediaPoolItemId>",
                      MC_MUSTER).group(1)
MC_CONT   = re.search(r'<Sm2SequenceContainer DbId="([0-9a-f-]+)">', DEF_MUSTER).group(1)
print(f"IDs aus Muster uebernommen: MC={MC_DBID[:8]} Seq={MC_SEQ[:8]} Cont={MC_CONT[:8]}")

mc = MC_MUSTER
mc = re.sub(r"<Name>[^<]*</Name>", el("Name", MCNAME), mc, count=1)
mc = re.sub(r"<MpFolder>[0-9a-f-]+</MpFolder>", el("MpFolder", master_folder), mc, count=1)
NEW_EXT = extents(MC_START / FPS, MC_DUR / FPS)
mc = re.sub(r"<MediaExtents>[0-9a-f]*</MediaExtents>", el("MediaExtents", NEW_EXT), mc, count=1)

# ⭐⭐ FrameRate-Feld der Muster-Sequence auf die FPS DIESES Projekts umstellen — sonst
# rechnet Resolve die Multicam-Sequence intern mit der geerbten Muster-FPS (z.B. 29.97 aus
# einem alten Projekt), und der Clip bricht ab einer gewissen Position SCHWARZ ab (nicht am
# Anfang, sondern mitten drin — sieht wie ein Datenfehler aus, ist aber nur die falsche
# Zeitbasis). Betrifft jedes Projekt, dessen FPS von der Muster-DRT abweicht (z.B. 25 vs.
# 29.97) — nicht nur 25fps. Verifiziert Projekt-J 06.08.2026: Multicam-Clip brach bei
# ~654s statt der echten 1510s ab, GetClipProperty('FPS') zeigte weiterhin 29.97 obwohl das
# Projekt 25fps war. Fix: FrameRate-Hex (8-Byte little-endian double + 8 Nullbytes) IMMER auf
# die eigene FPS umschreiben, auch wenn sie zufaellig mit dem Muster uebereinstimmt.
NEW_FR = (struct.pack("<d", FPS) + b"\x00" * 8).hex()
mc = re.sub(r"<FrameRate>[0-9a-f]*</FrameRate>", el("FrameRate", NEW_FR), mc, count=1)

# ⭐ Der FieldsBlob des Multicam-Elements traegt eine ZWEITE Kopie der MediaExtents
#    (zstd-komprimiert). Bleibt sie auf den Werten des Musters stehen, importiert Resolve
#    den Clip mit Dauer 0 -> schwarzes Bild. Also mitziehen.
def patch_blob_extents(hexstr, alt_ext_hex, neu_ext_hex):
    from compression import zstd
    raw = binascii.unhexlify(hexstr)
    i = raw.find(b"\x28\xb5\x2f\xfd")
    if i < 0:
        return hexstr.replace(alt_ext_hex, neu_ext_hex)
    prefix, data = raw[:i], zstd.decompress(raw[i:])
    alt_b, neu_b = binascii.unhexlify(alt_ext_hex), binascii.unhexlify(neu_ext_hex)
    if alt_b not in data:
        print("  ! MediaExtents nicht im Blob gefunden")
        return hexstr
    data = data.replace(alt_b, neu_b)
    comp = zstd.compress(data)
    # Praefix: 4 Byte ?, 4 Byte Laenge des komprimierten Blocks inkl. 0x81-Marker
    head = prefix[:4]
    return (head + struct.pack(">I", len(comp) + 1) + b"\x81" + comp).hex()

alt_ext = re.search(r"<MediaExtents>([0-9a-f]*)</MediaExtents>", MC_MUSTER).group(1)
mfb = re.search(r"<FieldsBlob>([0-9a-f]+)</FieldsBlob>", mc)
if mfb:
    neu_fb = patch_blob_extents(mfb.group(1), alt_ext, NEW_EXT)
    mc = mc[:mfb.start(1)] + neu_fb + mc[mfb.end(1):]
    print("FieldsBlob des Multicam-Elements gepatcht:",
          len(mfb.group(1))//2, "->", len(neu_fb)//2, "bytes")
# Mark-Bereich auf den ganzen Clip
for tag, val in (("MarkInVideo", 0), ("MarkInAudio", 0),
                 ("MarkOutVideo", MC_DUR - 1), ("MarkOutAudio", MC_DUR - 1),
                 ("CurPlayheadPosition", 0)):
    mc = re.sub(rf"<{tag}>-?\d*</{tag}>", el(tag, val), mc, count=1)

# ---------------------------------------------------------------- 4. Definitionscontainer bauen
dm = DEF_MUSTER
# Tracks des Musters einzeln nehmen und neu befuellen
def track_blocks(text, tag):
    out = []
    for m in re.finditer(rf"<{tag} DbId=", text):
        s = m.start()
        e = text.index(f"</{tag}>", s) + len(f"</{tag}>")
        out.append(text[s:e])
    return out

vtracks = track_blocks(dm[dm.index("<VideoTrackVec>"):dm.index("</VideoTrackVec>")], "Sm2TiTrack")
atracks = track_blocks(dm[dm.index("<AudioTrackVec>"):dm.index("</AudioTrackVec>")], "Sm2TiTrack")
print(f"Definitionsmuster: {len(vtracks)} Video-, {len(atracks)} Audiotracks")

def make_track(muster, cam, clip_tag):
    """Muster-Track auf eine Kamera umbiegen."""
    t = muster
    start, dur = GEO[cam]
    dbid = tl_items[f"{NAME} {cam}"][0]
    t = re.sub(r"<UserDefinedName>[^<]*</UserDefinedName>",
               el("UserDefinedName", f"Angle {ANGLE[cam]}"), t)
    t = re.sub(r"<Name>[^<]*</Name>", el("Name", f"{NAME} {cam}"), t)
    t = re.sub(r"<Start>-?\d+</Start>", el("Start", start), t)
    t = re.sub(r"<Duration>\d+</Duration>", el("Duration", dur), t)
    t = re.sub(r"<MediaRef>[0-9a-f-]+</MediaRef>", el("MediaRef", dbid), t)
    t = re.sub(r"<MediaStartTime>[-\d.eE+]*</MediaStartTime>",
               el("MediaStartTime", repr(start / FPS)), t)
    t = re.sub(r"<MediaTimemapBA>[0-9a-f]*</MediaTimemapBA>",
               el("MediaTimemapBA", timemap(dur / FPS)), t)
    return t

new_v = "".join(f"<Element>{make_track(vtracks[min(i, len(vtracks)-1)], c, 'Sm2TiVideoClip')}</Element>"
                for i, c in enumerate(CAMS))
new_a = "".join(f"<Element>{make_track(atracks[min(i, len(atracks)-1)], c, 'Sm2TiAudioClip')}</Element>"
                for i, c in enumerate(CAMS))

defc = dm
defc = re.sub(r"<VideoTrackVec>.*</VideoTrackVec>", "<VideoTrackVec>" + new_v + "</VideoTrackVec>",
              defc, flags=re.S)
defc = re.sub(r"<AudioTrackVec>.*</AudioTrackVec>", "<AudioTrackVec>" + new_a + "</AudioTrackVec>",
              defc, flags=re.S)

# ---------------------------------------------------------------- 5. Schnitt-Timeline auf Multicam umbiegen
sch = basis[schnitt_container]
clips = []
for m in re.finditer(r"<Sm2TiVideoClip DbId=", sch):
    s = m.start(); e = sch.index("</Sm2TiVideoClip>", s) + len("</Sm2TiVideoClip>")
    clips.append((s, e))
print("Schnitt-Clips:", len(clips))

# Wunschkamera je Clip = Reihenfolge aus dem Plan (die Nesting-Clips tragen den Kameranamen)
cams_seq = []
for s, e in clips:
    nm = re.search(r"<Name>([^<]*)</Name>", sch[s:e]).group(1)
    cams_seq.append("weit" if nm.endswith("weit") else "seite")
print("Winkelfolge:", "".join("W" if c == "weit" else "S" for c in cams_seq))

def to_mc(block, cam):
    b = block
    b = re.sub(r"<Name>[^<]*</Name>", el("Name", MCNAME), b, count=1)
    b = re.sub(r"<MediaRef>[0-9a-f-]+</MediaRef>", el("MediaRef", MC_DBID), b, count=1)
    b = re.sub(r"<MediaStartTime>[-\d.eE+]*</MediaStartTime>",
               el("MediaStartTime", repr(MC_START / FPS)), b, count=1)
    b = re.sub(r"<MediaTimemapBA>[0-9a-f]*</MediaTimemapBA>",
               el("MediaTimemapBA", timemap(MC_DUR / FPS)), b, count=1)
    b = re.sub(r"<CurrentSelectorIdx>-?\d+</CurrentSelectorIdx>",
               el("CurrentSelectorIdx", MC_SELIDX), b, count=1)
    # In: im Nesting-Clip relativ zur Quell-Timeline (Frame 0 = Kamerastart).
    #     ton-Frame = In_alt + off_frames[cam];  Multicam-Frame = ton-Frame - MC0.
    in_alt = int(re.search(r"<In>(-?\d*)</In>", b).group(1) or 0)
    inn = in_alt + OFF[cam]["frames"] - MC0
    b = re.sub(r"<In>-?\d*</In>", el("In", inn), b, count=1)
    # Winkel-Ziffer in den FieldsBlob
    fb = MC_FIELDS
    p = fb.find(PAT) + len(PAT)
    fb = fb[:p] + f"3{ANGLE[cam]}" + fb[p + 2:]
    b = re.sub(r"<FieldsBlob>[0-9a-f]*</FieldsBlob>", el("FieldsBlob", fb), b, count=1)
    return b

out = []
prev = 0
for (s, e), cam in zip(clips, cams_seq):
    out.append(sch[prev:s]); out.append(to_mc(sch[s:e], cam)); prev = e
out.append(sch[prev:])
sch_new = "".join(out)

# ---------------------------------------------------------------- 6. DRT schreiben
mpf_new = mpf.replace("</Sm2MpFolder>", f"<Element>{mc}</Element></Sm2MpFolder>", 1) \
    if "<Element>" not in mpf else re.sub(r"(</Element>)(?!.*</Element>)",
                                          r"\1<Element>" + mc.replace("\\", "\\\\") + "</Element>",
                                          mpf, flags=re.S)

with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as zo:
    for n, d in basis.items():
        if n == "MediaPool/Master/MpFolder.xml":
            d = mpf_new
        elif n == schnitt_container:
            d = sch_new
        zo.writestr(n, d.encode("utf-8"))
    zo.writestr(f"SeqContainer/{MC_CONT}.xml", defc.encode("utf-8"))

json.dump({"MC0": MC0, "MC_START": MC_START, "MC_DUR": MC_DUR,
           "angle": ANGLE, "cams": cams_seq},
          open(SEQOUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print(f"\ngeschrieben: {OUT}  ({os.path.getsize(OUT)} bytes)")
print(f"Multicam-DbId {MC_DBID}  Sequence {MC_SEQ}  Container {MC_CONT}")
print("Angle-Mapping:", ANGLE)
