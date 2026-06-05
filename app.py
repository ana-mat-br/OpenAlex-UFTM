"""Painel DAAD — produção científica da UFTM via OpenAlex.

Diretoria de Avaliação e Análise de Dados (DAAD) · PROPPG/UFTM.
Lê o cache local (data/*.parquet|csv) gerado por fetch_uftm_ods.py e fetch_observatorio.py.
Rodar:  streamlit run app.py
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from streamlit_option_menu import option_menu

DATA = Path(__file__).parent / "data"
SCORE_CUTOFF = 0.4

# paleta UFTM — clara e minimalista (verde #00983A de destaque)
T = {
    "primary": "#00983A",       # uftmgreen — destaques, links, títulos
    "primary_deep": "#007A2E",  # uftmgreendeep
    "primary_dark": "#005C22",  # uftmgreendark
    "green_mid": "#A6DBB7",     # uftmgreenmid — barras secundárias
    "green_tint": "#E6F4EA",    # uftmgreentint — fundos de destaque
    "secondary": "#E87722",     # uftmaccent — laranja de acento (2ª série)
    "accent": "#E87722",
    "bg": "#FAFAF8",            # fundo "papel" (off-white levemente quente)
    "surface": "#FFFFFF",       # cards
    "border": "#EAEAEA",        # rulelight
    "border_med": "#DCDCDC",    # rulemed
    "text": "#2B2B2B",          # inkdark
    "text_soft": "#5C5C5C",     # inksoft
    "muted": "#8A8A8A",         # inkmute
    "faint": "#B5B5B5",         # inkfaint
    "alert": "#E87722",
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

st.set_page_config(page_title="Painel DAAD — UFTM", layout="wide",
                   initial_sidebar_state="expanded")

SERIF = "'Palatino', 'Palatino Linotype', 'Book Antiqua', Georgia, serif"
st.markdown(f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
  html, body, [class*="css"], p, div, span, label {{ font-family: 'Inter', sans-serif; }}
  h1, h2, h3, h4, .obs-header h1 {{ font-family: {SERIF}; color: {T['text']};
    font-weight: 600; letter-spacing: .2px; }}
  .stApp {{ background: {T['bg']}; }}
  .block-container {{ padding-top: 2.2rem; max-width: 1280px; }}
  [data-testid="stSidebar"] {{ background: {T['surface']}; border-right: 1px solid {T['border']}; }}
  .obs-header {{ background: transparent; border: none;
    border-bottom: 1px solid {T['border']}; padding: .1rem 0 .85rem; margin-bottom: 1.4rem; }}
  .obs-header h1 {{ color: {T['text']}; font-size: 1.75rem; margin: 0; letter-spacing: -.01em; }}
  .obs-header p {{ color: {T['muted']}; margin: .4rem 0 0; font-size: .92rem;
    font-family: 'Inter', sans-serif; }}
  [data-testid="stMetric"] {{ background: transparent; border: none; border-radius: 0;
    border-top: 2px solid {T['primary']}; padding: .6rem .1rem 0; }}
  [data-testid="stMetricValue"] {{ color: {T['text']}; font-weight: 700;
    font-family: 'Inter', sans-serif; font-size: 2.05rem; letter-spacing: -.02em; }}
  [data-testid="stMetricLabel"] {{ color: {T['muted']}; font-weight: 600;
    text-transform: uppercase; letter-spacing: .07em; font-size: .7rem; }}
  a, .stMarkdown a {{ color: {T['primary']}; }}
  hr {{ border-color: {T['border']}; }}
  div[data-baseweb="select"] > div, .stTextInput input {{
    background: {T['surface']}; border-color: {T['border']}; }}
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
             "scimago_quartis", "rede_autores_nos", "rede_autores_arestas",
             "lens_patentes"]
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
        cores = [T["primary"] if str(c) == destaque else T["green_mid"] for c in d[cat]]
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
            line=dict(color=T["primary"] if is_d else T["faint"],
                      width=3 if is_d else 1.3),
            opacity=1 if is_d else 0.7,
            hovertemplate=str(nome) + " %{x}: %{y:,.0f}<extra></extra>"))
    fig = fig_layout(fig, h)
    fig.update_layout(yaxis_title=ytitle)
    return fig


PALETA_COM = ["#00983A", "#E87722", "#2563EB", "#7C3AED", "#DB2777", "#0891B2",
              "#65A30D", "#CA8A04", "#DC2626", "#475569"]


def grafo_coautoria(nos, arestas, h=560):
    """Rede de coautoria: arestas + nós coloridos por comunidade e dimensionados por produção."""
    pos = {r.id: (r.x, r.y) for r in nos.itertuples()}
    ex, ey = [], []
    for e in arestas.itertuples():
        if e.origem in pos and e.destino in pos:
            x0, y0 = pos[e.origem]
            x1, y1 = pos[e.destino]
            ex += [x0, x1, None]
            ey += [y0, y1, None]
    edge = go.Scatter(x=ex, y=ey, mode="lines", hoverinfo="none",
                      line=dict(color=T["border"], width=0.6))
    wmax = max(nos["works"].max(), 1)
    node = go.Scatter(
        x=nos["x"], y=nos["y"], mode="markers", hoverinfo="text",
        text=[f"{r.nome}<br>{r.works} produções · grau {int(r.grau)}" for r in nos.itertuples()],
        marker=dict(size=[7 + (w / wmax) * 24 for w in nos["works"]],
                    color=[PALETA_COM[int(c) % len(PALETA_COM)] for c in nos["comunidade"]],
                    line=dict(color=T["bg"], width=0.6), opacity=0.9))
    centrais = nos.sort_values("betw", ascending=False).head(8)
    rotulos = go.Scatter(
        x=centrais["x"], y=centrais["y"], mode="text",
        text=[n.split()[-1] for n in centrais["nome"]], hoverinfo="none",
        textposition="top center", textfont=dict(color=T["text"], size=10))
    fig = go.Figure([edge, node, rotulos])
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      height=h, margin=dict(l=0, r=0, t=0, b=0), showlegend=False,
                      xaxis=dict(visible=False), yaxis=dict(visible=False),
                      hoverlabel=dict(bgcolor=T["surface"], font_color=T["text"]))
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
    st.markdown(f"<h3 style='color:{T['primary']};margin-bottom:0;font-family:{SERIF}'>"
                f"Painel DAAD</h3>"
                f"<p style='color:{T['muted']};font-size:.8rem;margin-top:.2rem'>"
                f"Diretoria de Avaliação e Análise de Dados · PROPPG/UFTM</p>",
                unsafe_allow_html=True)

    NAV = ["Visão Geral", "Impacto científico", "Comparação", "Ciência Aberta", "Impacto Social",
           "ODS", "Pesquisadores", "Colaboração", "Temas", "Onde publicamos",
           "Qualidade das revistas", "Explorar", "Transparência"]
    ICONS = ["speedometer2", "award", "bar-chart-line", "unlock", "globe-americas",
             "bullseye", "person-badge", "diagram-3", "tags", "journal-text",
             "patch-check", "search", "info-circle"]
    _override = st.session_state.pop("ir_para", None)  # navegação por link (ex.: rodapé)
    # key dependente do conteúdo+estilo: força o re-render quando ordem/ícones/visual mudam
    _menu_sig = hashlib.md5(("|".join(NAV) + "|".join(ICONS) + "estilo-v3").encode()).hexdigest()[:8]
    pagina = option_menu(
        None, NAV, icons=ICONS, default_index=0, key=f"navmenu-{_menu_sig}",
        manual_select=(NAV.index(_override) if _override in NAV else None),
        styles={
            "container": {"padding": "0.2rem 0", "background-color": T["surface"]},
            "icon": {"color": T["muted"], "font-size": "13px"},
            "nav-link": {"color": T["text_soft"], "font-size": "14px", "font-weight": "500",
                         "border-radius": "0", "margin": "0", "padding": "6px 6px",
                         "--hover-color": "#F4F4F2"},
            "nav-link-selected": {"background-color": "transparent", "color": T["primary"],
                                  "font-weight": "700"},
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
    cabecalho("Visão Geral", "A pesquisa da UFTM, em números claros")
    st.markdown(
        f"<div style='border-left:2px solid {T['primary']};padding:.15rem 0 .15rem 1.1rem;"
        f"margin:.1rem 0 1.6rem;color:{T['text_soft']};font-size:1.05rem;line-height:1.65;"
        f"max-width:760px'>"
        f"O Painel DAAD é a prestação de contas da pesquisa da UFTM à sociedade. De forma "
        f"transparente e com dados abertos, mostra o que a universidade produz em ciência e o "
        f"impacto disso para as pessoas. Os números vêm do "
        f"<b style='color:{T['text']}'>OpenAlex</b> — base científica mundial e gratuita — e são "
        f"atualizados todo mês.</div>", unsafe_allow_html=True)
    fwci_med = fraw["fwci"].dropna().mean() if "fwci" in fraw else None
    top10 = fraw["top10"].mean() if "top10" in fraw else None
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Produções", br(len(fraw)))
    c2.metric("Citações", br(int(fraw["cited_by"].sum())))
    c3.metric("FWCI médio", br(fwci_med, 2) if fwci_med else "—")
    c4.metric("Top 10%", f"{top10:.0%}" if top10 is not None else "—",
              help="Parte das pesquisas que está entre as 10% mais citadas do mundo na sua área.")
    c5.metric("Acesso aberto", f"{fraw['is_oa'].mean():.0%}" if len(fraw) else "—")
    st.caption(
        "**Como ler estes números** · **Produções**: pesquisas publicadas no período · "
        "**Citações**: vezes que essas pesquisas foram usadas por outros estudos · "
        "**FWCI**: impacto comparado à média mundial da área (1,0 = média do mundo; acima de 1 "
        "é acima da média) · **Top 10%**: fatia das pesquisas entre as 10% mais citadas do "
        "planeta · **Acesso aberto**: parte que qualquer pessoa pode ler de graça.")

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
    cabecalho("Impacto científico", "O quanto a pesquisa da UFTM é reconhecida no mundo")
    if "fwci" not in fraw.columns:
        st.info("Re-colete os dados (fetch_uftm_ods.py) para habilitar FWCI e percentis.")
        return
    excluir = st.checkbox("Não contar os 2 anos mais recentes (pesquisas novas ainda estão "
                          "recebendo citações)", value=True)
    base = fraw[fraw["year"] <= faixa[1] - 2] if excluir else fraw
    fw = base["fwci"].dropna()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("FWCI médio", br(fw.mean(), 2) if len(fw) else "—",
              help="1,0 = média mundial do campo. Acima de 1 = acima da média global.")
    c2.metric("% com FWCI > 1", f"{(fw > 1).mean():.0%}" if len(fw) else "—")
    c3.metric("No top 10% mundial", f"{base['top10'].mean():.1%}" if len(base) else "—")
    c4.metric("No top 1% mundial", f"{base['top1'].mean():.1%}" if len(base) else "—")
    st.caption(
        "**Como ler** · Estes números comparam cada pesquisa da UFTM com a média mundial da "
        "sua área. **FWCI 1,0** = exatamente a média do mundo (acima de 1 é acima da média). "
        "**Top 10% / Top 1%** = a fatia das pesquisas que está entre as mais citadas do "
        "planeta — quanto maior, mais reconhecida lá fora.  \n"
        "_Detalhe técnico: FWCI (Field-Weighted Citation Impact) usa a mesma fórmula da Scopus "
        "(base científica paga), calculada aqui pelo OpenAlex; os valores não são comparáveis "
        "entre bases diferentes._")

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
    cabecalho("Impacto Social", "O alcance da pesquisa da UFTM além da universidade")
    st.caption("**Como ler** · Aqui vemos o retorno da pesquisa para a sociedade: alinhamento aos "
               "**ODS** (os objetivos da ONU), quanto vem de **financiamento** público/privado, "
               "o custo de deixar a pesquisa aberta e — quando ativado — quantas **patentes** "
               "citam a UFTM.")
    c1, c2, c3, c4 = st.columns(4)
    n_ods = fsdg["work_id"].nunique()
    fin = fraw[fraw["n_grants"] > 0] if "n_grants" in fraw else fraw.iloc[0:0]
    apc_tot = fraw["apc_usd"].dropna().sum() if "apc_usd" in fraw else 0
    c1.metric("Produções com ODS", br(n_ods),
              help="Pesquisas ligadas a pelo menos um dos 17 objetivos da ONU, segundo "
                   "estimativa por inteligência artificial do OpenAlex.")
    c2.metric("Produções financiadas", br(len(fin)),
              f"{len(fin)/max(len(fraw),1):.0%} do total")
    c3.metric("Financiadores distintos",
              br(fraw["funders"].explode().nunique()) if "funders" in fraw else "—")
    c4.metric("APC estimado (US$)", br(apc_tot) if apc_tot else "—",
              help="Custo de publicação (Article Processing Charges) reportado ao OpenAlex.")

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
    st.subheader("Impacto em inovação — citações em patentes (The Lens)")
    lp = obs.get("lens_patentes")
    if lp is not None and len(lp):
        m1, m2, m3 = st.columns(3)
        m1.metric("Produções citadas por patentes", br(len(lp)))
        m2.metric("Citações em patentes (total)", br(int(lp["n_patentes"].sum())))
        m3.metric("Citações por patente (média)",
                  br(lp["n_patentes"].mean(), 1) if len(lp) else "—")
        top = lp.sort_values("n_patentes", ascending=False).head(12).copy()
        top["rotulo"] = top["title"].str.slice(0, 60)
        st.plotly_chart(barra_h(top, "rotulo", "n_patentes", h=440, cor=T["secondary"]),
                        width="stretch")
        st.caption("Patentes (mundiais) que citam produções da UFTM — proxy de impacto em "
                   "inovação e transferência de tecnologia. Fonte: The Lens (base aberta que "
                   "liga pesquisas a patentes).")
    else:
        st.info(
            "**Patentes ainda não ativadas.** Esta seção acende com dados reais quando um "
            "**token gratuito do The Lens** estiver configurado. Passo a passo:\n"
            "1. Crie conta em **lens.org** e solicite acesso à **Scholarly API** (uso acadêmico, gratuito).\n"
            "2. Guarde o token como segredo **`LENS_TOKEN`** no GitHub (Settings → Secrets → Actions) "
            "e/ou rode localmente: `LENS_TOKEN=seu_token python fetch_lens.py`.\n"
            "3. Na próxima atualização, patentes que citam a pesquisa da UFTM aparecem aqui.")
    st.caption("Políticas públicas (Overton) e atenção online (Altmetric) exigem assinatura paga "
               "e ficam como evolução futura. Declaramos também que algumas medidas de bases "
               "pagas (como número de visualizações) não têm equivalente em dados abertos.")


def render_ciencia_aberta():
    cabecalho("Ciência Aberta", "Quanto da pesquisa da UFTM qualquer pessoa pode ler de graça")
    if "oa_status" not in fraw.columns:
        st.info("Re-colete os dados (fetch_uftm_ods.py) para habilitar esta aba.")
        return
    st.caption("**Como ler** · *Acesso aberto* é a pesquisa que você lê sem pagar. **Diamante** = "
               "grátis para quem lê e para quem publica; **Verde** = cópia gratuita num "
               "repositório; **Ouro** = aberta, mas a universidade paga uma taxa (APC). "
               "**DOAJ** é um selo de revista aberta confiável.")
    oa_pt = {"diamond": "Diamante (grátis autor e leitor)", "gold": "Ouro (com APC)",
             "green": "Verde (repositório)", "hybrid": "Híbrido", "bronze": "Bronze",
             "closed": "Fechado"}
    oa_cor = {"diamond": T["primary"], "gold": T["accent"], "green": T["green_mid"],
              "hybrid": "#2563EB", "bronze": "#B5733A", "closed": T["faint"]}

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
    apc_ano = fraw.groupby("year")["apc_usd"].sum().reset_index()
    fig = go.Figure(go.Bar(x=apc_ano["year"], y=apc_ano["apc_usd"], marker_color=T["accent"],
                           hovertemplate="%{x}: US$ %{y:,.0f}<extra></extra>"))
    st.plotly_chart(fig_layout(fig, 300), width="stretch")
    st.caption("APC = Article Processing Charge reportado ao OpenAlex — estimativa do gasto com "
               "publicação em acesso aberto pago (não inclui acordos transformativos/descontos).")


def render_benchmarking():
    cabecalho("Comparação", "A UFTM ao lado das 11 universidades federais de Minas Gerais")
    bi = obs.get("bench_instituicoes")
    if bi is None:
        st.info("Rode `python fetch_observatorio.py` para gerar os dados de benchmarking.")
        return
    st.caption("**Como ler** · Cada barra é uma universidade; a **UFTM aparece em verde** e as "
               "demais em verde-claro. Escolha o indicador para comparar (quantidade de "
               "pesquisas, impacto, acesso aberto, etc.).")
    metricas = {
        "Produções": ("works", ",.0f"), "Citações": ("citacoes", ",.0f"),
        "Citações por trabalho": ("cit_por_trabalho", ",.2f"),
        "Impacto médio (citações por trabalho recente)": ("mean_citedness", ",.2f"),
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
    ref = ("  Referência: no mundo, por definição ~10% das pesquisas estão no top 10% e ~1% no "
           "top 1% — acima disso é estar acima da média mundial."
           if col in ("top10_share", "top1_share") else "")
    st.caption(nota + ref)

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
    cabecalho("Colaboração", "Com quem a UFTM pesquisa — no Brasil e no mundo")
    st.caption("**Como ler** · *Internacional* = pesquisa feita com pelo menos um país estrangeiro; "
               "*Nacional* = com outra instituição brasileira; *Institucional* = só UFTM. A **rede** "
               "no fim mostra quais pesquisadores da UFTM trabalham juntos (cada ponto é um "
               "pesquisador; as linhas, parcerias).")
    if "is_international" in fraw.columns and len(fraw):
        intl = fraw["is_international"].mean()
        nac = (~fraw["is_international"] & (fraw["n_institutions"] > 1)).mean()
        inst = (fraw["n_institutions"] <= 1).mean()
        c1, c2, c3 = st.columns(3)
        c1.metric("Internacional", f"{intl:.0%}", help="≥ 2 países distintos.")
        c2.metric("Nacional", f"{nac:.0%}", help="Só Brasil, ≥ 2 instituições.")
        c3.metric("Institucional", f"{inst:.0%}", help="Apenas UFTM.")

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

    nos = obs.get("rede_autores_nos")
    arestas = obs.get("rede_autores_arestas")
    if nos is not None and arestas is not None and len(nos):
        st.subheader("Rede de coautoria dos pesquisadores da UFTM")
        m1, m2, m3 = st.columns(3)
        m1.metric("Pesquisadores na rede", br(len(nos)))
        m2.metric("Conexões", br(len(arestas)))
        m3.metric("Grupos (comunidades)", br(nos["comunidade"].nunique()))
        st.plotly_chart(grafo_coautoria(nos, arestas), width="stretch")
        st.caption("Cada nó é um pesquisador da UFTM (tamanho = nº de produções); ligações = "
                   "coautorias. Cores = grupos de colaboração (comunidades); rótulos = os 8 "
                   "que mais conectam grupos diferentes. Passe o mouse para ver nomes.")


def render_ods():
    cabecalho("ODS", "Como a pesquisa da UFTM se conecta à Agenda 2030 da ONU")
    st.caption("**Como ler** · Os **ODS** são os 17 Objetivos de Desenvolvimento Sustentável da "
               "ONU (saúde, educação, igualdade, clima...). Mostramos com quais a pesquisa da "
               "UFTM mais se relaciona. A associação é uma **estimativa por inteligência "
               "artificial** do OpenAlex — uma aproximação, não uma declaração dos autores.")
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
        cores = [T["primary"], T["accent"], "#2563EB", "#7C3AED", "#DB2777", "#0891B2"]
        for i, (nome, gg) in enumerate(ev.groupby("ODS")):
            fig.add_trace(go.Scatter(x=gg["year"], y=gg["n"], mode="lines+markers",
                                     name=nome, line=dict(color=cores[i % len(cores)], width=2.5)))
        fig = fig_layout(fig, 360)
        fig.update_layout(showlegend=True, legend=dict(font=dict(color=T["text"], size=10)))
        st.plotly_chart(fig, width="stretch")


def render_temas():
    cabecalho("Temas", "As áreas e assuntos em que a UFTM mais pesquisa")
    st.caption("**Como ler** · As grandes áreas do conhecimento (Medicina, Ciências Sociais...) e "
               "os assuntos específicos mais frequentes nas pesquisas da UFTM.")
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
    cabecalho("Pesquisadores", "Os nomes por trás da pesquisa da UFTM")
    st.caption("**Como ler** · Pesquisadores com vínculo na UFTM, ordenados por **citações** "
               "(quantas vezes seus trabalhos foram usados por outros). O **índice h** resume "
               "produção e impacto: um h de 30 significa 30 trabalhos citados ao menos 30 vezes "
               "cada. O **i10** é quantos trabalhos têm pelo menos 10 citações. **ORCID** é o "
               "identificador único do pesquisador.")
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
    cabecalho("Onde publicamos", "As revistas científicas que mais publicam pesquisa da UFTM")
    st.caption("**Como ler** · Cada barra é uma revista científica (periódico); o tamanho mostra "
               "quantas pesquisas da UFTM saíram nela no período.")
    top = (fraw[fraw["source"].notna()]["source"].value_counts().head(20)
           .rename_axis("Periódico").reset_index(name="n"))
    st.plotly_chart(barra_h(top, "Periódico", "n", h=540), width="stretch")


def render_qualidade():
    cabecalho("Qualidade das revistas", "Em que nível estão as revistas onde a UFTM publica")
    sq = obs.get("scimago_quartis")
    if sq is None or "issn_l" not in fraw.columns:
        st.info("Rode `python fetch_scimago.py` para baixar os quartis Scimago.")
        return
    st.caption("**Como ler** · As revistas do mundo são divididas em 4 níveis por área, do mais "
               "ao menos influente: **Q1** (as 25% melhores), Q2, Q3 e Q4. Quanto mais pesquisa "
               "em Q1, mais a UFTM publica nas revistas de ponta. A classificação vem do "
               "**Scimago/SJR**, um ranking mundial e gratuito de revistas científicas.")
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
                   "periódicos fora dessas bases internacionais (ex.: muitos periódicos nacionais).")

    qcor = {"Q1": T["primary"], "Q2": "#2563EB", "Q3": T["accent"], "Q4": T["faint"]}
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
    st.caption("Usamos o melhor quartil de cada revista no ranking Scimago (edição 2025), "
               "ligando os dados pelo código de cada revista (ISSN). Revistas fora dessas bases "
               "internacionais (muitas nacionais) não recebem quartil.")


def render_explorar():
    cabecalho("Explorar", "Procure qualquer pesquisa da UFTM pelo título")
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


def render_transparencia():
    cabecalho("Transparência", "De onde vêm os dados e o que cada termo significa")

    st.subheader("Entenda os termos")
    glossario = {
        "OpenAlex": "Base de dados científica mundial, aberta e gratuita, que reúne informações "
        "de publicações, autores e instituições. É a fonte principal deste painel.",
        "Produção / produção científica": "Um trabalho de pesquisa publicado — artigo de "
        "revista, livro, capítulo, tese, dado etc.",
        "Citação": "Quando outro estudo usa e referencia uma pesquisa. Mais citações = a "
        "pesquisa foi mais aproveitada por outros cientistas.",
        "FWCI (impacto científico)": "Compara as citações de uma pesquisa com a média mundial "
        "da mesma área e ano. 1,0 = média do mundo; 2,0 = o dobro da média; 0,5 = metade.",
        "Top 10% / Top 1% mundial": "A fatia de pesquisas que está entre as 10% (ou 1%) mais "
        "citadas do planeta na sua área. É um sinal de pesquisa de ponta.",
        "Acesso aberto": "Pesquisa que qualquer pessoa pode ler de graça, sem assinatura.",
        "Tipos de acesso aberto": "**Diamante**: grátis para ler e para publicar. **Verde**: "
        "cópia gratuita guardada num repositório (biblioteca digital). **Ouro**: aberta, mas a "
        "universidade paga uma taxa (APC). **Bronze**: de graça para ler, mas sem licença livre. "
        "**Híbrido**: revista paga em que só este artigo foi aberto. **Fechado**: só com "
        "assinatura.",
        "Repositório": "Biblioteca digital onde uma cópia gratuita da pesquisa fica guardada e "
        "disponível para todos (ex.: o repositório institucional da UFTM).",
        "APC": "Article Processing Charge — taxa que algumas revistas cobram para deixar a "
        "pesquisa aberta. Mostramos a estimativa desse custo.",
        "DOAJ": "Diretório de revistas de acesso aberto confiáveis — um selo de qualidade.",
        "Scimago / SJR": "Scimago é um ranking mundial e gratuito de revistas científicas. O "
        "SJR (SCImago Journal Rank) é a nota de prestígio de cada revista — leva em conta "
        "quantas vezes ela é citada e o peso de quem a cita. É o que define os quartis.",
        "Quartil (Q1–Q4)": "Nível da revista na sua área, segundo o Scimago/SJR: Q1 são as 25% "
        "melhores, depois Q2, Q3 e Q4 (as menos influentes).",
        "ODS": "Os 17 Objetivos de Desenvolvimento Sustentável da ONU (Agenda 2030).",
        "Índice h": "Resume produção e impacto de um pesquisador: h = 30 significa 30 trabalhos "
        "citados pelo menos 30 vezes cada.",
        "Índice i10": "Número de trabalhos do pesquisador com pelo menos 10 citações cada.",
        "Colaboração internacional": "Pesquisa feita em parceria com pelo menos um país "
        "estrangeiro.",
        "ROR": "Research Organization Registry — um código único e gratuito que identifica cada "
        "instituição no mundo. O da UFTM é 01av3m334.",
        "ISSN": "Código que identifica unicamente uma revista científica — como um RG da revista.",
        "DOI": "Endereço permanente de uma publicação na internet: um link que nunca muda e "
        "sempre leva ao trabalho.",
        "ORCID": "Identificador único e gratuito de cada pesquisador, que evita confundir "
        "pessoas com nomes parecidos.",
    }
    for termo, definicao in glossario.items():
        st.markdown(f"**{termo}** — {definicao}")

    st.divider()
    st.subheader("Metodologia — como o painel é feito")
    st.markdown(
        f"**Em resumo:** o painel reúne **{br(len(raw))} produções** da UFTM registradas no "
        f"OpenAlex (anos {ymin}–{ymax}), compara com **11 universidades federais de Minas "
        f"Gerais** e é atualizado automaticamente todo mês. Todo o código é aberto.")

    st.markdown("**1. Fonte principal — OpenAlex**")
    st.markdown(
        "- Os dados vêm do [OpenAlex](https://openalex.org), base científica mundial, aberta e "
        "gratuita, que cataloga publicações, autores, instituições e citações.\n"
        "- A produção da UFTM é identificada pelo seu código institucional único "
        "(**ROR `01av3m334`**): entram todos os trabalhos com pelo menos um autor vinculado à "
        "universidade.")

    st.markdown("**2. Fontes complementares**")
    st.markdown(
        "- **Scimago (SJR):** ranking mundial e gratuito de revistas — define os quartis (Q1–Q4) "
        "da aba *Qualidade das revistas*, ligado pelo código (ISSN) de cada revista.\n"
        "- **The Lens:** base aberta que liga pesquisas a patentes — alimenta as patentes da aba "
        "*Impacto Social* (quando há credencial de acesso).")

    st.markdown("**3. Como cada indicador é calculado**")
    st.markdown(
        "- **Produções:** número de trabalhos no período.\n"
        "- **Citações:** soma das vezes que esses trabalhos foram citados por outros.\n"
        "- **Impacto científico (FWCI):** média do índice que o OpenAlex calcula por trabalho, "
        "comparando as citações com a média mundial da mesma área e ano (1,0 = média do mundo).\n"
        "- **Top 10% / Top 1%:** % de trabalhos que o OpenAlex marca entre os mais citados do "
        "mundo na sua área.\n"
        "- **Acesso aberto:** classificação de acesso do OpenAlex (diamante, verde, ouro, "
        "bronze, híbrido, fechado).\n"
        "- **Comparação entre universidades:** dados institucionais do OpenAlex para as 11 "
        "federais de MG.\n"
        "- **Qualidade das revistas:** quartil Scimago de cada revista, ligado pelo ISSN.\n"
        "- **Colaboração:** a partir dos países e instituições dos coautores de cada trabalho.\n"
        "- **Rede de coautoria:** construída com a biblioteca aberta *networkx* (quem publica "
        "com quem), destacando grupos e os pesquisadores que mais conectam.\n"
        "- **ODS:** classificação automática por inteligência artificial do OpenAlex (modelo "
        "Aurora), contada quando a confiança é de pelo menos 0,4 (escala de 0 a 1).\n"
        "- **Patentes:** trabalhos da UFTM citados por patentes no mundo, segundo o The Lens.")

    st.markdown("**4. Atualização e reprodutibilidade**")
    st.markdown(
        "- A coleta roda **automaticamente todo mês**, sem intervenção manual; o período "
        "aparece no topo de cada página e pode ser ajustado na barra lateral.\n"
        "- Todo o código que coleta e monta o painel é **aberto e auditável** em "
        "[github.com/ana-mat-br/painel-daad](https://github.com/ana-mat-br/painel-daad).")

    st.markdown("**5. Limites e cuidados (honestidade dos dados)**")
    st.markdown(
        "- A associação aos **ODS** é uma **estimativa por inteligência artificial**, não uma "
        "classificação declarada pelos autores — leia como aproximação.\n"
        "- O **FWCI** dos 2 anos mais recentes ainda é provisório (pesquisas novas seguem "
        "recebendo citações).\n"
        "- A cobertura depende do que está indexado no OpenAlex; **revistas não indexadas** "
        "(muitas nacionais) podem não receber quartil ou impacto.\n"
        "- Indicadores de impacto **não são comparáveis entre bases diferentes** — o OpenAlex e "
        "as bases científicas pagas contam de formas distintas.")


PAGINAS = {
    "Visão Geral": render_visao_geral, "Impacto científico": render_excelencia,
    "Comparação": render_benchmarking, "Ciência Aberta": render_ciencia_aberta,
    "Impacto Social": render_impacto_social, "ODS": render_ods,
    "Pesquisadores": render_pesquisadores, "Colaboração": render_colaboracao,
    "Temas": render_temas, "Onde publicamos": render_periodicos,
    "Qualidade das revistas": render_qualidade, "Explorar": render_explorar,
    "Transparência": render_transparencia,
}
_forcar = os.environ.get("OBS_FORCE_PAGE")  # seam de teste (sem efeito em produção)
PAGINAS.get(_forcar or pagina or "Visão Geral", render_visao_geral)()

# ----------------------------------------------------------------- rodapé
st.divider()
if pagina != "Transparência":
    _f1, _f2, _f3 = st.columns([1, 2, 1])
    with _f2:
        if st.button("Como calculamos cada número?  →  Transparência", key="ir_transp",
                     width="stretch"):
            st.session_state["ir_para"] = "Transparência"
            st.rerun()
st.markdown(f"<div style='text-align:center;color:{T['muted']};font-size:.85rem'>"
            f"<b style='color:{T['primary']}'>Painel DAAD</b> · Diretoria de Avaliação e Análise "
            f"de Dados · PROPPG/UFTM · dados abertos do OpenAlex (ROR 01av3m334)</div>",
            unsafe_allow_html=True)
