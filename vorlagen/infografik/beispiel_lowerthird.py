# -*- coding: utf-8 -*-
"""#1 Fachbegriffe-Lower-Third (RGBA) fuer #3 Kraefttuerme."""
import numpy as np
from PIL import Image, ImageDraw
from stil_modul import *

img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
d = ImageDraw.Draw(img)

# Panel unten: transparent -> dunkelblau
panel_top = 880*S
ph = H - panel_top
t = (np.arange(ph)/ph).reshape(-1, 1)
a = (t*208).astype(np.uint8)
panel = np.zeros((ph, W, 4), np.uint8)
panel[..., 0], panel[..., 1], panel[..., 2] = 6, 15, 30
panel[..., 3] = np.repeat(a, W, axis=1)
img.alpha_composite(Image.fromarray(panel), (0, panel_top))
d.line([(140*S, panel_top+8*S), (W-140*S, panel_top+8*S)], fill=(240, 180, 74, 90), width=2*S)

begriffe = [
    ("ENTSTÖRUNG",     "Störende Einflüsse an einem Platz ausgleichen"),
    ("HARMONISIERUNG", "Grundstück, Haus oder Landschaft wieder ins Gleichgewicht bringen"),
    ("Thema-Y",      "Senkrechtes Rohr mit Mineralien, das Lebensenergie verdichtet"),
]
x0 = 200*S
def_x = x0 + 42*S + 420*S
y = 965*S
for term, dfn in begriffe:
    d.ellipse([x0-2*S, y+14*S, x0+16*S, y+32*S], fill=(240, 180, 74, 255))
    d.text((x0+42*S, y+22*S), term, font=bebas(48), fill=(240, 180, 74, 255), anchor="lm")
    d.text((def_x, y+24*S), dfn, font=segoe(30), fill=CREAM+(255,), anchor="lm")
    y += 72*S

save(img, "g1_fachbegriffe.png", alpha=True, lower_third=True)
