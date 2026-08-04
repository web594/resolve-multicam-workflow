# -*- coding: utf-8 -*-
"""#8 Wie viele Menschen sich belastet fühlen (BfS-Umfragen)."""
from PIL import Image, ImageDraw
from stil_modul import *

img = background()
d = ImageDraw.Draw(img)
titel(d, "DAMIT IST MAN NICHT ALLEIN", "WIE DIE BEVÖLKERUNG DIE STRAHLUNG ERLEBT")

CY = 660*S
RAD = 185*S

lx = int(W*0.30)
donut(img, lx, CY, RAD, 40*S, 30, GOLD, glow=True)
ctext(d, lx, CY-25*S, "30", bebas(180), CREAM)
ctext(d, lx, CY+90*S, "%", bebas(64), GOLD_HI)
ctext(d, lx, CY+280*S, "MACHEN SICH SORGEN", bebas(54), GOLD_HI, ls=4)
ctext(d, lx, CY+336*S, "wegen der Strahlung des Mobilfunks", segoe(29), (196, 178, 150))

rx = int(W*0.70)
donut(img, rx, CY, RAD, 40*S, 7, BLUE_MUTED)
ctext(d, rx, CY-25*S, "7", bebas(180), CREAM)
ctext(d, rx, CY+90*S, "%", bebas(64), BLUE_MUTED)
ctext(d, rx, CY+280*S, "SPÜREN BESCHWERDEN", bebas(54), BODY, ls=4)
ctext(d, rx, CY+336*S, "fühlen sich gesundheitlich beeinträchtigt", segoe(29), MUTED)

ctext(d, W//2, 1120*S, "Rund ein Drittel der Menschen in Deutschland sorgt sich wegen Mobilfunkstrahlung –", segoe(36), CREAM)
ctext(d, W//2, 1168*S, "jeder Vierzehnte spürt körperliche Beschwerden.", segoe(36), CREAM)
quelle(d, "Quelle: Bundesamt für Strahlenschutz, Umfragen zur Risikowahrnehmung Mobilfunk", y=1212)

save(img, "g8_sorge_strahlung.png")
