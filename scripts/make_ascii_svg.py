"""Turn assets/warrior.jpg into an animated, colored ASCII-art SVG (warrior-ascii.svg).

Run locally whenever the source image changes:
    python scripts/make_ascii_svg.py
"""
import colorsys
import os
from xml.sax.saxutils import escape

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

from svg_common import TITLE_H, MUTED, GOLD, write, window

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "assets", "warrior.jpg")
OUT = os.path.join(ROOT, "warrior-ascii.svg")

W, H = 370, 560
PAD = 10
FOOTER = 22
COLS = 80
RAMP = " .`:-=+*cs#%@"  # sparse -> dense
N_COLORS = 7
FOCUS = (0.52, 0.68)  # subject center (x, y) as a fraction of the image
ZOOM = 0.78  # crop height as a fraction of the image height
DETAIL = 0.55
DARK = 0.22  # below this the cell counts as silhouette / rock
SHADE_RAMP = "  ..:-="
RIM = "#ffe9a8"
SHADE = "#3c4b5e"
STATIC = os.environ.get("STATIC") == "1"


def load_grid():
    area_w = W - 2 * PAD
    area_h = H - TITLE_H - PAD - FOOTER - PAD
    cw = area_w / COLS
    rows = round(area_h / (cw * 2.0))  # monospace cells are ~2x taller than wide
    lh = area_h / rows

    im = Image.open(SRC).convert("RGB")
    # crop around the subject, matching the aspect ratio of the text area
    target = area_w / area_h
    iw, ih = im.size
    fx, fy = FOCUS
    ch = round(ih * ZOOM)
    cw_px = round(ch * target)
    left = min(max(0, round(fx * iw - cw_px / 2)), iw - cw_px)
    top = min(max(0, round(fy * ih - ch / 2)), ih - ch)
    im = im.crop((left, top, left + cw_px, top + ch))

    small = im.resize((COLS, rows), Image.LANCZOS)
    # global tone + local detail (a cheap CLAHE stand-in) so rocks and armor keep texture
    gray = im.convert("L")
    detail = np.asarray(gray, dtype=np.float32) - np.asarray(gray.filter(ImageFilter.GaussianBlur(18)), dtype=np.float32)
    detail = Image.fromarray(np.clip(128 + detail * 2.2, 0, 255).astype(np.uint8)).resize((COLS, rows), Image.LANCZOS)
    lum = np.asarray(ImageOps.autocontrast(small.convert("L"), cutoff=1), dtype=np.float32) / 255.0
    det = np.asarray(detail, dtype=np.float32) / 255.0 - 0.5
    lum = np.clip(lum ** 1.1 + det * DETAIL, 0, 1)

    # vivid display colors, readable on a dark background
    vivid = ImageEnhance.Color(small).enhance(1.6)
    px = np.asarray(vivid, dtype=np.float32) / 255.0
    disp = np.zeros_like(px)
    for y in range(rows):
        for x in range(COLS):
            h, s, v = colorsys.rgb_to_hsv(*px[y, x])
            disp[y, x] = colorsys.hsv_to_rgb(h, min(1.0, s * 1.2), 0.55 + 0.45 * v)
    disp_img = Image.fromarray((disp * 255).astype(np.uint8))
    q = disp_img.quantize(colors=N_COLORS, method=Image.MEDIANCUT)
    idx = np.asarray(q)
    pal = q.getpalette()[: N_COLORS * 3]
    colors = ["#%02x%02x%02x" % tuple(pal[i * 3: i * 3 + 3]) for i in range(N_COLORS)]

    chars = [[RAMP[min(len(RAMP) - 1, int(lum[y, x] * len(RAMP)))] for x in range(COLS)] for y in range(rows)]
    idx = idx.astype(np.int32).copy()

    # silhouette pass: dark cells become a dim slate texture, and the dark cells that
    # touch the bright sky get a directional "rim light" stroke in pale gold
    base = np.asarray(ImageOps.autocontrast(small.convert("L"), cutoff=1), dtype=np.float32) / 255.0
    dark = base < DARK
    gy, gx = np.gradient(base)
    gy = gy / 2.0  # rows are ~2x taller than columns
    rim_i, shade_i = len(colors), len(colors) + 1
    colors += [RIM, SHADE]
    for y in range(rows):
        for x in range(COLS):
            if not dark[y, x]:
                continue
            near_sky = any(
                0 <= y + dy < rows and 0 <= x + dx < COLS and base[y + dy, x + dx] > DARK + 0.12
                for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1))
            )
            if near_sky:
                phi = np.degrees(np.arctan2(gx[y, x], gy[y, x])) % 180  # edge tangent angle
                chars[y][x] = "-" if phi < 22.5 or phi >= 157.5 else "/" if phi < 67.5 else "|" if phi < 112.5 else "\\"
                idx[y, x] = rim_i
            else:
                t = np.clip(base[y, x] / DARK + det[y, x] * 2.5, 0, 0.999)
                chars[y][x] = SHADE_RAMP[int(t * len(SHADE_RAMP))]
                idx[y, x] = shade_i
    return rows, cw, lh, chars, idx, colors


def main():
    rows, cw, lh, chars, idx, colors = load_grid()
    x0, y0 = PAD, TITLE_H + PAD
    fs = lh * 0.98
    tl = COLS * cw

    css = [f".c{i}{{fill:{c}}}" for i, c in enumerate(colors)]
    css.append(f".a{{font-size:{fs:.2f}px;white-space:pre}}")
    css.append(f".foot{{fill:{MUTED};font-size:11px}} .prompt{{fill:{GOLD}}}")
    css.append("@keyframes blink{0%,49%{opacity:1}50%,100%{opacity:0}} .cur{animation:blink 1s step-end infinite}")

    defs, body = [], []
    for y in range(rows):
        by = y0 + y * lh
        if not STATIC:
            begin = 0.25 + y * 0.045
            defs.append(
                f'<clipPath id="r{y}"><rect x="{x0}" y="{by:.2f}" width="0" height="{lh + 0.5:.2f}">'
                f'<animate attributeName="width" from="0" to="{tl:.2f}" begin="{begin:.3f}s" dur="0.55s" fill="freeze" '
                f'calcMode="spline" keySplines="0.2 0.7 0.3 1" keyTimes="0;1"/></rect></clipPath>'
            )
        parts = []
        for ci in range(len(colors)):
            line = "".join(chars[y][x] if idx[y, x] == ci and chars[y][x] != " " else " " for x in range(COLS))
            if not line.strip():
                continue
            parts.append(
                f'<text class="a c{ci}" x="{x0}" y="{by + lh * 0.8:.2f}" textLength="{tl:.2f}" '
                f'lengthAdjust="spacingAndGlyphs" xml:space="preserve">{escape(line)}</text>'
            )
        clip = "" if STATIC else f' clip-path="url(#r{y})"'
        body.append(f"<g{clip}>{''.join(parts)}</g>")

    fy = H - PAD - 6
    body.append(
        f'<text class="foot" x="{PAD}" y="{fy}"><tspan class="prompt">can@github</tspan> ~ $ cat warrior.txt'
        f'<tspan class="cur prompt"> █</tspan></text>'
    )

    svg = window(W, H, "can@github: ~/art — ./portrait.sh", "\n".join(body),
                 extra_defs="\n".join(defs), extra_css="\n".join(css))
    write(OUT, svg)


if __name__ == "__main__":
    main()
