"""Coleta citações por PATENTE das produções da UFTM via The Lens Scholarly API.

Key-gated: requer um token acadêmico GRATUITO do The Lens na variável de ambiente
LENS_TOKEN. Sem token, encerra sem erro (a aba Impacto Social mostra instruções).
Gera data/lens_patentes.csv: doi, title, year, n_patentes.

Token gratuito (uso acadêmico/não comercial): https://www.lens.org/lens/user/subscriptions
"""
from __future__ import annotations

import json
import os
import time
import urllib.request
from pathlib import Path

import pandas as pd

OUT = Path(__file__).parent / "data"
TOKEN = os.environ.get("LENS_TOKEN", "").strip()
URL = "https://api.lens.org/scholarly/search"
LOTE = 400  # DOIs por requisição (terms query aceita até 10.000)


def bare_doi(d: str) -> str:
    return str(d).replace("https://doi.org/", "").strip().lower()


def consulta(dois: list[str]) -> dict:
    body = {
        "query": {"bool": {"must": [
            {"terms": {"external_ids.value": dois}},
            {"match": {"has_patent_citations": True}},
        ]}},
        "include": ["lens_id", "title", "year_published", "external_ids",
                    "referenced_by_patent_count"],
        "size": len(dois),
    }
    req = urllib.request.Request(
        URL, data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.load(r)


def main() -> None:
    if not TOKEN:
        print("LENS_TOKEN ausente — pulando coleta de patentes "
              "(a aba Impacto Social mostrará instruções para ativar).")
        return
    raw = pd.read_parquet(OUT / "uftm_works_raw.parquet")
    dois = [bare_doi(d) for d in raw["doi"].dropna().unique()]
    print(f"DOIs a consultar no The Lens: {len(dois)}")

    rows, achou_total = [], 0
    for i in range(0, len(dois), LOTE):
        lote = dois[i:i + LOTE]
        try:
            res = consulta(lote)
        except Exception as e:
            print(f"  lote {i // LOTE + 1}: ERRO {str(e)[:100]}")
            time.sleep(3)
            continue
        achou_total += res.get("total", 0)
        for d in res.get("data", []):
            doi = next((x.get("value") for x in (d.get("external_ids") or [])
                        if x.get("type") == "doi"), None)
            rows.append({"doi": doi, "title": d.get("title"),
                         "year": d.get("year_published"),
                         "n_patentes": d.get("referenced_by_patent_count", 0)})
        print(f"  lote {i // LOTE + 1}/{(len(dois) + LOTE - 1) // LOTE}: "
              f"total={res.get('total')} acumulado={len(rows)}")
        time.sleep(1.2)

    df = pd.DataFrame(rows).dropna(subset=["doi"]).drop_duplicates("doi")
    df.to_csv(OUT / "lens_patentes.csv", index=False)
    if achou_total == 0:
        print("AVISO: nenhum resultado — verifique o token ou o campo de consulta "
              "(external_ids.value).")
    print(f"produções citadas por patentes: {len(df)} | "
          f"citações em patentes (soma): {int(df['n_patentes'].sum()) if len(df) else 0}")


if __name__ == "__main__":
    main()
