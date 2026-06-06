# Painel DAAD — UFTM

Painel web da produção científica da UFTM (Diretoria de Avaliação e Análise de Dados —
DAAD/PROPPG), com dados do **OpenAlex** (ROR `01av3m334`). Construído em **Streamlit**.

Reproduz, com fontes abertas, análises no estilo SciVal/Stela Experta: indicadores
**normalizados** (FWCI, percentis top 1%/10%), benchmarking com as federais de MG e com pares de porte semelhante no país,
colaboração/internacionalização, ODS e impacto social. Visual claro e minimalista
(verde UFTM #00983A, Inter + Palatino).

## Páginas

Visão Geral · **Impacto científico** (FWCI e percentis mundiais) · **Comparação** (federais de MG + pares de porte semelhante no Brasil) · **ODS** · **Financiamento** · **Patentes** · **Ciência Aberta** · Colaboração (com rede de coautoria) · ODS · Temas · Pesquisadores · **Onde
publicamos** · **Qualidade das revistas** (quartis Scimago) · Explorar · **Transparência**
(glossário + metodologia) — navegação por menu lateral (`streamlit-option-menu`).

Linguagem voltada à **prestação de contas com a sociedade**: cada indicador tem um "como
ler" em português claro, e a aba Transparência explica os termos e a metodologia.

## Rodar no seu computador

```bash
.venv/bin/streamlit run app.py
```

Abre sozinho no navegador (`http://localhost:8501`). Para alguém na mesma rede
acessar, o Streamlit também mostra um endereço "Network URL".

## Atualizar os dados

```bash
.venv/bin/python fetch_uftm_ods.py      # produção + ODS + FWCI/percentis/OA/DOAJ (data/*.parquet)
.venv/bin/python fetch_observatorio.py  # benchmarking, colaboração, pesquisadores, temas (data/*.csv)
.venv/bin/python fetch_scimago.py       # quartis Scimago Q1–Q4 por ISSN (data/scimago_quartis.csv)
.venv/bin/python fetch_colaboracao.py   # rede de coautoria (data/rede_autores_*.csv)
LENS_TOKEN=seu_token \
  .venv/bin/python fetch_lens.py        # patentes que citam a UFTM (opcional; token grátis do The Lens)
```

### Ativar patentes (Impacto Social)

A seção de patentes usa o **The Lens** (token acadêmico gratuito):
1. Crie conta em **lens.org** e solicite acesso à **Scholarly API**.
2. Guarde o token como segredo **`LENS_TOKEN`** no GitHub (Settings → Secrets and
   variables → Actions) — o coletor mensal passa a trazer patentes automaticamente.
3. Ou rode local: `LENS_TOKEN=seu_token python fetch_lens.py` e dê commit do
   `data/lens_patentes.csv`.

O `fetch_observatorio.py` compara a UFTM com as 11 universidades federais de MG
(UFMG, UFU, UFV, UFJF, UFSJ, UFOP, UFLA, UFVJM, UNIFAL, UNIFEI) e usa agregações
leves do OpenAlex (não baixa todos os works).

O painel lê o cache em `data/`, então é rápido. Rode quando quiser dados frescos.

## Publicar na internet (Streamlit Community Cloud — grátis)

1. Crie uma conta no **GitHub** e suba este projeto num repositório
   (inclua `app.py`, `requirements.txt` e a pasta `data/` com os `.parquet`).
2. Acesse **https://share.streamlit.io** e faça login com o GitHub.
3. Clique em **"New app"**, escolha o repositório e o arquivo `app.py`.
4. Clique em **Deploy**. Em ~2 min você recebe uma URL pública, ex.:
   `https://observatorio-proppg.streamlit.app`
5. **Pronto:** mande esse link por e-mail, coloque num slide / QR code, fixe no site da PROPPG.

> Para atualizar o painel publicado, basta dar `git push` no repositório —
> o Streamlit Cloud reimplanta automaticamente.

### Versão oficial (depois)

Quando a PROPPG adotar, peça ao **NTI/DTI da UFTM** para hospedar num subdomínio
institucional (ex.: `observatorio.uftm.edu.br`).

## Observação metodológica

A marcação de ODS é uma **estimativa automática** do classificador **Aurora/mBERT** do
OpenAlex (score ≥ 0,4) — indicador probabilístico, não declarado pelos autores. **FWCI** e
**percentis** são normalizados por campo (metodologia equivalente à do Scopus; valores não
comparáveis entre bases). Para o FWCI, a janela de citação (ano + 3) fica incompleta nos
2 anos mais recentes — a aba Impacto científico permite excluí-los.

## APIs gratuitas no roadmap (impacto social e rankings)

Crossref, ROR v2, Scimago (quartis Q1–Q4), DOAJ, Unpaywall, ORCID, OpenCitations,
BIP! Scholar; e para impacto societal: The Lens (patentes), Overton/Sage Policy
Profiles (políticas públicas) e Altmetric (atenção online).
