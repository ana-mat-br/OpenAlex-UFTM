"""Monta a rede de coautoria dos pesquisadores da UFTM a partir do OpenAlex.

Nós = autores afiliados à UFTM; arestas = nº de produções em coautoria.
Pré-computa layout (spring), centralidade (grau e intermediação) e comunidades,
gravando data/rede_autores_nos.csv e data/rede_autores_arestas.csv — o app só desenha.
"""
from __future__ import annotations

import os
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

import networkx as nx
import pandas as pd
from pyalex import Works, config

from fetch_observatorio import _chave_autor  # mesma deduplicação dos Pesquisadores

ROR_UFTM = "01av3m334"
OUT = Path(__file__).parent / "data"
OUT.mkdir(exist_ok=True)
config.email = os.environ.get("OPENALEX_EMAIL", "anapaula.fernandes@uftm.edu.br")

TOP_N = 150          # nº de autores (por produção) que entram na rede
PESO_MIN = 2         # mínimo de coautorias para manter a aresta


def coletar():
    n_works = Counter()             # pessoa (chave) -> nº de produções na UFTM
    nomes = {}                      # chave -> melhor nome (variante mais completa)
    pares = Counter()               # (a, b) -> nº de coautorias
    campos = defaultdict(Counter)   # chave -> Counter de grandes áreas (para rotular grupos)
    q = (Works().filter(authorships={"institutions": {"ror": ROR_UFTM}})
         .select(["id", "authorships", "primary_topic"]))
    print(f"works: {q.count()}")
    for page in q.paginate(per_page=200, n_max=None):
        for w in page:
            pt = w.get("primary_topic") or {}
            campo = ((pt.get("subfield") or {}).get("display_name")  # subárea: mais específica
                     or (pt.get("field") or {}).get("display_name"))
            chaves = []
            for a in (w.get("authorships") or []):
                rors = {(i.get("ror") or "").rsplit("/", 1)[-1]
                        for i in (a.get("institutions") or [])}
                if ROR_UFTM not in rors:
                    continue
                au = a.get("author") or {}
                nome = au.get("display_name") or (au.get("id") or "").rsplit("/", 1)[-1]
                if not nome:
                    continue
                k = _chave_autor(nome)           # junta a mesma pessoa dividida em vários ids
                chaves.append(k)
                if len(nome) > len(nomes.get(k, "")):
                    nomes[k] = nome
                if campo:
                    campos[k][campo] += 1
            chaves = sorted(set(chaves))
            for k in chaves:
                n_works[k] += 1
            for a, b in combinations(chaves, 2):
                pares[(a, b)] += 1
    return n_works, nomes, pares, campos


def main():
    n_works, nomes, pares, campos = coletar()
    topo = {a for a, _ in n_works.most_common(TOP_N)}

    G = nx.Graph()
    for a in topo:
        G.add_node(a, nome=nomes.get(a, a), works=n_works[a])
    for (a, b), w in pares.items():
        if a in topo and b in topo and a != b and w >= PESO_MIN:
            G.add_edge(a, b, weight=w)
    G.remove_nodes_from(list(nx.isolates(G)))
    print(f"rede: {G.number_of_nodes()} nós, {G.number_of_edges()} arestas")

    pos = nx.spring_layout(G, weight="weight", seed=42, k=0.6)
    grau = dict(G.degree(weight="weight"))
    betw = nx.betweenness_centrality(G, weight="weight")
    comunidades = list(nx.community.greedy_modularity_communities(G, weight="weight"))
    comuni, area_com = {}, {}
    for i, com in enumerate(comunidades):     # já vêm ordenadas da maior para a menor
        for a in com:
            comuni[a] = i
        cont = Counter()
        for a in com:
            cont.update(campos.get(a, {}))
        area_com[i] = cont.most_common(1)[0][0] if cont else "Diversos"  # subárea crua (EN)

    nos = pd.DataFrame([{
        "id": a, "nome": G.nodes[a]["nome"], "works": G.nodes[a]["works"],
        "x": round(pos[a][0], 4), "y": round(pos[a][1], 4),
        "grau": grau.get(a, 0), "betw": round(betw.get(a, 0), 4),
        "comunidade": comuni.get(a, 0),
        "grupo": area_com.get(comuni.get(a, 0), "Diversos"),
    } for a in G.nodes])
    nos.to_csv(OUT / "rede_autores_nos.csv", index=False)

    arestas = pd.DataFrame([{"origem": a, "destino": b, "peso": d["weight"]}
                            for a, b, d in G.edges(data=True)])
    arestas.to_csv(OUT / "rede_autores_arestas.csv", index=False)
    print(f"comunidades: {nos['comunidade'].nunique()} | "
          f"mais central: {nos.sort_values('betw', ascending=False).iloc[0]['nome']}")


if __name__ == "__main__":
    main()
