"""Coleta works da UFTM no OpenAlex e gera CSVs/Parquet agregados por ODS.

Enriquecido para o Observatório DAAD: além de ODS, traz indicadores normalizados
(FWCI, percentis top 1%/10%), tópico/campo, colaboração (países/instituições),
acesso aberto detalhado (status, repositório, APC) e financiamento (funders).
"""
from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
from pyalex import Works, config

ROR_UFTM = "01av3m334"
OUT = Path(__file__).parent / "data"
OUT.mkdir(exist_ok=True)

config.email = os.environ.get("OPENALEX_EMAIL", "anapaula.fernandes@uftm.edu.br")
SCORE_CUTOFF = 0.4  # mesmo limiar do Aurora mBERT citado no policy brief

SELECT = [
    "id", "doi", "title", "publication_year", "type", "language",
    "cited_by_count", "sustainable_development_goals", "primary_location",
    "open_access", "fwci", "citation_normalized_percentile", "primary_topic",
    "authorships", "apc_paid", "apc_list", "funders",
    "corresponding_institution_ids", "is_retracted", "is_paratext",
]
OPENALEX_ID_UFTM = "I4210106570"


def fetch_works() -> pd.DataFrame:
    rows = []
    query = Works().filter(authorships={"institutions": {"ror": ROR_UFTM}}).select(SELECT)
    total = query.count()
    print(f"UFTM works no OpenAlex: {total}")

    for w in query.paginate(per_page=200, n_max=None):
        for work in w:
            sdgs = work.get("sustainable_development_goals") or []
            primary = (work.get("primary_location") or {}).get("source") or {}
            cnp = work.get("citation_normalized_percentile") or {}
            pt = work.get("primary_topic") or {}
            field = (pt.get("field") or {}).get("display_name")
            auth = work.get("authorships") or []
            countries = sorted({c for a in auth for c in (a.get("countries") or [])})
            inst_rors = {(i.get("ror") or "").rsplit("/", 1)[-1]
                         for a in auth for i in (a.get("institutions") or []) if i.get("ror")}
            oa = work.get("open_access") or {}
            apc = (work.get("apc_paid") or work.get("apc_list") or {}) or {}
            funder_list = work.get("funders") or []
            funders = sorted({f.get("display_name") for f in funder_list
                              if f.get("display_name")})
            rows.append({
                "id": work["id"],
                "doi": work.get("doi"),
                "title": work.get("title"),
                "year": work.get("publication_year"),
                "type": work.get("type"),
                "language": work.get("language"),
                "cited_by": work.get("cited_by_count"),
                "is_oa": oa.get("is_oa"),
                "oa_status": oa.get("oa_status"),
                "in_repository": oa.get("any_repository_has_fulltext"),
                "source": primary.get("display_name"),
                "issn_l": primary.get("issn_l"),
                "in_doaj": primary.get("is_in_doaj"),
                "fwci": work.get("fwci"),
                "pct": cnp.get("value"),
                "top1": cnp.get("is_in_top_1_percent"),
                "top10": cnp.get("is_in_top_10_percent"),
                "topic": pt.get("display_name"),
                "field": field,
                "countries": countries,
                "n_countries": len(countries),
                "is_international": any(c != "BR" for c in countries),
                "n_institutions": len(inst_rors),
                "apc_usd": apc.get("value_usd"),
                "funders": funders,
                "n_grants": len(funder_list),
                "lidera": any(OPENALEX_ID_UFTM in str(c)
                              for c in (work.get("corresponding_institution_ids") or [])),
                "is_retracted": bool(work.get("is_retracted")),
                "is_paratext": bool(work.get("is_paratext")),
                "sdgs": sdgs,
            })
        print(f"  baixados {len(rows)}...")
    return pd.DataFrame(rows)


def explode_sdgs(df: pd.DataFrame) -> pd.DataFrame:
    out = []
    for _, r in df.iterrows():
        for s in r["sdgs"]:
            score = s.get("score", 0) or 0
            if score < SCORE_CUTOFF:
                continue
            out.append({
                "work_id": r["id"], "year": r["year"], "type": r["type"],
                "language": r["language"], "cited_by": r["cited_by"],
                "is_oa": r["is_oa"], "source": r["source"],
                "fwci": r["fwci"], "top10": r["top10"],
                "sdg_id": s["id"].rsplit("/", 1)[-1],
                "sdg_name": s["display_name"], "sdg_score": score,
            })
    return pd.DataFrame(out)


def main():
    works = fetch_works()
    works.to_parquet(OUT / "uftm_works_raw.parquet", index=False)

    long = explode_sdgs(works)
    long.to_parquet(OUT / "uftm_works_by_sdg.parquet", index=False)
    long.to_csv(OUT / "uftm_works_by_sdg.csv", index=False)

    by_sdg = long.groupby(["sdg_id", "sdg_name"]).agg(
        n_works=("work_id", "nunique"),
        citations=("cited_by", "sum"),
        oa_share=("is_oa", "mean"),
    ).reset_index().sort_values("n_works", ascending=False)
    by_sdg.to_csv(OUT / "agg_by_sdg.csv", index=False)

    by_sdg_year = long.groupby(["sdg_id", "year"]).agg(
        n_works=("work_id", "nunique"),
    ).reset_index()
    by_sdg_year.to_csv(OUT / "agg_by_sdg_year.csv", index=False)

    top_sources = (
        long.groupby(["sdg_id", "source"]).size().reset_index(name="n")
        .sort_values(["sdg_id", "n"], ascending=[True, False])
    )
    top_sources.to_csv(OUT / "agg_top_sources_by_sdg.csv", index=False)

    print("\nResumo por ODS:")
    print(by_sdg.to_string(index=False))


if __name__ == "__main__":
    main()
