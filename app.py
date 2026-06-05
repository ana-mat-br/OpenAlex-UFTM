"""Observatório DAAD — produção científica da UFTM via OpenAlex.

Diretoria de Avaliação e Análise de Dados (DAAD) · PROPPG/UFTM.
Lê o cache local (data/*.parquet|csv) gerado por fetch_uftm_ods.py e fetch_observatorio.py.
Rodar:  streamlit run app.py
"""
from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from streamlit_extras.metric_cards import style_metric_cards
from streamlit_option_menu import option_menu

DATA = Path(__file__).parent / "data"
SCORE_CUTOFF = 0.4

# paleta "Verde Sage Sofisticado" (dark)
T = {
    "primary": "#2DD4A7", "secondary": "#38BDF8", "accent": "#F2B441",
    "bg": "#10211C", "surface": "#16302A", "border": "#234A40",
    "text": "#EAF2EF", "muted": "#8FA89F", "alert": "#F87171",
}

ODS_PT = {
    1: "Erradicação da Pobreza", 2: "Fome Zero", 3: "Saúde e Bem-Estar",
    4: "Educação de Qualidade", 5: "Igualdade de Gênero", 6: "Água Limpa e Saneamento",
    7: "Energia Limpa e Acessível", 8: "Trabalho Decente e Cresc. Econômico",
    9: "Indústria, Inovação e Infraestrutura", 10: "Redução das Desigualdades",
    11: "Cidades e Comunidades Sustentáveis", 12: "Consumo e Produção Responsáveis",
    13: "Ação Contra a Mudança do Clima", 14: "Vida na Água", 15: "Vida Terrestre",
    16: "Paz, Justiça e Instituições Eficazes", 17: "Parcerias e Meios de Implementação",
}

st.set_page_config(page_title="Observatório DAAD/UFTM", layout="wide",
                   initial_sidebar_state="expanded")

st.markdown(f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
  html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; }}
  .stApp {{ background: {T['bg']}; }}
  [data-testid="stSidebar"] {{ background: {T['surface']}; border-right: 1px solid {T['border']}; }}
  .obs-header {{
    background: linear-gradient(120deg, {T['surface']} 0%, #1d5f4e 60%, {T['primary']} 135%);
    padding: 1.3rem 1.7rem; border-radius: 16px; margin-bottom: 1.1rem;
    border: 1px solid {T['border']};
  }}
  .obs-header h1 {{ color: #fff; font-size: 1.5rem; margin: 0; font-weight: 700; }}
  .obs-header p {{ color: #d6f5ec; margin: .25rem 0 0; font-size: .9rem; }}
  h1, h2, h3, h4 {{ color: {T['text']}; }}
  [data-testid="stMetricValue"] {{ color: {T['primary']}; font-weight: 700; }}
  [data-testid="stMetricLabel"] {{ color: {T['muted']}; }}
  .stTabs [aria-selected="true"] {{ color: {T['primary']} !important; }}
  div[data-baseweb="select"] > div, .stTextInput input {{ background: {T['surface']}; }}
</style>
""", unsafe_allow_html=True)


# ----------------------------------------------------------------- dados
def _data_sig():
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
    nomes = ["bench_instituicoes", "bench_por_ano", "colab_instituicoes",
             "colab_paises", "temas_campo", "temas_topicos", "top_autores",
             "scimago_quartis"]
    return {n: (pd.read_csv(DATA / f"{n}.csv") if (DATA / f"{n}.csv").exists() else None)
            for n in nomes}


_sig = _data_sig()
raw, sdg = load(_sig)
obs = load_obs(_sig)


# ----------------------------------------------------------------- helpers
def br(n, dec=0):
    s = f"{n:,.{dec}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def fig_layout(fig, h=420):
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=T["text"], family="Inter"), height=h,
        margin=dict(l=8, r=24, t=24, b=8), showlegend=False,
        xaxis=dict(gridcolor=T["border"], zerolinecolor=T["border"]),
        yaxis=dict(gridcolor=T["border"], zerolinecolor=T["border"]),
        hoverlabel=dict(bgcolor=T["surface"], font_color=T["text"]),
    )
    return fig


def barra_h(df, cat, val, h=420, fmt=",.0f", destaque=None, cor=None):
    """Barras horizontais em ordem decrescente (maior no topo) com rótulos."""
    d = df[[cat, val]].copy().sort_values(val, ascending=True)
    if destaque:
        cores = [T["primary"] if str(c) == destaque else T["muted"] for c in d[cat]]
    else:
        cores = cor or T["primary"]
    fig = go.Figure(go.Bar(
        x=d[val], y=d[cat].astype(str), orientation="h", marker_color=cores,
        text=d[val], texttemplate="%{text:" + fmt + "}", textposition="outside",
        textfont=dict(color=T["text"], size=11), cliponaxis=False,
        hovertemplate="%{y}: %{x:" + fmt + "}<extra></extra>"))
    return fig_layout(fig, h)


def linhas_tempo(df, x, y, series, destaque=None, h=360, ytitle=""):
    """Múltiplas linhas; opcionalmente destaca uma série."""
    fig = go.Figure()
    for nome, g in df.groupby(series):
        g = g.sort_values(x)
        is_d = (str(nome) == destaque)
        fig.add_trace(go.Scatter(
            x=g[x], y=g[y], mode="lines" + ("+markers" if is_d else ""),
            name=str(nome),
            line=dict(color=T["primary"] if is_d else T["muted"],
                      width=3 if is_d else 1.3),
            opacity=1 if is_d else 0.55,
            hovertemplate=str(nome) + " %{x}: %{y:,.0f}<extra></extra>"))
    fig = fig_layout(fig, h)
    fig.update_layout(yaxis_title=ytitle)
    return fig


def aplica_filtros(faixa, tipos, so_oa):
    m_raw = raw["year"].between(*faixa) & raw["type"].isin(tipos)
    m_sdg = sdg["year"].between(*faixa) & sdg["type"].isin(tipos)
    if so_oa:
        m_raw &= raw["is_oa"] == True  # noqa: E712
        m_sdg &= sdg["is_oa"] == True  # noqa: E712
    return raw[m_raw], sdg[m_sdg]


# ----------------------------------------------------------------- sidebar
with st.sidebar:
    st.markdown(f"<h3 style='color:{T['primary']};margin-bottom:0'>Observatório DAAD</h3>"
                f"<p style='color:{T['muted']};font-size:.8rem;margin-top:.2rem'>"
                f"Diretoria de Avaliação e Análise de Dados · PROPPG/UFTM</p>",
                unsafe_allow_html=True)

    pagina = option_menu(
        None,
        ["Visão Geral", "Excelência", "Benchmarking", "Impacto Social", "Ciência Aberta",
         "Colaboração", "ODS", "Temas", "Pesquisadores", "Periódicos", "Qualidade", "Explorar"],
        icons=["speedometer2", "award", "bar-chart-line", "globe-americas", "unlock",
               "diagram-3", "bullseye", "tags", "person-badge", "journal-text",
               "patch-check", "search"],
        default_index=0,
        styles={
            "container": {"padding": "0", "background-color": T["surface"]},
            "icon": {"color": T["primary"], "font-size": "15px"},
            "nav-link": {"color": T["text"], "font-size": "14px", "--hover-color": "#1d4a3f"},
            "nav-link-selected": {"background-color": T["primary"], "color": "#0d211c",
                                  "font-weight": "600"},
        })

    st.divider()
    anos = raw["year"].dropna()
    ymin, ymax = int(anos.min()), int(anos.max())
    faixa = st.slider("Período", ymin, ymax, (max(ymin, ymax - 9), ymax))
    tipos = sorted(raw["type"].dropna().unique())
    sel_tipos = st.multiselect("Tipo de produção", tipos, default=tipos)
    so_oa = st.checkbox("Apenas acesso aberto", value=False)

    if st.button("Recarregar dados", width="stretch"):
        st.cache_data.clear()
        st.rerun()
    st.caption(f"Fonte: OpenAlex · ROR 01av3m334 · dados {ymin}–{ymax}")

fraw, fsdg = aplica_filtros(faixa, sel_tipos, so_oa)


# ----------------------------------------------------------------- páginas
def cabecalho(titulo, sub):
    st.markdown(f"<div class='obs-header'><h1>{titulo}</h1><p>{sub} · "
                f"período {faixa[0]}–{faixa[1]}</p></div>", unsafe_allow_html=True)


def render_visao_geral():
    cabecalho("Visão Geral", "Produção científica da UFTM")
    fwci_med = fraw["fwci"].dropna().mean() if "fwci" in fraw else None
    top10 = fraw["top10"].mean() if "top10" in fraw else None
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Produções", br(len(fraw)))
    c2.metric("Citações", br(int(fraw["cited_by"].sum())))
    c3.metric("FWCI médio", br(fwci_med, 2) if fwci_med else "—")
    c4.metric("No top 10% mundial", f"{top10:.0%}" if top10 is not None else "—")
    c5.metric("Acesso aberto", f"{fraw['is_oa'].mean():.0%}" if len(fraw) else "—")
    style_metric_cards(background_color=T["surface"], border_left_color=T["primary"],
                       border_color=T["border"], box_shadow=False)

    st.subheader("Produção por ano")
    por_ano = fraw.groupby("year").size().reset_index(name="n")
    fig = go.Figure(go.Bar(x=por_ano["year"], y=por_ano["n"], marker_color=T["primary"],
                           hovertemplate="%{x}: %{y}<extra></extra>"))
    st.plotly_chart(fig_layout(fig, 320), width="stretch")

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Por tipo de produção")
        tp = fraw["type"].value_counts().reset_index()
        tp.columns = ["tipo", "n"]
        st.plotly_chart(barra_h(tp.head(10), "tipo", "n", h=360), width="stretch")
    with c2:
        st.subheader("Acesso aberto por ano")
        oa = fraw.groupby("year")["is_oa"].mean().reset_index()
        fig = go.Figure(go.Scatter(x=oa["year"], y=oa["is_oa"], mode="lines+markers",
                                   line=dict(color=T["accent"], width=3),
                                   hovertemplate="%{x}: %{y:.0%}<extra></extra>"))
        fig = fig_layout(fig, 360)
        fig.update_yaxes(tickformat=".0%")
        st.plotly_chart(fig, width="stretch")


def render_excelencia():
    cabecalho("Excelência", "Indicadores normalizados por campo (FWCI e percentis mundiais)")
    if "fwci" not in fraw.columns:
        st.info("Re-colete os dados (fetch_uftm_ods.py) para habilitar FWCI e percentis.")
        return
    excluir = st.checkbox("Excluir os 2 anos mais recentes (janela FWCI ainda incompleta)",
                          value=True)
    base = fraw[fraw["year"] <= faixa[1] - 2] if excluir else fraw
    fw = base["fwci"].dropna()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("FWCI médio", br(fw.mean(), 2) if len(fw) else "—",
              help="1,0 = média mundial do campo. Acima de 1 = acima da média global.")
    c2.metric("% com FWCI > 1", f"{(fw > 1).mean():.0%}" if len(fw) else "—")
    c3.metric("No top 10% mundial", f"{base['top10'].mean():.1%}" if len(base) else "—")
    c4.metric("No top 1% mundial", f"{base['top1'].mean():.1%}" if len(base) else "—")
    style_metric_cards(background_color=T["surface"], border_left_color=T["primary"],
                       border_color=T["border"], box_shadow=False)
    st.caption("FWCI: razão entre citações recebidas e esperadas no campo/ano (fórmula do "
               "Scopus, publicada nativamente pelo OpenAlex). Normaliza por subfield do "
               "OpenAlex — comparável, mas não idêntico ao SciVal. Não comparar entre bases.")

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("FWCI médio por ano")
        s = base.dropna(subset=["fwci"]).groupby("year")["fwci"].mean().reset_index()
        fig = go.Figure(go.Scatter(x=s["year"], y=s["fwci"], mode="lines+markers",
                                   line=dict(color=T["primary"], width=3),
                                   hovertemplate="%{x}: %{y:.2f}<extra></extra>"))
        fig = fig_layout(fig, 360)
        fig.add_hline(y=1.0, line_dash="dash", line_color=T["muted"],
                      annotation_text="média mundial", annotation_font_color=T["muted"])
        st.plotly_chart(fig, width="stretch")
    with c2:
        st.subheader("FWCI médio por grande área")
        s = (base.dropna(subset=["fwci", "field"]).groupby("field")
             .agg(fwci=("fwci", "mean"), n=("id", "count")).reset_index())
        s = s[s["n"] >= 20].sort_values("fwci", ascending=False).head(12)
        st.plotly_chart(barra_h(s, "field", "fwci", h=360, fmt=".2f"),
                        width="stretch")

    bi = obs.get("bench_instituicoes")
    if bi is not None and "top10_share" in bi.columns:
        st.subheader("Excelência comparada — % no top 10% mundial (11 federais de MG)")
        d = bi[["sigla", "top10_share"]].copy()
        d["top10_share"] = d["top10_share"] * 100
        st.plotly_chart(barra_h(d, "sigla", "top10_share", h=380, fmt=".1f",
                                destaque="UFTM"), width="stretch")
        st.caption("Percentual de produções entre as 10% mais citadas do mundo no seu campo. "
                   "Métrica normalizada — total acumulado por instituição (OpenAlex).")


def render_impacto_social():
    cabecalho("Impacto Social e Societal", "Para além das citações acadêmicas")
    c1, c2, c3, c4 = st.columns(4)
    n_ods = fsdg["work_id"].nunique()
    fin = fraw[fraw["n_grants"] > 0] if "n_grants" in fraw else fraw.iloc[0:0]
    apc_tot = fraw["apc_usd"].dropna().sum() if "apc_usd" in fraw else 0
    c1.metric("Produções com ODS", br(n_ods),
              help="Alinhamento à Agenda 2030 (classificador Aurora ≥ 0,4).")
    c2.metric("Produções financiadas", br(len(fin)),
              f"{len(fin)/max(len(fraw),1):.0%} do total")
    c3.metric("Financiadores distintos",
              br(fraw["funders"].explode().nunique()) if "funders" in fraw else "—")
    c4.metric("APC estimado (US$)", br(apc_tot) if apc_tot else "—",
              help="Custo de publicação (Article Processing Charges) reportado ao OpenAlex.")
    style_metric_cards(background_color=T["surface"], border_left_color=T["accent"],
                       border_color=T["border"], box_shadow=False)

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Alinhamento aos ODS")
        g = fsdg.copy()
        g["ODS"] = g["sdg_id"].map(lambda x: f"{int(x)}. {ODS_PT.get(int(x), '')}"
                                   if pd.notna(x) else None)
        po = g.groupby("ODS")["work_id"].nunique().reset_index(name="n")
        st.plotly_chart(barra_h(po, "ODS", "n", h=480, cor=T["accent"]),
                        width="stretch")
    with c2:
        st.subheader("Principais financiadores")
        if "funders" in fraw:
            f = fraw["funders"].explode().dropna().value_counts().head(15).reset_index()
            f.columns = ["financiador", "n"]
            if len(f):
                st.plotly_chart(barra_h(f, "financiador", "n", h=480, cor=T["secondary"]),
                                width="stretch")
            else:
                st.info("Sem dados de financiamento na seleção atual.")

    st.divider()
    st.subheader("Em desenvolvimento — impacto fora da academia")
    st.markdown(
        "Estes eixos completam o módulo de impacto societal (o que SciVal/Stela cobram). "
        "Integração incremental com fontes gratuitas:\n"
        "- **Patentes** que citam a pesquisa — via **The Lens** (Scholar↔Patent)\n"
        "- **Políticas públicas** que citam a pesquisa — via **Overton / Sage Policy Profiles**\n"
        "- **Atenção online** (mídia, redes, Wikipedia) — via **Altmetric** (exige chave de pesquisa)\n\n"
        "Lacuna conhecida e declarada: *Views/Field-Weighted Views* do Scopus não têm "
        "equivalente em dados abertos.")


def render_ciencia_aberta():
    cabecalho("Ciência Aberta", "Acesso aberto, repositório verde, custos de publicação e DOAJ")
    if "oa_status" not in fraw.columns:
        st.info("Re-colete os dados (fetch_uftm_ods.py) para habilitar esta aba.")
        return
    oa_pt = {"diamond": "Diamante (grátis autor e leitor)", "gold": "Ouro (com APC)",
             "green": "Verde (repositório)", "hybrid": "Híbrido", "bronze": "Bronze",
             "closed": "Fechado"}
    oa_cor = {"diamond": T["primary"], "gold": T["accent"], "green": "#4ade80",
              "hybrid": T["secondary"], "bronze": "#d97706", "closed": T["muted"]}

    oa = fraw["is_oa"].mean() if len(fraw) else 0
    diam = (fraw["oa_status"] == "diamond").mean() if len(fraw) else 0
    verde = fraw["in_repository"].mean() if "in_repository" in fraw.columns else None
    oa_works = fraw[fraw["is_oa"] == True]  # noqa: E712
    doaj = oa_works["in_doaj"].mean() if "in_doaj" in fraw.columns and len(oa_works) else None
    apc = fraw["apc_usd"].dropna()
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Acesso aberto", f"{oa:.0%}")
    c2.metric("Diamante (sem custo)", f"{diam:.0%}", help="Grátis para autor e leitor.")
    c3.metric("Via verde (repositório)", f"{verde:.0%}" if verde is not None else "—")
    c4.metric("Em periódico DOAJ", f"{doaj:.0%}" if doaj is not None else "—",
              help="Entre as produções OA, % em periódicos com selo DOAJ (qualidade).")
    c5.metric("APC total (US$)", br(apc.sum()) if len(apc) else "—")
    style_metric_cards(background_color=T["surface"], border_left_color=T["primary"],
                       border_color=T["border"], box_shadow=False)

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Composição do acesso aberto")
        comp = fraw["oa_status"].value_counts().reset_index()
        comp.columns = ["status", "n"]
        comp = comp.sort_values("n", ascending=True)
        fig = go.Figure(go.Bar(
            x=comp["n"], y=comp["status"].map(oa_pt), orientation="h",
            marker_color=[oa_cor.get(s, T["muted"]) for s in comp["status"]],
            text=comp["n"], texttemplate="%{text:,.0f}", textposition="outside",
            textfont=dict(color=T["text"], size=11), cliponaxis=False,
            hovertemplate="%{y}: %{x:,.0f}<extra></extra>"))
        st.plotly_chart(fig_layout(fig, 360), width="stretch")
    with c2:
        st.subheader("Acesso aberto ao longo do tempo")
        ev = fraw.groupby("year")["is_oa"].mean().reset_index()
        fig = go.Figure(go.Scatter(x=ev["year"], y=ev["is_oa"], mode="lines+markers",
                                   line=dict(color=T["primary"], width=3),
                                   hovertemplate="%{x}: %{y:.0%}<extra></extra>"))
        fig = fig_layout(fig, 360)
        fig.update_yaxes(tickformat=".0%")
        st.plotly_chart(fig, width="stretch")

    st.subheader("Custos de publicação (APC)")
    pagos = fraw[fraw["apc_usd"] > 0]
    c1, c2, c3 = st.columns(3)
    c1.metric("Produções com APC", br(len(pagos)),
              f"{len(pagos)/max(len(fraw),1):.0%} do total")
    c2.metric("APC médio (US$)", br(pagos["apc_usd"].mean()) if len(pagos) else "—")
    c3.metric("Sem custo para o autor", f"{1 - len(pagos)/max(len(fraw),1):.0%}",
              help="Diamante, verde, bronze e fechado não cobram APC do autor.")
    style_metric_cards(background_color=T["surface"], border_left_color=T["accent"],
                       border_color=T["border"], box_shadow=False)
    apc_ano = fraw.groupby("year")["apc_usd"].sum().reset_index()
    fig = go.Figure(go.Bar(x=apc_ano["year"], y=apc_ano["apc_usd"], marker_color=T["accent"],
                           hovertemplate="%{x}: US$ %{y:,.0f}<extra></extra>"))
    st.plotly_chart(fig_layout(fig, 300), width="stretch")
    st.caption("APC = Article Processing Charge reportado ao OpenAlex — estimativa do gasto com "
               "publicação em acesso aberto pago (não inclui acordos transformativos/descontos).")


def render_benchmarking():
    cabecalho("Benchmarking", "UFTM e as 11 universidades federais de Minas Gerais")
    bi = obs.get("bench_instituicoes")
    if bi is None:
        st.info("Rode `python fetch_observatorio.py` para gerar os dados de benchmarking.")
        return
    metricas = {
        "Produções": ("works", ",.0f"), "Citações": ("citacoes", ",.0f"),
        "Citações por trabalho": ("cit_por_trabalho", ",.2f"),
        "FWCI / Impacto médio (citedness)": ("mean_citedness", ",.2f"),
        "No top 10% mundial (%)": ("top10_share", ".1%"),
        "No top 1% mundial (%)": ("top1_share", ".1%"),
        "Colaboração internacional (%)": ("intl_share", ".1%"),
        "Acesso aberto (%)": ("oa_share", ".1%"),
        "Índice h": ("h_index", ",.0f"),
    }
    metricas = {k: v for k, v in metricas.items() if v[0] in bi.columns}
    escolha = st.selectbox("Métrica", list(metricas.keys()))
    col, fmt = metricas[escolha]

    por_periodo = col in ("works", "citacoes")
    if por_periodo:
        sl = obs["bench_por_ano"]
        sl = sl[sl["year"].between(*faixa)]
        d = sl.groupby("sigla", as_index=False)[col].sum()
        nota = f"Recorte do período {faixa[0]}–{faixa[1]}."
    else:
        d = bi[["sigla", col]].copy()
        if col.endswith("_share"):
            d[col] = d[col] * 100
            fmt = ".1f"
        nota = "Total acumulado (não afetado pelo filtro de período)."
    st.plotly_chart(barra_h(d, "sigla", col, h=400, fmt=fmt, destaque="UFTM"),
                    width="stretch")
    st.caption(nota + ("  Referência mundial: FWCI/citedness ≈ 1,0; top 10% ≈ 10%; top 1% ≈ 1%."
                       if col in ("mean_citedness", "top10_share", "top1_share") else ""))

    st.subheader("Evolução temporal")
    eixo = st.radio("Indicador", ["works", "citacoes"], horizontal=True,
                    format_func=lambda x: "Produções" if x == "works" else "Citações")
    ba = obs["bench_por_ano"]
    am = min(int(ba["year"].max()), ymax)
    ba = ba[ba["year"].between(am - 9, am)]
    st.plotly_chart(linhas_tempo(ba, "year", eixo, "sigla", destaque="UFTM", h=380),
                    width="stretch")
    st.caption("UFTM em verde; demais federais de MG em cinza.")


def render_colaboracao():
    cabecalho("Colaboração", "Parcerias institucionais e internacionalização")
    if "is_international" in fraw.columns and len(fraw):
        intl = fraw["is_international"].mean()
        nac = (~fraw["is_international"] & (fraw["n_institutions"] > 1)).mean()
        inst = (fraw["n_institutions"] <= 1).mean()
        c1, c2, c3 = st.columns(3)
        c1.metric("Internacional", f"{intl:.0%}", help="≥ 2 países distintos.")
        c2.metric("Nacional", f"{nac:.0%}", help="Só Brasil, ≥ 2 instituições.")
        c3.metric("Institucional", f"{inst:.0%}", help="Apenas UFTM.")
        style_metric_cards(background_color=T["surface"], border_left_color=T["secondary"],
                           border_color=T["border"], box_shadow=False)

    ci = obs.get("colab_instituicoes")
    if ci is None:
        st.info("Rode `python fetch_observatorio.py` para os dados de colaboração.")
        return
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Instituições parceiras")
        st.plotly_chart(barra_h(ci.head(15), "instituicao", "n", h=460),
                        width="stretch")
    with c2:
        st.subheader("Países parceiros (exceto Brasil)")
        cp = obs["colab_paises"]
        cp = cp[cp["pais"] != "Brazil"].head(15)
        st.plotly_chart(barra_h(cp, "pais", "n", h=460, cor=T["secondary"]),
                        width="stretch")


def render_ods():
    cabecalho("Objetivos de Desenvolvimento Sustentável", "Classificação automática (Aurora ≥ 0,4)")
    g = fsdg.copy()
    g["ODS"] = g["sdg_id"].map(lambda x: f"{int(x)}. {ODS_PT.get(int(x), '')}"
                               if pd.notna(x) else None)
    po = g.groupby("ODS")["work_id"].nunique().reset_index(name="n")
    st.plotly_chart(barra_h(po, "ODS", "n", h=520), width="stretch")

    st.subheader("Evolução temporal — escolha os ODS")
    nomes = [f"{i}. {ODS_PT[i]}" for i in range(1, 18)]
    sel = st.multiselect("ODS", nomes, default=["3. Saúde e Bem-Estar", "4. Educação de Qualidade"])
    ids = [int(s.split(".")[0]) for s in sel]
    sub = g[g["sdg_id"].isin(ids)]
    if len(sub):
        ev = sub.groupby(["year", "ODS"])["work_id"].nunique().reset_index(name="n")
        fig = go.Figure()
        cores = [T["primary"], T["secondary"], T["accent"], "#c084fc", "#f87171", "#a3e635"]
        for i, (nome, gg) in enumerate(ev.groupby("ODS")):
            fig.add_trace(go.Scatter(x=gg["year"], y=gg["n"], mode="lines+markers",
                                     name=nome, line=dict(color=cores[i % len(cores)], width=2.5)))
        fig = fig_layout(fig, 360)
        fig.update_layout(showlegend=True, legend=dict(font=dict(color=T["text"], size=10)))
        st.plotly_chart(fig, width="stretch")


def render_temas():
    cabecalho("Temas", "Áreas de força da UFTM (tópicos do OpenAlex)")
    tc = obs.get("temas_campo")
    if tc is None:
        st.info("Rode `python fetch_observatorio.py` para os dados de temas.")
        return
    st.subheader("Por grande área do conhecimento")
    st.plotly_chart(barra_h(tc.head(15), "campo", "n", h=460), width="stretch")
    st.subheader("Tópicos mais frequentes")
    tt = obs["temas_topicos"]
    st.plotly_chart(barra_h(tt.head(20), "topico", "n", h=540, cor=T["secondary"]),
                    width="stretch")


def render_pesquisadores():
    cabecalho("Pesquisadores", "Destaques por impacto (OpenAlex Authors)")
    ta = obs.get("top_autores")
    if ta is None:
        st.info("Rode `python fetch_observatorio.py` para os dados de pesquisadores.")
        return
    st.plotly_chart(barra_h(ta.head(15), "autor", "citacoes", h=460), width="stretch")
    st.dataframe(
        ta.rename(columns={"autor": "Pesquisador", "works": "Produções",
                           "citacoes": "Citações", "h_index": "Índice h", "i10": "i10"}),
        width="stretch", height=420, hide_index=True,
        column_config={"orcid": st.column_config.LinkColumn("ORCID")})


def render_periodicos():
    cabecalho("Periódicos", "Onde a UFTM mais publica")
    top = (fraw[fraw["source"].notna()]["source"].value_counts().head(20)
           .rename_axis("Periódico").reset_index(name="n"))
    st.plotly_chart(barra_h(top, "Periódico", "n", h=540), width="stretch")


def render_qualidade():
    cabecalho("Qualidade de Periódicos", "Quartis Scimago (SJR) das produções em periódico")
    sq = obs.get("scimago_quartis")
    if sq is None or "issn_l" not in fraw.columns:
        st.info("Rode `python fetch_scimago.py` para baixar os quartis Scimago.")
        return
    f = fraw[fraw["issn_l"].notna()].copy()
    f["issn"] = f["issn_l"].str.replace("-", "", regex=False).str.upper()
    m = f.merge(sq[["issn", "quartile", "sjr"]], on="issn", how="left")
    cq = m[m["quartile"].isin(["Q1", "Q2", "Q3", "Q4"])]
    cobertura = len(cq) / max(len(m), 1)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Em Q1", f"{(cq['quartile'] == 'Q1').mean():.0%}" if len(cq) else "—",
              help="Entre as produções com quartil Scimago conhecido.")
    c2.metric("Em Q1 ou Q2", f"{cq['quartile'].isin(['Q1', 'Q2']).mean():.0%}" if len(cq) else "—")
    c3.metric("SJR médio", br(cq["sjr"].mean(), 2) if len(cq) else "—")
    c4.metric("Cobertura Scimago", f"{cobertura:.0%}",
              help="% das produções em periódico com quartil no Scimago. O restante são "
                   "periódicos fora do Scopus/Scimago (ex.: muitos periódicos nacionais).")
    style_metric_cards(background_color=T["surface"], border_left_color=T["primary"],
                       border_color=T["border"], box_shadow=False)

    qcor = {"Q1": T["primary"], "Q2": T["secondary"], "Q3": T["accent"], "Q4": "#d97706"}
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Distribuição por quartil")
        dist = (cq["quartile"].value_counts().reindex(["Q4", "Q3", "Q2", "Q1"])
                .fillna(0).reset_index())
        dist.columns = ["quartile", "n"]
        fig = go.Figure(go.Bar(
            x=dist["n"], y=dist["quartile"], orientation="h",
            marker_color=[qcor[q] for q in dist["quartile"]], text=dist["n"],
            texttemplate="%{text:,.0f}", textposition="outside",
            textfont=dict(color=T["text"], size=12), cliponaxis=False,
            hovertemplate="%{y}: %{x:,.0f}<extra></extra>"))
        st.plotly_chart(fig_layout(fig, 320), width="stretch")
    with c2:
        st.subheader("% em Q1 ao longo do tempo")
        yr = (cq.assign(is_q1=cq["quartile"] == "Q1").groupby("year")["is_q1"]
              .mean().reset_index())
        fig = go.Figure(go.Scatter(x=yr["year"], y=yr["is_q1"], mode="lines+markers",
                                   line=dict(color=T["primary"], width=3),
                                   hovertemplate="%{x}: %{y:.0%}<extra></extra>"))
        fig = fig_layout(fig, 320)
        fig.update_yaxes(tickformat=".0%")
        st.plotly_chart(fig, width="stretch")

    st.subheader("Principais periódicos Q1")
    q1j = cq[cq["quartile"] == "Q1"]["source"].value_counts().head(15).reset_index()
    q1j.columns = ["Periódico", "n"]
    if len(q1j):
        st.plotly_chart(barra_h(q1j, "Periódico", "n", h=460), width="stretch")
    st.caption("Quartil pelo melhor ranking Scimago (SJR Best Quartile, edição 2025), cruzado "
               "por ISSN. Periódicos fora do Scopus/Scimago não recebem quartil.")


def render_explorar():
    cabecalho("Explorar", "Busca nas produções")
    termo = st.text_input("Filtrar por palavra no título")
    cols = [c for c in ["title", "year", "type", "is_oa", "fwci", "cited_by", "source", "doi"]
            if c in fraw.columns]
    tab = fraw[cols].copy()
    if termo:
        tab = tab[tab["title"].str.contains(termo, case=False, na=False)]
    tab = tab.sort_values("cited_by", ascending=False)
    st.dataframe(tab, width="stretch", height=520,
                 column_config={"doi": st.column_config.LinkColumn("DOI")})
    st.download_button("Baixar CSV", tab.to_csv(index=False).encode("utf-8"),
                       "producoes_uftm.csv", "text/csv")


PAGINAS = {
    "Visão Geral": render_visao_geral, "Excelência": render_excelencia,
    "Benchmarking": render_benchmarking, "Impacto Social": render_impacto_social,
    "Ciência Aberta": render_ciencia_aberta,
    "Colaboração": render_colaboracao, "ODS": render_ods, "Temas": render_temas,
    "Pesquisadores": render_pesquisadores, "Periódicos": render_periodicos,
    "Qualidade": render_qualidade, "Explorar": render_explorar,
}
_forcar = os.environ.get("OBS_FORCE_PAGE")  # seam de teste (sem efeito em produção)
PAGINAS.get(_forcar or pagina or "Visão Geral", render_visao_geral)()

# ----------------------------------------------------------------- rodapé
st.divider()
st.markdown(f"<div style='text-align:center;color:{T['muted']};font-size:.85rem'>"
            f"<b style='color:{T['primary']}'>DAAD · PROPPG · UFTM</b> — Observatório da "
            f"Produção Científica · dados OpenAlex (ROR 01av3m334)</div>",
            unsafe_allow_html=True)
st.caption("A classificação de ODS é estimativa automática do classificador Aurora/mBERT do "
           "OpenAlex (score ≥ 0,4). FWCI e percentis são indicadores normalizados por campo "
           "do OpenAlex (metodologia equivalente à do Scopus, valores não comparáveis entre bases).")
