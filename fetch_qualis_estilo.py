"""Estrato 'estilo Qualis' (ABERTO) para as revistas da UFTM.

A CAPES estratifica revistas por PERCENTIL do CiteScore dentro da área (A1=top 12,5%...).
O CiteScore oficial não é obtenível em escala (login/limite de 1000 no export da Scopus).
Aqui reproduzimos a LÓGICA com dados abertos:
  - área de cada revista: ASJC do 'Source title list' da Scopus (ext_list — só títulos/áreas,
    sem métricas, parte pública);
  - métrica: 2yr_mean_citedness do OpenAlex (análogo do CiteScore);
  - percentil de cada revista DENTRO da área -> estrato A1..B4 (regra de 12,5% da CAPES);
  - cada revista fica com o MELHOR estrato entre suas áreas (como o 'highest percentile').

É APROXIMAÇÃO (métrica aberta, não o CiteScore oficial). Gera, para as revistas da UFTM,
data/qualis_estilo.csv: issn, area, percentil, estrato.

Uso:  EXT_LIST=/caminho/ext_list.xlsx python fetch_qualis_estilo.py
"""
from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pandas as pd
from pyalex import Sources, config

config.email = os.environ.get("OPENALEX_EMAIL", "anapaula.fernandes@uftm.edu.br")
OUT = Path(__file__).parent / "data"
EXT = os.environ.get("EXT_LIST", str(Path.home() / "Downloads" / "ext_list_May_2026.xlsx"))


def _norm(s) -> str:
    return "".join(ch for ch in str(s).upper() if ch.isalnum())


def _estrato(p):
    for lo, lab in [(87.5, "A1"), (75, "A2"), (62.5, "A3"), (50, "A4"),
                    (37.5, "B1"), (25, "B2"), (12.5, "B3"), (0, "B4")]:
        if p >= lo:
            return lab
    return "C"


def main() -> None:
    # 1) análogo (2yr_mean_citedness) de TODAS as revistas do OpenAlex
    print("coletando 2yr_mean_citedness de todas as revistas do OpenAlex...")
    analog = {}
    q = Sources().filter(type="journal").select(["issn_l", "issn", "summary_stats"])
    n = 0
    for page in q.paginate(per_page=200, n_max=None):
        for s in page:
            v = (s.get("summary_stats") or {}).get("2yr_mean_citedness")
            if v is None:
                continue
            for code in ([s.get("issn_l")] + (s.get("issn") or [])):
                if code:
                    analog[_norm(code)] = float(v)
        n += len(page)
        if n % 4000 == 0:
            print(f"  {n} revistas...")
    print(f"análogo coletado: {len(analog)} ISSNs")

    # 2) áreas ASJC do ext_list (Scopus source title list — sem métricas)
    d = pd.read_excel(EXT, sheet_name="Scopus Sources May 2026")
    cols = list(d.columns)
    area_cols = cols[25:52]                      # 27 áreas ASJC (2 dígitos)
    area_nome = {c: str(c).split("\n")[-1].strip() for c in area_cols}
    regs = []
    for _, r in d.iterrows():
        issns = [_norm(r["ISSN"]), _norm(r["EISSN"])]
        issns = [i for i in issns if i and i != "NAN"]
        val = next((analog[i] for i in issns if i in analog), None)
        if val is None:
            continue
        areas = [area_nome[c] for c in area_cols if pd.notna(r[c])]
        regs.append({"issns": issns, "val": val, "areas": areas})
    print(f"revistas com área e análogo: {len(regs)}")

    # 3) percentil por área -> melhor estrato
    dist = {}
    for x in regs:
        for a in x["areas"]:
            dist.setdefault(a, []).append(x["val"])
    arr = {a: np.sort(np.array(v)) for a, v in dist.items()}
    saida = []
    for x in regs:
        melhor = -1.0
        area_m = None
        for a in x["areas"]:
            v = arr[a]
            pct = float(np.searchsorted(v, x["val"], side="left")) / max(len(v), 1) * 100
            if pct > melhor:
                melhor, area_m = pct, a
        for issn in x["issns"]:
            saida.append({"issn": issn, "area": area_m,
                          "percentil": round(melhor, 1), "estrato": _estrato(melhor),
                          "citescore_analogo": round(x["val"], 2)})
    full = pd.DataFrame(saida).drop_duplicates("issn")

    # 4) salva só as revistas da UFTM (mantém o arquivo pequeno)
    raw = pd.read_parquet(OUT / "uftm_works_raw.parquet")
    uftm = {_norm(i) for i in raw["issn_l"].dropna().unique()}
    sub = full[full["issn"].isin(uftm)]
    sub.to_csv(OUT / "qualis_estilo.csv", index=False)
    print(f"qualis_estilo: {len(sub)} revistas da UFTM com estrato "
          f"({sub['estrato'].value_counts().to_dict()})")


if __name__ == "__main__":
    main()
