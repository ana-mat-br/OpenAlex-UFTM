"""Coletor do Observatório PROPPG/UFTM — métricas de benchmarking, colaboração,
pesquisadores e temas via OpenAlex (usa agregações leves, sem baixar todos os works).

Gera CSVs em data/ consumidos por app.py. Rodar:  python fetch_observatorio.py
"""
from __future__ import annotations

import os
import time
import unicodedata
from collections import Counter
from pathlib import Path

import pandas as pd
from pyalex import Authors, Institutions, Works, config

config.email = os.environ.get("OPENALEX_EMAIL", "anapaula.fernandes@uftm.edu.br")
OUT = Path(__file__).parent / "data"


def _chave_autor(nome: str) -> str:
    """Chave para juntar a mesma pessoa dividida em vários ids do OpenAlex.
    Normaliza acentos/maiúsculas/hífens e trata abreviação do 1º nome:
    'Eliane Lages-Silva' == 'E. Lages‐Silva'. Para evitar juntar gente diferente,
    só usa a inicial quando o sobrenome é COMPOSTO (>= 2 tokens, mais distintivo);
    com sobrenome de 1 token exige o primeiro nome inteiro."""
    n = unicodedata.normalize("NFKD", nome or "")
    n = "".join(c for c in n if not unicodedata.combining(c)).lower()
    for d in ("-", "‐", "–", "—", "."):
        n = n.replace(d, " ")
    toks = n.split()
    if not toks:
        return (nome or "").lower()
    first, sur = toks[0], toks[1:]
    if len(sur) >= 2:
        return f"i|{first[0]}|{' '.join(sur)}"
    if len(sur) == 1:
        return f"f|{first}|{sur[0]}"
    return f"s|{first}"
OUT.mkdir(exist_ok=True)

UFTM = "01av3m334"
# As 11 universidades federais de Minas Gerais (comparação regional)
INSTS = {
    "UFTM": "01av3m334", "UFMG": "0176yjw32", "UFU": "04x3wvr31",
    "UFV": "0409dgb37", "UFJF": "04yqw9c44", "UFSJ": "03vrj4p82",
    "UFOP": "056s65p46", "UFLA": "0122bmm03", "UFVJM": "02gen2282",
    "UNIFAL": "034vpja60", "UNIFEI": "00235nr42",
}

# Federais de PORTE semelhante à UFTM (≈ 8,4k–14,8k produções), Brasil inteiro
INSTS_PORTE = {
    "UFTM": "01av3m334", "UFERSA": "05x2svh05", "UNIR": "02842cb31",
    "UFGD": "0310smc09", "UNIPAMPA": "003qt4p19", "UFCSPA": "00x0nkm13",
    "UNIVASF": "00devjr72", "UFRB": "057mvv518", "UFFS": "03z9wm572",
    "UFRA": "02j71c790",
}


def _share_true(ror: str, campo: str) -> float:
    """Proporção de works de uma instituição com flag booleana True (via group_by barato)."""
    g = {str(x["key_display_name"]).lower(): x["count"]
         for x in Works().filter(institutions={"ror": ror}).group_by(campo).get()}
    return g.get("true", 0) / max(sum(g.values()), 1)


def _intl_share(ror: str) -> float:
    """Proporção de works com colaboração internacional (>= 2 países distintos)."""
    g = Works().filter(institutions={"ror": ror}).group_by("countries_distinct_count").get()
    total = sum(x["count"] for x in g)
    intl = sum(x["count"] for x in g if str(x["key"]).isdigit() and int(x["key"]) >= 2)
    return intl / max(total, 1)


def _inst_share(ror: str) -> float:
    """Proporção de works só institucionais (1 instituição distinta)."""
    g = Works().filter(institutions={"ror": ror}).group_by("institutions_distinct_count").get()
    total = sum(x["count"] for x in g)
    single = sum(x["count"] for x in g if str(x["key"]) == "1")
    return single / max(total, 1)


def benchmarking_grupo(insts: dict, prefixo: str) -> None:
    linhas, series = [], []
    for sigla, ror in insts.items():
        inst = Institutions()[f"https://ror.org/{ror}"]
        ss = inst.get("summary_stats", {})
        oa_share = _share_true(ror, "open_access.is_oa")
        top10 = _share_true(ror, "citation_normalized_percentile.is_in_top_10_percent")
        top1 = _share_true(ror, "citation_normalized_percentile.is_in_top_1_percent")
        intl = _intl_share(ror)  # colaboração internacional (>= 2 países)
        instc = _inst_share(ror)  # só institucional (1 instituição)
        nac = max(0.0, 1 - instc - intl)  # nacional = ≥2 instituições, só Brasil
        linhas.append({
            "sigla": sigla, "instituicao": inst["display_name"], "ror": ror,
            "works": inst["works_count"], "citacoes": inst["cited_by_count"],
            "h_index": ss.get("h_index"), "i10": ss.get("i10_index"),
            "mean_citedness": round(ss.get("2yr_mean_citedness", 0), 3),
            "oa_share": round(oa_share, 4),
            "top10_share": round(top10, 4),
            "top1_share": round(top1, 4),
            "intl_share": round(intl, 4),
            "nac_share": round(nac, 4),
            "inst_share": round(instc, 4),
            "cit_por_trabalho": round(inst["cited_by_count"] / max(inst["works_count"], 1), 2),
        })
        for c in inst.get("counts_by_year", []):
            series.append({"sigla": sigla, "year": c["year"],
                           "works": c["works_count"], "citacoes": c["cited_by_count"]})
        time.sleep(0.3)
    pd.DataFrame(linhas).to_csv(OUT / f"{prefixo}_instituicoes.csv", index=False)
    pd.DataFrame(series).to_csv(OUT / f"{prefixo}_por_ano.csv", index=False)
    print(f"{prefixo}: {len(linhas)} instituições")


def benchmarking() -> None:
    benchmarking_grupo(INSTS, "bench")              # federais de MG
    benchmarking_grupo(INSTS_PORTE, "bench_porte")  # federais de porte semelhante (Brasil)


def colaboracao() -> None:
    w = Works().filter(authorships={"institutions": {"ror": UFTM}})
    inst = [{"instituicao": g["key_display_name"], "oa_id": str(g["key"]).split("/")[-1], "n": g["count"]}
            for g in w.group_by("authorships.institutions.id").get(per_page=200)]
    df = pd.DataFrame(inst)
    df = df[df["oa_id"] != "I4210106570"].sort_values("n", ascending=False).head(25)  # exclui a própria UFTM
    df.to_csv(OUT / "colab_instituicoes.csv", index=False)

    pais = [{"pais": g["key_display_name"], "cod": g["key"], "n": g["count"]}
            for g in w.group_by("authorships.countries").get(per_page=200)]
    pd.DataFrame(pais).sort_values("n", ascending=False).to_csv(OUT / "colab_paises.csv", index=False)
    print(f"colaboração: {len(df)} instituições, {len(pais)} países")


def temas() -> None:
    w = Works().filter(authorships={"institutions": {"ror": UFTM}})
    campo = [{"campo": g["key_display_name"], "n": g["count"]}
             for g in w.group_by("primary_topic.field.id").get(per_page=200)]
    pd.DataFrame(campo).sort_values("n", ascending=False).to_csv(OUT / "temas_campo.csv", index=False)

    topic = [{"topico": g["key_display_name"], "n": g["count"]}
             for g in w.group_by("primary_topic.id").get(per_page=200)]
    pd.DataFrame(topic).sort_values("n", ascending=False).head(30).to_csv(OUT / "temas_topicos.csv", index=False)
    print(f"temas: {len(campo)} campos")


def pesquisadores() -> None:
    """Pesquisadores ANCORADOS na UFTM: conta, a partir dos works da UFTM, quem os assina
    estando afiliado à UFTM, e as citações *desses* works (não a carreira inteira)."""
    n_works, citac, nomes, orcids = Counter(), Counter(), {}, {}
    q = (Works().filter(authorships={"institutions": {"ror": UFTM}})
         .select(["id", "cited_by_count", "authorships"]))
    for page in q.paginate(per_page=200, n_max=None):
        for w in page:
            c = w.get("cited_by_count", 0) or 0
            vistos = set()
            for a in (w.get("authorships") or []):
                rors = {(i.get("ror") or "").rsplit("/", 1)[-1]
                        for i in (a.get("institutions") or [])}
                if UFTM not in rors:
                    continue
                au = a.get("author") or {}
                aid = (au.get("id") or "").rsplit("/", 1)[-1]
                if aid and aid not in vistos:
                    vistos.add(aid)
                    n_works[aid] += 1
                    citac[aid] += c
                    nomes[aid] = au.get("display_name") or aid
                    if au.get("orcid"):
                        orcids[aid] = au["orcid"]
    df = pd.DataFrame([{"id": a, "autor": nomes[a], "works_uftm": n_works[a],
                        "citacoes_uftm": citac[a], "orcid": orcids.get(a)} for a in n_works])
    # mescla a mesma pessoa dividida em vários ids do OpenAlex — soma works/citações
    df["_key"] = df["autor"].map(_chave_autor)
    df = df.sort_values("works_uftm", ascending=False)
    # nome de exibição: a variante mais completa (mais longa) de cada pessoa
    nome_disp = (df.assign(_l=df["autor"].str.len()).sort_values("_l", ascending=False)
                 .groupby("_key")["autor"].first())
    df = (df.groupby("_key", as_index=False)
          .agg(works_uftm=("works_uftm", "sum"), citacoes_uftm=("citacoes_uftm", "sum"),
               orcid=("orcid", "first"), id=("id", "first")))
    df["autor"] = df["_key"].map(nome_disp)
    df = (df.drop(columns="_key").sort_values("citacoes_uftm", ascending=False)
          .head(50).reset_index(drop=True))

    # h-index / i10 de carreira para o top 50 (rótulo deixa claro que é carreira)
    hidx, i10 = {}, {}
    for aid in df["id"]:
        try:
            ss = (Authors()[f"https://openalex.org/{aid}"].get("summary_stats") or {})
            hidx[aid], i10[aid] = ss.get("h_index"), ss.get("i10_index")
        except Exception:
            hidx[aid], i10[aid] = None, None
        time.sleep(0.2)
    df["h_index"], df["i10"] = df["id"].map(hidx), df["id"].map(i10)
    df.drop(columns=["id"]).to_csv(OUT / "top_autores.csv", index=False)
    print(f"pesquisadores ancorados na UFTM: {len(df)}")


def ods_perfil() -> None:
    """Perfil de ODS (share por objetivo) da UFTM e dos pares, para comparação."""
    insts = dict(INSTS)
    insts.update(INSTS_PORTE)  # união (UFTM aparece uma vez)
    rows = []
    for sigla, ror in insts.items():
        g = (Works().filter(institutions={"ror": ror})
             .group_by("sustainable_development_goals.id").get())
        total = sum(x["count"] for x in g)
        for x in g:
            rows.append({"sigla": sigla, "sdg_id": str(x["key"]).rsplit("/", 1)[-1],
                         "n": x["count"], "share": round(x["count"] / max(total, 1), 5)})
        time.sleep(0.3)
    pd.DataFrame(rows).to_csv(OUT / "ods_por_instituicao.csv", index=False)
    print(f"ods_perfil: {len(insts)} instituições")


def main() -> None:
    benchmarking()
    colaboracao()
    temas()
    pesquisadores()
    ods_perfil()
    print("OK — arquivos gravados em data/")


if __name__ == "__main__":
    main()
