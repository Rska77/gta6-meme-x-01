#!/usr/bin/env python3
"""meme.py -- GTA 6 meme generator for the make.fun "Post a GTA 6 meme on X" bounty.

Everything is drawn from PIL primitives: a Vice-City scene kit (sunset gradient
sky, striped sun, skyline, palm silhouettes, sea / road), the make.fun ghost
(white body, thick black outline, two black four-pointed sparkle eyes, a round
little hand holding a magenta coin with a white star), assorted props, and a
caption compositor (DejaVu Sans Bold, white letters, thick black outline).

No downloaded assets, no network. Canvas is 1200x750, opaque, full-bleed.

Usage:
  python3 meme.py candidates --out DIR   render all tournament candidates
  python3 meme.py variants   --out DIR   render the winner's refinement variants
  python3 meme.py final      --out FILE  render the shipped meme.png
"""

import argparse
import math
import os

from PIL import Image, ImageDraw, ImageFont

W, H = 1200, 750
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

MAGENTA = (236, 0, 140)
MAGENTA_LIGHT = (255, 92, 190)
BLACK = (10, 8, 14)
WHITE = (255, 255, 255)


def font(size, bold=True):
    return ImageFont.truetype(FONT_BOLD if bold else FONT_REG, size)


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


# ---------------------------------------------------------------- scene kit

def sky(d, top=(43, 10, 74), horizon_y=560):
    stops = [(0.0, top), (0.45, (146, 34, 114)), (0.75, (232, 84, 108)),
             (1.0, (255, 154, 61))]
    for y in range(horizon_y):
        t = y / max(1, horizon_y - 1)
        for i in range(len(stops) - 1):
            t0, c0 = stops[i]
            t1, c1 = stops[i + 1]
            if t0 <= t <= t1:
                d.line([(0, y), (W, y)], fill=lerp(c0, c1, (t - t0) / (t1 - t0)))
                break


def sun(d, cx=880, cy=330, r=150):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 205, 84))
    # synthwave slits across the lower half
    for i, yy in enumerate(range(cy + 18, cy + r, 26)):
        d.rectangle([cx - r, yy, cx + r, yy + 6 + i * 2], fill=(232, 84, 108))


def skyline(d, base=560, seed=7):
    import random
    rnd = random.Random(seed)
    x = -10
    dark = (22, 9, 40)
    while x < W:
        bw = rnd.randint(55, 110)
        bh = rnd.randint(90, 260)
        d.rectangle([x, base - bh, x + bw, base], fill=dark)
        for wy in range(base - bh + 14, base - 16, 26):
            for wx in range(x + 10, x + bw - 12, 22):
                if rnd.random() < 0.42:
                    d.rectangle([wx, wy, wx + 9, wy + 12], fill=(255, 219, 130))
        x += bw + rnd.randint(4, 18)


def palm(d, x, base=560, s=1.0, flip=False):
    dark = (13, 6, 25)
    sway = -38 * s * (1 if not flip else -1)
    top = (x + sway, base - 215 * s)
    pts = []
    for i in range(11):
        t = i / 10
        pts.append((x + sway * t * t, base - 215 * s * t))
    d.line(pts, fill=dark, width=max(3, int(13 * s)))
    for ang in (-165, -125, -85, -45, -8):
        a = math.radians(ang + (180 if flip else 0) * 0)
        length = 118 * s
        ex = top[0] + math.cos(a) * length * (1 if not flip else -1)
        ey = top[1] + math.sin(a) * length * 0.55 + 26 * s
        mx = top[0] + math.cos(a) * length * 0.5 * (1 if not flip else -1)
        my = top[1] + math.sin(a) * length * 0.3 - 14 * s
        d.line([top, (mx, my), (ex, ey)], fill=dark, width=max(2, int(7 * s)))


def ground_road(d, top=560):
    d.rectangle([0, top, W, H], fill=(38, 33, 52))
    d.rectangle([0, top, W, top + 8], fill=MAGENTA)
    for i, yy in enumerate(range(top + 46, H - 20, 52)):
        wd = 90 - i * 8
        d.rectangle([W // 2 - wd // 2, yy, W // 2 + wd // 2, yy + 12],
                    fill=(255, 236, 170))


def ground_beach(d, top=560):
    d.rectangle([0, top, W, top + 78], fill=(14, 116, 144))
    for yy in range(top + 12, top + 70, 18):
        for xx in range(30, W - 60, 170):
            d.line([(xx + (yy % 37), yy), (xx + 44 + (yy % 37), yy)],
                   fill=(125, 211, 220), width=3)
    d.rectangle([0, top + 78, W, H], fill=(240, 205, 145))
    d.rectangle([0, top + 78, W, top + 84], fill=(255, 240, 200))


def ground_floor(d, top=560, color=(64, 40, 84)):
    d.rectangle([0, top, W, H], fill=color)
    d.rectangle([0, top, W, top + 8], fill=MAGENTA_LIGHT)


def backdrop(d, ground="road", sun_xy=(880, 330), seed=7):
    sky(d)
    sun(d, *sun_xy)
    skyline(d, seed=seed)
    if ground == "road":
        ground_road(d)
    elif ground == "beach":
        ground_beach(d)
    else:
        ground_floor(d)
    palm(d, 86, s=1.05)
    palm(d, 1128, s=0.9, flip=True)


# ---------------------------------------------------------------- text kit

def text_w(d, s, f):
    return d.textlength(s, font=f)


def fit_font(d, s, max_w, start, min_size=20):
    size = start
    while size > min_size and text_w(d, s, font(size)) > max_w:
        size -= 2
    return font(size), size


def caption(d, lines, y, start=66, max_w=1130, fill=WHITE):
    """Centred meme caption: white bold letters, thick black outline."""
    if isinstance(lines, str):
        lines = [lines]
    f, size = fit_font(d, max(lines, key=lambda s: text_w(d, s, font(start))),
                       max_w, start)
    for i, line in enumerate(lines):
        yy = y + i * (size + 12)
        d.text((W // 2, yy), line, font=f, fill=fill, anchor="ma",
               stroke_width=max(3, size // 9), stroke_fill=BLACK)
    return y + len(lines) * (size + 12)


def label(d, xy, s, size=30, fill=WHITE, anchor="mm", stroke=0,
          color=BLACK):
    d.text(xy, s, font=font(size), fill=fill, anchor=anchor,
           stroke_width=stroke, stroke_fill=color)


# ---------------------------------------------------------------- the ghost

def star4(d, cx, cy, r, fill=BLACK):
    k = r * 0.26
    pts = [(cx, cy - r), (cx + k, cy - k), (cx + r, cy), (cx + k, cy + k),
           (cx, cy + r), (cx - k, cy + k), (cx - r, cy), (cx - k, cy - k)]
    d.polygon(pts, fill=fill)


def star5_pts(cx, cy, r):
    pts = []
    for i in range(10):
        ang = -math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * 0.45
        pts.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
    return pts


def coin(d, cx, cy, r):
    cx, cy, r = int(cx), int(cy), int(r)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=MAGENTA,
              outline=BLACK, width=max(3, r // 7))
    d.ellipse([cx - r + 5, cy - r + 5, cx + r - 5, cy + r - 5],
              outline=MAGENTA_LIGHT, width=2)
    d.polygon(star5_pts(cx, cy, r * 0.58), fill=WHITE)


def ghost_body_pts(cx, top, w, h):
    r = w / 2
    cy = top + r
    pts = []
    for i in range(25):  # dome, left -> right
        ang = math.pi * (1 - i / 24)
        pts.append((cx + r * math.cos(ang), cy - r * math.sin(ang)))
    wave_top = top + h - (h * 0.10)
    pts.append((cx + r, wave_top))
    n = 3  # bottom scallops, right -> left
    for s in range(n):
        x0 = cx + r - (w / n) * s
        for i in range(1, 13):
            ang = math.pi * (i / 12)
            xx = x0 - (w / n / 2) * (1 - math.cos(ang)) - (w / n / 2) * 0 \
                if False else x0 - (w / n) * (i / 12)
            yy = wave_top + (h * 0.10) * math.sin(ang) * -1 + (h * 0.10)
            pts.append((xx, yy))
    pts.append((cx - r, wave_top))
    return pts


def ghost(d, cx, top, w=240, h=300, coin_xy=None, disc=True, eyes="sparkle"):
    """Draw the make.fun ghost. Returns (hand_x, hand_y) for prop placement."""
    if disc:
        d.ellipse([int(cx - w * 0.62), int(top + h - 26),
                   int(cx + w * 0.62), int(top + h + 22)], fill=MAGENTA)
    pts = ghost_body_pts(cx, top, w, h)
    d.polygon(pts, fill=WHITE)
    d.line(pts + [pts[0]], fill=BLACK, width=max(5, w // 26), joint="curve")
    r = w / 2
    eye_y = top + r * 1.02
    for sgn in (-1, 1):
        ex = cx + sgn * w * 0.19
        if eyes == "sparkle":
            star4(d, ex, eye_y, w * 0.115)
        elif eyes == "happy":
            d.arc([ex - w * 0.09, eye_y - w * 0.09, ex + w * 0.09,
                   eye_y + w * 0.09], start=200, end=340, fill=BLACK, width=6)
    # round little hand + the magenta coin it holds
    hand_x, hand_y = cx + r * 0.96, top + h * 0.52
    if coin_xy is not None:
        coin(d, coin_xy[0], coin_xy[1], w * 0.30)
        hand_x, hand_y = coin_xy[0] - w * 0.24, coin_xy[1] + w * 0.10
    hr = int(w * 0.13)
    d.ellipse([int(hand_x) - hr, int(hand_y) - hr, int(hand_x) + hr,
               int(hand_y) + hr], fill=WHITE, outline=BLACK,
              width=max(4, int(w) // 34))
    return hand_x, hand_y


def party_hat(d, cx, top, w=70, h=95):
    d.polygon([(cx - w // 2, top), (cx + w // 2, top), (cx + 8, top - h)],
              fill=(255, 205, 60), outline=BLACK)
    d.line([(cx - w // 2, top), (cx + w // 2, top), (cx + 8, top - h),
            (cx - w // 2, top)], fill=BLACK, width=4)
    d.ellipse([cx - 6, top - h - 16, cx + 22, top - h + 12], fill=MAGENTA,
              outline=BLACK, width=3)


def sunglasses(d, cx, eye_y, w):
    bw, bh = w * 0.30, w * 0.20
    for sgn in (-1, 1):
        ex = cx + sgn * w * 0.19
        d.rounded_rectangle([ex - bw / 2, eye_y - bh / 2, ex + bw / 2,
                             eye_y + bh / 2], radius=12, fill=BLACK)
    d.rectangle([cx - w * 0.10, eye_y - 6, cx + w * 0.10, eye_y + 2],
                fill=BLACK)


def cane(d, x, y_top, y_bot):
    d.line([(x, y_bot), (x, y_top + 26)], fill=(120, 72, 20), width=9)
    d.arc([x - 4, y_top - 16, x + 44, y_top + 30], start=270, end=95,
          fill=(120, 72, 20), width=9)


def cobweb(d, cx, cy, r):
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    for ang in range(0, 360, 36):
        a = math.radians(ang)
        od.line([(cx, cy), (cx + r * math.cos(a), cy + r * math.sin(a))],
                fill=(255, 255, 255, 150), width=2)
    for rr in (0.35, 0.65, 0.95):
        od.arc([cx - r * rr, cy - r * rr, cx + r * rr, cy + r * rr],
               start=0, end=360, fill=(255, 255, 255, 130), width=2)
    return ov


def game_case(d, x, y, w=170, h=235, title="GTA VI", sub="LEONIDA"):
    d.rounded_rectangle([x, y, x + w, y + h], radius=10, fill=(16, 14, 30),
                        outline=MAGENTA, width=5)
    d.rectangle([x + 10, y + 10, x + w - 10, y + 62], fill=MAGENTA)
    label(d, (x + w / 2, y + 36), title, size=30)
    label(d, (x + w / 2, y + h - 58), "GRAND", size=19,
          fill=(255, 190, 220))
    label(d, (x + w / 2, y + h - 32), "THEFT AUTO", size=19,
          fill=(255, 190, 220))
    label(d, (x + w / 2, y + 96), sub, size=17, fill=(150, 240, 230))


def stamp_approved(d, cx, cy):
    layer = Image.new("RGBA", (340, 130), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    ld.rounded_rectangle([6, 6, 334, 124], radius=14, outline=(214, 30, 40),
                         width=9)
    ld.text((170, 65), "APPROVED", font=font(52), fill=(214, 30, 40),
            anchor="mm")
    return layer.rotate(14, expand=True)


def base(ground="road", seed=7, sun_xy=(880, 330)):
    img = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(img)
    backdrop(d, ground=ground, seed=seed, sun_xy=sun_xy)
    return img, d


# ---------------------------------------------------------------- scenes

def c01(top_lines=("WAITED 13 YEARS FOR THIS",),
        bot_lines=("PAID WITH MY make.fun", "BOUNTY MONEY"),
        ghost_cx=400, ghost_w=270, ghost_top=215, cap_top_y=26, cap_bot_y=618):
    """Store counter: the ghost hands its coin over for a GTA VI case."""
    img, d = base(ground="floor", seed=11)
    caption(d, list(top_lines), cap_top_y, start=64)
    # counter
    d.rectangle([90, 468, 1110, 492], fill=(146, 96, 44))
    d.rectangle([90, 492, 1110, 640], fill=(104, 64, 30))
    d.rectangle([90, 492, 1110, 640], outline=BLACK, width=4)
    # the game, standing proud on the counter
    game_case(d, 742, 252, 196, 268)
    d.polygon([(742, 520), (938, 520), (968, 556), (716, 556)],
              fill=(30, 22, 44))
    # the ghost, coin stretched toward the case
    ghost(d, ghost_cx, ghost_top, w=ghost_w, h=int(ghost_w * 1.22),
          coin_xy=(ghost_cx + ghost_w * 0.86, ghost_top + ghost_w * 0.62))
    caption(d, list(bot_lines), cap_bot_y, start=58)
    return img


def c02():
    """Boss ghost stamps the sick-leave form; worker ghost cheers."""
    img, d = base(ground="floor", seed=5)
    caption(d, "SICK LEAVE: APPROVED", 26, start=64)
    # the form
    d.rectangle([368, 168, 800, 520], fill=(250, 248, 240), outline=BLACK,
                width=5)
    label(d, (584, 208), "SICK LEAVE FORM", size=33, fill=(30, 30, 40))
    rows = [("NAME:", "THE GHOST"), ("REASON:", "LEONIDA"),
            ("DURATION:", "UNTIL 100%"), ("GAME:", "GTA VI")]
    for i, (k, v) in enumerate(rows):
        yy = 268 + i * 52
        label(d, (398, yy), k, size=27, fill=(90, 90, 100), anchor="lm")
        label(d, (540, yy), v, size=29, fill=(20, 20, 30), anchor="lm")
        d.line([(392, yy + 24), (776, yy + 24)], fill=(200, 200, 205),
               width=2)
    img.paste(stamp_approved(d, 0, 0), (520, 372), stamp_approved(d, 0, 0))
    # worker ghost with controller (left)
    ghost(d, 218, 300, w=168, h=205, disc=False)
    d.rounded_rectangle([128, 452, 268, 512], radius=24, fill=(24, 24, 34),
                        outline=BLACK, width=4)
    d.ellipse([226, 470, 250, 494], fill=MAGENTA)
    d.ellipse([152, 474, 168, 490], fill=(255, 220, 90))
    # boss ghost with stamp (right)
    ghost(d, 976, 268, w=196, h=240, disc=False)
    d.rectangle([884, 452, 956, 500], fill=(160, 40, 40), outline=BLACK,
                width=4)
    d.rectangle([902, 424, 938, 454], fill=(90, 60, 30), outline=BLACK,
                width=3)
    caption(d, "SEE YOU AT 100%, BOSS", 640, start=56)
    return img


def c03():
    """In the queue since 2013: cobwebs, a tattered ticket, flying years."""
    img, d = base(ground="road", seed=9)
    caption(d, "IN THIS QUEUE SINCE 2013", 26, start=64)
    # queue barrier
    d.rectangle([120, 470, 1080, 486], fill=(150, 30, 60))
    for xx in range(140, 1080, 160):
        d.rectangle([xx, 470, xx + 12, 620], fill=(60, 55, 70))
    label(d, (600, 448), "NOW SERVING: LAUNCH WEEK", size=30,
          stroke=4)
    # flying calendar pages
    years = [("2013", 150, 150, -12), ("2017", 330, 108, 8),
             ("2021", 830, 118, -7), ("2024", 1000, 176, 13),
             ("2026", 660, 128, 4)]
    for txt, xx, yy, _r in years:
        d.rectangle([xx, yy, xx + 96, yy + 76], fill=(250, 248, 240),
                    outline=BLACK, width=3)
        d.rectangle([xx, yy, xx + 96, yy + 22], fill=(200, 40, 60))
        label(d, (xx + 48, yy + 50), txt, size=26, fill=(30, 30, 40))
    # the ghost, patient and webbed
    ghost(d, 560, 216, w=252, h=308, coin_xy=(560 + 218, 216 + 168))
    img.paste(cobweb(d, 452, 236, 92), (0, 0), cobweb(d, 452, 236, 92))
    # tattered ticket in the other hand
    d.rectangle([330, 372, 452, 424], fill=(245, 230, 180), outline=BLACK,
                width=3)
    label(d, (391, 398), "GTA VI", size=25, fill=(40, 30, 20))
    caption(d, "STILL FIRST IN LINE", 648, start=56)
    return img


def c04():
    """The download bar stuck at 99% -- the real final boss."""
    img, d = base(ground="floor", seed=3)
    caption(d, "THE REAL FINAL BOSS", 24, start=66)
    # monitor
    d.rounded_rectangle([330, 150, 1130, 520], radius=18, fill=(13, 16, 30),
                        outline=BLACK, width=6)
    label(d, (392, 196), "DOWNLOADING: GTA VI", size=31, anchor="lm",
          fill=(170, 240, 235))
    d.rounded_rectangle([392, 268, 1068, 330], radius=26,
                        outline=WHITE, width=5)
    d.rounded_rectangle([400, 276, 400 + int(668 * 0.99), 322], radius=20,
                        fill=MAGENTA)
    label(d, (730, 382), "99%", size=64, fill=WHITE)
    label(d, (730, 446), "TIME REMAINING: 3 YEARS", size=36,
          fill=(255, 190, 90))
    d.rectangle([700, 520, 760, 566], fill=BLACK)
    d.rectangle([620, 566, 840, 580], fill=BLACK)
    # the ghost, hypnotised
    ghost(d, 190, 268, w=200, h=246, disc=False)
    caption(d, "IT HAS BEEN 99% SINCE TUESDAY", 636, start=54)
    return img


def c05():
    """Florida ghost: sunglasses, deck chair, five wanted stars."""
    img, d = base(ground="beach", seed=13, sun_xy=(240, 210))
    caption(d, "LEONIDA'S MOST WANTED", 26, start=66)
    # wanted stars
    for i in range(5):
        d.polygon(star5_pts(838 + i * 66, 118, 27), fill=(255, 205, 40),
                  outline=BLACK)
    # deck chair
    d.polygon([(640, 640), (880, 640), (820, 520), (610, 520)],
              fill=(240, 90, 120))
    for i in range(5):
        yy = 544 + i * 20
        d.line([(622 - i * 2, yy), (838 - i * 4, yy)], fill=WHITE, width=7)
    d.line([(640, 640), (600, 690)], fill=(90, 60, 30), width=9)
    d.line([(880, 640), (920, 690)], fill=(90, 60, 30), width=9)
    # the ghost of the beach
    gx, gw, gt = 400, 262, 238
    ghost(d, gx, gt, w=gw, h=320, coin_xy=(gx + 232, gt + 176))
    sunglasses(d, gx, gt + (gw / 2) * 1.02, gw)
    caption(d, "(CHARGE: EXCESSIVE VIBES)", 652, start=52)
    return img


def c06():
    """Third launch date's the charm: crossed-out delays, circled date."""
    img, d = base(ground="road", seed=17)
    caption(d, "THIRD LAUNCH DATE'S THE CHARM", 22, start=60)
    pages = [("MAY", "2025", 128, 168), ("MAY", "2026", 330, 150)]
    for mon, yr, xx, yy in pages:
        d.rectangle([xx, yy, xx + 168, yy + 196], fill=(250, 248, 240),
                    outline=BLACK, width=4)
        d.rectangle([xx, yy, xx + 168, yy + 46], fill=(70, 70, 90))
        label(d, (xx + 84, yy + 23), mon, size=28)
        label(d, (xx + 84, yy + 108), yr, size=52, fill=(30, 30, 40))
        label(d, (xx + 84, yy + 158), "DELAYED", size=24,
              fill=(200, 40, 50))
        d.line([(xx + 12, yy + 180), (xx + 156, yy + 60)], fill=(214, 30, 40),
               width=10)
        d.line([(xx + 12, yy + 60), (xx + 156, yy + 180)], fill=(214, 30, 40),
               width=10)
    # the surviving page, circled
    xx, yy = 560, 140
    d.rectangle([xx, yy, xx + 210, yy + 240], fill=(255, 252, 235),
                outline=BLACK, width=5)
    d.rectangle([xx, yy, xx + 210, yy + 54], fill=MAGENTA)
    label(d, (xx + 105, yy + 27), "NOVEMBER", size=29)
    label(d, (xx + 105, yy + 122), "2026", size=60, fill=(30, 30, 40))
    label(d, (xx + 105, yy + 188), "LAUNCH WEEK", size=25,
          fill=(200, 30, 90))
    d.ellipse([xx - 16, yy + 66, xx + 226, yy + 226], outline=(214, 30, 40),
              width=9)
    # celebrating ghost
    gx, gt, gw = 972, 268, 216
    ghost(d, gx, gt, w=gw, h=264, coin_xy=(gx + 192, gt + 150))
    party_hat(d, gx - 20, gt + 16)
    caption(d, "PARTY HAT STAYED ON SINCE 2025", 646, start=52)
    return img


def c07():
    """Getaway driver: bounty money bought the Vice City convertible."""
    img, d = base(ground="road", seed=19, sun_xy=(250, 200))
    # passengers: Jason-and-Lucia silhouettes in the back
    for hx, hair in ((742, (30, 22, 30)), (838, (52, 30, 44))):
        d.ellipse([hx - 34, 318, hx + 34, 386], fill=hair)
        d.polygon([(hx - 46, 420), (hx + 46, 420), (hx + 30, 378),
                   (hx - 30, 378)], fill=hair)
    d.rectangle([700, 330, 792, 344], fill=(16, 14, 24))  # Lucia's ponytail base
    # driver ghost (car body will overlap its lower half)
    gx, gt, gw = 520, 218, 224
    ghost(d, gx, gt, w=gw, h=274, disc=False,
          coin_xy=(gx + 216, gt + 96))
    # convertible body
    d.polygon([(180, 560), (236, 452), (420, 428), (640, 420), (880, 428),
               (1010, 470), (1036, 560)], fill=(38, 178, 170))
    d.polygon([(180, 560), (1036, 560), (1036, 606), (180, 606)],
              fill=(24, 130, 128))
    d.polygon([(430, 428), (520, 352), (700, 352), (760, 428)],
              fill=(170, 225, 240))
    d.line([(430, 428), (520, 352), (700, 352), (760, 428)], fill=BLACK,
           width=5)
    d.rectangle([180, 540, 1036, 552], fill=MAGENTA)
    for wx in (330, 880):
        d.ellipse([wx - 62, 540, wx + 62, 664], fill=(12, 12, 16))
        d.ellipse([wx - 28, 574, wx + 28, 630], fill=(225, 228, 235))
    # steering wheel in front of the ghost
    d.ellipse([596, 420, 668, 492], outline=BLACK, width=9)
    # number plate sells the joke quietly
    d.rectangle([928, 566, 1030, 600], fill=WHITE, outline=BLACK, width=3)
    label(d, (979, 583), "MAKE.FUN", size=19, fill=(20, 20, 30))
    # motion lines
    for yy in (470, 516, 560):
        d.line([(36, yy), (140, yy)], fill=(255, 255, 255), width=6)
    caption(d, ["MY make.fun BOUNTIES", "PAID FOR THE GETAWAY CAR"], 622,
            start=56)
    return img


def c08():
    """We got AI agents winning real money before GTA VI."""
    img, d = base(ground="floor", seed=23)
    caption(d, ["WE GOT AI AGENTS WINNING", "REAL MONEY BEFORE GTA VI"], 22,
            start=56)
    # podium
    d.polygon([(420, 640), (780, 640), (740, 540), (460, 540)],
              fill=(120, 60, 140))
    d.rectangle([460, 516, 740, 544], fill=(150, 80, 170))
    # trophy with a coin for a cup
    d.rectangle([578, 428, 622, 520], fill=(230, 175, 40))
    d.polygon([(540, 520), (660, 520), (646, 552), (554, 552)],
              fill=(230, 175, 40))
    d.arc([492, 330, 580, 430], start=300, end=140, fill=(230, 175, 40),
          width=12)
    d.arc([620, 330, 708, 430], start=40, end=240, fill=(230, 175, 40),
          width=12)
    coin(d, 600, 372, 74)
    # shrugging ghost on the podium
    ghost(d, 600, 168, w=190, h=232, disc=False)
    for sgn in (-1, 1):  # both hands up, empty -- the shrug
        hx, hy = 600 + sgn * 128, 330
        d.ellipse([hx - 24, hy - 24, hx + 24, hy + 24], fill=WHITE,
                  outline=BLACK, width=5)
    # confetti
    import random
    rnd = random.Random(4)
    for _ in range(46):
        xx, yy = rnd.randint(30, 1170), rnd.randint(150, 500)
        d.rectangle([xx, yy, xx + 10, yy + 5],
                    fill=rnd.choice([MAGENTA, (255, 205, 60),
                                     (90, 220, 210), WHITE]))
    caption(d, "NOBODY PLANNED THIS TIMELINE", 656, start=50)
    return img


def c09():
    """The price is scary; the coin is ready."""
    img, d = base(ground="floor", seed=29)
    caption(d, "GTA VI PRICE REVEAL DAY", 26, start=62)
    # giant price tag
    tx, ty, tw, th = 700, 170, 380, 300
    d.polygon([(tx, ty), (tx + tw - 90, ty), (tx + tw, ty + th // 2),
               (tx + tw - 90, ty + th), (tx, ty + th)], fill=(250, 240, 205))
    d.line([(tx, ty), (tx + tw - 90, ty), (tx + tw, ty + th // 2),
            (tx + tw - 90, ty + th), (tx, ty + th), (tx, ty)], fill=BLACK,
           width=6, joint="curve")
    d.ellipse([tx + 34, ty + th // 2 - 20, tx + 74, ty + th // 2 + 20],
              fill=(240, 205, 145), outline=BLACK, width=4)
    label(d, (tx + 218, ty + 74), "GTA VI", size=54, fill=(30, 30, 40))
    label(d, (tx + 218, ty + 168), "$100?!", size=72, fill=(200, 30, 40))
    label(d, (tx + 218, ty + 238), "STILL BUYING IT", size=27,
          fill=(90, 80, 60))
    # ghost holding its coin high
    gx, gt, gw = 330, 262, 246
    ghost(d, gx, gt, w=gw, h=300, coin_xy=(gx + 208, gt - 58))
    caption(d, ["GOOD THING MY AGENT EARNS", "REAL MONEY ON make.fun"], 606,
            start=56)
    return img


def c10():
    """Same ghost: 2013 hopeful vs launch-week elderly. Worth it."""
    img, d = base(ground="road", seed=31)
    caption(d, "THE WAIT CHANGED HIM", 22, start=64)
    # divider + faded left panel
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    od.rectangle([0, 0, 596, H], fill=(70, 70, 90, 110))
    img.paste(ov, (0, 0), ov)
    d = ImageDraw.Draw(img)
    d.rectangle([596, 120, 604, 700], fill=WHITE)
    label(d, (300, 132), "2013", size=44, stroke=5)
    label(d, (900, 132), "LAUNCH WEEK", size=44, stroke=5)
    # 2013: young and hopeful, game-case dreams
    ghost(d, 300, 268, w=190, h=232, disc=False)
    d.rounded_rectangle([120, 176, 420, 232], radius=18, fill=WHITE,
                        outline=BLACK, width=4)
    label(d, (270, 204), "ANY DAY NOW!", size=27, fill=(25, 25, 35))
    d.polygon([(330, 232), (352, 262), (306, 232)], fill=WHITE)
    # launch week: cane, party hat, and finally the game
    gx, gt, gw = 892, 252, 216
    ghost(d, gx, gt, w=gw, h=264, coin_xy=(gx + 196, gt + 150))
    party_hat(d, gx - 16, gt + 14)
    cane(d, gx - 150, gt + 190, gt + 440)
    game_case(d, 986, 470, 118, 164, title="GTA VI", sub="")
    caption(d, "WORTH IT.", 664, start=54)
    return img


def c11():
    """Breaking news: the Leonida flu outbreak."""
    img, d = base(ground="beach", seed=37, sun_xy=(980, 200))
    d.rectangle([26, 24, 130, 76], fill=(200, 30, 40))
    label(d, (78, 50), "LIVE", size=32)
    label(d, (1010, 52), "VICE CITY TV", size=28, stroke=4)
    # the patient, coughing into a phone
    gx, gt, gw = 430, 196, 252
    ghost(d, gx, gt, w=gw, h=308, coin_xy=(gx + 226, gt + 170))
    d.rounded_rectangle([gx + 108, gt + 128, gx + 152, gt + 216], radius=8,
                        fill=(20, 20, 28), outline=BLACK, width=3)
    for i, (dx, dy) in enumerate(((-70, 96), (-96, 130), (-66, 164))):
        label(d, (gx + dx, gt + dy), "*", size=40 - i * 6,
              fill=(255, 240, 180), stroke=3)
    label(d, (gx - 118, gt + 66), "COUGH. COUGH.", size=28, stroke=4)
    # chyron
    d.rectangle([0, 566, W, H], fill=(245, 245, 248))
    d.rectangle([0, 566, 250, H], fill=(200, 30, 40))
    label(d, (125, 622), "BREAKING", size=37)
    label(d, (125, 676), "NEWS", size=37)
    label(d, (282, 616), "LEONIDA FLU OUTBREAK", size=47, fill=(18, 18, 26),
          anchor="lm")
    label(d, (282, 672), "MILLIONS CALL IN SICK FOR GTA VI LAUNCH WEEK",
          size=29, fill=(90, 40, 60), anchor="lm")
    return img


def c12():
    """Collector's edition: huge. Coin purse: empty. Worth it."""
    img, d = base(ground="floor", seed=41)
    caption(d, "COLLECTOR'S EDITION: HUGE.", 24, start=60)
    # the box, taller than the ghost
    bx, by, bw, bh = 620, 168, 330, 452
    d.rectangle([bx, by, bx + bw, by + bh], fill=(26, 20, 44),
                outline=MAGENTA, width=6)
    d.rectangle([bx + bw // 2 - 17, by, bx + bw // 2 + 17, by + bh],
                fill=MAGENTA)
    d.rectangle([bx, by + 150, bx + bw, by + 184], fill=MAGENTA)
    label(d, (bx + bw / 2, by + 66), "GTA VI", size=56)
    label(d, (bx + bw / 2, by + 268), "COLLECTOR'S", size=31,
          fill=(255, 190, 220))
    label(d, (bx + bw / 2, by + 306), "EDITION", size=31,
          fill=(255, 190, 220))
    label(d, (bx + bw / 2, by + bh - 52), "STEELBOOK + STATUE + MAP",
          size=19, fill=(160, 240, 230))
    # the ghost, hugging it, purse empty
    gx, gt, gw = 448, 262, 238
    ghost(d, gx, gt, w=gw, h=292, coin_xy=(gx + 218, gt + 158))
    d.polygon([(250, 620), (330, 620), (342, 676), (238, 676)],
              fill=(140, 95, 45))
    d.line([(250, 620), (330, 620)], fill=BLACK, width=5)
    label(d, (290, 700), "PURSE: EMPTY", size=24, stroke=4)
    caption(d, "WORTH IT.", 700 - 44, start=52)
    return img


SCENES = {"c01": c01, "c02": c02, "c03": c03, "c04": c04, "c05": c05,
          "c06": c06, "c07": c07, "c08": c08, "c09": c09, "c10": c10,
          "c11": c11, "c12": c12}

# ------------------------------------------------------- winner refinement
# c01 won the tournament (see tournament.md). Variants explore caption
# wording, ghost size / placement and caption placement around it.

def v1():
    return c01()


def v2():
    return c01(top_lines=("13 YEARS OF WAITING.",),
               bot_lines=("MY AGENT'S make.fun BOUNTIES", "PAID FOR THE GAME"),
               ghost_cx=380, ghost_w=300, ghost_top=196)


def v3():
    return c01(top_lines=("WAITED 13 YEARS FOR THIS",),
               bot_lines=("PAID IN FULL — WITH MY", "make.fun BOUNTY MONEY"),
               ghost_cx=430, ghost_w=246, ghost_top=232, cap_bot_y=628)


VARIANTS = {"v1": v1, "v2": v2, "v3": v3}
FINAL_VARIANT = "v2"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["candidates", "variants", "final"])
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    if args.mode == "candidates":
        os.makedirs(args.out, exist_ok=True)
        for name, fn in SCENES.items():
            fn().save(os.path.join(args.out, name + ".png"))
            print("rendered", name)
    elif args.mode == "variants":
        os.makedirs(args.out, exist_ok=True)
        for name, fn in VARIANTS.items():
            fn().save(os.path.join(args.out, name + ".png"))
            print("rendered", name)
    else:
        VARIANTS[FINAL_VARIANT]().save(args.out)
        print("rendered final ->", args.out)


if __name__ == "__main__":
    main()
