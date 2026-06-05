# Observatório PROPPG/UFTM

Painel web da produção científica da UFTM, com dados do **OpenAlex** (ROR `01av3m334`).
Construído em **Streamlit** (Python).

## Rodar no seu computador

```bash
.venv/bin/streamlit run app.py
```

Abre sozinho no navegador (`http://localhost:8501`). Para alguém na mesma rede
acessar, o Streamlit também mostra um endereço "Network URL".

## Atualizar os dados

```bash
.venv/bin/python fetch_uftm_ods.py      # produção + ODS (data/*.parquet)
.venv/bin/python fetch_observatorio.py  # benchmarking, colaboração, pesquisadores, temas (data/*.csv)
```

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

A marcação de ODS é uma **estimativa automática** do classificador de IA
**Aurora/mBERT** do OpenAlex (score ≥ 0,4). É um indicador probabilístico, não uma
classificação declarada pelos autores — pode divergir de painéis manuais (ex.: Capivara).
