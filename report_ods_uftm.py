"""Relatorio UFTM por ODS — A4 retrato, layout moderno."""
from __future__ import annotations

from datetime import date
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.backends.backend_pdf import PdfPages

BASE = Path(__file__).parent
DATA = BASE / "data"
PDF_OUT = BASE / f"relatorio_ods_uftm_{date.today().isoformat()}.pdf"

A4 = (8.27, 11.69)  # retrato

# Paleta moderna
INK = "#1a202c"
MUTED = "#718096"
ACCENT = "#2c7a7b"     # teal
ACCENT2 = "#dd6b20"    # laranja
BG = "#f7fafc"

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "axes.edgecolor": "#cbd5e0",
    "axes.labelcolor": INK,
    "axes.titlecolor": INK,
    "axes.titleweight": "bold",
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "axes.spines.top": False,
    "axes.spines.right": False,
})

DISCLAIMER = (
    "Dados: OpenAlex · ROR 01av3m334 (UFTM). "
    "Classificação por ODS via modelo Aurora mBERT (score ≥ 0,4). "
    "Conforme policy brief Métricas.edu, esses números são heurísticos: "
    "diferentes bases (Scopus, OpenAlex, OSDG) produzem corpora distintos "
    "com baixa sobreposição. Use como mapeamento exploratório, não como "
    "indicador determinístico. Um mesmo trabalho pode contar em mais de um ODS."
)

SDG_SHORT = {
    "1": "Erradicação da pobreza", "2": "Fome zero", "3": "Saúde e bem-estar",
    "4": "Educação de qualidade", "5": "Igualdade de gênero",
    "6": "Água potável e saneamento", "7": "Energia limpa",
    "8": "Trabalho decente", "9": "Indústria e inovação",
    "10": "Redução das desigualdades", "11": "Cidades sustentáveis",
    "12": "Consumo responsável", "13": "Ação climática",
    "14": "Vida na água", "15": "Vida terrestre",
    "16": "Paz e justiça", "17": "Parcerias",
}


def header(fig, eyebrow, title, subtitle=None):
    fig.patch.set_facecolor("white")
    fig.text(0.08, 0.955, eyebrow, fontsize=8, color=ACCENT,
             weight="bold")
    fig.text(0.08, 0.925, title, fontsize=17, weight="bold", color=INK)
    if subtitle:
        fig.text(0.08, 0.902, subtitle, fontsize=9.5, color=MUTED)
    # linha
    fig.add_artist(plt.Line2D([0.08, 0.92], [0.888, 0.888],
                              color="#e2e8f0", linewidth=0.8))


def footer(fig, pagenum):
    fig.text(0.08, 0.035, "Relatório UFTM · ODS · OpenAlex",
             fontsize=7.5, color=MUTED)
    fig.text(0.92, 0.035, f"{pagenum}", fontsize=7.5,
             color=MUTED, ha="right")


def page_cover(pdf, total_works, total_with_sdg):
    fig = plt.figure(figsize=A4)
    fig.patch.set_facecolor("white")
    ax = fig.add_axes([0, 0, 1, 1]); ax.axis("off")

    # bloco superior colorido
    ax.add_patch(plt.Rectangle((0, 0.78), 1, 0.22, color=ACCENT, transform=ax.transAxes))
    ax.text(0.08, 0.93, "RELATÓRIO INSTITUCIONAL", fontsize=10,
            color="white", weight="bold", transform=ax.transAxes)
    ax.text(0.08, 0.86, "Produção científica\nda UFTM por ODS",
            fontsize=28, color="white", weight="bold",
            transform=ax.transAxes, va="top")
    ax.text(0.08, 0.795, f"Gerado em {date.today().strftime('%d de %B de %Y')}",
            fontsize=10, color="#e6fffa", transform=ax.transAxes)

    # cards de destaque
    cards = [
        (str(total_works), "trabalhos da UFTM\nno OpenAlex"),
        (str(total_with_sdg), "com pelo menos\num ODS atribuído"),
        ("17", "ODS cobertos\npela produção"),
    ]
    for i, (big, small) in enumerate(cards):
        x = 0.08 + i * 0.30
        ax.add_patch(plt.Rectangle((x, 0.58), 0.26, 0.13,
                                    facecolor=BG, edgecolor="#e2e8f0",
                                    transform=ax.transAxes))
        ax.text(x + 0.13, 0.665, big, fontsize=24, weight="bold",
                color=ACCENT, ha="center", transform=ax.transAxes)
        ax.text(x + 0.13, 0.605, small, fontsize=8.5,
                color=MUTED, ha="center", transform=ax.transAxes)

    # sumário
    ax.text(0.08, 0.50, "Neste relatório", fontsize=11,
            weight="bold", color=INK, transform=ax.transAxes)
    items = [
        "Ranking de ODS por número de trabalhos",
        "Série temporal dos top 6 ODS",
        "Tabela resumo com citações e acesso aberto",
        "Distribuição por idioma (geral e por ODS)",
        "Top fontes de publicação dos principais ODS",
    ]
    for i, txt in enumerate(items):
        ax.text(0.10, 0.46 - i*0.025, f"·  {txt}",
                fontsize=10, color=INK, transform=ax.transAxes)

    # disclaimer
    ax.add_patch(plt.Rectangle((0.08, 0.08), 0.84, 0.18,
                                facecolor=BG, edgecolor="#e2e8f0",
                                transform=ax.transAxes))
    ax.text(0.10, 0.235, "NOTA METODOLÓGICA", fontsize=8,
            weight="bold", color=ACCENT2,
            transform=ax.transAxes)
    ax.text(0.10, 0.21, DISCLAIMER, fontsize=8.5, color=INK,
            transform=ax.transAxes, va="top",
            wrap=True)
    # workaround wrap
    import textwrap
    wrapped = "\n".join(textwrap.wrap(DISCLAIMER, width=95))
    ax.texts[-1].set_text(wrapped)

    pdf.savefig(fig); plt.close(fig)


def page_ranking(pdf, by_sdg, pagenum):
    fig = plt.figure(figsize=A4)
    header(fig, "01 · VISÃO GERAL",
           "Ranking de ODS na produção da UFTM",
           "Número de trabalhos únicos com score Aurora ≥ 0,4")

    ax = fig.add_axes([0.30, 0.10, 0.62, 0.76])
    d = by_sdg.sort_values("n_works", ascending=True).copy()
    d["label"] = d["sdg_id"].astype(str) + "  " + d["sdg_id"].astype(str).map(SDG_SHORT)
    colors = [ACCENT if v >= d["n_works"].quantile(0.66)
              else (ACCENT2 if v >= d["n_works"].quantile(0.33) else "#cbd5e0")
              for v in d["n_works"]]
    ax.barh(d["label"], d["n_works"], color=colors, height=0.7)
    ax.set_xlabel("Trabalhos", fontsize=9)
    ax.tick_params(axis="y", labelsize=9)
    for i, v in enumerate(d["n_works"]):
        ax.text(v + d["n_works"].max()*0.01, i, f"{v:,}".replace(",", "."),
                va="center", fontsize=8.5, color=INK)
    ax.set_xlim(0, d["n_works"].max() * 1.12)

    footer(fig, pagenum)
    pdf.savefig(fig); plt.close(fig)


def page_timeseries(pdf, by_sdg_year, by_sdg, pagenum):
    fig = plt.figure(figsize=A4)
    header(fig, "02 · EVOLUÇÃO",
           "Série temporal — top 6 ODS",
           "Trabalhos publicados por ano")

    ax = fig.add_axes([0.10, 0.10, 0.82, 0.76])
    top = by_sdg.nlargest(6, "n_works")["sdg_id"].astype(str).tolist()
    palette = ["#2c7a7b", "#dd6b20", "#3182ce", "#9f7aea",
               "#e53e3e", "#38a169"]
    d = by_sdg_year.copy()
    d["sdg_id"] = d["sdg_id"].astype(str)
    d = d[d["sdg_id"].isin(top) & (d["year"] >= 2000) & (d["year"] <= date.today().year)]

    for sdg, color in zip(top, palette):
        s = d[d["sdg_id"] == sdg].sort_values("year")
        ax.plot(s["year"], s["n_works"], marker="o", markersize=4,
                linewidth=2, color=color,
                label=f"ODS {sdg} · {SDG_SHORT.get(sdg,'')}")
    ax.set_xlabel("Ano", fontsize=9)
    ax.set_ylabel("Trabalhos", fontsize=9)
    ax.grid(axis="y", alpha=0.2)
    ax.legend(fontsize=8, frameon=False, loc="upper left")

    footer(fig, pagenum)
    pdf.savefig(fig); plt.close(fig)


def page_summary_table(pdf, by_sdg, pagenum):
    fig = plt.figure(figsize=A4)
    header(fig, "03 · RESUMO",
           "Tabela por ODS",
           "Trabalhos · citações · proporção de acesso aberto")

    ax = fig.add_axes([0.08, 0.10, 0.84, 0.76]); ax.axis("off")

    d = by_sdg.sort_values("n_works", ascending=False).copy()
    d["ODS"] = d["sdg_id"].astype(str)
    d["Nome"] = d["sdg_id"].astype(str).map(SDG_SHORT)
    d["Trabalhos"] = d["n_works"].map(lambda v: f"{v:,}".replace(",", "."))
    d["Citações"] = d["citations"].map(lambda v: f"{v:,}".replace(",", "."))
    d["% OA"] = (d["oa_share"] * 100).round(0).astype(int).astype(str) + "%"
    show = d[["ODS", "Nome", "Trabalhos", "Citações", "% OA"]]

    tbl = ax.table(cellText=show.values, colLabels=show.columns,
                   loc="upper center", cellLoc="left",
                   colWidths=[0.07, 0.42, 0.16, 0.16, 0.10])
    tbl.auto_set_font_size(False); tbl.set_fontsize(9); tbl.scale(1, 1.6)
    # estiliza cabecalho
    for j in range(len(show.columns)):
        c = tbl[0, j]
        c.set_facecolor(ACCENT); c.set_text_props(color="white", weight="bold")
    # zebra
    for i in range(1, len(show) + 1):
        for j in range(len(show.columns)):
            cell = tbl[i, j]
            cell.set_edgecolor("#e2e8f0")
            if i % 2 == 0:
                cell.set_facecolor(BG)

    footer(fig, pagenum)
    pdf.savefig(fig); plt.close(fig)


def page_language(pdf, lang_general, lang_by_sdg, pagenum):
    fig = plt.figure(figsize=A4)
    header(fig, "04 · IDIOMA",
           "Distribuição por idioma de publicação",
           "Pesquisa em PT-BR é majoritária em ODS de ciências humanas e sociais")

    # donut geral
    ax1 = fig.add_axes([0.08, 0.50, 0.36, 0.32])
    top_langs = lang_general.head(4)
    others = lang_general.iloc[4:].sum()
    values = list(top_langs.values) + [others]
    labels = list(top_langs.index) + ["outros"]
    colors = [ACCENT, ACCENT2, "#3182ce", "#a0aec0", "#e2e8f0"]
    wedges, _ = ax1.pie(values, colors=colors, startangle=90,
                         wedgeprops=dict(width=0.35, edgecolor="white"))
    total = sum(values)
    ax1.text(0, 0.05, f"{total:,}".replace(",", "."),
             ha="center", fontsize=18, weight="bold", color=INK)
    ax1.text(0, -0.15, "trabalhos\ncom ODS", ha="center",
             fontsize=8, color=MUTED)
    ax1.set_title("Visão geral", fontsize=10, pad=10)

    # legenda
    ax_leg = fig.add_axes([0.48, 0.50, 0.40, 0.32]); ax_leg.axis("off")
    name_map = {"en":"Inglês", "pt":"Português", "es":"Espanhol",
                "fr":"Francês", "outros":"Outros", "desconhecido":"Não detectado"}
    for i, (lab, val, col) in enumerate(zip(labels, values, colors)):
        y = 0.85 - i*0.12
        ax_leg.add_patch(plt.Rectangle((0.0, y), 0.04, 0.06,
                                        color=col, transform=ax_leg.transAxes))
        ax_leg.text(0.08, y + 0.02,
                    f"{name_map.get(lab, lab)}",
                    fontsize=10, color=INK, transform=ax_leg.transAxes,
                    weight="bold")
        ax_leg.text(0.55, y + 0.02,
                    f"{val:,}".replace(",", ".") + f"   ({val/total*100:.1f}%)",
                    fontsize=9.5, color=MUTED, transform=ax_leg.transAxes)

    # barras empilhadas por ODS
    ax2 = fig.add_axes([0.08, 0.10, 0.84, 0.32])
    d = lang_by_sdg.copy().sort_values("total", ascending=True)
    d["label"] = d["sdg_id"].astype(str) + " " + d["sdg_id"].astype(str).map(SDG_SHORT)
    en = d.get("en", 0) / d["total"] * 100
    pt = d.get("pt", 0) / d["total"] * 100
    es = d.get("es", 0) / d["total"] * 100
    outros = 100 - en - pt - es
    ax2.barh(d["label"], en, color=ACCENT, label="Inglês", height=0.7)
    ax2.barh(d["label"], pt, left=en, color=ACCENT2, label="Português", height=0.7)
    ax2.barh(d["label"], es, left=en+pt, color="#3182ce", label="Espanhol", height=0.7)
    ax2.barh(d["label"], outros, left=en+pt+es, color="#cbd5e0", label="Outros", height=0.7)
    ax2.set_xlim(0, 100)
    ax2.set_xlabel("% dos trabalhos", fontsize=9)
    ax2.tick_params(axis="y", labelsize=8)
    ax2.legend(fontsize=8, frameon=False, ncol=4,
               loc="upper center", bbox_to_anchor=(0.5, -0.12))
    ax2.set_title("Composição linguística por ODS", fontsize=10, pad=10, loc="left")

    footer(fig, pagenum)
    pdf.savefig(fig); plt.close(fig)


def page_top_sources(pdf, top_sources, by_sdg, pagenum_start):
    pn = pagenum_start
    top_sdgs = by_sdg.nlargest(5, "n_works")["sdg_id"].astype(str).tolist()
    for idx, sdg in enumerate(top_sdgs):
        d = (top_sources[top_sources["sdg_id"].astype(str) == sdg]
             .dropna(subset=["source"]).head(10).iloc[::-1])
        if d.empty:
            continue
        fig = plt.figure(figsize=A4)
        header(fig, f"05.{idx+1} · FONTES",
               f"Top 10 fontes — ODS {sdg} · {SDG_SHORT.get(sdg, '')}",
               "Periódicos, repositórios e demais canais de publicação")
        ax = fig.add_axes([0.35, 0.10, 0.57, 0.76])
        labels = [s[:55] + ("…" if len(s) > 55 else "") for s in d["source"]]
        ax.barh(labels, d["n"], color=ACCENT, height=0.7)
        for i, v in enumerate(d["n"]):
            ax.text(v + d["n"].max()*0.01, i, str(v),
                    va="center", fontsize=8.5, color=INK)
        ax.set_xlabel("Trabalhos", fontsize=9)
        ax.tick_params(axis="y", labelsize=8)
        ax.set_xlim(0, d["n"].max()*1.12)
        footer(fig, pn)
        pdf.savefig(fig); plt.close(fig)
        pn += 1
    return pn


def compute_language(works_long: pd.DataFrame):
    works = works_long.drop_duplicates("work_id").copy()
    works["language"] = works["language"].fillna("desconhecido")
    lang_general = works["language"].value_counts()

    by = (works_long.drop_duplicates(["work_id", "sdg_id"])
          .assign(language=lambda d: d["language"].fillna("desconhecido"))
          .groupby(["sdg_id", "language"]).size().unstack(fill_value=0))
    by["total"] = by.sum(axis=1)
    by = by.reset_index()
    return lang_general, by


def main():
    by_sdg = pd.read_csv(DATA / "agg_by_sdg.csv")
    by_sdg_year = pd.read_csv(DATA / "agg_by_sdg_year.csv")
    top_sources = pd.read_csv(DATA / "agg_top_sources_by_sdg.csv")
    long = pd.read_parquet(DATA / "uftm_works_by_sdg.parquet")
    raw = pd.read_parquet(DATA / "uftm_works_raw.parquet")

    lang_general, lang_by_sdg = compute_language(long)
    total_works = len(raw)
    total_with_sdg = long["work_id"].nunique()

    with PdfPages(PDF_OUT) as pdf:
        page_cover(pdf, total_works, total_with_sdg)
        page_ranking(pdf, by_sdg, 2)
        page_timeseries(pdf, by_sdg_year, by_sdg, 3)
        page_summary_table(pdf, by_sdg, 4)
        page_language(pdf, lang_general, lang_by_sdg, 5)
        page_top_sources(pdf, top_sources, by_sdg, 6)

    print(f"PDF gerado: {PDF_OUT}")


if __name__ == "__main__":
    main()
