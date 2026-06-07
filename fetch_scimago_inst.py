"""Coletor (PROTÓTIPO) do Scimago Institutions Rankings (SIR) — UFTM e pares.

O SIR (scimagoir.com) ranqueia instituições por três fatores: Research (base
Scopus), Innovation (patentes) e Societal (visibilidade web / altmetrics). É fonte
real e gratuita, do mesmo grupo do Scimago Journal Rank que o painel já usa
(fetch_scimago.py). O Societal cobre, em parte, o ângulo de "visibilidade" que
buscávamos no Webometrics.

ACESSO: a página do SIR fica atrás do Cloudflare (challenge JavaScript), então o
download automático costuma dar 403. O jeito garantido é baixar pelo NAVEGADOR:

    1) Abra:  https://www.scimagoir.com/rankings.php?country=BRA&sector=Higher%20educ.
    2) Clique no ícone de Excel (ou abra direto, no navegador):
       https://www.scimagoir.com/rankings.php?country=BRA&sector=Higher%20educ.&out=xls
    3) Salve em ~/ODS (ex.: sir_brasil.xls) e rode:
       python fetch_scimago_inst.py sir_brasil.xls

Sem argumento, ele TENTA baixar (pode falhar no Cloudflare). O arquivo do Scimago
chama-se .xls mas é um CSV separado por ";". Gera data/scimago_inst_uftm.csv.
"""
from __future__ import annotations

import io
import re
import socket
import sys
import unicodedata
import urllib.error
import urllib.request
from pathlib import Path

import pandas as pd

OUT = Path(__file__).parent / "data"
OUT.mkdir(exist_ok=True)

SIR_URL = ("https://www.scimagoir.com/rankings.php"
           "?country=BRA&sector=Higher%20educ.&out=xls")
HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"),
    "Referer": "https://www.scimagoir.com/rankings.php",
    "Accept": "text/csv,application/vnd.ms-excel,*/*",
}

# Mesmas instituições-alvo das outras abas (sigla -> trecho distintivo, sem acento).
ALVOS = {
    "UFTM": "federal do triangulo mineiro",
    "USP": "universidade de sao paulo",
    "UNICAMP": "estadual de campinas",
    "UFU": "federal de uberlandia",
    "UnB": "universidade de brasilia",
}


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s or ""))
    s = "".join(c for c in s if not unicodedata.combining(c))
    return " ".join(s.lower().split())


def _num(s):
    d = re.sub(r"[^\d]", "", str(s or ""))
    return int(d) if d else None


def _baixa() -> bytes:
    req = urllib.request.Request(SIR_URL, headers=HEADERS)
    try:
        return urllib.request.urlopen(req, timeout=120).read()
    except (urllib.error.URLError, urllib.error.HTTPError, socket.timeout) as e:
        raise RuntimeError(
            f"Download automático falhou ({e}). O SIR fica atrás do Cloudflare. "
            "Baixe o Excel pelo navegador e rode: python fetch_scimago_inst.py <arquivo>. "
            "Veja as instruções no topo de fetch_scimago_inst.py.")


def _ler(src) -> pd.DataFrame:
    """Lê o arquivo do Scimago: tenta CSV ';' (formato real) e cai p/ Excel."""
    try:
        df = pd.read_csv(src, sep=";", decimal=",", low_memory=False)
        if df.shape[1] >= 4:
            return df
    except Exception:
        pass
    if hasattr(src, "seek"):
        src.seek(0)
    return pd.read_excel(src)


def main(fonte: str | None = None) -> None:
    if fonte and Path(fonte).exists():
        print(f"(lendo arquivo local: {fonte})")
        df = _ler(fonte)
    else:
        df = _ler(io.BytesIO(_baixa()))

    cols = {c: _norm(c) for c in df.columns}

    def col(*chaves, exato=None):
        for c, n in cols.items():
            if exato is not None and n == exato:
                return c
        for c, n in cols.items():
            if exato is None and any(k in n for k in chaves):
                return c
        return None

    c_nome = col("organization", "institution", "name")
    c_rank = col(exato="rank") or col("ranking")
    c_overall = col("overall")
    c_research = col("research")
    c_innov = col("innovation")
    c_soc = col("societal")
    if c_nome is None or all(x is None for x in (c_overall, c_research, c_innov, c_soc)):
        raise RuntimeError("Colunas do SIR não reconhecidas. Colunas encontradas: "
                           f"{list(df.columns)}. Ajuste o mapeamento em col().")

    linhas = []
    for nrank, (_, r) in enumerate(df.iterrows(), start=1):
        nome = str(r[c_nome])
        n = _norm(nome)
        sigla = next((s for s, k in ALVOS.items() if k in n), None)
        if not sigla:
            continue
        linhas.append({
            "sigla": sigla,
            "instituicao": nome.strip(),
            "rank_nacional": _num(r[c_rank]) if c_rank else nrank,
            "overall": _num(r[c_overall]) if c_overall else None,
            "research": _num(r[c_research]) if c_research else None,
            "innovation": _num(r[c_innov]) if c_innov else None,
            "societal": _num(r[c_soc]) if c_soc else None,
        })

    if not linhas:
        raise RuntimeError("Nenhuma instituição-alvo encontrada. Confira os nomes "
                           f"na coluna '{c_nome}' (ex.: {df[c_nome].head(3).tolist()}).")

    out = (pd.DataFrame(linhas).drop_duplicates("sigla")
           .sort_values("rank_nacional").reset_index(drop=True))
    out.to_csv(OUT / "scimago_inst_uftm.csv", index=False)
    print("Scimago Institutions (Brasil) — data/scimago_inst_uftm.csv:")
    for r in out.itertuples():
        print(f"  {r.sigla:<8} BR#{r.rank_nacional} | overall {r.overall} · "
              f"research {r.research} · innovation {r.innovation} · societal {r.societal}")
    faltam = set(ALVOS) - set(out["sigla"])
    if faltam:
        print("  (não encontradas:", ", ".join(faltam), "— confira o nome no arquivo)")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
