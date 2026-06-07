"""Coletor (PROTÓTIPO) do Ranking Web of Universities — Webometrics (Cybermetrics
Lab / CSIC). Webometrics NÃO tem API: este coletor raspa a página pública do
Brasil e extrai a posição da UFTM e de pares (USP, UNICAMP, UFU, UnB) nos três
pilares — Visibilidade/Impact (50%), Excelência/Scholar (40%) e
Transparência/Openness (10%).

ATENÇÃO: protótipo NÃO testado no ambiente onde foi escrito (o domínio
webometrics.info não resolvia ali). Rode de uma rede que o alcance:

    python fetch_webometrics.py

Se a estrutura da tabela tiver mudado, o coletor falha de forma explícita e salva
o HTML bruto em data/_webometrics_raw.html para você conferir colunas/cabeçalho
(e ajustar ALVOS / o mapeamento de colunas, se preciso).

Gera data/webometrics_uftm.csv.
"""
from __future__ import annotations

import re
import socket
import sys
import unicodedata
import urllib.error
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

import pandas as pd

OUT = Path(__file__).parent / "data"
OUT.mkdir(exist_ok=True)

# Página de ranking do Brasil (ordenada por rank mundial). Sem "www" (o subdomínio
# www.webometrics.info é NXDOMAIN). Confirme a URL exata no seu navegador e ajuste
# aqui se necessário — ou rode passando um HTML salvo:  python fetch_webometrics.py pagina.html
BRAZIL_URL = "https://webometrics.info/en/Latin_America/Brazil"
HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
}

# Instituições-alvo: sigla -> trecho DISTINTIVO do nome (sem acento, minúsculo).
# Distintivo o bastante para não casar com homônimas (ex.: "estadual de campinas"
# evita PUC-Campinas; "federal de uberlandia" evita faculdades privadas locais).
ALVOS = {
    "UFTM": "federal do triangulo mineiro",
    "USP": "universidade de sao paulo",
    "UNICAMP": "estadual de campinas",
    "UFU": "federal de uberlandia",
    "UnB": "universidade de brasilia",
}


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return " ".join(s.lower().split())


class _Tabelas(HTMLParser):
    """Coleta toda <table> como lista de linhas; cada linha, lista de células."""

    def __init__(self):
        super().__init__()
        self.tabelas: list[list[list[str]]] = []
        self._tab = None
        self._linha = None
        self._cel = None

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self._tab = []
        elif tag == "tr" and self._tab is not None:
            self._linha = []
        elif tag in ("td", "th") and self._linha is not None:
            self._cel = []

    def handle_data(self, data):
        if self._cel is not None:
            self._cel.append(data)

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self._cel is not None:
            self._linha.append(" ".join("".join(self._cel).split()))
            self._cel = None
        elif tag == "tr" and self._linha is not None:
            self._tab.append(self._linha)
            self._linha = None
        elif tag == "table" and self._tab is not None:
            self.tabelas.append(self._tab)
            self._tab = None


def _baixa(url: str) -> str:
    req = urllib.request.Request(url, headers=HEADERS)
    ultimo = None
    for _ in range(3):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read().decode("utf-8", "replace")
        except (urllib.error.URLError, socket.timeout) as e:
            ultimo = e
    raise RuntimeError(f"Não consegui baixar {url}: {ultimo}. "
                       "Rode de uma rede que resolva webometrics.info.")


def _num(s: str):
    d = re.sub(r"[^\d]", "", s or "")
    return int(d) if d else None


def _tabela_ranking(tabelas):
    """A tabela cujo cabeçalho traz os três pilares do Webometrics."""
    for tab in tabelas:
        if tab:
            cab = _norm(" ".join(tab[0]))
            if "impact" in cab and "openness" in cab and "excellence" in cab:
                return tab
    return None


def _dump(html: str) -> Path:
    p = OUT / "_webometrics_raw.html"
    p.write_text(html, encoding="utf-8")
    return p


def main(fonte: str | None = None) -> None:
    # fonte = caminho de um HTML salvo do navegador (validação offline); senão, baixa.
    if fonte and Path(fonte).exists():
        print(f"(lendo HTML local: {fonte})")
        html = Path(fonte).read_text(encoding="utf-8", errors="replace")
    else:
        html = _baixa(BRAZIL_URL)
    parser = _Tabelas()
    parser.feed(html)
    tab = _tabela_ranking(parser.tabelas)
    if not tab or len(tab) < 2:
        raise RuntimeError("Tabela de ranking não encontrada. HTML salvo em "
                           f"{_dump(html)} — confira o cabeçalho/estrutura.")

    cab = [_norm(c) for c in tab[0]]

    def col(*chaves):
        for i, c in enumerate(cab):
            if any(k in c for k in chaves):
                return i
        return None

    i_uni = col("university", "institution", "organization")
    i_world = col("world rank", "ranking", "rank")
    i_imp, i_open, i_exc = col("impact"), col("openness"), col("excellence")
    if None in (i_uni, i_imp, i_open, i_exc):
        raise RuntimeError(f"Colunas não mapeadas (cabeçalho={cab}). "
                           f"HTML salvo em {_dump(html)}.")

    linhas = []
    for nrank, row in enumerate(tab[1:], start=1):   # ordem da página = rank nacional
        if len(row) <= max(i_uni, i_imp, i_open, i_exc):
            continue
        nome = row[i_uni]
        nnome = _norm(nome)
        sigla = next((s for s, chave in ALVOS.items() if chave in nnome), None)
        if not sigla:
            continue
        linhas.append({
            "sigla": sigla,
            "instituicao": nome,
            "rank_brasil": nrank,
            "rank_mundial": _num(row[i_world]) if i_world is not None else None,
            "impact_rank": _num(row[i_imp]),
            "openness_rank": _num(row[i_open]),
            "excellence_rank": _num(row[i_exc]),
        })

    if not linhas:
        raise RuntimeError("Nenhuma instituição-alvo encontrada na tabela; o nome "
                           f"pode estar diferente. Ajuste ALVOS. HTML: {_dump(html)}.")

    df = pd.DataFrame(linhas).drop_duplicates("sigla").sort_values("rank_brasil")
    df = df.reset_index(drop=True)
    df.to_csv(OUT / "webometrics_uftm.csv", index=False)
    print("Webometrics (Brasil) — gravado em data/webometrics_uftm.csv:")
    for r in df.itertuples():
        print(f"  {r.sigla:<8} BR#{r.rank_brasil}  mundo#{r.rank_mundial}  | "
              f"Impact {r.impact_rank} · Openness {r.openness_rank} · "
              f"Excellence {r.excellence_rank}")
    faltam = set(ALVOS) - set(df["sigla"])
    if faltam:
        print("  (não encontradas, verifique o nome na página:", ", ".join(faltam), ")")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
