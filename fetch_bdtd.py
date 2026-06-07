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

import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

OUT = Path(__file__).parent / "data"
OUT.mkdir(exist_ok=True)

API = "https://bdtd.ibict.br/vufind/api/v1/search"
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


if __name__ == "__main__":
    main()
