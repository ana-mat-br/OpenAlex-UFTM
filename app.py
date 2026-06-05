"""Observatório PROPPG/UFTM — painel da produção científica via OpenAlex.

Lê o cache local (data/*.parquet) gerado por fetch_uftm_ods.py.
Rodar local:  streamlit run app.py
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

DATA = Path(__file__).parent / "data"
SCORE_CUTOFF = 0.4  # mesmo limiar Aurora mBERT usado na coleta

# nomes oficiais dos ODS em PT-BR (o OpenAlex devolve em inglês)
ODS_PT = {
    1: "Erradicação da Pobreza", 2: "Fome Zero", 3: "Saúde e Bem-Estar",
    4: "Educação de Qualidade", 5: "Igualdade de Gênero", 6: "Água Limpa e Saneamento",
    7: "Energia Limpa e Acessível", 8: "Trabalho Decente e Cresc. Econômico",
    9: "Indústria, Inovação e Infraestrutura", 10: "Redução das Desigualdades",
    11: "Cidades e Comunidades Sustentáveis", 12: "Consumo e Produção Responsáveis",
    13: "Ação Contra a Mudança do Clima", 14: "Vida na Água", 15: "Vida Terrestre",
    16: "Paz, Justiça e Instituições Eficazes", 17: "Parcerias e Meios de Implementação",
}

st.set_page_config(page_title="Observatório PROPPG/UFTM", page_icon="🎯", layout="wide")


@st.cache_data
def load():
    raw = pd.read_parquet(DATA / "uftm_works_raw.parquet")
    sdg = pd.read_parquet(DATA / "uftm_works_by_sdg.parquet")
    raw["year"] = pd.to_numeric(raw["year"], errors="coerce")
    sdg["year"] = pd.to_numeric(sdg["year"], errors="coerce")
    sdg["sdg_id"] = pd.to_numeric(sdg["sdg_id"], errors="coerce").astype("Int64")
    return raw, sdg


raw, sdg = load()

# ---------------------------------------------------------------- barra lateral
st.sidebar.title("🎯 Observatório PROPPG")
st.sidebar.caption("Produção científica da UFTM · dados do OpenAlex")

anos = raw["year"].dropna()
ymin, ymax = int(anos.min()), int(anos.max())
faixa = st.sidebar.slider("Período", ymin, ymax, (max(ymin, 2010), ymax))

tipos = sorted(raw["type"].dropna().unique())
sel_tipos = st.sidebar.multiselect("Tipo de produção", tipos, default=tipos)

so_oa = st.sidebar.checkbox("Apenas acesso aberto", value=False)

# filtros aplicados
m_raw = raw["year"].between(*faixa) & raw["type"].isin(sel_tipos)
m_sdg = sdg["year"].between(*faixa) & sdg["type"].isin(sel_tipos)
if so_oa:
    m_raw &= raw["is_oa"] == True  # noqa: E712
    m_sdg &= sdg["is_oa"] == True  # noqa: E712
fraw, fsdg = raw[m_raw], sdg[m_sdg]

# ----------------------------------------------------------------------- abas
st.title("Observatório da Produção Científica — PROPPG/UFTM")
tab_geral, tab_ods, tab_fontes, tab_explorar = st.tabs(
    ["📊 Visão Geral", "🎯 ODS", "📚 Periódicos", "🔎 Explorar"]
)

with tab_geral:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Produções", f"{len(fraw):,}".replace(",", "."))
    c2.metric("Citações", f"{int(fraw['cited_by'].sum()):,}".replace(",", "."))
    oa_share = fraw["is_oa"].mean() if len(fraw) else 0
    c3.metric("Acesso aberto", f"{oa_share:.0%}")
    c4.metric("Produções com ODS", f"{fsdg['work_id'].nunique():,}".replace(",", "."))

    st.subheader("Produção por ano")
    por_ano = fraw.groupby("year").size().rename("Produções")
    st.bar_chart(por_ano)

    cc1, cc2 = st.columns(2)
    with cc1:
        st.subheader("Por tipo")
        st.bar_chart(fraw["type"].value_counts())
    with cc2:
        st.subheader("Acesso aberto por ano")
        oa_ano = fraw.groupby("year")["is_oa"].mean().rename("% OA")
        st.line_chart(oa_ano)

with tab_ods:
    st.subheader("Distribuição pelos 17 ODS")
    g = fsdg.copy()
    g["ODS"] = g["sdg_id"].map(lambda x: f"{int(x)}. {ODS_PT.get(int(x), '')}" if pd.notna(x) else None)
    por_ods = g.groupby("ODS")["work_id"].nunique().sort_values(ascending=True)
    st.bar_chart(por_ods, horizontal=True)

    st.subheader("Evolução temporal — escolha os ODS")
    nomes = [f"{i}. {ODS_PT[i]}" for i in range(1, 18)]
    sel = st.multiselect("ODS", nomes, default=["3. Saúde e Bem-Estar", "4. Educação de Qualidade"])
    ids = [int(s.split(".")[0]) for s in sel]
    sub = g[g["sdg_id"].isin(ids)]
    if len(sub):
        piv = sub.pivot_table(index="year", columns="ODS", values="work_id",
                              aggfunc="nunique", fill_value=0)
        st.line_chart(piv)

with tab_fontes:
    st.subheader("Periódicos onde a UFTM mais publica")
    top = (fraw[fraw["source"].notna()]["source"].value_counts().head(20)
           .rename_axis("Periódico").rename("Produções"))
    st.bar_chart(top, horizontal=True)

with tab_explorar:
    st.subheader("Buscar produções")
    termo = st.text_input("Filtrar por palavra no título")
    cols = ["title", "year", "type", "is_oa", "cited_by", "source", "doi"]
    tab = fraw[cols].copy()
    if termo:
        tab = tab[tab["title"].str.contains(termo, case=False, na=False)]
    tab = tab.sort_values("cited_by", ascending=False)
    st.dataframe(tab, use_container_width=True, height=500,
                 column_config={"doi": st.column_config.LinkColumn("DOI")})
    st.download_button("⬇️ Baixar CSV", tab.to_csv(index=False).encode("utf-8"),
                       "producoes_uftm.csv", "text/csv")

# ------------------------------------------------------------------- rodapé
st.divider()
st.caption(
    f"**Fonte:** OpenAlex (ROR UFTM `01av3m334`). "
    f"**Atenção metodológica:** a marcação de ODS é uma *estimativa automática* do classificador "
    f"de IA Aurora/mBERT do OpenAlex (lê título e resumo e atribui um score de 0 a 1 por ODS). "
    f"Só são contadas associações com score ≥ {SCORE_CUTOFF}. É um indicador probabilístico, "
    f"não uma classificação declarada pelos autores — pode divergir de painéis baseados em "
    f"classificação manual (ex.: Capivara)."
)
