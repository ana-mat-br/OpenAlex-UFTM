# Nota Técnica DAAD nº ___/2026

**Assunto:** Atribuição de DOI às teses e dissertações da UFTM — diagnóstico, benefícios e plano de implantação

**De:** Diretoria de Avaliação e Análise de Dados (DAAD) — PROPPG/UFTM

**Para:** Pró-Reitoria de Pesquisa e Pós-Graduação (PROPPG)

**Data:** _____ / _____ / 2026

---

## 1. Objeto

Esta nota recomenda que a UFTM passe a atribuir **DOI (Digital Object Identifier)** a todas as suas teses e dissertações, por meio da agência **DataCite**, representada no Brasil pelo **IBICT**. Apresenta o diagnóstico da situação atual (com dados do Painel DAAD), os benefícios institucionais, as razões pelas quais isso ainda não é feito e um plano de implantação em fases, com responsáveis e custos.

## 2. Diagnóstico — situação atual

A produção da pós-graduação *stricto sensu* da UFTM está, hoje, **praticamente invisível fora da BDTD**. Levantamento feito pela DAAD nas fontes abertas mostra:

| Fonte | Teses/dissertações da UFTM | Observação |
|---|---|---|
| **BDTD (IBICT)** | **1.953** (1.727 dissertações + 226 teses), 2006–2025 | Base completa; **0 com DOI** |
| **OpenAlex** | **~19** | Indexa sobretudo o que tem DOI |
| **DataCite** | **0 teses** | Nenhuma tese da UFTM possui DOI |
| **OpenAIRE** | espelha a BDTD | Sem ganho próprio |

Ou seja: as **1.953** teses e dissertações existem e estão acessíveis na BDTD, mas como **nenhuma possui DOI**, elas não são captadas pelos grandes índices internacionais (OpenAlex, DataCite Commons, OpenAIRE, BASE) nem rastreadas em métricas de citação. O único motivo dessa invisibilidade é a **ausência do identificador persistente** — não a falta de produção nem de acesso aberto.

**Para dimensionar o contraste:** as instituições onde teses de autores ligados à UFTM acabaram depositadas já registram DOI para suas dissertações em larga escala — na Crossref, a **USP** acumula ~148,6 mil teses com DOI; a **UNICAMP**, ~67,4 mil; a **UFU**, ~12,9 mil; a **UnB**, ~10,5 mil. A **UFTM: zero**. Os volumes refletem também o porte e o acervo histórico de cada instituição; o ponto não é o número absoluto, e sim o **hábito de atribuir DOI**, ausente na UFTM.

## 3. O que é o DOI e as duas vias de registro (DataCite e Crossref)

O **DOI** é um identificador persistente: um endereço permanente que aponta sempre para o documento, mesmo que o sistema do repositório mude de endereço no futuro. É o padrão internacional de citação de produção científica.

Existem **duas agências** que emitem DOI, e **ambas servem para teses e dissertações** — a UFTM pode escolher uma ou usar as duas:

- **DataCite — via IBICT.** Agência internacional voltada a **objetos de pesquisa** (teses, dissertações, dados, software). No Brasil, o **IBICT** é o ponto de articulação e suporte técnico, no âmbito do consórcio nacional de ciência aberta (iniciativa **CoNCienciA**, com CNPq e RNP). A instituição adere, recebe um **prefixo próprio** (`10.xxxxx`) e cunha os DOIs a partir do seu repositório. É o caminho usual para repositórios e dados de pesquisa.
- **Crossref — adesão direta (ou via convênio).** Tradicionalmente voltada a artigos, também registra teses (tipo *dissertation*). Na prática, é a via que as **maiores universidades brasileiras já usam** para suas teses: **USP, UNICAMP, UFU e UnB** registram o DOI das dissertações na Crossref, com o DOI resolvendo para o repositório de cada uma (o DOI de uma tese da USP, por exemplo, leva a `teses.usp.br`).

Em ambos os casos o resultado é o mesmo: um DOI que torna a tese citável e rastreável. A escolha entre **DataCite/IBICT** e **Crossref** é operacional (custo por DOI, integração com o DSpace, conveniência); o essencial é **passar a atribuir DOI**.

## 4. Benefícios para a UFTM

**Visibilidade e indexação internacional**
- As teses passam a ser **localizáveis e citáveis** no OpenAlex, DataCite Commons, OpenAIRE, BASE e Google Scholar — hoje só aparecem na BDTD.
- Apoio direto à **internacionalização dos PPGs**, fator relevante para programas que buscam elevar conceito (notas 6 e 7) na avaliação da CAPES.

**Mensuração e avaliação**
- Torna possível **contar citações e usos (downloads/visualizações)** das teses — a DataCite oferece métricas de uso padronizadas.
- **Alimenta o próprio Painel DAAD** com uma nova dimensão (pós-graduação), substituindo, com dado aberto, parte do que ferramentas pagas (SciVal, Stela Experta) cobram caro.
- Alinha-se à agenda de **Ciência Aberta** da CAPES/MCTI e facilita o acompanhamento de indicadores dos programas.

**Integridade, autoria e preservação**
- **Atribuição correta de autoria**: o DOI vincula autor (via **ORCID**) e orientador, reduzindo ambiguidade de nomes.
- **Link que não quebra**: boa prática de preservação digital (combina com a Rede Cariniana, do IBICT).
- Os **conjuntos de dados** gerados nas teses também podem receber DOI próprio — atendendo a exigências crescentes de financiadores quanto a dados abertos.

**Custo-benefício**
- O custo é **modesto** e a infraestrutura usa o repositório que a UFTM já mantém — muito inferior ao de soluções comerciais de bibliometria.

### Reflexo potencial em rankings universitários

O efeito existe, mas varia conforme o que cada ranking mede — e convém **não exagerar**:

- **Rankings de visibilidade web — efeito direto.** O **Ranking Web of Universities (Webometrics)** e seu **Transparent Ranking / Ranking Web of Repositories** medem explicitamente o conteúdo do repositório indexado no **Google Scholar**, e penalizam erros de metadados. Teses com DOI e metadados corretos aumentam diretamente os registros indexados — e o Google Scholar é justamente onde as teses recebem citações.
- **Rankings baseados em Scopus/Web of Science — THE, QS, CWUR — efeito indireto, porém real.** As teses, em geral, **não** estão na Scopus; logo o DOI **não soma citações diretamente** nesses rankings (no **THE**, a "Qualidade de Pesquisa" pesa **30%** e usa dados da Scopus/Elsevier; na **CWUR**, os indicadores de pesquisa somam **40%**, contando artigos e citações). O ganho vem por dois caminhos comprovados: (1) **atribuição correta de afiliação e autoria** — há evidência de que artigos "perdidos" por divergência de afiliação custam posições no ranking, e DOI + **ORCID** + **ROR** reduzem esse problema; (2) **maior visibilidade e citação** dos trabalhos da instituição, efeito associado ao uso de identificadores persistentes.
- **Leitura honesta.** Atribuir DOI às teses **não é atalho** para subir no THE ou na QS. É uma prática de base (qualidade de dados + ciência aberta) cujo retorno em rankings se dá sobretudo em **visibilidade** (Webometrics), em **citações via Google Scholar** e na **atribuição correta** que alimenta todos os indicadores bibliométricos.

*Fontes:* [THE — metodologia 2025](https://www.timeshighereducation.com/world-university-rankings/world-university-rankings-2025-methodology) · [CWUR — metodologia](https://cwur.org/methodology/world-university-rankings.php) · [Webometrics — Ranking Web of Repositories (Transparent Ranking)](https://repositories.webometrics.info/en/transparent) · [Discrepâncias de afiliação entre Scopus, WoS, Dimensions e Microsoft Academic e impacto em rankings — *Quantitative Science Studies*, MIT Press (2022)](https://direct.mit.edu/qss/article/3/1/99/109079/The-prevalence-and-impact-of-university) · [Efeito do ORCID na visibilidade e recuperação de publicações — *Scientometrics* (2025)](https://link.springer.com/article/10.1007/s11192-025-05505-w)

## 5. Por que a UFTM ainda não faz isso

Não se trata de uma decisão recusada, e sim de um passo que **nunca foi formalizado** — em geral por envolver mais de um setor:

1. **Articulação intersetorial ausente.** Depende de PROPPG (decisão e norma) + Sistema de Bibliotecas (curadoria) + TI (repositório), e nunca houve um encaminhamento conjunto.
2. **Sem adesão formal a uma agência.** A UFTM nunca aderiu a uma agência de DOI (DataCite/IBICT **ou** Crossref), logo **não possui prefixo DOI**.
3. **Repositório sem o módulo de DOI configurado.** O `bdtd.uftm.edu.br` (DSpace) tem suporte nativo a DataCite (e há plugins para Crossref), mas a função não está habilitada.
4. **Ausência de norma** que torne o DOI parte obrigatória do fluxo de depósito da tese/dissertação.
5. **Qualidade de metadados** ainda irregular (ORCID e área CNPq incompletos em parte dos registros), o que é pré-requisito para um DOI bem formado.
6. **Percepção de custo/complexidade** sem diagnóstico prévio — que esta nota busca suprir.

## 6. Como começar — plano de implantação por fases

**Fase 0 — Decisão e grupo de trabalho (PROPPG).** Instituir um GT enxuto com PROPPG, Sistema de Bibliotecas, TI/STI e DAAD, com prazo definido.

**Fase 1 — Adesão a uma agência de DOI e obtenção do prefixo.** Escolher a via: **DataCite via IBICT** (serviço de DOI / Rede Cariniana — `cariniana@ibict.br`, com adesão ao consórcio nacional) **ou Crossref** (adesão direta, como já fazem USP, UNICAMP, UFU e UnB para suas teses). Em qualquer das duas, **obter o prefixo DOI institucional** (`10.xxxxx`).

**Fase 2 — Habilitação técnica no repositório.** Configurar no DSpace o módulo da agência escolhida (DataCite ou Crossref); mapear os metadados ao schema correspondente (na DataCite, os campos obrigatórios são *Creator, Title, Publisher, PublicationYear, ResourceType*); validar em ambiente de teste antes de produção.

**Fase 3 — Qualidade de metadados e ORCID.** Exigir **ORCID** do autor (e, idealmente, do orientador) e completar área CNPq, idioma, resumo e licença (ex.: Creative Commons).

**Fase 4 — Normatização.** Publicar resolução/portaria da PROPPG tornando o **DOI obrigatório** no depósito de toda tese/dissertação homologada, e atualizar o fluxo nas secretarias dos PPGs e na Biblioteca.

**Fase 5 — Acervo retroativo.** Cunhar DOI, em lote, para o acervo já depositado (as ~1.950 teses e dissertações existentes).

**Fase 6 — Monitoramento.** Acompanhar, pelo Painel DAAD, a aparição progressiva das teses no OpenAlex, DataCite e OpenAIRE — evidência objetiva do retorno.

> **Piloto sugerido:** começar por **1 ou 2 PPGs** (Fases 1–4) antes de estender a todos e ao acervo retroativo (Fase 5).

## 7. Custos e recursos necessários

- **Via DataCite/IBICT:** no modelo do consórcio nacional, o prefixo é obtido **sem custo de aquisição**, com pagamento **por DOI atribuído** (historicamente baixo, da ordem de poucos centavos a ~1 USD por DOI a depender do convênio). **Os valores vigentes devem ser confirmados diretamente com o IBICT.**
- **Via Crossref:** envolve **anuidade de associada** (em faixas, conforme o porte) mais uma **taxa por DOI de conteúdo** registrado; é a via adotada por USP, UNICAMP, UFU e UnB para teses. **Confirmar valores vigentes com a Crossref** (ou via convênio nacional, p. ex. ABEC).
- **Recursos humanos:** equipe do Sistema de Bibliotecas (curadoria/operação) e do setor de TI (configuração e manutenção do DSpace). **Não há necessidade de software pago.**
- **Comparativo:** em qualquer das vias, o custo total é muito inferior ao de ferramentas comerciais de análise (SciVal, Stela Experta), que o Painel DAAD já substitui parcialmente com dados abertos.

## 8. Governança sugerida

| Ator | Responsabilidade |
|---|---|
| **PROPPG** | Decisão, norma (resolução), articulação intersetorial |
| **Sistema de Bibliotecas (SIB)** | Gestão do prefixo, curadoria de metadados, operação da cunhagem |
| **TI / STI** | Configuração e manutenção do módulo de DOI (DataCite ou Crossref) no DSpace |
| **DAAD** | Diagnóstico, monitoramento de indicadores e demonstração de valor (Painel DAAD) |
| **Secretarias dos PPGs** | Garantir ORCID e metadados completos no momento do depósito |

## 9. Recomendação e encaminhamento

A DAAD recomenda que a **PROPPG institua o grupo de trabalho (Fase 0)** e inicie o **contato de adesão a uma agência de DOI — IBICT/DataCite ou Crossref — (Fase 1)** ainda neste semestre, com **piloto em 1–2 PPGs**. O investimento é baixo, a infraestrutura já existe, e o retorno — visibilidade internacional, mensurabilidade e alinhamento à Ciência Aberta — é alto e diretamente verificável pelo próprio Painel DAAD.

---

### Anexo — Fontes consultadas

- BDTD — Biblioteca Digital Brasileira de Teses e Dissertações (IBICT): https://bdtd.ibict.br
- IBICT — Solicitar prefixo DOI (Wiki): https://wiki.ibict.br/index.php/Solicitar_o_prefixo_DOI
- Rede Cariniana (IBICT) — contato `cariniana@ibict.br`: https://cariniana.ibict.br
- CNPq — Consórcio CoNCienciA (Ciência Aberta / DataCite): https://www.gov.br/cnpq
- Atribuição de DOI em Teses e Dissertações da UFU (relato de experiência) — Revista Ciência da Informação (IBICT): https://revista.ibict.br/ciinf/article/view/4854
- DataCite — agência de DOI para objetos de pesquisa: https://datacite.org
- Crossref — agência de DOI (via usada por USP, UNICAMP, UFU, UnB para teses): https://www.crossref.org
- ABEC Brasil — convênio de atribuição de DOI (Crossref): https://www.abecbrasil.org.br/parcerias/atribuicao-doi/

**Rankings (Seção 4):**
- THE — World University Rankings, metodologia 2025: https://www.timeshighereducation.com/world-university-rankings/world-university-rankings-2025-methodology
- CWUR — metodologia: https://cwur.org/methodology/world-university-rankings.php
- Webometrics — Ranking Web of Repositories (Transparent Ranking): https://repositories.webometrics.info/en/transparent
- Discrepâncias de afiliação entre bases e impacto em rankings — *Quantitative Science Studies*, MIT Press (2022): https://direct.mit.edu/qss/article/3/1/99/109079/The-prevalence-and-impact-of-university
- Efeito do ORCID na visibilidade e recuperação de publicações — *Scientometrics* (2025): https://link.springer.com/article/10.1007/s11192-025-05505-w

*Levantamento de dados (BDTD, OpenAlex, DataCite, Crossref) realizado pela DAAD em junho/2026, reprodutível pelo coletor `fetch_bdtd.py` do Painel DAAD. Números de teses com DOI por instituição (USP, UNICAMP, UFU, UnB): Crossref REST API, filtro `type:dissertation` por prefixo.*
