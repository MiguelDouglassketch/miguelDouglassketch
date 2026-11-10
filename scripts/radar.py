#!/usr/bin/env python3
"""Gera gráfico de radar em SVG (claro e escuro).
Uso: python scripts/radar.py --data assets/skills.json -o assets/radar [--values]
"""
import argparse, html, json, math
from pathlib import Path

FONT = "'JetBrains Mono',ui-monospace,Consolas,monospace"
THEMES = {
    "dark":  dict(line="#2a3a4d", text="#c9d1d9", dim="#7d8590", acc="#3ddc97"),
    "light": dict(line="#d0d7de", text="#1f2328", dim="#656d76", acc="#0a7f55"),
}


def render(cfg, theme, show_values):
    t, e = THEMES[theme], html.escape
    W, H, cx, cy, R = 440, 400, 220, 215, 115
    axes, n, vmax = cfg["axes"], len(cfg["axes"]), cfg.get("max", 100)

    def pt(i, f):
        a = -math.pi / 2 + 2 * math.pi * i / n
        return cx + R * f * math.cos(a), cy + R * f * math.sin(a)

    poly = lambda f: " ".join("%.1f,%.1f" % pt(i, f) for i in range(n))
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="{FONT}">',
         f'<style>.d{{animation:g 1s ease-out both;transform-origin:{cx}px {cy}px}}@keyframes g{{from{{transform:scale(0);opacity:0}}}}</style>',
         f'<text x="{cx}" y="26" fill="{t["text"]}" font-size="13" font-weight="700" text-anchor="middle">{e(cfg["title"])}</text>',
         f'<text x="{cx}" y="43" fill="{t["dim"]}" font-size="9" text-anchor="middle">{e(cfg.get("subtitle",""))}</text>']
    for k in range(1, 5):
        s.append(f'<polygon points="{poly(k/4)}" fill="none" stroke="{t["line"]}"/>')
    for i in range(n):
        x, y = pt(i, 1)
        s.append(f'<line x1="{cx}" y1="{cy}" x2="{x:.1f}" y2="{y:.1f}" stroke="{t["line"]}"/>')
    pts = [pt(i, max(0, min(1, a["value"] / vmax))) for i, a in enumerate(axes)]
    s.append(f'<g class="d"><polygon points="{" ".join("%.1f,%.1f" % p for p in pts)}" fill="{t["acc"]}" fill-opacity=".22" stroke="{t["acc"]}" stroke-width="2"/>')
    s += [f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="{t["acc"]}"/>' for x, y in pts]
    s.append("</g>")
    for i, a in enumerate(axes):
        x, y = pt(i, 1.2)
        c = math.cos(-math.pi / 2 + 2 * math.pi * i / n)
        anc = "start" if c > 0.3 else "end" if c < -0.3 else "middle"
        s.append(f'<text x="{x:.1f}" y="{y+4:.1f}" fill="{t["text"]}" font-size="10" text-anchor="{anc}">{e(a["label"])}</text>')
        if show_values:
            s.append(f'<text x="{x:.1f}" y="{y+16:.1f}" fill="{t["dim"]}" font-size="9" text-anchor="{anc}">{a["value"]}</text>')
    s.append("</svg>")
    return "\n".join(s)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("-o", required=True)
    ap.add_argument("--values", action="store_true")
    a = ap.parse_args()
    cfg = json.loads(Path(a.data).read_text(encoding="utf-8"))
    for theme in THEMES:
        Path(f"{a.o}-{theme}.svg").write_text(render(cfg, theme, a.values), encoding="utf-8")
        print("ok", f"{a.o}-{theme}.svg")
