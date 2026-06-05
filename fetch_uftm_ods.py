"""Coleta works da UFTM no OpenAlex e gera CSVs/Parquet agregados por ODS."""
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


def fetch_works() -> pd.DataFrame:
    rows = []
    query = (
        Works()
        .filter(authorships={"institutions": {"ror": ROR_UFTM}})
        .select([
            "id", "doi", "title", "publication_year", "type", "language",
            "cited_by_count", "sustainable_development_goals",
            "primary_location", "open_access",
        ])
    )
    total = query.count()
    print(f"UFTM works no OpenAlex: {total}")

    for i, w in enumerate(query.paginate(per_page=200, n_max=None)):
        for work in w:
            sdgs = work.get("sustainable_development_goals") or []
            primary = (work.get("primary_location") or {}).get("source") or {}
            rows.append({
                "id": work["id"],
                "doi": work.get("doi"),
                "title": work.get("title"),
                "year": work.get("publication_year"),
                "type": work.get("type"),
                "language": work.get("language"),
                "cited_by": work.get("cited_by_count"),
                "is_oa": (work.get("open_access") or {}).get("is_oa"),
                "source": primary.get("display_name"),
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
                "work_id": r["id"],
                "year": r["year"],
                "type": r["type"],
                "language": r["language"],
                "cited_by": r["cited_by"],
                "is_oa": r["is_oa"],
                "source": r["source"],
                "sdg_id": s["id"].rsplit("/", 1)[-1],
                "sdg_name": s["display_name"],
                "sdg_score": score,
            })
    return pd.DataFrame(out)


def main():
    works = fetch_works()
    works.to_parquet(OUT / "uftm_works_raw.parquet", index=False)

    long = explode_sdgs(works)
    long.to_parquet(OUT / "uftm_works_by_sdg.parquet", index=False)
    long.to_csv(OUT / "uftm_works_by_sdg.csv", index=False)

    # Agregações
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
        long.groupby(["sdg_id", "source"])
        .size().reset_index(name="n")
        .sort_values(["sdg_id", "n"], ascending=[True, False])
    )
    top_sources.to_csv(OUT / "agg_top_sources_by_sdg.csv", index=False)

    print("\nResumo por ODS:")
    print(by_sdg.to_string(index=False))


if __name__ == "__main__":
    main()
