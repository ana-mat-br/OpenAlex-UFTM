"""Coletor de teses e dissertações da UFTM na BDTD (IBICT).

Por que a BDTD: as teses/dissertações da UFTM quase não aparecem no OpenAlex
(captado neste painel para artigos) porque ficam em repositório institucional
SEM DOI — e o OpenAlex indexa sobretudo o que tem DOI. A Biblioteca Digital
Brasileira de Teses e Dissertações é a fonte completa: ~1.950 itens da UFTM,
com API aberta e gratuita (VuFind REST), sem chave nem custo.

Endpoint:  https://bdtd.ibict.br/vufind/api/v1/search
Filtro:    institution:"UFTM"  (rótulo da UFTM na BDTD)

Gera data/bdtd_uftm.csv consumido por app.py (aba "Dissertações e Teses").
Rodar:  python fetch_bdtd.py
"""
from __future__ import annotations

import html
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

OUT = Path(__file__).parent / "data"
OUT.mkdir(exist_ok=True)

API = "https://bdtd.ibict.br/vufind/api/v1/search"
OPENALEX = "https://api.openalex.org/works"
UFTM_ROR = "https://ror.org/01av3m334"
MAILTO = "anapaula.fernandes@uftm.edu.br"
INSTITUICAO = "UFTM"           # rótulo da UFTM na faceta institution da BDTD
PER_PAGE = 100                 # limite máximo por página na API VuFind
HEADERS = {"User-Agent": "PainelDAAD-UFTM/1.0 (anapaula.fernandes@uftm.edu.br)"}

# Campos pedidos à API (reduz o payload e deixa explícito o que captamos)
CAMPOS = ["id", "title", "authors", "summary", "publicationDates",
          "languages", "formats", "subjects", "urls", "cleanDoi"]

TIPO_PT = {"masterThesis": "Dissertação (mestrado)",
           "doctoralThesis": "Tese (doutorado)"}

IDIOMA_PT = {"por": "Português", "eng": "Inglês", "spa": "Espanhol",
             "fre": "Francês", "ger": "Alemão", "ita": "Italiano"}

# Grandes áreas CNPq (vêm em CAIXA ALTA e sem acento na BDTD) -> rótulo legível
AREA_CNPQ_PT = {
    "CIENCIAS EXATAS E DA TERRA": "Ciências Exatas e da Terra",
    "CIENCIAS BIOLOGICAS": "Ciências Biológicas",
    "ENGENHARIAS": "Engenharias",
    "CIENCIAS DA SAUDE": "Ciências da Saúde",
    "CIENCIAS AGRARIAS": "Ciências Agrárias",
    "CIENCIAS SOCIAIS APLICADAS": "Ciências Sociais Aplicadas",
    "CIENCIAS HUMANAS": "Ciências Humanas",
    "LINGUISTICA LETRAS E ARTES": "Linguística, Letras e Artes",
    "LINGUISTICA, LETRAS E ARTES": "Linguística, Letras e Artes",
    "OUTROS": "Outros",
    "MULTIDISCIPLINAR": "Multidisciplinar",
}


def _busca(page: int) -> dict:
    """Uma página da API VuFind da BDTD, com 3 tentativas."""
    params = [("lookfor", ""), ("type", "AllFields"),
              ("limit", str(PER_PAGE)), ("page", str(page)),
              ("filter[]", f'institution:"{INSTITUICAO}"'), ("sort", "title")]
    params += [("field[]", c) for c in CAMPOS]
    url = f"{API}?{urllib.parse.urlencode(params)}"
    for tent in range(3):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:
            if tent == 2:
                raise
            time.sleep(2 * (tent + 1))
    return {}


def _primeiro_autor(rec: dict) -> tuple[str | None, str | None]:
    """Nome do autor e link do Lattes (quando houver) do autor primário."""
    prim = (rec.get("authors") or {}).get("primary") or {}
    if not prim:
        return None, None
    nome = next(iter(prim))
    info = prim[nome]
    # info pode ser dict ({"profile": [...]}) ou list, dependendo do registro
    if isinstance(info, dict):
        perfis = info.get("profile") or []
    elif isinstance(info, list):
        perfis = info
    else:
        perfis = []
    lattes = next((p for p in perfis if "lattes" in str(p).lower()), None)
    return nome, lattes


def _area_e_palavras(rec: dict) -> tuple[str | None, str]:
    """Grande área CNPq (a 1ª encontrada) + palavras-chave livres (sem CNPq)."""
    area, kws = None, []
    for s in (rec.get("subjects") or []):
        termo = s[0] if isinstance(s, list) and s else s
        if not isinstance(termo, str):
            continue
        if termo.upper().startswith("CNPQ::"):
            if area is None:
                partes = termo.split("::")
                if len(partes) >= 2:
                    bruto = partes[1].strip().upper()
                    area = AREA_CNPQ_PT.get(bruto, partes[1].strip().title())
        else:
            kws.append(termo.strip().rstrip("."))
    # remove duplicatas preservando ordem
    kws = list(dict.fromkeys(k for k in kws if k))
    return area, "; ".join(kws[:8])


def openalex_dissertacoes() -> None:
    """Teses/dissertações de autores ligados à UFTM já indexadas no OpenAlex.
    Em geral têm DOI cunhado pelo repositório de OUTRA instituição (a UFTM não
    emite DOI) — daí aparecerem aqui e quase nenhuma das ~1.950 da BDTD aparecer.
    Grava data/openalex_teses_uftm.csv."""
    flt = f"authorships.institutions.ror:{UFTM_ROR},type:dissertation"
    sel = "id,doi,title,publication_year,authorships,primary_location"
    qs = urllib.parse.urlencode({"filter": flt, "per-page": 200,
                                 "select": sel, "mailto": MAILTO})
    req = urllib.request.Request(f"{OPENALEX}?{qs}", headers=HEADERS)
    with urllib.request.urlopen(req, timeout=90) as r:
        d = json.loads(r.read().decode("utf-8"))

    linhas = []
    for w in d.get("results", []):
        auts = [a.get("author", {}).get("display_name")
                for a in (w.get("authorships") or [])]
        auts = [a for a in auts if a]
        fonte = ((w.get("primary_location") or {}).get("source") or {}).get("display_name")
        titulo = html.unescape(w.get("title") or "").replace("\r", " ").replace("\n", " ")
        linhas.append({
            "ano": pd.to_numeric(w.get("publication_year"), errors="coerce"),
            "titulo": " ".join(titulo.split()).strip(),
            "autor": "; ".join(auts[:3]),
            "doi": w.get("doi"),
            "fonte": fonte,
            "url": w.get("id"),
        })
    df = pd.DataFrame(linhas)
    df["ano"] = pd.to_numeric(df["ano"], errors="coerce").astype("Int64")
    df = df.sort_values("ano", ascending=False).reset_index(drop=True)
    df.to_csv(OUT / "openalex_teses_uftm.csv", index=False)
    print(f"OpenAlex teses/dissertações UFTM: {len(df)} (com DOI: {df['doi'].notna().sum()})")


CROSSREF = "https://api.crossref.org/prefixes"
# Prefixos Crossref que cada instituição usa para registrar DOI de teses/disserta-
# ções (o DOI resolve para o repositório dela, ex.: teses.usp.br). A UFTM não tem.
PREFIXOS_TESE = {"USP": "10.11606", "UNICAMP": "10.47749",
                 "UFU": "10.14393", "UnB": "10.26512"}


def crossref_teses_doi() -> None:
    """Nº de teses/dissertações COM DOI registradas na Crossref, por instituição
    (filtro type:dissertation sob o prefixo de cada uma — onde os DOIs de fato
    moram). A UFTM entra com 0: não possui prefixo nem DOIs. É a métrica honesta
    do hábito de atribuir DOI (o OpenAlex subconta muito). Grava
    data/crossref_teses_doi.csv."""
    linhas = [{"sigla": "UFTM", "prefixo": "—", "n": 0}]
    for sigla, p in PREFIXOS_TESE.items():
        qs = urllib.parse.urlencode({"filter": "type:dissertation",
                                     "rows": 0, "mailto": MAILTO})
        req = urllib.request.Request(f"{CROSSREF}/{p}/works?{qs}", headers=HEADERS)
        with urllib.request.urlopen(req, timeout=60) as r:
            n = json.loads(r.read().decode("utf-8"))["message"]["total-results"]
        linhas.append({"sigla": sigla, "prefixo": p, "n": int(n)})
        time.sleep(0.3)
    df = pd.DataFrame(linhas).sort_values("n", ascending=False).reset_index(drop=True)
    df.to_csv(OUT / "crossref_teses_doi.csv", index=False)
    print("Crossref teses com DOI: "
          + ", ".join(f"{r.sigla} {r.n}" for r in df.itertuples()))


def main() -> None:
    primeira = _busca(1)
    total = int(primeira.get("resultCount") or 0)
    if not total:
        raise RuntimeError("BDTD retornou 0 itens para a UFTM — verifique o rótulo institution.")
    n_paginas = (total + PER_PAGE - 1) // PER_PAGE

    linhas, com_doi = [], 0
    for page in range(1, n_paginas + 1):
        d = primeira if page == 1 else _busca(page)
        for rec in d.get("records", []):
            nome, lattes = _primeiro_autor(rec)
            area, palavras = _area_e_palavras(rec)
            datas = rec.get("publicationDates") or []
            idiomas = rec.get("languages") or []
            formatos = rec.get("formats") or []
            url = (rec.get("urls") or [{}])[0].get("url")
            resumo = (rec.get("summary") or [""])
            resumo = resumo[0] if resumo else ""
            doi = rec.get("cleanDoi")
            if doi:
                com_doi += 1
            linhas.append({
                "id": rec.get("id"),
                "tipo": TIPO_PT.get(formatos[0] if formatos else "", "Outro"),
                "titulo": (rec.get("title") or "").strip(),
                "autor": nome,
                "lattes": lattes,
                "ano": pd.to_numeric(datas[0], errors="coerce") if datas else None,
                "idioma": IDIOMA_PT.get(idiomas[0] if idiomas else "", "—"),
                "area_cnpq": area,
                "palavras_chave": palavras,
                "resumo": (resumo or "").strip(),
                "doi": doi,
                "url": url,
            })
        time.sleep(0.4)

    df = pd.DataFrame(linhas)
    df["ano"] = pd.to_numeric(df["ano"], errors="coerce").astype("Int64")
    df = df.sort_values(["ano", "tipo"], ascending=[False, True]).reset_index(drop=True)
    df.to_csv(OUT / "bdtd_uftm.csv", index=False)

    n_mest = (df["tipo"] == TIPO_PT["masterThesis"]).sum()
    n_dout = (df["tipo"] == TIPO_PT["doctoralThesis"]).sum()
    print(f"BDTD UFTM: {len(df)} itens ({n_mest} dissertações, {n_dout} teses); "
          f"com DOI: {com_doi}; gravado em data/bdtd_uftm.csv")

    openalex_dissertacoes()
    crossref_teses_doi()


if __name__ == "__main__":
    main()
