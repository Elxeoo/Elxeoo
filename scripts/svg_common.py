"""Shared helpers for the profile SVGs: terminal window chrome, palette, fonts."""
from xml.sax.saxutils import escape

MONO = "ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,'Liberation Mono',monospace"

BG = "#0d1117"
BAR = "#161b22"
BORDER = "#30363d"
MUTED = "#8b949e"
TEXT = "#e6edf3"
GOLD = "#e3b341"
GOLD_LIGHT = "#ffd77a"
STEEL = "#79a6d2"

TITLE_H = 28


def window(width, height, title, body, extra_defs="", extra_css=""):
    """Wrap `body` (SVG markup) in a macOS-style dark terminal window."""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{escape(title)}">
<defs>
  <clipPath id="win"><rect x="0" y="0" width="{width}" height="{height}" rx="10"/></clipPath>
  {extra_defs}
</defs>
<style>
  text {{ font-family: {MONO}; }}
  .title {{ fill: {MUTED}; font-size: 11px; }}
  {extra_css}
</style>
<g clip-path="url(#win)">
  <rect width="{width}" height="{height}" fill="{BG}"/>
  <rect width="{width}" height="{TITLE_H}" fill="{BAR}"/>
  <line x1="0" y1="{TITLE_H}" x2="{width}" y2="{TITLE_H}" stroke="{BORDER}"/>
  <circle cx="16" cy="14" r="5.5" fill="#ff5f56"/>
  <circle cx="34" cy="14" r="5.5" fill="#ffbd2e"/>
  <circle cx="52" cy="14" r="5.5" fill="#27c93f"/>
  <text class="title" x="{width / 2}" y="18" text-anchor="middle">{escape(title)}</text>
{body}
</g>
<rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="10" fill="none" stroke="{BORDER}"/>
</svg>
"""


def write(path, svg):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(svg)
    print(f"wrote {path} ({len(svg.encode('utf-8')) / 1024:.1f} KB)")
