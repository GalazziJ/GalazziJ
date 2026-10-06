
import json
import os
import sys
import textwrap
import urllib.request
from collections import Counter
from datetime import date
from html import escape

NOME = "Jamille Galazi"
CARGO = "Desenvolvedora Front-End"
SUBTITULO = "Sistemas de Informação | IFES"
ESPECIALIDADES = "Prototipagem · Desenvolvimento Web · Responsividade"
RODAPE = "-----------"
SAIDA = "assets/aura.svg"


W, H = 800, 1090
SANS = "'Segoe UI',Helvetica,Arial,sans-serif"
MONO = "'SFMono-Regular',Consolas,'Liberation Mono',Menlo,monospace"
CORES_PILULAS = ["#ff5252", "#ff1744", "#ff4081", "#ff6e40", "#ff8a80", "#f50057", "#ff5c8a", "#ff3d00"]
CORES_BARRA = ["#ff1744", "#6b2a37", "#ff6e40", "#ff4081", "#c51162", "#ff8a80", "#ff9100", "#d50032", "#f50057", "#ff3d00"]
CORES_NIVEL = ["#1c070d", "#5e0b1e", "#a3112f", "#ff1744", "#ffa6b8", "#ffffff"]
CORES_STATS = ["#ffb300", "#ff8a80", "#ff4081", "#ff1744"]

Q_PERFIL = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      totalCommitContributions
      contributionCalendar {
        totalContributions
        weeks { contributionDays { contributionCount date } }
      }
    }
    pinnedItems(first: 3, types: REPOSITORY) {
      nodes { ... on Repository {
        name description stargazerCount forkCount primaryLanguage { name }
      } }
    }
  }
}"""

Q_REPOS = """
query($login: String!, $after: String) {
  user(login: $login) {
    repositories(first: 100, after: $after, ownerAffiliations: OWNER,
                 isFork: false, privacy: PUBLIC) {
      totalCount
      pageInfo { hasNextPage endCursor }
      nodes {
        name description stargazerCount forkCount primaryLanguage { name }
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name } }
        }
      }
    }
  }
}"""


def graphql(query, variaveis, token):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variaveis}).encode(),
        headers={
            "Authorization": f"bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "aura-perfil",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        dados = json.load(r)
    if "errors" in dados:
        sys.exit(f"Erro da API do GitHub: {dados['errors']}")
    return dados["data"]


def buscar_dados(login, token):
    perfil = graphql(Q_PERFIL, {"login": login}, token)["user"]
    if perfil is None:
        sys.exit(f"Usuário '{login}' não encontrado.")

    repos, depois, total_repos = [], None, 0
    while True:
        r = graphql(Q_REPOS, {"login": login, "after": depois}, token)["user"]["repositories"]
        total_repos = r["totalCount"]
        repos += r["nodes"]
        if not r["pageInfo"]["hasNextPage"]:
            break
        depois = r["pageInfo"]["endCursor"]

    linguagens = Counter()
    for rp in repos:
        for e in rp["languages"]["edges"]:
            linguagens[e["node"]["name"]] += e["size"]

    cards = [n for n in perfil["pinnedItems"]["nodes"] if n]
    usados = {c["name"] for c in cards}
    for rp in sorted(repos, key=lambda x: x["stargazerCount"], reverse=True):
        if len(cards) >= 3:
            break
        if rp["name"] not in usados:
            cards.append(rp)

    col = perfil["contributionsCollection"]
    return {
        "login": login,
        "estrelas": sum(r["stargazerCount"] for r in repos),
        "forks": sum(r["forkCount"] for r in repos),
        "repos": total_repos,
        "commits": col["totalCommitContributions"],
        "contribuicoes": col["contributionCalendar"]["totalContributions"],
        "semanas": col["contributionCalendar"]["weeks"],
        "linguagens": linguagens.most_common(10),
        "cards": cards[:3],
    }


def fmt(n):
    return f"{n:,}".replace(",", ".")


def esc(t):
    return escape(str(t), quote=True)


def nivel(qtd, maximo):
    if qtd == 0:
        return 0
    r = qtd / maximo
    if r > 0.9:
        return 5
    if r > 0.6:
        return 4
    if r > 0.3:
        return 3
    if r > 0.1:
        return 2
    return 1


def gerar_svg(d):
    o = []
    a = o.append
    a(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Cartão de perfil">')
    a('''<defs>
<linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#12030a"/><stop offset="1" stop-color="#070104"/></linearGradient>
<radialGradient id="g1" cx="50%" cy="50%" r="50%"><stop offset="0" stop-color="#ff0a3c" stop-opacity=".45"/><stop offset="1" stop-color="#ff0a3c" stop-opacity="0"/></radialGradient>
<radialGradient id="g2" cx="50%" cy="50%" r="50%"><stop offset="0" stop-color="#ff2a6d" stop-opacity=".35"/><stop offset="1" stop-color="#ff2a6d" stop-opacity="0"/></radialGradient>
<radialGradient id="g3" cx="50%" cy="50%" r="50%"><stop offset="0" stop-color="#d50032" stop-opacity=".40"/><stop offset="1" stop-color="#d50032" stop-opacity="0"/></radialGradient>
<linearGradient id="card" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#1c050c"/><stop offset="1" stop-color="#0d0206"/></linearGradient>
<filter id="glow" x="-20%" y="-50%" width="140%" height="200%"><feGaussianBlur stdDeviation="6" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<clipPath id="barclip"><rect x="60" y="550" width="680" height="6" rx="3"/></clipPath>
</defs>''')
    a(f'<rect width="{W}" height="{H}" rx="26" fill="url(#bg)"/>')
    a('<ellipse cx="260" cy="150" rx="260" ry="130" fill="url(#g1)"/>')
    a('<ellipse cx="600" cy="170" rx="230" ry="110" fill="url(#g2)"/>')
    a('<ellipse cx="560" cy="520" rx="300" ry="90" fill="url(#g3)"/>')
    a('<ellipse cx="300" cy="760" rx="300" ry="110" fill="url(#g1)" opacity=".7"/>')
    a('<ellipse cx="640" cy="930" rx="260" ry="100" fill="url(#g2)" opacity=".7"/>')
    a(f'<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="26" fill="none" stroke="#ff1744" stroke-opacity=".28"/>')
    a('<path d="M34 64 V34 H64" fill="none" stroke="#ff3355" stroke-width="2"/>')
    a(f'<path d="M{W-34} {H-64} V{H-34} H{W-64}" fill="none" stroke="#ff3355" stroke-width="2"/>')

    # cabeçalho (o tamanho do título se ajusta ao tamanho do nome)
    nome = NOME.upper()
    tam, esp = (60, 22) if len(nome) <= 6 else (46, 12) if len(nome) <= 10 else (34, 7)
    a(f'<text x="400" y="135" text-anchor="middle" font-family="{SANS}" font-size="{tam}" font-weight="800" letter-spacing="{esp}" fill="#fff" filter="url(#glow)">{esc(nome)}</text>')
    a(f'<text x="400" y="185" text-anchor="middle" font-family="{MONO}" font-size="14" letter-spacing="7" fill="#ff4d6d">{esc(CARGO)}</text>')
    a(f'<text x="400" y="225" text-anchor="middle" font-family="{MONO}" font-size="11" letter-spacing="4" fill="#f3d3da">{esc(SUBTITULO)}</text>')
    a(f'<text x="400" y="252" text-anchor="middle" font-family="{MONO}" font-size="10" letter-spacing="3" fill="#c2415d">{esc(ESPECIALIDADES)}</text>')
    a(f'<text x="400" y="278" text-anchor="middle" font-family="{MONO}" font-size="9" letter-spacing="2" fill="#6b2a37">github.com/{esc(d["login"])}</text>')

    # pílulas de linguagens (top 8)
    top = [n for n, _ in d["linguagens"][:8]]
    if top:
        ws = [len(n) * 8 + 34 for n in top]
        x = (W - (sum(ws) + 10 * (len(ws) - 1))) / 2
        for i, (n, w) in enumerate(zip(top, ws)):
            c = CORES_PILULAS[i % len(CORES_PILULAS)]
            a(f'<rect x="{x:.1f}" y="316" width="{w}" height="26" rx="13" fill="#1a050b" stroke="{c}" stroke-opacity=".7"/>')
            a(f'<text x="{x+w/2:.1f}" y="333" text-anchor="middle" font-family="{MONO}" font-size="11" font-weight="700" fill="{c}">{esc(n)}</text>')
            x += w + 10
    a('<line x1="60" y1="385" x2="740" y2="385" stroke="#ff1744" stroke-opacity=".18"/>')

    # números
    stats = [("ESTRELAS", d["estrelas"]), ("FORKS", d["forks"]), ("REPOSITÓRIOS", d["repos"]), ("COMMITS", d["commits"])]
    for i, (rot, v) in enumerate(stats):
        cx = 145 + i * 170
        a(f'<text x="{cx}" y="437" text-anchor="middle" font-family="{SANS}" font-size="38" font-weight="800" fill="#fff">{fmt(v)}</text>')
        a(f'<text x="{cx}" y="460" text-anchor="middle" font-family="{MONO}" font-size="10" font-weight="700" letter-spacing="3" fill="{CORES_STATS[i]}">{rot}</text>')
    a('<line x1="60" y1="492" x2="740" y2="492" stroke="#ff1744" stroke-opacity=".18"/>')

    def rotulo(t, y):
        a(f'<text x="60" y="{y}" font-family="{MONO}" font-size="10" font-weight="700" letter-spacing="4" fill="#ff3355">{t}</text>')

    # análise da stack
    rotulo("ANÁLISE DA STACK", 525)
    langs = d["linguagens"]
    total_all = sum(s for _, s in langs) or 1
    soma_top = sum(s for _, s in langs) or 1
    x = 60
    a('<g clip-path="url(#barclip)">')
    for i, (n, s) in enumerate(langs):
        w = 680 * s / soma_top
        a(f'<rect x="{x:.1f}" y="550" width="{w+1:.1f}" height="6" fill="{CORES_BARRA[i % len(CORES_BARRA)]}"/>')
        x += w
    a('</g>')
    for i, (n, s) in enumerate(langs):
        col, lin = i % 5, i // 5
        lx, ly = 60 + col * 136, 588 + lin * 28
        pct = s / total_all * 100
        txt = f"{pct:.0f}%" if pct >= 1 else "&lt;1%"
        a(f'<circle cx="{lx+4}" cy="{ly-4}" r="4" fill="{CORES_BARRA[i % len(CORES_BARRA)]}"/>')
        a(f'<text x="{lx+16}" y="{ly}" font-family="{SANS}" font-size="11" fill="#e8c4cc">{esc(n)} <tspan fill="#7d3a48" font-size="9">{txt}</tspan></text>')
    a('<line x1="60" y1="640" x2="740" y2="640" stroke="#ff1744" stroke-opacity=".18"/>')

    # atividade (calendário real, últimas 52 semanas)
    rotulo("ATIVIDADE", 672)
    a(f'<text x="740" y="672" text-anchor="end" font-family="{MONO}" font-size="10" font-weight="700" fill="#7d3a48">{fmt(d["contribuicoes"])} contribuições</text>')
    semanas = d["semanas"][-52:]
    maximo = max([dia["contributionCount"] for s in semanas for dia in s["contributionDays"]] + [1])
    pitch, cel = 13, 10
    x0 = (W - len(semanas) * pitch + 3) / 2
    for c, sem in enumerate(semanas):
        for dia in sem["contributionDays"]:
            r = (date.fromisoformat(dia["date"]).weekday() + 1) % 7  # domingo = 0
            cor = CORES_NIVEL[nivel(dia["contributionCount"], maximo)]
            a(f'<rect x="{x0 + c * pitch:.1f}" y="{695 + r * pitch}" width="{cel}" height="{cel}" rx="2" fill="{cor}"/>')
    a('<line x1="60" y1="805" x2="740" y2="805" stroke="#ff1744" stroke-opacity=".18"/>')

    # projetos principais (fixados no perfil)
    rotulo("PROJETOS PRINCIPAIS", 838)
    cw = 216
    for i, rp in enumerate(d["cards"]):
        cx = 60 + i * (cw + 16)
        c = CORES_PILULAS[i % len(CORES_PILULAS)]
        nome_rp = rp["name"] if len(rp["name"]) <= 20 else rp["name"][:19] + "…"
        linhas = textwrap.wrap(rp["description"] or "Sem descrição", width=34, max_lines=2, placeholder="…")
        lang = (rp["primaryLanguage"] or {}).get("name") or "—"
        a(f'<rect x="{cx}" y="860" width="{cw}" height="130" rx="14" fill="url(#card)" stroke="#ff1744" stroke-opacity=".4"/>')
        a(f'<text x="{cx+18}" y="896" font-family="{SANS}" font-size="15" font-weight="700" fill="#fff">{esc(nome_rp)}</text>')
        for j, ln in enumerate(linhas):
            a(f'<text x="{cx+18}" y="{920 + j * 15}" font-family="{SANS}" font-size="10.5" fill="#b07884">{esc(ln)}</text>')
        a(f'<circle cx="{cx+22}" cy="968" r="4" fill="{c}"/>')
        a(f'<text x="{cx+34}" y="972" font-family="{MONO}" font-size="10" font-weight="700" fill="{c}">{esc(lang)}</text>')
        a(f'<text x="{cx+cw-18}" y="972" text-anchor="end" font-family="{MONO}" font-size="10" fill="#b07884">★ {rp["stargazerCount"]} · {rp["forkCount"]} forks</text>')

    a(f'<text x="400" y="1050" text-anchor="middle" font-family="{MONO}" font-size="8" letter-spacing="3" fill="#5e2a35">{esc(RODAPE)}</text>')
    a('</svg>')
    return "\n".join(o)


def main():
    login = os.environ.get("LOGIN") or os.environ.get("GITHUB_REPOSITORY_OWNER")
    token = os.environ.get("GH_TOKEN")
    if not login or not token:
        sys.exit("Defina as variáveis de ambiente LOGIN e GH_TOKEN.")
    svg = gerar_svg(buscar_dados(login, token))
    os.makedirs(os.path.dirname(SAIDA), exist_ok=True)
    with open(SAIDA, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"Arquivo {SAIDA} atualizado.")


if __name__ == "__main__":
    main()
