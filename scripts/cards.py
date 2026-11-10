#!/usr/bin/env python3
"""Gera cards de estatísticas e de linguagens (SVG claro/escuro) direto da API do GitHub.
Uso: GITHUB_TOKEN=... python scripts/cards.py --user SEU_USUARIO --out assets
Sem serviços públicos de terceiros: tudo é gerado no seu próprio repositório.
"""
import argparse, html, json, os, urllib.request
from pathlib import Path

API = "https://api.github.com"
FONT = "'JetBrains Mono',ui-monospace,Consolas,monospace"
THEMES = {
    "dark":  dict(bg="#111a24", line="#243447", text="#c9d1d9", dim="#7d8590", acc="#8f7cff"),
    "light": dict(bg="#f6f8fa", line="#d0d7de", text="#1f2328", dim="#656d76", acc="#5a3fd6"),
}
LANG_COLORS = {"Python": "#3572A5", "JavaScript": "#f1e05a", "TypeScript": "#3178c6", "HTML": "#e34c26",
               "CSS": "#563d7c", "Shell": "#89e051", "Java": "#b07219", "C": "#555555", "C++": "#f34b7d",
               "C#": "#178600", "PHP": "#4F5D95", "Go": "#00ADD8", "Rust": "#dea584", "SQL": "#e38c00",
               "Jupyter Notebook": "#DA5B0B", "Batchfile": "#C1F12E", "PowerShell": "#012456"}
FALLBACK = ["#8b949e", "#a371f7", "#f778ba", "#79c0ff", "#ffa657", "#56d364"]


def call(url, token=None, body=None):
    h = {"Accept": "application/vnd.github+json", "User-Agent": "profile-cards"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=body, headers=h)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def streaks(counts):
    best = run = 0
    for c in counts:
        run = run + 1 if c > 0 else 0
        best = max(best, run)
    cur, seq = 0, list(counts)
    if seq and seq[-1] == 0:  # hoje ainda pode estar zerado
        seq = seq[:-1]
    for c in reversed(seq):
        if c > 0:
            cur += 1
        else:
            break
    return cur, best


def collect(user, token):
    u = call(f"{API}/users/{user}", token)
    repos, page = [], 1
    while True:
        b = call(f"{API}/users/{user}/repos?per_page=100&type=owner&page={page}", token)
        repos += b
        if len(b) < 100:
            break
        page += 1
    own = [r for r in repos if not r["fork"]]
    langs = {}
    for r in own[:40]:
        try:
            for k, v in call(r["languages_url"], token).items():
                langs[k] = langs.get(k, 0) + v
        except Exception:
            pass
    d = dict(user=user, stars=sum(r["stargazers_count"] for r in own), repos=u["public_repos"],
             followers=u["followers"], contrib=None, cur=None, best=None, langs=langs)
    if token:
        q = "query($l:String!){user(login:$l){contributionsCollection{contributionCalendar{totalContributions weeks{contributionDays{contributionCount}}}}}}"
        try:
            r = call(f"{API}/graphql", token, json.dumps({"query": q, "variables": {"l": user}}).encode())
            cal = r["data"]["user"]["contributionsCollection"]["contributionCalendar"]
            counts = [x["contributionCount"] for w in cal["weeks"] for x in w["contributionDays"]]
            d["contrib"] = cal["totalContributions"]
            d["cur"], d["best"] = streaks(counts)
        except Exception as ex:
            print("aviso: sem calendário de contribuições:", ex)
    return d


def stats_svg(d, t):
    e = html.escape
    fmt = lambda v: "—" if v is None else f"{v:,}".replace(",", ".")
    items = [("Estrelas", d["stars"]), ("Repositórios", d["repos"]), ("Seguidores", d["followers"]),
             ("Contribuições (1 ano)", d["contrib"]), ("Sequência atual", d["cur"]), ("Maior sequência", d["best"])]
    cells = []
    for i, (k, v) in enumerate(items):
        x, y = 24 + (i % 3) * 150, 70 + (i // 3) * 52
        cells.append(f'<text x="{x}" y="{y}" fill="{t["text"]}" font-size="22" font-weight="700">{fmt(v)}</text>'
                     f'<text x="{x}" y="{y+16}" fill="{t["dim"]}" font-size="9">{e(k)}</text>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 480 180" width="480" height="180" font-family="{FONT}">'
            f'<rect x="1" y="1" width="478" height="178" rx="10" fill="{t["bg"]}" stroke="{t["line"]}"/>'
            f'<text x="24" y="32" fill="{t["acc"]}" font-size="14" font-weight="700">{e(d["user"])}</text>'
            f'<text x="456" y="32" fill="{t["dim"]}" font-size="9" text-anchor="end">em números</text>'
            + "".join(cells) + "</svg>")


def langs_svg(d, t):
    e = html.escape
    items = sorted(d["langs"].items(), key=lambda kv: -kv[1])[:6]
    total = sum(v for _, v in items) or 1
    bar, leg, x = [], [], 24
    for i, (k, v) in enumerate(items):
        col = LANG_COLORS.get(k, FALLBACK[i % len(FALLBACK)])
        w = 432 * v / total
        bar.append(f'<rect x="{x:.1f}" y="48" width="{max(w,1):.1f}" height="10" fill="{col}"/>')
        x += w
        lx, ly = 24 + (i % 3) * 150, 90 + (i // 3) * 22
        leg.append(f'<circle cx="{lx+4}" cy="{ly-3}" r="4" fill="{col}"/>'
                   f'<text x="{lx+14}" y="{ly}" fill="{t["text"]}" font-size="10">{e(k)} <tspan fill="{t["dim"]}">{100*v/total:.1f}%</tspan></text>')
    if not items:
        leg.append(f'<text x="24" y="90" fill="{t["dim"]}" font-size="10">Nenhum código detectado ainda.</text>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 480 140" width="480" height="140" font-family="{FONT}">'
            f'<rect x="1" y="1" width="478" height="138" rx="10" fill="{t["bg"]}" stroke="{t["line"]}"/>'
            f'<text x="24" y="32" fill="{t["acc"]}" font-size="14" font-weight="700">Linguagens mais usadas</text>'
            f'<clipPath id="c"><rect x="24" y="48" width="432" height="10" rx="5"/></clipPath>'
            f'<g clip-path="url(#c)">{"".join(bar)}</g>' + "".join(leg) + "</svg>")


def write_all(d, out):
    for name, fn in (("stats", stats_svg), ("langs", langs_svg)):
        for theme, t in THEMES.items():
            p = out / f"card-{name}-{theme}.svg"
            p.write_text(fn(d, t), encoding="utf-8")
            print("ok", p.name)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--user", required=True)
    ap.add_argument("--out", default="assets")
    a = ap.parse_args()
    write_all(collect(a.user, os.environ.get("GITHUB_TOKEN")), Path(a.out))
