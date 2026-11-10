"""Atualiza a tabela de projetos do README com os repositórios públicos mais recentes."""
import json
import os
import re
import urllib.request

USER = os.environ.get("GH_USER", "MiguelDouglassketch")
TOKEN = os.environ.get("GH_TOKEN", "")
MAX_REPOS = 6
START, END = "<!--PROJECTS:START-->", "<!--PROJECTS:END-->"


def fetch_repos():
    url = f"https://api.github.com/users/{USER}/repos?per_page=100&sort=pushed"
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)


def build_table(repos):
    rows = ["| Projeto | Descrição | Tecnologia |", "|---|---|---|"]
    for r in repos:
        desc = (r.get("description") or "—").replace("|", "/")
        lang = r.get("language") or "—"
        rows.append(f"| [{r['name']}]({r['html_url']}) | {desc} | {lang} |")
    return "\n".join(rows)


def main():
    repos = [
        r for r in fetch_repos()
        if not r["fork"] and not r["archived"] and r["name"].lower() != USER.lower()
    ][:MAX_REPOS]

    with open("README.md", encoding="utf-8") as f:
        content = f.read()

    new_block = f"{START}\n{build_table(repos)}\n{END}"
    content = re.sub(f"{re.escape(START)}.*?{re.escape(END)}", new_block, content, flags=re.S)

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(content)


if __name__ == "__main__":
    main()
