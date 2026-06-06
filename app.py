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


def _data_coleta():
    f = DATA / "coletado_em.txt"
    if f.exists():
        try:
            a, m, d = f.read_text(encoding="utf-8").strip().split("-")
            return f"{d}/{m}/{a}"
        except Exception:
            return None
    return None


DATA_COLETA = _data_coleta()

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

# Subáreas do OpenAlex (EN) -> PT, para rotular os grupos da rede de coautoria
SUBAREA_PT = {
    "Epidemiology": "Epidemiologia", "General Health Professions": "Profissões da Saúde",
    "Materials Chemistry": "Química de Materiais", "Neurology": "Neurologia",
    "Physiology": "Fisiologia", "Education": "Educação",
    "Clinical Psychology": "Psicologia Clínica", "Infectious Diseases": "Doenças Infecciosas",
    "Immunology and Allergy": "Imunologia e Alergia", "Immunology": "Imunologia",
    "Cardiology and Cardiovascular Medicine": "Cardiologia", "Oncology": "Oncologia",
    "Public Health, Environmental and Occupational Health": "Saúde Pública",
    "Surgery": "Cirurgia", "Obstetrics and Gynecology": "Obstetrícia e Ginecologia",
    "Pediatrics, Perinatology and Child Health": "Pediatria", "Microbiology": "Microbiologia",
    "Parasitology": "Parasitologia", "Pharmacology": "Farmacologia",
    "Pharmacology (medical)": "Farmacologia", "Nursing": "Enfermagem", "Dentistry": "Odontologia",
    "Nutrition and Dietetics": "Nutrição", "Psychiatry and Mental Health": "Psiquiatria e Saúde Mental",
    "Genetics": "Genética", "Cell Biology": "Biologia Celular", "Ecology": "Ecologia",
    "Plant Science": "Botânica", "Endocrinology": "Endocrinologia", "Pathology": "Patologia",
    "Radiology, Nuclear Medicine and Imaging": "Radiologia e Imagem",
    "Physical Therapy, Sports Therapy and Rehabilitation": "Fisioterapia e Reabilitação",
    "Sociology and Political Science": "Sociologia e Ciência Política",
    "Social Sciences": "Ciências Sociais", "Health Policy": "Políticas de Saúde",
    "Biotechnology": "Biotecnologia", "Food Science": "Ciência de Alimentos",
    "General Medicine": "Medicina Geral", "Anatomy": "Anatomia", "Gastroenterology": "Gastroenterologia",
    "Geriatrics and Gerontology": "Geriatria e Gerontologia", "Veterinary": "Veterinária",
    "Veterinary (miscellaneous)": "Veterinária", "Biochemistry": "Bioquímica",
    "Molecular Biology": "Biologia Molecular", "Linguistics and Language": "Linguística",
    "History": "História", "Philosophy": "Filosofia", "Law": "Direito",
    "Condensed Matter Physics": "Física da Matéria Condensada", "Diversos": "Diversos",
}

# Tópicos do OpenAlex (EN) -> PT — mais específico que a subárea, distingue melhor os grupos
TOPICO_PT = {
    "Trypanosoma species research and implications": "Doença de Chagas",
    "Health, Nursing, Elderly Care": "Enfermagem e Saúde do Idoso",
    "Cervical Cancer and HPV Research": "Câncer Cervical e HPV",
    "Metal complexes synthesis and properties": "Síntese de Complexos Metálicos",
    "Stroke Rehabilitation and Recovery": "Reabilitação de AVC",
    "Physical Activity and Health": "Atividade Física e Saúde",
    "Science and Education Research": "Ensino de Ciências",
    "Psychology and Mental Health": "Psicologia e Saúde Mental",
    "Physical Education and Sports Studies": "Educação Física e Esportes",
}

# Códigos de idioma (ISO 639-1) -> PT
IDIOMA_PT = {
    "en": "Inglês", "pt": "Português", "es": "Espanhol", "fr": "Francês", "de": "Alemão",
    "it": "Italiano", "ru": "Russo", "ca": "Catalão", "lv": "Letão", "hr": "Croata",
    "eo": "Esperanto", "gu": "Guzerate", "nl": "Holandês", "ja": "Japonês", "zh": "Chinês",
    "la": "Latim", "pl": "Polonês", "uk": "Ucraniano",
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
  /* sidebar mais compacto: menos folga entre slider, divisor e menu */
  [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {{ gap: .5rem; }}
  [data-testid="stSidebar"] hr {{ margin: .35rem 0; }}
  /* slider do Período: rótulo editorial e sem os números mín/máx (limpa o box) */
  [data-testid="stSidebar"] [data-testid="stSlider"] label {{ text-transform: uppercase;
    letter-spacing: .08em; font-size: .68rem; color: {T['muted']}; font-weight: 600; }}
  [data-testid="stSidebar"] [data-testid="stSliderTickBar"],
  [data-testid="stSidebar"] [data-testid="stSliderTickBarMin"],
  [data-testid="stSidebar"] [data-testid="stSliderTickBarMax"] {{ display: none; }}
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
    nomes = ["bench_instituicoes", "bench_por_ano",
             "bench_porte_instituicoes", "bench_porte_por_ano", "colab_instituicoes",
             "colab_paises", "temas_campo", "temas_topicos", "top_autores",
             "scimago_quartis", "rede_autores_nos", "rede_autores_arestas",
             "lens_patentes", "ods_por_instituicao"]
    return {n: (pd.read_csv(DATA / f"{n}.csv") if (DATA / f"{n}.csv").exists() else None)
            for n in nomes}


_sig = _data_sig()
raw, sdg = load(_sig)
obs = load_obs(_sig)


# ----------------------------------------------------------------- helpers
def br(n, dec=0):
    s = f"{n:,.{dec}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def pct(x, dec=0):
    """Percentual no padrão brasileiro (vírgula decimal)."""
    return br(x * 100, dec) + "%"


def fig_layout(fig, h=420):
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=T["text"], family="Inter"), height=h,
        margin=dict(l=8, r=24, t=24, b=8), showlegend=False, separators=",.",
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
              "#65A30D", "#CA8A04", "#DC2626", "#475569", "#0D9488", "#9D174D"]


def rotular_grupos(nos):
    """Rótulo de cada comunidade: tema dominante traduzido (tópico > subárea); quando o tema
    repete, distingue pelo pesquisador central (hub). Retorna DataFrame ordenado por tamanho."""
    tem_topico = "topico" in nos.columns
    tem_grupo = "grupo" in nos.columns
    ordem = list(nos["comunidade"].value_counts().index)  # maior primeiro

    def _base(c):
        sub = nos[nos["comunidade"] == c]
        topico = str(sub["topico"].iloc[0]) if tem_topico else ""
        if topico in TOPICO_PT:                       # tópico específico traduzido (preferido)
            return TOPICO_PT[topico]
        if tem_grupo:                                 # senão, subárea traduzida
            g = str(sub["grupo"].iloc[0])
            return SUBAREA_PT.get(g, g)
        return f"Grupo {int(c) + 1}"

    bases = {c: _base(c) for c in ordem}
    cont = {}
    for b in bases.values():
        cont[b] = cont.get(b, 0) + 1
    repetidos = {b for b, n in cont.items() if n > 1}
    linhas = []
    for c in ordem:
        sub = nos[nos["comunidade"] == c]
        hub = sub.sort_values("betw", ascending=False).iloc[0]["nome"]
        tema = bases[c]
        if tema in repetidos:                         # mesmo tema em +1 grupo -> usa o hub
            tema = f"{tema} · {hub.split()[-1]}"
        linhas.append({"comunidade": c, "tema": tema, "tamanho": len(sub), "hub": hub,
                       "cor": PALETA_COM[int(c) % len(PALETA_COM)]})
    return pd.DataFrame(linhas)


def grafo_coautoria(nos, arestas, h=520):
    """Rede de coautoria: nós coloridos por comunidade, dimensionados por produção. Sem legenda
    interna (a legenda é a tabela de grupos, legível em qualquer tela); arrastar e zoom ativos."""
    pos = {r.id: (r.x, r.y) for r in nos.itertuples()}
    ex, ey = [], []
    for e in arestas.itertuples():
        if e.origem in pos and e.destino in pos:
            x0, y0 = pos[e.origem]
            x1, y1 = pos[e.destino]
            ex += [x0, x1, None]
            ey += [y0, y1, None]
    edge = go.Scatter(x=ex, y=ey, mode="lines", hoverinfo="none", showlegend=False,
                      line=dict(color=T["border"], width=0.6))
    wmax = max(nos["works"].max(), 1)
    grupos = rotular_grupos(nos)
    cor_de = dict(zip(grupos["comunidade"], grupos["cor"]))
    tema_de = dict(zip(grupos["comunidade"], grupos["tema"]))
    traces = [edge]
    for c in grupos["comunidade"]:
        sub = nos[nos["comunidade"] == c]
        traces.append(go.Scatter(
            x=sub["x"], y=sub["y"], mode="markers", hoverinfo="text", showlegend=False,
            text=[f"<b>{tema_de[c]}</b><br>{r.nome}<br>{r.works} produções · "
                  f"{int(r.grau)} coautorias na rede" for r in sub.itertuples()],
            marker=dict(size=[7 + (w / wmax) * 24 for w in sub["works"]],
                        color=cor_de[c], line=dict(color=T["bg"], width=0.6), opacity=0.9)))
    centrais = nos.sort_values("betw", ascending=False).head(8)
    traces.append(go.Scatter(
        x=centrais["x"], y=centrais["y"], mode="text", showlegend=False,
        text=[n.split()[-1] for n in centrais["nome"]], hoverinfo="none",
        textposition="top center", textfont=dict(color=T["text"], size=10)))
    fig = go.Figure(traces)
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      height=h, margin=dict(l=0, r=0, t=0, b=0), separators=",.",
                      showlegend=False, dragmode="pan",
                      xaxis=dict(visible=False), yaxis=dict(visible=False),
                      hoverlabel=dict(bgcolor=T["surface"], font_color=T["text"]))
    return fig


def aplica_filtros(faixa):
    return raw[raw["year"].between(*faixa)], sdg[sdg["year"].between(*faixa)]


TIPOS = sorted(raw["type"].dropna().unique())
TIPOS_PT = {
    "article": "Artigo", "book": "Livro", "book-chapter": "Capítulo de livro",
    "dataset": "Conjunto de dados", "dissertation": "Tese / dissertação",
    "editorial": "Editorial", "erratum": "Errata", "letter": "Carta", "other": "Outro",
    "paratext": "Paratexto", "peer-review": "Parecer (revisão por pares)",
    "preprint": "Preprint", "report": "Relatório", "review": "Revisão",
}


def tipo_pt(t):
    return TIPOS_PT.get(t, t)


def filtro_tipo(df, key, com_oa=False):
    """Filtros locais discretos: tipo de produção (traduzido) e, opcionalmente, acesso aberto."""
    if com_oa:
        c1, c2 = st.columns([2, 1.3], gap="small")
        with c1:
            escolha = st.selectbox("Tipo de produção", ["Todos os tipos"] + TIPOS,
                                   format_func=lambda t: "Todos os tipos" if t == "Todos os tipos"
                                   else tipo_pt(t), key=key)
        with c2:
            st.markdown("<div style='height:1.8rem'></div>", unsafe_allow_html=True)
            so_oa = st.toggle("Apenas acesso aberto", key=key + "_oa")
    else:
        escolha = st.selectbox("Tipo de produção", ["Todos os tipos"] + TIPOS,
                               format_func=lambda t: "Todos os tipos" if t == "Todos os tipos"
                               else tipo_pt(t), key=key)
        so_oa = False
    out = df if escolha == "Todos os tipos" else df[df["type"] == escolha]
    if so_oa:
        out = out[out["is_oa"] == True]  # noqa: E712
    return out


# ----------------------------------------------------------------- sidebar
with st.sidebar:
    st.markdown(
        f"<div style='font-family:{SERIF};font-size:2.15rem;font-weight:700;line-height:1;"
        f"margin:.15rem 0 .3rem'><span style='color:{T['text']}'>Painel</span> "
        f"<span style='color:{T['primary']}'>DAAD</span></div>"
        f"<p style='color:{T['muted']};font-size:.62rem;line-height:1.6;margin:0 0 1.3rem;"
        f"letter-spacing:.02em'>"
        f"Diretoria de Avaliação e Análise de Dados<br>PROPPG · UFTM</p>",
        unsafe_allow_html=True)

    anos = raw["year"].dropna()
    ymin, ymax = int(anos.min()), int(anos.max())
    faixa = st.slider("Período", ymin, ymax, (max(ymin, ymax - 9), ymax))

    st.divider()
    NAV = ["Visão Geral", "Impacto científico", "Comparação", "Ciência Aberta", "Impacto Social",
           "Financiamento", "Patentes", "Pesquisadores", "Colaboração", "Temas",
           "Onde publicamos", "Qualidade das revistas", "Publicações por língua", "Explorar",
           "Transparência"]
    ICONS = ["speedometer2", "award", "bar-chart-line", "unlock", "globe-americas",
             "cash-coin", "lightbulb", "person-badge", "diagram-3", "tags",
             "journal-text", "patch-check", "translate", "search", "info-circle"]
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

fraw, fsdg = aplica_filtros(faixa)


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
        f"Quanto a UFTM pesquisa, com que impacto e quanto desse trabalho está aberto a todos. "
        f"Dados do <b style='color:{T['text']}'>OpenAlex</b>, atualizados todo mês.</div>",
        unsafe_allow_html=True)
    fr = filtro_tipo(fraw, "tipo_vg", com_oa=True)
    fwci_med = fr["fwci"].dropna().mean() if "fwci" in fr else None
    top10 = fr["top10"].mean() if "top10" in fr else None
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Produções", br(len(fr)))
    c2.metric("Citações", br(int(fr["cited_by"].sum())))
    c3.metric("FWCI médio", br(fwci_med, 2) if fwci_med else "—")
    c4.metric("Top 10%", f"{top10:.0%}" if top10 is not None else "—",
              help="Parte das pesquisas que está entre as 10% mais citadas do mundo na sua área.")
    c5.metric("Acesso aberto", f"{fr['is_oa'].mean():.0%}" if len(fr) else "—")
    st.caption(
        "**Como ler estes números** · **Produções**: pesquisas publicadas no período · "
        "**Citações**: vezes que essas pesquisas foram usadas por outros estudos · "
        "**FWCI**: impacto comparado à média mundial da área (1,0 = média do mundo; acima de 1 "
        "é acima da média) · **Top 10%**: fatia das pesquisas entre as 10% mais citadas do "
        "planeta · **Acesso aberto**: parte que qualquer pessoa pode ler de graça.")
    if st.button("Por que nem toda a produção aparece? Entenda a cobertura dos dados  →",
                 type="tertiary", key="cobertura_vg"):
        st.session_state["ir_para"] = "Transparência"
        st.rerun()

    st.subheader("Produção por ano")
    por_ano = fr.groupby("year").size().reset_index(name="n")
    fig = go.Figure(go.Bar(x=por_ano["year"], y=por_ano["n"], marker_color=T["primary"],
                           hovertemplate="%{x}: %{y}<extra></extra>"))
    st.plotly_chart(fig_layout(fig, 320), width="stretch")

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Por tipo de produção")
        tp = fraw["type"].value_counts().reset_index()  # sempre todos os tipos (visão do mix)
        tp.columns = ["tipo", "n"]
        tp["tipo"] = tp["tipo"].map(tipo_pt)
        st.plotly_chart(barra_h(tp.head(10), "tipo", "n", h=360), width="stretch")
    with c2:
        st.subheader("Citações por ano")
        cit = fr.groupby("year")["cited_by"].sum().reset_index()
        fig = go.Figure(go.Scatter(x=cit["year"], y=cit["cited_by"], mode="lines+markers",
                                   line=dict(color=T["accent"], width=3),
                                   fill="tozeroy", fillcolor="rgba(232,119,34,.08)",
                                   hovertemplate="%{x}: %{y:,.0f} citações<extra></extra>"))
        st.plotly_chart(fig_layout(fig, 360), width="stretch")
        st.caption("Citações acumuladas pelas pesquisas publicadas em cada ano. Os anos mais "
                   "recentes tendem a ser menores — ainda estão recebendo citações.")


def render_excelencia():
    cabecalho("Impacto científico", "O quanto a pesquisa da UFTM é reconhecida no mundo")
    if "fwci" not in fraw.columns:
        st.info("Re-colete os dados (fetch_uftm_ods.py) para habilitar FWCI e percentis.")
        return
    st.markdown(
        f"<div style='border-left:2px solid {T['primary']};padding:.15rem 0 .15rem 1.1rem;"
        f"margin:.1rem 0 1.1rem;color:{T['text_soft']};font-size:1.02rem;line-height:1.6;"
        f"max-width:840px'>O <b style='color:{T['text']}'>FWCI (Field-Weighted Citation "
        f"Impact)</b> é o indicador-padrão de impacto <b>normalizado por área</b>, definido pelo "
        f"<b>Snowball Metrics</b> (consórcio internacional de universidades) e adotado pela "
        f"Scopus/SciVal. Compara as citações de uma pesquisa com a média mundial de pesquisas "
        f"semelhantes: <b style='color:{T['text']}'>1,0 = a média do mundo</b>; acima de 1, "
        f"acima da média. A fórmula completa está na aba Transparência.</div>",
        unsafe_allow_html=True)
    excluir = st.checkbox("Excluir os 2 anos mais recentes (a janela de citações deles ainda "
                          "está incompleta)", value=False)
    base = fraw[fraw["year"] <= faixa[1] - 2] if excluir else fraw
    fw = base["fwci"].dropna()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("FWCI médio", br(fw.mean(), 2) if len(fw) else "—",
              help="1,0 = média mundial do campo. Acima de 1 = acima da média global.")
    c2.metric("% com FWCI > 1", f"{(fw > 1).mean():.0%}" if len(fw) else "—")
    c3.metric("No top 10% mundial", pct(base["top10"].mean(), 1) if len(base) else "—")
    c4.metric("No top 1% mundial", pct(base["top1"].mean(), 1) if len(base) else "—")
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
        if len(s):
            ya = int(s["year"].max())          # marca os 2 anos mais recentes como provisórios
            fig.add_vrect(x0=ya - 1.5, x1=ya + 0.5, fillcolor=T["muted"], opacity=0.08,
                          line_width=0, annotation_text="provisório",
                          annotation_position="top left",
                          annotation_font=dict(color=T["muted"], size=10))
        st.plotly_chart(fig, width="stretch")
        st.caption("Os 2 anos mais recentes são **provisórios**: pesquisas novas quase não foram "
                   "citadas ainda, e o FWCI fica instável (poucas citações geram valores enormes). "
                   "Use o filtro acima para excluí-los.")
    with c2:
        st.subheader("FWCI médio por grande área")
        s = (base.dropna(subset=["fwci", "field"]).groupby("field")
             .agg(fwci=("fwci", "mean"), n=("id", "count")).reset_index())
        s = s[s["n"] >= 20].sort_values("fwci", ascending=False).head(12)
        s["rotulo"] = s.apply(lambda r: f"{r['field']} ({br(r['n'])})", axis=1)
        st.plotly_chart(barra_h(s, "rotulo", "fwci", h=380, fmt=".2f"), width="stretch")
        st.caption("Número entre parênteses = nº de trabalhos (só áreas com ≥ 20). Médias altas "
                   "em áreas pequenas vêm de poucos artigos muito citados — inclusive "
                   "megacolaborações de centenas de autores (ex.: física de partículas).")

    st.subheader("Trabalhos por área — o que está por trás de cada número")
    sel = st.selectbox("Área", s["field"].tolist(), key="area_trabalhos")
    wl = base[base["field"] == sel].sort_values("fwci", ascending=False).copy()
    trunc = (wl["autores_truncados"] if "autores_truncados" in wl.columns
             else pd.Series(False, index=wl.index))
    show = wl[["title", "year", "fwci", "cited_by"]].copy()
    if "autores_uftm" in wl.columns:
        show["autores"] = [
            "megacolaboração (100+ autores)" if t
            else (", ".join(map(str, L)) if hasattr(L, "__len__") and len(L) else "—")
            for L, t in zip(wl["autores_uftm"], trunc)]
    if "n_autores" in wl.columns:
        show["n_autores"] = [f"{int(n)}+" if t else br(int(n))
                             for n, t in zip(wl["n_autores"], trunc)]
    show = show.rename(columns={"title": "Título", "year": "Ano", "fwci": "FWCI",
                                "cited_by": "Citações", "autores": "Autores UFTM",
                                "n_autores": "Nº autores"})
    show["Título"] = show["Título"].astype(str).str.replace(r"<[^>]+>", "", regex=True)
    st.dataframe(show, hide_index=True, width="stretch", height=420,
                 column_config={"FWCI": st.column_config.NumberColumn(format="%.2f")})
    st.caption("Ordenado por FWCI. *Nº autores* alto (centenas) indica **megacolaboração** — a "
               "UFTM é um entre muitos coautores, mas o FWCI do artigo entra inteiro na média da "
               "área. Por isso a mediana costuma contar uma história diferente da média.")


def render_patentes():
    cabecalho("Patentes", "Quando a pesquisa da UFTM vira inovação")
    st.caption("**Como ler** · Mostra quantas **patentes no mundo citam** pesquisas da UFTM — "
               "um sinal de que o conhecimento gerado aqui chega à indústria e gera inovação "
               "(transferência de tecnologia). Fonte: The Lens.")
    lp = obs.get("lens_patentes")
    if lp is not None and len(lp):
        m1, m2, m3 = st.columns(3)
        m1.metric("Produções citadas por patentes", br(len(lp)))
        m2.metric("Citações em patentes (total)", br(int(lp["n_patentes"].sum())))
        m3.metric("Citações por patente (média)", br(lp["n_patentes"].mean(), 1))
        st.subheader("Pesquisas da UFTM mais citadas por patentes")
        top = lp.sort_values("n_patentes", ascending=False).head(15).copy()
        top["rotulo"] = top["title"].fillna("(sem título)").str.slice(0, 60)
        st.plotly_chart(barra_h(top, "rotulo", "n_patentes", h=480, cor=T["secondary"]),
                        width="stretch")
        st.caption("Cada barra é uma pesquisa da UFTM e o número de patentes (no mundo) que a "
                   "citam. Quanto mais citações em patentes, maior o uso prático do conhecimento.")
    else:
        st.info("As **patentes que citam a pesquisa da UFTM** aparecerão aqui — um indicador de "
                "impacto em inovação e transferência de tecnologia para a sociedade. "
                "**Recurso em implantação.**")
        with st.expander("Para administradores do painel — como ativar"):
            st.markdown(
                "Usa o **The Lens** (token acadêmico gratuito):\n"
                "1. Crie conta em lens.org e solicite acesso à **Scholarly API**.\n"
                "2. Guarde o token como segredo **`LENS_TOKEN`** no GitHub "
                "(Settings → Secrets → Actions), ou rode local: "
                "`LENS_TOKEN=seu_token python fetch_lens.py`.\n"
                "3. Na próxima atualização mensal, as patentes aparecem nesta aba.")
    st.caption("Outros sinais de impacto fora da academia — citações em **políticas públicas** "
               "e **atenção na mídia** — dependem de bases pagas e ficam como evolução futura.")


def render_ciencia_aberta():
    cabecalho("Ciência Aberta", "Quanto da pesquisa da UFTM qualquer pessoa pode ler de graça")
    if "oa_status" not in fraw.columns:
        st.info("Re-colete os dados (fetch_uftm_ods.py) para habilitar esta aba.")
        return
    st.markdown(
        f"<div style='border-left:2px solid {T['primary']};padding:.15rem 0 .15rem 1.1rem;"
        f"margin:.1rem 0 1.1rem;color:{T['text_soft']};font-size:1.02rem;line-height:1.6;"
        f"max-width:840px'><b style='color:{T['text']}'>Ciência Aberta</b> é tornar todo o "
        f"processo de pesquisa — não só o artigo final — transparente, acessível e reutilizável "
        f"por qualquer pessoa (definição da <b>UNESCO</b>, base dos cursos de Ciência Aberta da "
        f"USP). Vai além das publicações: inclui dados, código, métodos e avaliação abertos. "
        f"Aqui medimos a dimensão que os dados do OpenAlex permitem — o "
        f"<b style='color:{T['text']}'>acesso aberto às publicações</b>.</div>",
        unsafe_allow_html=True)
    with st.expander("As dimensões da Ciência Aberta (Recomendação da UNESCO, 2021)"):
        st.markdown(
            "- **Conhecimento científico aberto** — acesso aberto a publicações, **dados "
            "abertos**, **código/software aberto** e hardware aberto.\n"
            "- **Infraestruturas abertas** — repositórios, plataformas e serviços compartilhados.\n"
            "- **Engajamento aberto da sociedade** — ciência cidadã e diálogo com a sociedade.\n"
            "- **Diálogo com outros sistemas de conhecimento** — saberes tradicionais e locais.\n\n"
            "*Este painel cobre, por ora, o **acesso aberto às publicações**; as demais dimensões "
            "ainda não têm métrica consolidada em bases abertas.*")
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
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Acesso aberto", f"{oa:.0%}")
    c2.metric("Diamante (sem custo)", f"{diam:.0%}", help="Grátis para autor e leitor.")
    c3.metric("Via verde (repositório)", f"{verde:.0%}" if verde is not None else "—")
    c4.metric("Em periódico DOAJ", f"{doaj:.0%}" if doaj is not None else "—",
              help="Entre as produções OA, % em periódicos com selo DOAJ (qualidade).")

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
    st.caption("O custo de publicar em acesso aberto (APC) fica na aba **Financiamento**.")


def render_financiamento():
    cabecalho("Financiamento", "De onde vem o dinheiro da pesquisa — e quanto custa publicá-la em aberto")
    if "n_grants" not in fraw.columns or not len(fraw):
        st.info("Re-colete os dados (fetch_uftm_ods.py).")
        return
    fin = fraw[fraw["n_grants"] > 0]
    naofin = fraw[fraw["n_grants"] == 0]
    c1, c2, c3 = st.columns(3)
    c1.metric("Produções financiadas", br(len(fin)),
              f"{len(fin)/max(len(fraw),1):.0%} do total")
    c2.metric("Financiadores distintos", br(fraw["funders"].explode().nunique()))
    fwci_fin = fin["fwci"].dropna().mean() if len(fin) else float("nan")
    fwci_nao = naofin["fwci"].dropna().mean() if len(naofin) else float("nan")
    c3.metric("FWCI: financiada × não", f"{br(fwci_fin, 2)} × {br(fwci_nao, 2)}",
              help="Impacto médio das produções com financiamento declarado vs. sem. "
                   "Costuma ser maior nas financiadas.")
    st.caption("**Como ler** · *Financiada* = a produção declara ao menos uma agência de fomento "
               "(ex.: CAPES, CNPq, FAPEMIG). Nem toda pesquisa registra isso, então é um **piso** "
               "do que é financiado, não o total.")

    st.subheader("Principais financiadores")
    f = fraw["funders"].explode().dropna().value_counts().head(15).reset_index()
    f.columns = ["financiador", "n"]
    if len(f):
        st.plotly_chart(barra_h(f, "financiador", "n", h=480, cor=T["accent"]), width="stretch")

    st.subheader("Produção financiada ao longo do tempo")
    ev = fraw.assign(fin=fraw["n_grants"] > 0).groupby("year")["fin"].mean().reset_index()
    fig = go.Figure(go.Scatter(x=ev["year"], y=ev["fin"], mode="lines+markers",
                               line=dict(color=T["primary"], width=3), fill="tozeroy",
                               fillcolor="rgba(0,152,58,.06)",
                               hovertemplate="%{x}: %{y:.0%}<extra></extra>"))
    fig = fig_layout(fig, 320)
    fig.update_yaxes(tickformat=".0%")
    st.plotly_chart(fig, width="stretch")

    st.divider()
    st.subheader("Custos de publicação (APC)")
    st.caption("**Como ler** · Algumas revistas cobram uma taxa (**APC**) para deixar a pesquisa "
               "aberta a todos. Aqui está a estimativa desse gasto da UFTM.")
    apc = fraw["apc_usd"].dropna()
    pagos = fraw[fraw["apc_usd"] > 0]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("APC total estimado (US$)", br(apc.sum()) if len(apc) else "—")
    c2.metric("Produções com APC", br(len(pagos)),
              f"{len(pagos)/max(len(fraw),1):.0%} do total")
    c3.metric("APC médio (US$)", br(pagos["apc_usd"].mean()) if len(pagos) else "—")
    c4.metric("Sem custo para o autor", f"{1 - len(pagos)/max(len(fraw),1):.0%}",
              help="Diamante, verde, bronze e fechado não cobram APC do autor.")
    apc_ano = fraw.groupby("year")["apc_usd"].sum().reset_index()
    fig = go.Figure(go.Bar(x=apc_ano["year"], y=apc_ano["apc_usd"], marker_color=T["accent"],
                           hovertemplate="%{x}: US$ %{y:,.0f}<extra></extra>"))
    st.plotly_chart(fig_layout(fig, 320), width="stretch")
    st.caption("APC = Article Processing Charge reportado ao OpenAlex — estimativa do gasto com "
               "publicação em acesso aberto pago (não inclui acordos transformativos/descontos).")


def render_benchmarking():
    cabecalho("Comparação", "A UFTM diante de pares — em Minas Gerais e no Brasil")
    bi = obs.get("bench_instituicoes")
    bp = obs.get("bench_porte_instituicoes")
    if bi is None:
        st.info("Rode `python fetch_observatorio.py` para gerar os dados de comparação.")
        return
    st.caption("**Como ler** · Cada barra é uma instituição; a **UFTM aparece em verde** e as "
               "demais em verde-claro. À esquerda, as **federais de Minas Gerais** (comparação "
               "regional); à direita, **federais de porte semelhante** no Brasil inteiro "
               "(nº de produções parecido com o da UFTM). Escolha o indicador para comparar.")
    metricas = {
        "Produções": ("works", ",.0f"), "Citações": ("citacoes", ",.0f"),
        "Citações por trabalho": ("cit_por_trabalho", ",.2f"),
        "Impacto médio (citações por trabalho recente)": ("mean_citedness", ",.2f"),
        "No top 10% mundial (%)": ("top10_share", ".1%"),
        "No top 1% mundial (%)": ("top1_share", ".1%"),
        "Colaboração internacional (%)": ("intl_share", ".1%"),
        "Colaboração nacional (%)": ("nac_share", ".1%"),
        "Colaboração só institucional (%)": ("inst_share", ".1%"),
        "Acesso aberto (%)": ("oa_share", ".1%"),
        "Índice h": ("h_index", ",.0f"),
        "Índice i10": ("i10", ",.0f"),
    }
    metricas = {k: v for k, v in metricas.items() if v[0] in bi.columns}
    escolha = st.selectbox("Métrica", list(metricas.keys()))
    col, fmt0 = metricas[escolha]

    def grupo_df(bi_df, ba_df):
        if col in ("works", "citacoes"):
            sl = ba_df[ba_df["year"].between(*faixa)]
            return sl.groupby("sigla", as_index=False)[col].sum(), fmt0
        d = bi_df[["sigla", col]].copy()
        if col.endswith("_share"):
            d[col] = d[col] * 100
            return d, ".1f"
        return d, fmt0

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Federais de Minas Gerais**")
        d, f = grupo_df(bi, obs["bench_por_ano"])
        st.plotly_chart(barra_h(d, "sigla", col, h=440, fmt=f, destaque="UFTM"), width="stretch")
    with c2:
        st.markdown("**Federais de porte semelhante (Brasil)**")
        if bp is not None:
            d, f = grupo_df(bp, obs["bench_porte_por_ano"])
            st.plotly_chart(barra_h(d, "sigla", col, h=440, fmt=f, destaque="UFTM"),
                            width="stretch")
        else:
            st.info("Rode `python fetch_observatorio.py` para gerar o grupo de porte.")

    por_periodo = col in ("works", "citacoes")
    nota = (f"Recorte do período {faixa[0]}–{faixa[1]}." if por_periodo
            else "Total acumulado (não afetado pelo filtro de período).")
    ref = ("  Referência: no mundo, ~10% das pesquisas estão no top 10% e ~1% no top 1% — acima "
           "disso é estar acima da média mundial." if col in ("top10_share", "top1_share") else "")
    cit = ("  As citações aqui vêm do **contador institucional do OpenAlex** (igual para todas "
           "as universidades, para comparar), maior que a soma trabalho a trabalho da Visão "
           "Geral — entenda na aba Transparência."
           if col in ("citacoes", "cit_por_trabalho") else "")
    st.caption(nota + ref + cit)


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
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Internacional", f"{intl:.0%}", help="≥ 2 países distintos.")
        c2.metric("Nacional", f"{nac:.0%}", help="Só Brasil, ≥ 2 instituições.")
        c3.metric("Institucional", f"{inst:.0%}", help="Apenas UFTM.")
        if "lidera" in fraw.columns:
            c4.metric("UFTM lidera", f"{fraw['lidera'].mean():.0%}",
                      help="Produções em que a UFTM é a instituição correspondente (autor de "
                           "contato) — sinal de protagonismo, não apenas participação.")

    ci = obs.get("colab_instituicoes")
    if ci is None:
        st.info("Rode `python fetch_observatorio.py` para os dados de colaboração.")
        return
    st.subheader("Instituições parceiras")
    st.plotly_chart(barra_h(ci.head(15), "instituicao", "n", h=480), width="stretch")

    st.subheader("Países parceiros (exceto Brasil)")
    cp = obs["colab_paises"]
    cp = cp[cp["pais"] != "Brazil"].head(15)
    st.plotly_chart(barra_h(cp, "pais", "n", h=480, cor=T["secondary"]), width="stretch")

    nos = obs.get("rede_autores_nos")
    arestas = obs.get("rede_autores_arestas")
    if nos is not None and arestas is not None and len(nos):
        st.subheader("Rede de coautoria dos pesquisadores da UFTM")
        m1, m2, m3 = st.columns(3)
        m1.metric("Pesquisadores na rede", br(len(nos)))
        m2.metric("Conexões", br(len(arestas)))
        m3.metric("Grupos (comunidades)", br(nos["comunidade"].nunique()))
        st.plotly_chart(grafo_coautoria(nos, arestas), width="stretch",
                        config={"responsive": True, "scrollZoom": True, "displaylogo": False})
        st.caption("Cada ponto é um pesquisador da UFTM (tamanho = nº de produções); as linhas são "
                   "coautorias. As cores são grupos de colaboração — veja o tema de cada um na "
                   "lista abaixo. Arraste e use o zoom para explorar; passe o mouse para ver nomes.")

        grupos = rotular_grupos(nos)
        st.markdown("**Grupos de pesquisa na rede**")
        cab = (f"<tr style='color:{T['muted']};font-size:.74rem;text-align:left'>"
               f"<th style='padding:0 12px 4px 0'></th><th style='padding:0 14px 4px 0'>TEMA</th>"
               f"<th style='padding:0 14px 4px 0'>PESQUISADORES</th>"
               f"<th style='padding:0 0 4px 0'>PESQUISADOR CENTRAL</th></tr>")
        linhas = "".join(
            f"<tr>"
            f"<td style='padding:3px 12px 3px 0'><span style='display:inline-block;width:11px;"
            f"height:11px;border-radius:50%;background:{r.cor}'></span></td>"
            f"<td style='padding:3px 14px 3px 0;color:{T['text']}'>{r.tema}</td>"
            f"<td style='padding:3px 14px 3px 0;color:{T['text_soft']}'>{r.tamanho}</td>"
            f"<td style='padding:3px 0;color:{T['text_soft']}'>{r.hub}</td></tr>"
            for r in grupos.itertuples())
        st.markdown(f"<table style='font-size:.9rem;border-collapse:collapse'>{cab}{linhas}</table>",
                    unsafe_allow_html=True)
        st.caption("Esta lista é a legenda do grafo e funciona em qualquer tela: cada cor é um "
                   "grupo, o tema vem do assunto mais frequente e o pesquisador central é quem "
                   "mais conecta os membros.")


def render_ods():
    cabecalho("Impacto Social", "A contribuição da UFTM para a sociedade — pelos Objetivos da ONU (ODS)")
    st.markdown(
        f"<div style='border-left:2px solid {T['primary']};padding:.15rem 0 .15rem 1.1rem;"
        f"margin:.1rem 0 1.1rem;color:{T['text_soft']};font-size:1.02rem;line-height:1.6;"
        f"max-width:840px'>Os <b style='color:{T['text']}'>ODS</b> são os 17 <b>Objetivos de "
        f"Desenvolvimento Sustentável</b> da <b>Agenda 2030</b>, adotada por todos os "
        f"países-membros da <b>ONU em 2015</b> — um chamado global para acabar com a pobreza, "
        f"proteger o planeta e garantir paz e prosperidade. Vê-los na pesquisa é uma forma de "
        f"medir o <b style='color:{T['text']}'>impacto social</b> da universidade.</div>",
        unsafe_allow_html=True)
    st.caption("**Como ler** · Mostramos com quais objetivos a pesquisa da UFTM mais se "
               "relaciona. A associação é uma **estimativa por inteligência artificial** do "
               "OpenAlex — uma aproximação, não uma declaração dos autores.")
    n_ods = fsdg["work_id"].nunique()
    c1, c2 = st.columns(2)
    c1.metric("Produções ligadas a ODS", br(n_ods), f"{n_ods/max(len(fraw),1):.0%} do total")
    c2.metric("ODS distintos", f"{fsdg['sdg_id'].nunique()} de 17")
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

    if "topic" in fraw.columns and len(fraw):
        st.subheader("Temas emergentes")
        st.caption("**Como ler** · Assuntos que **mais cresceram**: comparamos os 3 anos mais "
                   "recentes do período com os 3 anteriores. Barras maiores = temas em ascensão "
                   "na UFTM.")
        am = min(int(fraw["year"].max()), ymax)
        rec = fraw[fraw["year"].between(am - 2, am)]["topic"].value_counts()
        ant = fraw[fraw["year"].between(am - 5, am - 3)]["topic"].value_counts()
        df = pd.DataFrame({"recente": rec, "anterior": ant}).fillna(0)
        df = df[(df["recente"] + df["anterior"]) >= 12]
        df["cresc"] = df["recente"] - df["anterior"]
        emg = df.sort_values("cresc", ascending=False).head(12).reset_index()
        emg.columns = ["topico", "recente", "anterior", "cresc"]
        if len(emg):
            st.plotly_chart(barra_h(emg, "topico", "cresc", h=460),
                            width="stretch")
            st.caption("Crescimento = nº de produções nos 3 anos recentes menos os 3 anteriores.")


def render_pesquisadores():
    cabecalho("Pesquisadores", "Os nomes por trás da pesquisa da UFTM")
    ta = obs.get("top_autores")
    if ta is None or "citacoes_uftm" not in ta.columns:
        st.info("Rode `python fetch_observatorio.py` para os dados de pesquisadores.")
        return
    st.caption("**Como ler** · Pesquisadores **que assinam trabalhos com afiliação à UFTM**, "
               "ordenados pelas **citações das produções feitas na UFTM** (não pela carreira "
               "inteira). *Produções (UFTM)* = nº desses trabalhos. O **índice h** e o **i10** "
               "são de **carreira** (todo o histórico do pesquisador, em qualquer instituição); "
               "**ORCID** é o identificador único.")
    ta = ta.sort_values("citacoes_uftm", ascending=False)
    st.plotly_chart(barra_h(ta.head(15), "autor", "citacoes_uftm", h=460), width="stretch")
    cols = [c for c in ["autor", "citacoes_uftm", "works_uftm", "h_index", "i10", "orcid"]
            if c in ta.columns]
    disp = ta[cols].rename(columns={
        "autor": "Pesquisador", "citacoes_uftm": "Citações (na UFTM)",
        "works_uftm": "Produções (UFTM)", "h_index": "Índice h (carreira)",
        "i10": "i10 (carreira)"})
    st.dataframe(disp, width="stretch", height=420, hide_index=True,
                 column_config={"orcid": st.column_config.LinkColumn("ORCID")})


def render_periodicos():
    cabecalho("Onde publicamos", "As revistas científicas que mais publicam pesquisa da UFTM")
    st.caption("**Como ler** · Cada barra é uma revista científica (periódico); o tamanho mostra "
               "quantas pesquisas da UFTM saíram nela no período.")
    fr = filtro_tipo(fraw, "tipo_periodicos", com_oa=True)
    top = (fr[fr["source"].notna()]["source"].value_counts().head(20)
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


def render_idiomas():
    cabecalho("Publicações por língua", "Em que idiomas a pesquisa da UFTM é publicada")
    if "language" not in fraw.columns or not fraw["language"].notna().any():
        st.info("Re-colete os dados (fetch_uftm_ods.py) para habilitar o idioma.")
        return
    st.caption("**Como ler** · O idioma de cada trabalho, segundo o OpenAlex. Publicar em "
               "**inglês** amplia o alcance internacional; em **português**, aproxima a pesquisa "
               "da sociedade e da comunidade científica nacional.")
    lang = fraw["language"].dropna()
    c1, c2, c3 = st.columns(3)
    c1.metric("Em inglês", pct((lang == "en").mean()))
    c2.metric("Em português", pct((lang == "pt").mean()))
    c3.metric("Idiomas distintos", br(lang.nunique()))

    st.subheader("Distribuição por idioma")
    comp = (lang.map(lambda x: IDIOMA_PT.get(x, str(x).upper())).value_counts()
            .head(10).rename_axis("idioma").reset_index(name="n"))
    st.plotly_chart(barra_h(comp, "idioma", "n", h=420), width="stretch")

    st.subheader("Inglês × português ao longo do tempo")
    df = fraw.dropna(subset=["language"]).copy()
    df["grp"] = df["language"].map(lambda x: "Inglês" if x == "en"
                                   else ("Português" if x == "pt" else "Outros"))
    tot_ano = df.groupby("year")["language"].size()
    ev = df.groupby(["year", "grp"]).size().reset_index(name="n")
    ev["share"] = ev.apply(lambda r: r["n"] / tot_ano[r["year"]], axis=1)
    cores = {"Inglês": T["primary"], "Português": T["accent"], "Outros": T["faint"]}
    fig = go.Figure()
    for g in ["Inglês", "Português", "Outros"]:
        gg = ev[ev["grp"] == g].sort_values("year")
        if len(gg):
            fig.add_trace(go.Scatter(x=gg["year"], y=gg["share"], mode="lines+markers", name=g,
                                     line=dict(color=cores[g], width=2.5)))
    fig = fig_layout(fig, 340)
    fig.update_yaxes(tickformat=".0%")
    fig.update_layout(showlegend=True, legend=dict(font=dict(color=T["text"], size=10)))
    st.plotly_chart(fig, width="stretch")
    st.caption("Percentual das produções de cada ano por idioma. Uma tendência de alta no inglês "
               "costuma indicar maior internacionalização da pesquisa.")


def render_explorar():
    cabecalho("Explorar", "Procure qualquer pesquisa da UFTM pelo título")
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        termo = st.text_input("Filtrar por palavra no título")
    with c2:
        tipo = st.selectbox("Tipo de produção", ["Todos os tipos"] + TIPOS, key="tipo_explorar",
                            format_func=lambda t: "Todos os tipos" if t == "Todos os tipos"
                            else tipo_pt(t))
    with c3:
        st.markdown("<div style='height:1.8rem'></div>", unsafe_allow_html=True)
        so_oa = st.toggle("Apenas acesso aberto", key="oa_explorar")
    f = fraw
    if tipo != "Todos os tipos":
        f = f[f["type"] == tipo]
    if so_oa:
        f = f[f["is_oa"] == True]  # noqa: E712
    cols = [c for c in ["title", "year", "type", "is_oa", "fwci", "cited_by", "source", "doi"]
            if c in f.columns]
    tab = f[cols].copy()
    tab["type"] = tab["type"].map(tipo_pt)
    if termo:
        tab = tab[tab["title"].str.contains(termo, case=False, na=False)]
    tab = tab.sort_values(["year", "cited_by"], ascending=[False, False])
    st.dataframe(tab, width="stretch", height=520,
                 column_config={"doi": st.column_config.LinkColumn("DOI"),
                                "type": "Tipo", "title": "Título", "year": "Ano",
                                "is_oa": "Acesso aberto", "fwci": "FWCI",
                                "cited_by": "Citações", "source": "Revista"})
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
        "(**ROR `01av3m334`**): entram os trabalhos com pelo menos um autor vinculado à "
        "universidade.")

    st.markdown("**Como uma pesquisa chega até o OpenAlex — e por que algumas faltam**")
    st.markdown(
        "- O OpenAlex não recebe os dados direto da UFTM. Ele reúne informações de grandes "
        "fontes abertas, sobretudo o **Crossref** — onde as revistas e editoras registram cada "
        "publicação ao criar um **DOI** (o endereço permanente do trabalho) — além de PubMed, "
        "DataCite, DOAJ, ORCID, arXiv, repositórios e outras.\n"
        "- Na prática: quando uma revista publica um artigo e registra o DOI, o OpenAlex capta "
        "esse registro. O trabalho é contado como “da UFTM” quando o vínculo do autor com a "
        "universidade está identificado.\n"
        "- Por isso, **nem toda a produção é captada**. Costumam ficar de fora: trabalhos **sem "
        "DOI** ou em veículos que não registram seus dados nessas fontes (parte de periódicos "
        "locais, anais de eventos, relatórios, alguns livros e materiais de extensão); trabalhos "
        "em que a **afiliação à UFTM não foi registrada ou reconhecida**; teses e dissertações "
        "que estão só no repositório, sem DOI; e publicações **muito recentes**, ainda não "
        "indexadas.\n"
        "- Em resumo: o painel mostra a parte da produção da UFTM **registrada em bases abertas "
        "internacionais** — uma fração grande e crescente, mas não 100% de tudo o que a "
        "universidade produz.")

    st.markdown("**2. Fontes complementares**")
    st.markdown(
        "- **Scimago (SJR):** ranking mundial e gratuito de revistas — define os quartis (Q1–Q4) "
        "da aba *Qualidade das revistas*, ligado pelo código (ISSN) de cada revista.\n"
        "- **The Lens:** base aberta que liga pesquisas a patentes — alimenta as patentes da aba "
        "*Patentes* (quando há credencial de acesso).")

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

    st.markdown("**A fórmula do FWCI, em detalhe**")
    st.latex(r"\text{FWCI} = \frac{\text{citações que a pesquisa recebeu}}"
             r"{\text{citações esperadas para pesquisas semelhantes}}")
    st.markdown(
        "- **Citações esperadas** = a média de citações de todas as pesquisas semelhantes no "
        "mundo: mesma **área** (subárea), mesmo **ano** de publicação e mesmo **tipo** de "
        "documento. É isso que torna o indicador justo entre áreas — comparar um artigo de "
        "matemática com um de medicina pela citação bruta seria injusto, porque as áreas citam "
        "em ritmos diferentes.\n"
        "- **Janela de tempo:** contam-se as citações do ano de publicação **mais os 3 anos "
        "seguintes**. Por isso os 2 anos mais recentes ficam provisórios (a janela ainda não "
        "fechou) — e há a opção de excluí-los na aba *Impacto científico*.\n"
        "- **Como ler:** **1,0** = exatamente a média mundial · **1,5** = 50% acima · **2,0** = o "
        "dobro · **0,5** = metade.\n"
        "- Para um conjunto (a UFTM, uma área, um pesquisador), usamos a **média** dos FWCI das "
        "pesquisas.\n"
        "- **Por que não dá para comparar com outras bases?** A fórmula é a mesma da Scopus/SciVal, "
        "mas o resultado depende de *quais publicações e citações cada base enxerga*. Este painel "
        "usa o **OpenAlex** (base científica aberta e gratuita); o SciVal usa a **Scopus** (base "
        "paga da Elsevier). Como cada base indexa um conjunto diferente de trabalhos, mudam tanto "
        "as **citações contadas** quanto a **“média esperada”** — e a classificação de áreas "
        "também difere. Por isso um FWCI de 1,2 no OpenAlex não equivale a 1,2 na Scopus. A "
        "comparação só faz sentido **dentro da mesma base** — é o que fazemos no *Comparação*, "
        "todo medido em OpenAlex.")

    st.markdown("**4. Atualização e reprodutibilidade**")
    st.markdown(
        ("- **Última coleta dos dados: " + DATA_COLETA + "**.\n" if DATA_COLETA else "") +
        "- A coleta roda **automaticamente todo mês**, sem intervenção manual; o período "
        "aparece no topo de cada página e pode ser ajustado na barra lateral.\n"
        "- Todos os dados são coletados na **mesma rodada** (um único `fetch_all.py`), no mesmo "
        "instante da base — então as páginas falam do mesmo retrato do OpenAlex.\n"
        "- Todo o código que coleta e monta o painel é **aberto e auditável** em "
        "[github.com/ana-mat-br/painel-daad](https://github.com/ana-mat-br/painel-daad).")

    st.markdown("**5. Limites e cuidados**")
    st.markdown(
        "- A associação aos **ODS** é uma **estimativa por inteligência artificial**, não uma "
        "classificação declarada pelos autores — leia como aproximação.\n"
        "- O **FWCI** dos 2 anos mais recentes ainda é provisório (pesquisas novas seguem "
        "recebendo citações).\n"
        "- A cobertura depende do que está indexado no OpenAlex; **revistas não indexadas** "
        "(muitas nacionais) podem não receber quartil ou impacto.\n"
        "- Indicadores de impacto **não são comparáveis entre bases diferentes** — o OpenAlex e "
        "as bases científicas pagas contam de formas distintas.")

    st.divider()
    st.subheader("Por que os números de citação variam entre fontes")
    soma_works = int(raw["cited_by"].sum())
    bi_t = obs.get("bench_instituicoes")
    agg_inst = (int(bi_t[bi_t["sigla"] == "UFTM"]["citacoes"].iloc[0])
                if bi_t is not None and "UFTM" in set(bi_t["sigla"]) else None)
    st.markdown(
        "Não existe **um único** número de citações: ele depende de **como se conta** e de "
        "**quais trabalhos entram**. Veja, todos a partir do OpenAlex, para a UFTM:\n"
        f"- **Soma trabalho a trabalho** — o que este painel usa na *Visão Geral*: "
        f"**{br(soma_works)}** citações. É a soma das citações de cada trabalho que você "
        f"consegue ver na aba *Explorar* (rastreável).\n"
        + (f"- **Contador agregado da instituição** no OpenAlex — usado na *Comparação*, para "
           f"medir todas as universidades do mesmo jeito: **{br(agg_inst)}**. É bem maior e "
           f"sabidamente inflado em relação à soma real dos trabalhos.\n" if agg_inst else "")
        + "- A **Capivara/UFTM** chega a ~122 mil porque parte de uma **lista diferente de "
        "trabalhos**: ela ancora no **Currículo Lattes** dos pesquisadores (o que cada um "
        "declarou) e busca as citações no OpenAlex para essa lista. Como o Lattes capta "
        "trabalhos que a afiliação no OpenAlex não registra, o total fica maior.\n\n"
        "**Nenhum está “errado”** — são âncoras diferentes (afiliação no OpenAlex × Currículo "
        "Lattes). Este painel é automático e sempre atualizado, mas só vê o que tem afiliação "
        "registrada; a Capivara é mais completa para a produção declarada, mas depende do "
        "Lattes estar em dia. Aqui priorizamos a **soma trabalho a trabalho** por ser "
        "rastreável: você enxerga, na aba *Explorar*, os trabalhos que formam o total.")

    if "is_retracted" in fraw.columns:
        st.divider()
        st.subheader("Integridade do acervo")
        st.markdown("Indicadores de **confiança nos dados** — quanto mais limpo o acervo, mais "
                    "sólidos os números acima. Período selecionado:")
        n = max(len(fraw), 1)
        c1, c2, c3 = st.columns(3)
        c1.metric("Retratações", br(int(fraw["is_retracted"].sum())),
                  help="Produções formalmente retiradas/retratadas. Quanto menos, melhor.")
        c2.metric("Com DOI", f"{fraw['doi'].notna().mean():.0%}",
                  help="Produções com identificador permanente (DOI). As sem DOI são mais "
                       "difíceis de rastrear e citar.")
        if "is_paratext" in fraw.columns:
            c3.metric("Paratexto", br(int(fraw["is_paratext"].sum())),
                      help="Itens marcados como paratexto (capas, sumários, expedientes) — não "
                           "são pesquisa; ficam de fora das análises de impacto.")
        st.caption("Fonte das marcações: OpenAlex (is_retracted, is_paratext, presença de DOI).")


PAGINAS = {
    "Visão Geral": render_visao_geral, "Impacto científico": render_excelencia,
    "Comparação": render_benchmarking, "Ciência Aberta": render_ciencia_aberta,
    "Impacto Social": render_ods, "Financiamento": render_financiamento,
    "Patentes": render_patentes,
    "Pesquisadores": render_pesquisadores, "Colaboração": render_colaboracao,
    "Temas": render_temas, "Onde publicamos": render_periodicos,
    "Qualidade das revistas": render_qualidade,
    "Publicações por língua": render_idiomas, "Explorar": render_explorar,
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
