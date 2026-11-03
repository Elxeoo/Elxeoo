"""Render data/contributions.json as an animated heatmap (contrib-heatmap.svg)."""
import json
import os
from datetime import date

from svg_common import BORDER, GOLD, GOLD_LIGHT, MUTED, TEXT, TITLE_H, window, write

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "data", "contributions.json")
OUT = os.path.join(ROOT, "contrib-heatmap.svg")
STATIC = os.environ.get("STATIC") == "1"

W = 860
PAD = 20
LABEL_W = 30
LEVELS = ["#161b22", "#3d2e0a", "#6b4f12", "#a87a1c", "#e3b341"]
MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()


def main():
    with open(SRC, encoding="utf-8") as f:
        data = json.load(f)
    days, s = data["days"], data["stats"]
    first = date.fromisoformat(days[0]["date"])
    start = first.toordinal() - (first.weekday() + 1) % 7  # back up to Sunday
    cells = []
    for d in days:
        dt = date.fromisoformat(d["date"])
        cells.append((dt, (dt.toordinal() - start) // 7, (dt.weekday() + 1) % 7, d))
    weeks = max(c[1] for c in cells) + 1

    x0 = PAD + LABEL_W
    step = (W - x0 - PAD) / weeks
    size = step * 0.78
    gy = TITLE_H + 70
    grid_h = 7 * step
    best = s["best_day"]["date"]

    body = [
        f'<text x="{PAD}" y="{TITLE_H + 28}"><tspan class="p">can@github</tspan>'
        f'<tspan class="t"> ~ $ ./contributions.sh --user {data["user"]} --year</tspan></text>'
    ]

    # month labels where a new month starts within a week column
    week_start = {}
    for dt, wk, _, _ in cells:
        week_start.setdefault(wk, dt)
    last = None
    for wk in range(weeks):
        m = week_start[wk].month
        if m != last:
            if wk < weeks - 2 and not (wk == 0 and week_start.get(1, week_start[0]).month != m):
                body.append(f'<text class="m" x="{x0 + wk * step:.1f}" y="{gy - 8}">{MONTHS[m - 1]}</text>')
            last = m
    for row, name in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        body.append(f'<text class="m" x="{PAD}" y="{gy + row * step + size * 0.85:.1f}">{name}</text>')

    for dt, wk, row, d in cells:
        delay = "" if STATIC else f' style="animation-delay:{0.3 + (wk + row) * 0.012:.3f}s"'
        stroke = f' stroke="{GOLD_LIGHT}" stroke-width="1.2"' if d["date"] == best and d["count"] else ""
        body.append(
            f'<rect class="d" x="{x0 + wk * step:.1f}" y="{gy + row * step:.1f}" width="{size:.1f}" '
            f'height="{size:.1f}" rx="2" fill="{LEVELS[min(d["level"], 4)]}"{stroke}{delay}/>'
        )

    ly = gy + grid_h + 22
    body.append(f'<text class="t" x="{x0}" y="{ly}"><tspan class="b">{s["total"]:,}</tspan> contributions in the last year</text>')
    lx = W - PAD - 5 * 15 - 70
    legend = [f'<text class="m" x="{lx}" y="{ly}">Less</text>']
    for i, c in enumerate(LEVELS):
        legend.append(f'<rect x="{lx + 32 + i * 15}" y="{ly - 10}" width="11" height="11" rx="2" fill="{c}"/>')
    legend.append(f'<text class="m" x="{lx + 32 + 5 * 15 + 4}" y="{ly}">More</text>')
    body += legend

    best_dt = date.fromisoformat(best)
    tiles = [
        ("current streak", f'{s["current_streak"]} days'),
        ("longest streak", f'{s["longest_streak"]} days'),
        ("best day", f'{s["best_day"]["count"]} · {MONTHS[best_dt.month - 1]} {best_dt.day}'),
        ("active days", f'{s["active_days"]} / {len(days)}'),
    ]
    ty = ly + 20
    tw = (W - x0 - PAD - 3 * 12) / 4
    for i, (label, value) in enumerate(tiles):
        tx = x0 + i * (tw + 12)
        delay = "" if STATIC else f' style="animation-delay:{1.4 + i * 0.12:.2f}s"'
        body.append(
            f'<g class="tile"{delay}><rect x="{tx:.1f}" y="{ty}" width="{tw:.1f}" height="44" rx="6" fill="#161b22" stroke="{BORDER}"/>'
            f'<text class="tl" x="{tx + 12:.1f}" y="{ty + 17}">{label}</text>'
            f'<text class="tv" x="{tx + 12:.1f}" y="{ty + 35}">{value}</text></g>'
        )
    height = ty + 44 + PAD

    css = [
        f".p{{fill:{GOLD};font-size:12px}} .t{{fill:{TEXT};font-size:12px}} .b{{fill:{GOLD_LIGHT};font-weight:700}}",
        f".m{{fill:{MUTED};font-size:10px}}",
        f".tl{{fill:{MUTED};font-size:10px}} .tv{{fill:{GOLD_LIGHT};font-size:14px;font-weight:700}}",
    ]
    if not STATIC:
        css.append(
            "@keyframes drop{from{opacity:0;transform:translateY(-6px)}to{opacity:1;transform:none}}"
            ".d,.tile{opacity:0;animation:drop .4s ease-out forwards}"
        )
    svg = window(W, height, "can@github: ~ — ./contributions.sh", "\n".join(body), extra_css="\n".join(css))
    write(OUT, svg)


if __name__ == "__main__":
    main()
