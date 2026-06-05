"""Coletor do Observatório PROPPG/UFTM — métricas de benchmarking, colaboração,
pesquisadores e temas via OpenAlex (usa agregações leves, sem baixar todos os works).

Gera CSVs em data/ consumidos por app.py. Rodar:  python fetch_observatorio.py
"""
from __future__ import annotations

import os
import time
from pathlib import Path

import pandas as pd
from pyalex import Authors, Institutions, Works, config

config.email = os.environ.get("OPENALEX_EMAIL", "anapaula.fernandes@uftm.edu.br")
OUT = Path(__file__).parent / "data"
OUT.mkdir(exist_ok=True)

UFTM = "01av3m334"
# As 11 universidades federais de Minas Gerais (referência do benchmarking)
INSTS = {
    "UFTM": "01av3m334", "UFMG": "0176yjw32", "UFU": "04x3wvr31",
    "UFV": "0409dgb37", "UFJF": "04yqw9c44", "UFSJ": "03vrj4p82",
    "UFOP": "056s65p46", "UFLA": "0122bmm03", "UFVJM": "02gen2282",
    "UNIFAL": "034vpja60", "UNIFEI": "00235nr42",
}


def benchmarking() -> None:
    linhas, series = [], []
    for sigla, ror in INSTS.items():
        inst = Institutions()[f"https://ror.org/{ror}"]
        ss = inst.get("summary_stats", {})
        # OA share via group_by (1 chamada)
        oa = {str(g["key_display_name"]).lower(): g["count"]
              for g in Works().filter(institutions={"ror": ror}).group_by("open_access.is_oa").get()}
        oa_share = oa.get("true", 0) / max(sum(oa.values()), 1)
        linhas.append({
            "sigla": sigla, "instituicao": inst["display_name"], "ror": ror,
            "works": inst["works_count"], "citacoes": inst["cited_by_count"],
            "h_index": ss.get("h_index"), "i10": ss.get("i10_index"),
            "mean_citedness": round(ss.get("2yr_mean_citedness", 0), 3),
            "oa_share": round(oa_share, 4),
            "cit_por_trabalho": round(inst["cited_by_count"] / max(inst["works_count"], 1), 2),
        })
        for c in inst.get("counts_by_year", []):
            series.append({"sigla": sigla, "year": c["year"],
                           "works": c["works_count"], "citacoes": c["cited_by_count"]})
        time.sleep(0.3)
    pd.DataFrame(linhas).to_csv(OUT / "bench_instituicoes.csv", index=False)
    pd.DataFrame(series).to_csv(OUT / "bench_por_ano.csv", index=False)
    print(f"benchmarking: {len(linhas)} instituições")


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
    autores = []
    q = (Authors()
         .filter(affiliations={"institution": {"ror": UFTM}})
         .sort(cited_by_count="desc"))
    for a in q.get(per_page=50):
        ss = a.get("summary_stats", {})
        autores.append({
            "autor": a["display_name"], "works": a["works_count"],
            "citacoes": a["cited_by_count"], "h_index": ss.get("h_index"),
            "i10": ss.get("i10_index"), "orcid": a.get("orcid"),
        })
    pd.DataFrame(autores).to_csv(OUT / "top_autores.csv", index=False)
    print(f"pesquisadores: {len(autores)} autores")


def main() -> None:
    benchmarking()
    colaboracao()
    temas()
    pesquisadores()
    print("OK — arquivos gravados em data/")


if __name__ == "__main__":
    main()
