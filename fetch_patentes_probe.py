"""Sonda do The Lens para PATENTES (diagnóstico antes de construir o coletor).

Descobre, com o token em LENS_TOKEN:
  (a) se a Patent API responde (patentes da própria UFTM);
  (b) os nomes reais dos campos de patente (titular, inventores, jurisdição...);
  (c) se a Scholarly API devolve a LISTA de patentes que citam um trabalho.

Uso:  LENS_TOKEN=seu_token python fetch_patentes_probe.py
Não grava nada — só imprime o diagnóstico.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

TOKEN = os.environ.get("LENS_TOKEN", "").strip()
PAT = "https://api.lens.org/patent/search"
SCH = "https://api.lens.org/scholarly/search"


def q(url, body):
    req = urllib.request.Request(
        url, data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        return {"erro": e.code, "msg": e.read()[:300].decode(errors="ignore")}


def main():
    if not TOKEN:
        print("LENS_TOKEN ausente."); return

    print("== (a) Patent API responde? (busca por UFTM como depositante) ==")
    body = {"query": {"match_phrase": {"applicant.name": "Universidade Federal do Triangulo Mineiro"}},
            "size": 3}
    r = q(PAT, body)
    print("  total:", r.get("total"), "| erro:", r.get("erro"), r.get("msg", ""))
    if r.get("data"):
        d = r["data"][0]
        print("  CAMPOS de uma patente:", sorted(d.keys()))
        print("  amostra:", json.dumps(d)[:400])

    print("\n== (a2) variações do nome / inglês ==")
    for nome in ["Universidade Federal do Triângulo Mineiro", "Federal University of Triangulo Mineiro"]:
        r2 = q(PAT, {"query": {"match_phrase": {"applicant.name": nome}}, "size": 1})
        print(f"  '{nome[:40]}': total={r2.get('total')} erro={r2.get('erro')}")

    print("\n== (b) Scholarly devolve a LISTA de patentes citantes? (CRISPR) ==")
    r3 = q(SCH, {"query": {"term": {"doi": "10.1126/science.1225829"}},
                 "include": ["patent_citations", "patent_citations_count"], "size": 1})
    if r3.get("data"):
        d = r3["data"][0]
        pc = d.get("patent_citations")
        print("  patent_citations_count:", d.get("patent_citations_count"))
        print("  tipo de patent_citations:", type(pc).__name__,
              "| amostra:", json.dumps(pc)[:200] if pc else pc)
    else:
        print("  erro:", r3.get("erro"), r3.get("msg", ""))


if __name__ == "__main__":
    main()
