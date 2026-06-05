"""Observatório PROPPG/UFTM — painel da produção científica via OpenAlex.

Lê o cache local (data/*.parquet) gerado por fetch_uftm_ods.py.
Rodar local:  streamlit run app.py
"""
from __future__ import annotations

from pathlib import Path

import altair as alt
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

st.set_page_config(page_title="Observatório PROPPG/UFTM", layout="wide")

# paleta verde do observatório
VERDE = "#15803d"        # primário
VERDE_CLARO = "#4ade80"  # destaque
VERDE_ESCURO = "#14532d"
CINZA = "#94a3b8"        # barras secundárias (não-UFTM) no benchmarking


def barra_h(df, cat, val, fmt=",.0f", cor=VERDE, altura=420, titulo_x=None):
    """Gráfico de barras horizontais em ordem decrescente, com rótulos de valor."""
    d = df[[cat, val]].copy().sort_values(val, ascending=False)
    ordem = d[cat].tolist()  # maior -> menor
    base = alt.Chart(d).encode(
        x=alt.X(f"{val}:Q", title=titulo_x, axis=alt.Axis(format=fmt)),
        y=alt.Y(f"{cat}:N", sort=ordem, title=None),
    )
    barras = base.mark_bar(cornerRadiusEnd=4, color=cor).encode(
        tooltip=[alt.Tooltip(f"{cat}:N", title=""), alt.Tooltip(f"{val}:Q", format=fmt)]
    )
    rotulos = base.mark_text(align="left", dx=4, color=VERDE_ESCURO, fontSize=11).encode(
        text=alt.Text(f"{val}:Q", format=fmt)
    )
    return (barras + rotulos).properties(height=altura)

st.markdown(
    """
    <style>
      /* cabeçalho em faixa verde */
      .obs-header {
        background: linear-gradient(120deg, #166534 0%, #15803d 55%, #22c55e 100%);
        padding: 1.4rem 1.8rem; border-radius: 16px; margin-bottom: 1.2rem;
        color: #ffffff; box-shadow: 0 6px 20px rgba(21,128,61,.18);
      }
      .obs-header h1 { color:#fff; font-size:1.7rem; margin:0; font-weight:700; }
      .obs-header p  { color:#dcfce7; margin:.3rem 0 0; font-size:.95rem; }
      /* cards de métrica arredondados */
      [data-testid="stMetric"] {
        background:#f0fdf4; border:1px solid #bbf7d0; border-radius:14px;
        padding:1rem 1.1rem; box-shadow:0 2px 6px rgba(20,83,45,.06);
      }
      [data-testid="stMetricValue"] { color:#15803d; font-weight:700; }
      [data-testid="stMetricLabel"] { color:#166534; }
      /* abas com destaque verde */
      .stTabs [aria-selected="true"] { color:#15803d !important; }
      .stTabs [data-baseweb="tab-highlight"] { background-color:#15803d !important; }
      h2, h3 { color:#14532d; }
    </style>
    """,
    unsafe_allow_html=True,
)


def _data_sig():
    """Assinatura (nome, data de modificação) dos arquivos de dados.
    Serve de chave de cache: se um arquivo muda, o cache é invalidado sozinho."""
    return tuple(sorted((p.name, p.stat().st_mtime) for p in DATA.glob("*")
                        if p.suffix in (".parquet", ".csv")))


@st.cache_data
def load(sig):
    raw = pd.read_parquet(DATA / "uftm_works_raw.parquet")
    sdg = pd.read_parquet(DATA / "uftm_works_by_sdg.parquet")
    raw["year"] = pd.to_numeric(raw["year"], errors="coerce")
    sdg["year"] = pd.to_numeric(sdg["year"], errors="coerce")
    sdg["sdg_id"] = pd.to_numeric(sdg["sdg_id"], errors="coerce").astype("Int64")
    return raw, sdg


@st.cache_data
def load_obs(sig):
    """Carrega os agregados de observatório (benchmarking, colaboração, temas, autores)."""
    arquivos = ["bench_instituicoes", "bench_por_ano", "colab_instituicoes",
                "colab_paises", "temas_campo", "temas_topicos", "top_autores"]
    d = {}
    for nome in arquivos:
        f = DATA / f"{nome}.csv"
        d[nome] = pd.read_csv(f) if f.exists() else None
    return d


_sig = _data_sig()
raw, sdg = load(_sig)
obs = load_obs(_sig)

# ---------------------------------------------------------------- barra lateral
st.sidebar.title("Observatório PROPPG")
st.sidebar.caption("Produção científica da UFTM · dados do OpenAlex")

anos = raw["year"].dropna()
ymin, ymax = int(anos.min()), int(anos.max())
faixa = st.sidebar.slider("Período", ymin, ymax, (max(ymin, ymax - 9), ymax))  # padrão: últimos 10 anos

tipos = sorted(raw["type"].dropna().unique())
sel_tipos = st.sidebar.multiselect("Tipo de produção", tipos, default=tipos)

so_oa = st.sidebar.checkbox("Apenas acesso aberto", value=False)

if st.sidebar.button("Recarregar dados", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

st.sidebar.divider()
st.sidebar.caption("Desenvolvido por **DAAD · PROPPG · UFTM**")

# filtros aplicados
m_raw = raw["year"].between(*faixa) & raw["type"].isin(sel_tipos)
m_sdg = sdg["year"].between(*faixa) & sdg["type"].isin(sel_tipos)
if so_oa:
    m_raw &= raw["is_oa"] == True  # noqa: E712
    m_sdg &= sdg["is_oa"] == True  # noqa: E712
fraw, fsdg = raw[m_raw], sdg[m_sdg]

# ----------------------------------------------------------------------- abas
st.markdown(
    """
    <div class="obs-header">
      <h1>Observatório da Produção Científica</h1>
      <p>PROPPG · Universidade Federal do Triângulo Mineiro — dados do OpenAlex</p>
    </div>
    """,
    unsafe_allow_html=True,
)
tab_geral, tab_bench, tab_ods, tab_colab, tab_pesq, tab_temas, tab_fontes, tab_explorar = st.tabs(
    ["Visão Geral", "Benchmarking", "ODS", "Colaboração",
     "Pesquisadores", "Temas", "Periódicos", "Explorar"]
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
    st.bar_chart(por_ano, color=VERDE)

    cc1, cc2 = st.columns(2)
    with cc1:
        st.subheader("Por tipo")
        st.bar_chart(fraw["type"].value_counts(), color=VERDE)
    with cc2:
        st.subheader("Acesso aberto por ano")
        oa_ano = fraw.groupby("year")["is_oa"].mean().rename("% OA")
        st.line_chart(oa_ano, color=VERDE)

with tab_ods:
    st.subheader("Distribuição pelos 17 ODS")
    g = fsdg.copy()
    g["ODS"] = g["sdg_id"].map(lambda x: f"{int(x)}. {ODS_PT.get(int(x), '')}" if pd.notna(x) else None)
    por_ods = g.groupby("ODS")["work_id"].nunique().reset_index(name="Produções")
    st.altair_chart(barra_h(por_ods, "ODS", "Produções", altura=520), use_container_width=True)

    st.subheader("Evolução temporal — escolha os ODS")
    nomes = [f"{i}. {ODS_PT[i]}" for i in range(1, 18)]
    sel = st.multiselect("ODS", nomes, default=["3. Saúde e Bem-Estar", "4. Educação de Qualidade"])
    ids = [int(s.split(".")[0]) for s in sel]
    sub = g[g["sdg_id"].isin(ids)]
    if len(sub):
        piv = sub.pivot_table(index="year", columns="ODS", values="work_id",
                              aggfunc="nunique", fill_value=0)
        st.line_chart(piv)

with tab_bench:
    st.subheader("Benchmarking — UFTM e as federais de Minas Gerais")
    bi = obs["bench_instituicoes"]
    if bi is None:
        st.info("Rode `python fetch_observatorio.py` para gerar os dados de benchmarking.")
    else:
        metricas = {
            "Produções": "works", "Citações": "citacoes",
            "Citações por trabalho": "cit_por_trabalho",
            "Impacto médio (citedness 2 anos)": "mean_citedness",
            "Índice h": "h_index", "Acesso aberto (%)": "oa_share",
        }
        escolha = st.selectbox("Métrica", list(metricas.keys()))
        col = metricas[escolha]

        # Produções e Citações respeitam o slider (somando bench_por_ano nos anos escolhidos);
        # as demais métricas são totais acumulados que o OpenAlex entrega prontos.
        por_periodo = col in ("works", "citacoes")
        if por_periodo:
            sl = obs["bench_por_ano"]
            sl = sl[sl["year"].between(*faixa)]
            d = sl.groupby("sigla", as_index=False)[col].sum().sort_values(col, ascending=False)
            nota = f"Recorte do período selecionado: {faixa[0]}–{faixa[1]}."
        else:
            d = bi[["sigla", col]].copy().sort_values(col, ascending=False)
            nota = "Total acumulado (métrica de carreira/instituição — não afetada pelo filtro de período)."

        ordem = d["sigla"].tolist()  # maior -> menor
        d["Destaque"] = d["sigla"].where(d["sigla"] == "UFTM", "Outras")
        cores = alt.Scale(domain=["UFTM", "Outras"], range=[VERDE, CINZA])
        fmt = ".0%" if col == "oa_share" else ",.2f" if col == "mean_citedness" else ",.0f"
        titulo_x = escolha if por_periodo else f"{escolha} (total acumulado)"
        base = alt.Chart(d).encode(
            x=alt.X(f"{col}:Q", title=titulo_x, axis=alt.Axis(format=fmt)),
            y=alt.Y("sigla:N", sort=ordem, title=None),  # ordem decrescente fixa
        )
        barras = base.mark_bar(cornerRadiusEnd=4).encode(
            color=alt.Color("Destaque:N", scale=cores, legend=None),
            tooltip=["sigla", alt.Tooltip(f"{col}:Q", title=escolha, format=fmt)],
        )
        rotulos = base.mark_text(align="left", dx=4, color="#14532d", fontSize=11).encode(
            text=alt.Text(f"{col}:Q", format=fmt)
        )
        st.altair_chart((barras + rotulos).properties(height=380), use_container_width=True)
        st.caption(nota)
        if col == "mean_citedness":
            st.caption("Referência: a média mundial de impacto é ≈ 1,0. Abaixo de 1,0 = abaixo da média global.")
        if col == "oa_share":
            st.caption("Proporção de produções em acesso aberto.")

        st.subheader("Evolução temporal")
        eixo = st.radio("Indicador", ["works", "citacoes"],
                        format_func=lambda x: "Produções" if x == "works" else "Citações",
                        horizontal=True)
        ba = obs["bench_por_ano"]
        ano_max = min(int(ba["year"].max()), ymax)  # ignora anos futuros vazios do OpenAlex
        ba = ba[ba["year"].between(ano_max - 9, ano_max)]  # últimos 10 anos
        base = alt.Chart(ba).encode(
            x=alt.X("year:O", title=None),
            y=alt.Y(f"{eixo}:Q", title="Produções" if eixo == "works" else "Citações"),
        )
        outras = base.transform_filter(alt.datum.sigla != "UFTM").mark_line(
            color="#cbd5e1", opacity=0.7).encode(detail="sigla:N",
            tooltip=["sigla", "year", alt.Tooltip(f"{eixo}:Q")])
        uftm = base.transform_filter(alt.datum.sigla == "UFTM").mark_line(
            color=VERDE, strokeWidth=3, point=alt.OverlayMarkDef(color=VERDE)).encode(
            tooltip=["sigla", "year", alt.Tooltip(f"{eixo}:Q")])
        st.altair_chart((outras + uftm).properties(height=360), use_container_width=True)
        st.caption("UFTM em verde; demais federais de MG em cinza. "
                   "Fonte: OpenAlex (Institutions API), dados completos da instituição.")

with tab_colab:
    st.subheader("Colaboração institucional")
    ci = obs["colab_instituicoes"]
    if ci is None:
        st.info("Rode `python fetch_observatorio.py` para gerar os dados de colaboração.")
    else:
        st.caption("Instituições que mais coassinam produções com a UFTM (exceto a própria UFTM).")
        st.altair_chart(barra_h(ci.head(15), "instituicao", "n", titulo_x="Coautorias"),
                        use_container_width=True)

        st.subheader("Internacionalização — países parceiros")
        cp = obs["colab_paises"]
        cp_int = cp[cp["pais"] != "Brazil"].head(15)
        st.altair_chart(barra_h(cp_int, "pais", "n", titulo_x="Coautorias"),
                        use_container_width=True)
        total_int = cp[cp["pais"] != "Brazil"]["n"].sum()
        st.caption(f"{len(cp)-1} países estrangeiros aparecem em coautorias da UFTM "
                   f"(Brasil excluído do gráfico para destacar a colaboração internacional).")

with tab_pesq:
    st.subheader("Pesquisadores em destaque")
    ta = obs["top_autores"]
    if ta is None:
        st.info("Rode `python fetch_observatorio.py` para gerar os dados de pesquisadores.")
    else:
        st.caption("Top 50 autores com vínculo na UFTM, por total de citações (OpenAlex Authors API).")
        st.altair_chart(barra_h(ta.head(15), "autor", "citacoes", titulo_x="Citações"),
                        use_container_width=True)
        st.dataframe(
            ta.rename(columns={"autor": "Pesquisador", "works": "Produções",
                               "citacoes": "Citações", "h_index": "Índice h", "i10": "i10"}),
            use_container_width=True, height=420, hide_index=True,
            column_config={"orcid": st.column_config.LinkColumn("ORCID")},
        )

with tab_temas:
    st.subheader("Áreas de força da UFTM")
    tc = obs["temas_campo"]
    if tc is None:
        st.info("Rode `python fetch_observatorio.py` para gerar os dados de temas.")
    else:
        st.caption("Produção por grande campo do conhecimento (classificação de tópicos do OpenAlex).")
        st.altair_chart(barra_h(tc.head(15), "campo", "n", titulo_x="Produções"),
                        use_container_width=True)
        st.subheader("Tópicos mais frequentes")
        tt = obs["temas_topicos"]
        st.altair_chart(barra_h(tt.head(20), "topico", "n", titulo_x="Produções", altura=520),
                        use_container_width=True)

with tab_fontes:
    st.subheader("Periódicos onde a UFTM mais publica")
    top = (fraw[fraw["source"].notna()]["source"].value_counts().head(20)
           .rename_axis("Periódico").reset_index(name="Produções"))
    st.altair_chart(barra_h(top, "Periódico", "Produções", altura=520), use_container_width=True)

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
    st.download_button("Baixar CSV", tab.to_csv(index=False).encode("utf-8"),
                       "producoes_uftm.csv", "text/csv")

# ------------------------------------------------------------------- rodapé
st.divider()
st.markdown(
    """
    <div style="text-align:center; color:#166534; font-weight:600;
                padding:.6rem 0 .2rem; letter-spacing:.3px;">
      DAAD · PROPPG · UFTM
    </div>
    """,
    unsafe_allow_html=True,
)
st.caption(
    f"**Fonte:** OpenAlex (ROR UFTM `01av3m334`). "
    f"**Atenção metodológica:** a marcação de ODS é uma *estimativa automática* do classificador "
    f"de IA Aurora/mBERT do OpenAlex (lê título e resumo e atribui um score de 0 a 1 por ODS). "
    f"Só são contadas associações com score ≥ {SCORE_CUTOFF}. É um indicador probabilístico, "
    f"não uma classificação declarada pelos autores."
)
