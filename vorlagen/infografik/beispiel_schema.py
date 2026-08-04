# -*- coding: utf-8 -*-
"""#N Aufbau eines Thema-Y - Schnittzeichnung (Daten aus Folie <nr>)."""
import random
from PIL import Image, ImageDraw
from stil_modul import *

# --- Vertikale Verteilung (29.07.2026 nachgemessen und ausgeglichen) ---
# Vorher: Rand oben 147 px, unten nur 71 px, und zwischen Erdreich und
# Bildunterschrift blieben magere 9 px. Drei getrennte Verschiebungen, damit
# oben/unten gleich viel Luft ist UND die Bildunterschrift nicht am Erdreich
# klebt: Titel -42, Turm-Block -59, Bildunterschrift -33.
DYT = -42*S      # Titelblock
DY  = -59*S      # Turm mit allen Beschriftungen
DYC = -33*S      # Bildunterschrift

img = background()
d = ImageDraw.Draw(img)
titel(d, "SO IST EIN Thema-Y AUFGEBAUT",
      "ROHR · MINERALIEN · HOLZKOHLE – IM WECHSEL GESCHICHTET", y=185 + DYT//S)

CX = int(W*0.33)
PW = 200*S                    # Rohrbreite
L, R = CX-PW//2, CX+PW//2
TIP_TOP, BODY_TOP, BODY_BOT = 560*S+DY, 620*S+DY, 1140*S+DY
GROUND = 1000*S+DY

STEIN = (176, 180, 186)
KOHLE = (52, 56, 62)
KIES  = (120, 104, 88)
ERDE  = (48, 37, 29)

# Erdreich
d.rectangle([210*S, GROUND, 1330*S, 1178*S+DY], fill=ERDE)
d.line([(210*S, GROUND), (1330*S, GROUND)], fill=(96, 122, 86), width=5*S)

# Rohrkörper: Schichten
y = BODY_TOP
band = True
random.seed(3)
while y < BODY_BOT-95*S:
    h = 66*S if band else 30*S
    h = min(h, BODY_BOT-95*S-y)
    d.rectangle([L, y, R, y+h], fill=STEIN if band else KOHLE)
    if band:   # Körnung andeuten
        for _ in range(90):
            px_, py_ = random.uniform(L+4*S, R-4*S), random.uniform(y+4*S, y+h-4*S)
            d.ellipse([px_, py_, px_+3*S, py_+3*S], fill=(140, 144, 150))
    y += h
    band = not band
# Fundament: grober Basaltkies
d.rectangle([L, BODY_BOT-95*S, R, BODY_BOT], fill=(74, 62, 50))
random.seed(7)
for _ in range(46):
    px_, py_ = random.uniform(L+8*S, R-14*S), random.uniform(BODY_BOT-88*S, BODY_BOT-14*S)
    r_ = random.uniform(7*S, 13*S)
    d.ellipse([px_, py_, px_+r_*2, py_+r_*2], fill=KIES)

# Rohrwand + Spitze
d.rectangle([L, BODY_TOP, R, BODY_BOT], outline=(214, 216, 220), width=4*S)
d.polygon([(L, BODY_TOP), (CX, TIP_TOP-45*S), (R, BODY_TOP)], fill=(196, 122, 96), outline=(226, 168, 140))
# Kupferspirale über der Spitze
lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
dl = ImageDraw.Draw(lay)
for i in range(3):
    yy = TIP_TOP-105*S - i*42*S
    dl.arc([CX-50*S, yy, CX+50*S, yy+52*S], 0, 360, fill=(226, 152, 74, 255), width=5*S)
glow_layer(img, lay, radius=7)

# --- Beschriftungen rechts ---
def label(y_anker, y_text, kopf, sub):
    x_end = 1345*S
    d.line([(R+18*S, y_anker), (x_end-40*S, y_anker)], fill=GOLD, width=3*S)
    d.line([(x_end-40*S, y_anker), (x_end-40*S, y_text)], fill=GOLD, width=3*S)
    d.ellipse([R+10*S, y_anker-8*S, R+26*S, y_anker+8*S], fill=GOLD)
    ltext(d, x_end, y_text-22*S, kopf, bebas(46), GOLD_HI, ls=3)
    ltext(d, x_end, y_text+26*S, sub, segoe(30), BODY)

label(TIP_TOP-150*S, 425*S+DY, "ÜBERTRAGUNGSEINRICHTUNG", "Spitze mit Kupferspirale")
label(BODY_TOP+33*S, 620*S+DY, "BASALTSPLITT + MAGNETITPULVER", "die verdichtende Mineralschicht")
# Anker exakt auf die MITTE einer schwarzen Kohleschicht:
# Schichtfolge ab BODY_TOP: hell 66 / dunkel 30 / hell 66 / dunkel 30 ...
# -> dunkle Baender bei 686-716, 782-812, 878-908, 974-1004; Mitte 797 (vor DY)
label(797*S+DY, 790*S+DY, "HOLZKOHLE", "organische Zwischenschicht")
label(BODY_BOT-48*S, 1070*S+DY, "GROBER BASALTKIES", "als Fundament im Erdreich")

# --- links: Rohr + Maß ---
d.line([(L-18*S, 700*S+DY), (L-140*S, 700*S+DY)], fill=(150, 168, 190), width=3*S)
d.text((L-160*S, 678*S+DY), "DAS ROHR", font=bebas(46), fill=CREAM, anchor="rm")
d.text((L-160*S, 726*S+DY), "Steingut, Kunststoff oder Kupfer", font=segoe(28), fill=MUTED, anchor="rm")
d.text((L-160*S, 770*S+DY), "ca. 2 m lang, eingegraben", font=segoe(28), fill=MUTED, anchor="rm")
d.text((260*S, 1050*S+DY), "Erdreich", font=segoe(28), fill=(146, 128, 108), anchor="lm")

ctext(d, W//2, 1200*S+DYC, "Der Wechsel von Stein und Kohle verdichtet die Lebensenergie – das Prinzip von Wilhelm Reich.",
      segoe(36), CREAM)

save(img, "g3_aufbau_Thema-Y.png", center=False)
