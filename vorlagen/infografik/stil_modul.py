# -*- coding: utf-8 -*-
"""
Gemeinsames Stil-Modul fuer Infografik-Einblendungen (Vollbild + Lower-Third).
Ein Modul, viele kurze Grafik-Skripte (`from stil_modul import *`).

PRO REIHE ANPASSEN (nur diese Zeilen):
  - OUT      : Zielordner der PNGs (Default per Env GR_OUT ueberschreibbar)
  - Farben   : BG_IN/BG_OUT/GOLD/CREAM ... an die Reihe angleichen
  - Fonts    : bebas()/segoe() falls andere Schriften
Alles andere (titel, donut, ctext, save mit AUTO-ZENTRIERUNG) ist generisch.

Stand Reihe-R #3 (29.07.2026): save() zentriert Vollbild-Grafiken
automatisch vertikal (center=True) und prueft die Zoom-Sicherheit -
damit entfaellt das Nachmessen und die Rueckfrage "mehr in die Mitte?".
"""
import math, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

S = 2
W, H = 2304*S, 1296*S
OUT = os.environ.get("GR_OUT", r"E:\Reihe-R Reihe-R\renderings\#3 Thema-Y")

BG_IN  = (16, 40, 70)
BG_OUT = (5, 12, 24)
CREAM  = (243, 237, 223)
GOLD   = (233, 168, 60)
GOLD_HI= (247, 196, 96)
BODY   = (200, 212, 226)
MUTED  = (150, 168, 190)
BLUE_MUTED = (74, 110, 150)
RING_BG = (30, 52, 82)

FDIR = "C:/Windows/Fonts/"
def bebas(px):  return ImageFont.truetype(FDIR+"BebasNeue-Regular.otf", int(px*S))
def segoe(px):  return ImageFont.truetype(FDIR+"segoeui.ttf", int(px*S))
def segoeb(px): return ImageFont.truetype(FDIR+"segoeuib.ttf", int(px*S))
def segoesb(px):return ImageFont.truetype(FDIR+"segoeuisl.ttf", int(px*S))


def background():
    """Radialer Verlauf, Mitte hell."""
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    cx, cy = W*0.5, H*0.42
    maxd = math.hypot(W*0.6, H*0.6)
    t = np.clip(np.hypot(xx-cx, yy-cy)/maxd, 0, 1)**2
    arr = np.zeros((H, W, 3), np.uint8)
    for i in range(3):
        arr[..., i] = (BG_IN[i] + (BG_OUT[i]-BG_IN[i])*t).astype(np.uint8)
    return Image.fromarray(arr)


def ctext(d, cx, y, text, font, fill, ls=0, anchor="mm"):
    """Zentrierter Text, optional mit Buchstabenabstand."""
    if ls:
        total = sum(d.textlength(c, font=font)+ls*S for c in text) - ls*S
        x = cx - total/2
        for c in text:
            d.text((x, y), c, font=font, fill=fill, anchor="lm")
            x += d.textlength(c, font=font)+ls*S
    else:
        d.text((cx, y), text, font=font, fill=fill, anchor=anchor)


def ltext(d, x, y, text, font, fill, ls=0):
    """Linksbuendiger Text mit optionalem Buchstabenabstand (Baseline mittig)."""
    if ls:
        for c in text:
            d.text((x, y), c, font=font, fill=fill, anchor="lm")
            x += d.textlength(c, font=font)+ls*S
        return x
    d.text((x, y), text, font=font, fill=fill, anchor="lm")
    return x + d.textlength(text, font=font)


def titel(d, text, unter=None, y=185):
    """Titelzeile + Goldlinie + optionale Unterzeile."""
    ctext(d, W//2, y*S, text, bebas(92), CREAM, ls=8)
    lw = 210*S
    d.line([(W//2-lw, (y+77)*S), (W//2+lw, (y+77)*S)], fill=GOLD, width=3*S)
    if unter:
        ctext(d, W//2, (y+120)*S, unter, segoesb(33), BODY, ls=2)


def glow_layer(img, layer, radius=12):
    """Weiches Leuchten einer RGBA-Ebene unter die Ebene legen."""
    g = layer.filter(ImageFilter.GaussianBlur(radius*S))
    img.paste(g.convert("RGB"), (0, 0), g)
    img.paste(layer.convert("RGB"), (0, 0), layer)


def donut(img, cx, cy, R, thick, pct, color, track=RING_BG, glow=False):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dl = ImageDraw.Draw(layer)
    bbox = [cx-R, cy-R, cx+R, cy+R]
    dl.arc(bbox, 0, 360, fill=track, width=thick)
    dl.arc(bbox, -90, -90+360*pct/100.0, fill=color, width=thick)
    if glow:
        glow_layer(img, layer)
    else:
        img.paste(layer.convert("RGB"), (0, 0), layer)


def quelle(d, text, y=1230):
    ctext(d, W//2, y*S, text, segoe(24), (110, 130, 155))


def _mess_inhalt(arr, alpha):
    """Bounding-Box des sichtbaren Inhalts (volle 2x-Aufloesung)."""
    if alpha:
        content = arr[..., 3] > 12
    else:
        ref = np.array(background().convert("RGB")).astype(int)
        content = (np.abs(arr[..., :3].astype(int) - ref).sum(2) > 45)
    ys, xs = np.where(content)
    return ys.min(), ys.max(), xs.min(), xs.max()


def save(img, name, alpha=False, dy=0, center=True, lower_third=False):
    """Auf 2304x1296 runterskalieren, speichern, Zoom-Sicherheit pruefen.

    center=True (Standard): der Inhalt wird automatisch VERTIKAL ZENTRIERT
      (Rand oben == Rand unten). Erspart das Nachmessen und die Rueckfrage
      "kann das mehr in die Mitte?". Bei Vollbild-Grafiken immer anlassen.
    lower_third=True: KEIN Zentrieren (das Panel MUSS unten sitzen) und der
      Zoom-Check gegen den unteren Rand wird uebersprungen.
    dy: manuelle Feinverschiebung in Endbild-Pixeln (negativ = nach oben),
      wird ZUSAETZLICH zum Auto-Zentrieren angewandt - fuer Sonderfaelle,
      in denen ein einzelnes Element sonst klebt.
    Hintergrund wird mitverschoben (beim Radialverlauf unsichtbar), der
    freiwerdende Rand mit frischem Hintergrund aufgefuellt.
    """
    from PIL import ImageChops
    mode = "RGBA" if alpha else "RGB"
    arr = np.array(img.convert("RGBA"))
    d_px = int(dy * S)
    if center and not lower_third:
        y0, y1, _, _ = _mess_inhalt(arr, alpha)
        d_px += ((H - 1 - y1) - y0) // 2      # so, dass Rand oben == unten
    if d_px:
        img = ImageChops.offset(img, 0, d_px)
        frisch = background().convert(mode) if not alpha else Image.new("RGBA", (W, H), (0, 0, 0, 0))
        if d_px < 0:      # nach oben -> unten Rand neu fuellen
            band = (0, H + d_px, W, H)
        else:             # nach unten -> oben Rand neu fuellen
            band = (0, 0, W, d_px)
        img.paste(frisch.crop(band), (band[0], band[1]))
    out = img.convert(mode).resize((2304, 1296), Image.LANCZOS)
    path = os.path.join(OUT, name)
    out.save(path)
    # Zoom-Check: Inhalt in den mittleren 86 %?
    a = np.array(out.convert("RGBA"))
    if alpha:
        content = a[..., 3] > 12
    else:
        ref = np.array(background().resize((2304, 1296), Image.LANCZOS)).astype(int)
        content = (np.abs(a[..., :3].astype(int) - ref).sum(2) > 45)
    ys, xs = np.where(content)
    cut, cutx = int(1296*0.0455), int(2304*0.0455)
    if lower_third:
        # Panel liegt bewusst unten und meist randlos ueber die volle Breite -
        # ein Zoom-Check ergibt hier keinen Sinn (der Panel-Verlauf DARF an die
        # Kante). Nur informieren, nicht bewerten.
        print("%-42s  Lower-Third (Panel unten, kein Zoom-Check)" % name)
        return path
    ok = (ys.min() >= cut and ys.max() <= 1296-cut and
          xs.min() >= cutx and xs.max() <= 2304-cutx)
    print("%-42s  x %4d-%4d  y %4d-%4d  zoomsicher=%s  (Rand oben %d, unten %d)"
          % (name, xs.min(), xs.max(), ys.min(), ys.max(),
             "JA" if ok else "NEIN", ys.min(), 1295-ys.max()))
    return path
