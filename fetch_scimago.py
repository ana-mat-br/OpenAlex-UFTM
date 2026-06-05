"""Baixa o Scimago Journal Rank (gratuito) e gera data/scimago_quartis.csv.

Mapeia cada ISSN -> quartil (Q1-Q4) e SJR, para cruzar com os periódicos da UFTM
(coluna issn_l do OpenAlex) e habilitar a aba Qualidade de Periódicos.
"""
from __future__ import annotations

import io
import urllib.request
from pathlib import Path

import pandas as pd

OUT = Path(__file__).parent / "data"
OUT.mkdir(exist_ok=True)
URL = "https://www.scimagojr.com/journalrank.php?out=xls"
HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"),
    "Referer": "https://www.scimagojr.com/journalrank.php",
    "Accept": "text/csv,application/vnd.ms-excel,*/*",
}


def norm_issn(s: str) -> str:
    return str(s).strip().replace("-", "").upper()


def main() -> None:
    req = urllib.request.Request(URL, headers=HEADERS)
    data = urllib.request.urlopen(req, timeout=120).read()
    df = pd.read_csv(io.BytesIO(data), sep=";", decimal=",", low_memory=False)
    df = df[["Title", "Issn", "SJR", "SJR Best Quartile"]].rename(
        columns={"Title": "title", "SJR": "sjr", "SJR Best Quartile": "quartile"})

    rows = []
    for _, r in df.iterrows():
        if pd.isna(r["Issn"]):
            continue
        for issn in str(r["Issn"]).split(","):
            issn = norm_issn(issn)
            if len(issn) >= 8:
                rows.append({"issn": issn, "sjr": r["sjr"],
                             "quartile": r["quartile"], "title": r["title"]})
    out = pd.DataFrame(rows).drop_duplicates("issn")
    out.to_csv(OUT / "scimago_quartis.csv", index=False)
    print(f"Scimago: {len(df)} periódicos -> {len(out)} ISSNs")
    print("quartis:", out["quartile"].value_counts(dropna=False).to_dict())


if __name__ == "__main__":
    main()
