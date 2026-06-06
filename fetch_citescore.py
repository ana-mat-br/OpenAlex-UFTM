"""Coleta um indicador ANÁLOGO ao CiteScore para as revistas onde a UFTM publica.

O CiteScore oficial (Elsevier/Scopus) exige login e tem licença restrita — não dá para
automatizar nem redistribuir. Aqui usamos o `2yr_mean_citedness` do OpenAlex (citações
médias em 2 anos por trabalho da revista), aberto e parecido em conceito com o CiteScore
(que usa janela de ~4 anos) — então é uma APROXIMAÇÃO, não o número oficial.

Gera data/citescore_analogo.csv: issn_l, citescore_analogo.
"""
from __future__ import annotations

import os
import time
from pathlib import Path

import pandas as pd
from pyalex import Sources, config

config.email = os.environ.get("OPENALEX_EMAIL", "anapaula.fernandes@uftm.edu.br")
OUT = Path(__file__).parent / "data"
LOTE = 40


def main() -> None:
    raw = pd.read_parquet(OUT / "uftm_works_raw.parquet")
    issns = sorted({str(i) for i in raw["issn_l"].dropna().unique()})
    print(f"revistas (ISSN) a consultar: {len(issns)}")
    rows = []
    for i in range(0, len(issns), LOTE):
        lote = issns[i:i + LOTE]
        try:
            res = Sources().filter(issn="|".join(lote)).get(per_page=LOTE + 20)
        except Exception as e:
            print(f"  lote {i // LOTE + 1}: erro {str(e)[:60]}")
            time.sleep(2)
            continue
        for s in res:
            ss = s.get("summary_stats") or {}
            rows.append({"issn_l": s.get("issn_l"),
                         "citescore_analogo": round(ss.get("2yr_mean_citedness", 0) or 0, 2)})
        time.sleep(0.4)
    df = pd.DataFrame(rows).dropna(subset=["issn_l"]).drop_duplicates("issn_l")
    df.to_csv(OUT / "citescore_analogo.csv", index=False)
    print(f"CiteScore-análogo coletado para {len(df)} revistas")


if __name__ == "__main__":
    main()
