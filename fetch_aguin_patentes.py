"""Coleta o PORTFÓLIO TECNOLÓGICO da UFTM (patentes e softwares) da Agência UFTM de
Inovação (AGUIN), fonte oficial da própria universidade.

O site (aguin.uftm.edu.br) é um app Vue; os dados ficam num módulo JS embutido. Aqui a
gente descobre o chunk dinamicamente (resiste a mudança de hash), converte o objeto JS
para JSON (lida com aspas ", ' e crase) e grava data/portfolio_uftm.csv.

Uso:  python fetch_aguin_patentes.py
"""
from __future__ import annotations

import json
import re
import urllib.request
from pathlib import Path

import pandas as pd

BASE = "https://aguin.uftm.edu.br"
OUT = Path(__file__).parent / "data"
OUT.mkdir(exist_ok=True)


def _baixar(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (PainelDAAD)"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8", "replace")


def _js_array_to_json(s: str) -> str:
    """Converte um array-literal JS (aspas ", ' e crase; chaves sem aspas) em JSON."""
    out, i, n = [], 0, len(s)
    while i < n:
        c = s[i]
        if c in "\"'`":                                  # string literal (qualquer aspa)
            q = c
            i += 1
            buf = ['"']
            while i < n and s[i] != q:
                ch = s[i]
                if ch == "\\":
                    nxt = s[i + 1] if i + 1 < n else ""
                    buf.append("\\" + nxt if nxt in "\"\\/bfnrtu" else nxt)
                    i += 2
                    continue
                buf.append({'"': '\\"', "\n": "\\n", "\r": "\\r", "\t": "\\t"}.get(ch, ch))
                i += 1
            buf.append('"')
            i += 1
            out.append("".join(buf))
        elif c in "{,":                                  # quoteia a chave que vem em seguida
            out.append(c)
            i += 1
            j = i
            while j < n and s[j] in " \n\r\t":
                j += 1
            k = j
            while k < n and (s[k].isalpha() or s[k] == "_"):
                k += 1
            if k > j and k < n and s[k] == ":":
                out.append('"' + s[j:k] + '"')
                i = k
        else:
            out.append(c)
            i += 1
    return "".join(out)


def main() -> None:
    home = _baixar(BASE + "/")
    bundle_path = re.search(r"assets/index-[A-Za-z0-9_-]+\.js", home).group(0)
    bundle = _baixar(f"{BASE}/{bundle_path}")
    chunk_path = re.search(r"assets/portfolio-[A-Za-z0-9_-]+\.js", bundle).group(0)
    js = _baixar(f"{BASE}/{chunk_path}")

    arr = re.search(r"const \w+=(\[.*\])\s*;?\s*export", js, re.S).group(1)
    dados = json.loads(_js_array_to_json(arr))
    df = pd.DataFrame(dados)
    df.columns = [c.lower() for c in df.columns]
    df.to_csv(OUT / "portfolio_uftm.csv", index=False)
    n_pat = int((df["tipo"].str.upper() == "PATENTE").sum()) if "tipo" in df else 0
    print(f"portfólio AGUIN: {len(df)} itens ({n_pat} patentes) -> portfolio_uftm.csv")


if __name__ == "__main__":
    main()
