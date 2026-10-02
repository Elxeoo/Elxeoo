"""Render info-card.svg: an extruded 3D ASCII "CAN" wordmark plus a neofetch-style card.

    python scripts/make_info_card.py          # animated
    STATIC=1 python scripts/make_info_card.py # frozen final frame (for previews)
"""
import os
from xml.sax.saxutils import escape

from svg_common import BORDER, GOLD, GOLD_LIGHT, MUTED, STEEL, TEXT, TITLE_H, window, write

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "info-card.svg")
STATIC = os.environ.get("STATIC") == "1"

W, H = 490, 560
PAD = 22

WORD = "CAN"
GLYPHS = {
    "C": [
        "..######",
        ".##....#",
        "##......",
        "##......",
        "##......",
        "##......",
        "##......",
        ".##....#",
        "..######",
    ],
    "A": [
        "...##...",
        "..####..",
        ".##..##.",
        "##....##",
        "##....##",
        "########",
        "##....##",
        "##....##",
        "##....##",
    ],
    "N": [
        "##....##",
        "###...##",
        "####..##",
        "##.##.##",
        "##..####",
        "##...###",
        "##....##",
        "##....##",
        "##....##",
    ],
}
PX_W = 2  # characters per glyph pixel (cells are ~2x taller than wide)
GAP = 4  # columns between letters
EXTRUDE = [(1, 1), (2, 1)]  # (dx cols, dy rows), front to back
FRONT, SIDE = "#", "+"

INFO = [
    ("Role", "Cloud & DevOps Engineer"),
    ("Cloud", "Azure · Terraform (Hub-Spoke)"),
    ("Network", "VNets · NSG · RBAC · Zero-Trust"),
    ("K8s", "AKS · Docker · Cilium eBPF"),
    ("CI/CD", "GitHub Actions · Azure Pipelines · Argo CD"),
    ("Certs", "AZ-104 908 · Network+ 815"),
    ("Now", "AZ-400 (in progress)"),
    ("Before", "500+ room resort ops & crisis desk"),
    ("Motto", "1% better every day"),
]
SWATCHES = ["#0d1117", "#3c4b5e", STEEL, "#6b4f12", "#a87a1c", GOLD, GOLD_LIGHT, "#ffe9a8"]


def wordmark_grid():
    rows = len(GLYPHS[WORD[0]])
    depth_x = max(dx for dx, _ in EXTRUDE)
    depth_y = max(dy for _, dy in EXTRUDE)
    width = len(WORD) * 8 * PX_W + (len(WORD) - 1) * GAP + depth_x
    front = set()
    col = 0
    for ch in WORD:
        for y, line in enumerate(GLYPHS[ch]):
            for x, p in enumerate(line):
                if p == "#":
                    for k in range(PX_W):
                        front.add((y, col + x * PX_W + k))
        col += 8 * PX_W + GAP
    grid = [[" "] * width for _ in range(rows + depth_y)]
    kind = [[None] * width for _ in range(rows + depth_y)]
    for dx, dy in reversed(EXTRUDE):
        for y, x in front:
            grid[y + dy][x + dx] = SIDE
            kind[y + dy][x + dx] = "side"
    for y, x in front:
        grid[y][x] = FRONT
        kind[y][x] = "front"
    return grid, kind, width


def main():
    grid, kind, cols = wordmark_grid()
    rows = len(grid)
    cw = (W - 2 * PAD) / cols
    lh = cw * 1.95
    fs = lh * 0.92
    tl = cols * cw
    wy = TITLE_H + 26

    defs = [
        f'<linearGradient id="gold" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="{W}" y2="0" spreadMethod="reflect">'
        f'<stop offset="0" stop-color="{GOLD}"/><stop offset="0.45" stop-color="{GOLD_LIGHT}"/>'
        f'<stop offset="0.5" stop-color="#fff6dc"/><stop offset="0.55" stop-color="{GOLD_LIGHT}"/>'
        f'<stop offset="1" stop-color="{GOLD}"/>'
        + ("" if STATIC else
           f'<animateTransform attributeName="gradientTransform" type="translate" from="-{W}" to="{W}" '
           f'begin="1.6s" dur="4s" repeatCount="indefinite"/>')
        + "</linearGradient>"
    ]
    css = [
        f".w{{font-size:{fs:.2f}px;white-space:pre;font-weight:700}}",
        ".front{fill:url(#gold)}",
        ".side{fill:#6b4f12}",
        f".sub{{fill:{MUTED};font-size:11px}}",
        f".p{{fill:{GOLD};font-size:12px}} .pc{{fill:{TEXT};font-size:12px}}",
        f".k{{fill:{GOLD};font-size:12px;font-weight:700}} .v{{fill:{TEXT};font-size:12px}}",
        f".h{{fill:{GOLD_LIGHT};font-size:13px;font-weight:700}} .rule{{stroke:{BORDER}}}",
        "@keyframes blink{0%,49%{opacity:1}50%,100%{opacity:0}} .cur{animation:blink 1s step-end infinite}",
    ]
    if not STATIC:
        css.append(
            "@keyframes rise{from{opacity:0;transform:translateX(-10px)}to{opacity:1;transform:none}}"
            ".ln{opacity:0;animation:rise .45s ease-out forwards}"
        )

    body = []
    for y in range(rows):
        by = wy + y * lh
        if not STATIC:
            defs.append(
                f'<clipPath id="w{y}"><rect x="{PAD}" y="{by:.2f}" width="0" height="{lh + 0.5:.2f}">'
                f'<animate attributeName="width" from="0" to="{tl + 2:.2f}" begin="{0.15 + y * 0.07:.2f}s" '
                f'dur="0.45s" fill="freeze"/></rect></clipPath>'
            )
        parts = []
        for k in ("side", "front"):
            line = "".join(grid[y][x] if kind[y][x] == k else " " for x in range(cols))
            if line.strip():
                parts.append(
                    f'<text class="w {k}" x="{PAD}" y="{by + lh * 0.8:.2f}" textLength="{tl:.2f}" '
                    f'lengthAdjust="spacingAndGlyphs" xml:space="preserve">{escape(line)}</text>'
                )
        clip = "" if STATIC else f' clip-path="url(#w{y})"'
        body.append(f"<g{clip}>{''.join(parts)}</g>")

    y = wy + rows * lh + 22
    lines = [
        f'<text class="sub" x="{W / 2}" y="{y:.1f}" text-anchor="middle">'
        f"Cloud &amp; DevOps Engineer · Azure · Kubernetes · GitOps</text>"
    ]
    y += 34
    lines.append(f'<text x="{PAD}" y="{y:.1f}"><tspan class="p">can@github</tspan><tspan class="pc"> ~ $ neofetch</tspan></text>')
    y += 24
    lines.append(f'<text class="h" x="{PAD}" y="{y:.1f}">can<tspan fill="{MUTED}">@</tspan>dumanli</text>')
    y += 8
    lines.append(f'<line class="rule" x1="{PAD}" y1="{y:.1f}" x2="{PAD + 150}" y2="{y:.1f}"/>')
    y += 20
    key_w = 9
    for key, val in INFO:
        lines.append(
            f'<text x="{PAD}" y="{y:.1f}" xml:space="preserve"><tspan class="k">{escape(key.ljust(key_w))}</tspan>'
            f'<tspan class="v">{escape(val)}</tspan></text>'
        )
        y += 19
    y += 4
    sw = "".join(
        f'<rect x="{PAD + i * 26}" y="{y:.1f}" width="22" height="11" rx="2" fill="{c}" stroke="{BORDER}"/>'
        for i, c in enumerate(SWATCHES)
    )
    lines.append(f"<g>{sw}</g>")
    y += 40
    lines.append(
        f'<text x="{PAD}" y="{y:.1f}"><tspan class="p">can@github</tspan><tspan class="pc"> ~ $ </tspan>'
        f'<tspan class="p cur">█</tspan></text>'
    )

    t0 = 0.15 + rows * 0.07 + 0.3
    for i, ln in enumerate(lines):
        if STATIC:
            body.append(ln)
        else:
            body.append(f'<g class="ln" style="animation-delay:{t0 + i * 0.12:.2f}s">{ln}</g>')

    svg = window(W, H, "can@github: ~ — ./wordmark.sh --3d", "\n".join(body),
                 extra_defs="\n".join(defs), extra_css="\n".join(css))
    write(OUT, svg)


if __name__ == "__main__":
    main()
