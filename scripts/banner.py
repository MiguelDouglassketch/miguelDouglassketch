#!/usr/bin/env python3
"""Gera assets/banner-dark.svg e assets/banner-light.svg (terminal animado).

Se existir assets/portrait.(png|jpg|jpeg|webp) ele vira o retrato em pontinhos;
caso contrário é desenhado um sigilo original (olho + anéis de energia).
"""
import html, json, math, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
COLS, ROWS, CELL = 36, 40, 5.2
FONT = "'JetBrains Mono',ui-monospace,SFMono-Regular,Consolas,Menlo,monospace"
THEMES = {
    "dark":  dict(bg="#0b0b16", panel="#11111f", line="#2b2b4a", text="#c9d1d9", dim="#7d8590", acc="#8f7cff", red="#ff5f56"),
    "light": dict(bg="#ffffff", panel="#f6f8fa", line="#d0d7de", text="#1f2328", dim="#656d76", acc="#5a3fd6", red="#cf222e"),
}


def padlock():
    g = [[0.0] * COLS for _ in range(ROWS)]
    cx, cy = (COLS - 1) / 2, 15
    for r in range(ROWS):
        for c in range(COLS):
            d = math.hypot(c - cx, r - cy)
            if r <= 17 and 5.5 <= d <= 10:
                g[r][c] = 1.0
            if 17 <= r <= 36 and 6 <= c <= 29:
                g[r][c] = 0.9 if (r + c) % 3 == 0 else 0.6
            if 23 <= r <= 32 and (math.hypot(c - cx, r - 26) <= 2.2 or (r >= 26 and abs(c - cx) <= 1)):
                g[r][c] = 0.0
    return g


def sigil():
    """Emblema original: olho dentro de aneis de selo, com particulas orbitando."""
    g = [[0.0] * COLS for _ in range(ROWS)]
    cx, cy = (COLS - 1) / 2, (ROWS - 1) / 2
    for r in range(ROWS):
        for c in range(COLS):
            dx, dy = c - cx, r - cy
            d = math.hypot(dx, dy)
            a = math.atan2(dy, dx)
            v = 0.0
            if 16.2 <= d <= 17.6:                       # anel externo
                v = 0.9 if int((a + math.pi) / (2 * math.pi) * 24) % 2 == 0 else 0.45
            if 12.3 <= d <= 13.3:                       # anel interno
                v = max(v, 0.7)
            if 13.3 < d < 16.2 and abs(math.sin(6 * a)) > 0.93 and d > 14:   # raios do selo
                v = max(v, 0.55)
            lid = 7.5 * math.sqrt(max(0.0, 1 - (dx / 11.0) ** 2))             # olho amendoado
            if abs(dx) <= 11 and abs(abs(dy) - lid) <= 0.9:
                v = max(v, 1.0)
            if d <= 5.2 and abs(dy) <= lid:             # iris e pupila
                v = max(v, 1.0 if d <= 2.6 else 0.55)
            g[r][c] = v
    for k in range(8):                                   # particulas de energia
        a = 2 * math.pi * k / 8 + 0.2
        for dr in (-0.6, 0.6):
            x, y = round(cx + 14.8 * math.cos(a) + dr * math.cos(a)), round(cy + 14.8 * math.sin(a) + dr * math.sin(a))
            if 0 <= x < COLS and 0 <= y < ROWS:
                g[y][x] = 1.0
    return g


def photo(path):
    from PIL import Image, ImageOps
    im = Image.open(path).convert("L")
    im = ImageOps.fit(im, (COLS, ROWS), Image.LANCZOS, centering=(0.5, 0.35))
    im = ImageOps.autocontrast(im, cutoff=2)
    px = im.load()
    return [[px[c, r] / 255 for c in range(COLS)] for r in range(ROWS)]


def dots(grid, t, x0, y0, invert):
    out = []
    for r, row in enumerate(grid):
        cs = []
        for c, v in enumerate(row):
            v = 1 - v if invert else v
            if v < 0.18:
                continue
            rad = round(CELL * 0.5 * (0.25 + 0.75 * v), 2)
            cs.append(f'<circle cx="{c*CELL+CELL/2:.1f}" cy="{r*CELL+CELL/2:.1f}" r="{rad}"/>')
        if cs:
            out.append(f'<g class="row" style="animation-delay:{0.9+r*0.035:.2f}s">{"".join(cs)}</g>')
    return f'<g transform="translate({x0},{y0})" fill="{t["acc"]}">{"".join(out)}</g>'


def render(cfg, theme, grid, is_photo):
    t = THEMES[theme]
    e = html.escape
    info = cfg["info"][:12]
    rows = []
    for i, (k, v) in enumerate(info):
        y = 98 + i * 15.5
        d = 0.6 + i * 0.12
        rows.append(
            f'<g class="ln" style="animation-delay:{d:.2f}s">'
            f'<text x="318" y="{y}" fill="{t["dim"]}" font-size="11">{e(k)}</text>'
            f'<text x="840" y="{y}" fill="{t["text"]}" font-size="11" text-anchor="end">{e(v)}</text></g>')
    x0 = 24 + (262 - COLS * CELL) / 2
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 880 340" width="880" height="340" font-family="{FONT}">
<style>
.row,.ln{{opacity:0;animation:in .5s ease forwards}}
@keyframes in{{to{{opacity:1}}}}
.blink{{animation:bl 1.2s steps(2,start) infinite}}
@keyframes bl{{50%{{opacity:0}}}}
</style>
<rect x="8" y="8" width="864" height="324" rx="12" fill="{t["panel"]}" stroke="{t["line"]}"/>
<circle cx="28" cy="28" r="5" fill="#ff5f56"/><circle cx="46" cy="28" r="5" fill="#ffbd2e"/><circle cx="64" cy="28" r="5" fill="#27c93f"/>
<text x="440" y="32" fill="{t["dim"]}" font-size="11" text-anchor="middle">{e(cfg["window_title"])}</text>
<rect x="24" y="50" width="262" height="262" rx="8" fill="{t["bg"]}" stroke="{t["line"]}"/>
<text x="38" y="70" fill="{t["acc"]}" font-size="10" font-weight="700">VISUAL.MAP</text>
{dots(grid, t, round(x0,1), 80, is_photo and theme == "light")}
<text x="38" y="304" fill="{t["dim"]}" font-size="9">PTS {COLS*ROWS} · {"FOTO" if is_photo else "SIGILO"}</text>
<rect x="302" y="50" width="554" height="262" rx="8" fill="{t["bg"]}" stroke="{t["line"]}"/>
<text x="318" y="70" fill="{t["acc"]}" font-size="10" font-weight="700">SYSTEM.INFO</text>
<circle class="blink" cx="520" cy="66" r="3" fill="{t["red"]}"/><text x="528" y="70" fill="{t["red"]}" font-size="9" font-weight="700">LIVE</text>
<text x="840" y="70" fill="{t["acc"]}" font-size="10" text-anchor="end">@{e(cfg["handle"])}</text>
{"".join(rows)}
<text x="318" y="300" fill="{t["acc"]}" font-size="9">{e(cfg["footer"])}</text>
<text x="840" y="300" fill="{t["dim"]}" font-size="9" text-anchor="end">{e(cfg["timezone"])}</text>
</svg>'''


def main():
    cfg = json.loads((ASSETS / "profile.json").read_text(encoding="utf-8"))
    img = next((p for ext in ("png", "jpg", "jpeg", "webp") if (p := ASSETS / f"portrait.{ext}").exists()), None)
    grid, is_photo = (photo(img), True) if img else (sigil(), False)
    for theme in THEMES:
        out = ASSETS / f"banner-{theme}.svg"
        out.write_text(render(cfg, theme, grid, is_photo), encoding="utf-8")
        print("ok", out.name, out.stat().st_size // 1024, "KB")


if __name__ == "__main__":
    sys.exit(main())
