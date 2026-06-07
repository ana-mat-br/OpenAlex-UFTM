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

## 3. O que é o DOI e qual o papel do IBICT/DataCite

O **DOI** é um identificador persistente: um endereço permanente que aponta sempre para o documento, mesmo que o sistema do repositório mude de endereço no futuro. É o padrão internacional de citação de produção científica.

- **DataCite** é a agência internacional que emite DOI para **objetos de pesquisa** — teses, dissertações, conjuntos de dados, software. (A **Crossref** é a agência voltada a **artigos de periódicos**; por isso a via correta para teses é a DataCite.)
- No Brasil, o **IBICT** é o ponto de articulação e suporte técnico para DOI via DataCite, no âmbito do consórcio nacional de ciência aberta (iniciativa **CoNCienciA**, com CNPq e RNP). A instituição adere ao consórcio, recebe um **prefixo DOI próprio** (`10.xxxxx`) e passa a cunhar os DOIs a partir do seu repositório.

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

## 5. Por que a UFTM ainda não faz isso

Não se trata de uma decisão recusada, e sim de um passo que **nunca foi formalizado** — em geral por envolver mais de um setor:

1. **Articulação intersetorial ausente.** Depende de PROPPG (decisão e norma) + Sistema de Bibliotecas (curadoria) + TI (repositório), e nunca houve um encaminhamento conjunto.
2. **Sem adesão formal a uma agência.** A UFTM nunca aderiu à DataCite via IBICT, logo **não possui prefixo DOI**.
3. **Repositório sem o módulo de DOI configurado.** O `bdtd.uftm.edu.br` (DSpace) tem suporte nativo a DataCite, mas a função não está habilitada.
4. **Ausência de norma** que torne o DOI parte obrigatória do fluxo de depósito da tese/dissertação.
5. **Qualidade de metadados** ainda irregular (ORCID e área CNPq incompletos em parte dos registros), o que é pré-requisito para um DOI bem formado.
6. **Percepção de custo/complexidade** sem diagnóstico prévio — que esta nota busca suprir.

## 6. Como começar — plano de implantação por fases

**Fase 0 — Decisão e grupo de trabalho (PROPPG).** Instituir um GT enxuto com PROPPG, Sistema de Bibliotecas, TI/STI e DAAD, com prazo definido.

**Fase 1 — Adesão à DataCite via IBICT.** Contatar o IBICT (serviço de DOI / Rede Cariniana — `cariniana@ibict.br`), formalizar a adesão ao consórcio nacional e **obter o prefixo DOI institucional**.

**Fase 2 — Habilitação técnica no repositório.** Configurar o módulo DataCite no DSpace; mapear os metadados ao **DataCite Metadata Schema** (campos obrigatórios: *Creator, Title, Publisher, PublicationYear, ResourceType*); validar em ambiente de teste antes de produção.

**Fase 3 — Qualidade de metadados e ORCID.** Exigir **ORCID** do autor (e, idealmente, do orientador) e completar área CNPq, idioma, resumo e licença (ex.: Creative Commons).

**Fase 4 — Normatização.** Publicar resolução/portaria da PROPPG tornando o **DOI obrigatório** no depósito de toda tese/dissertação homologada, e atualizar o fluxo nas secretarias dos PPGs e na Biblioteca.

**Fase 5 — Acervo retroativo.** Cunhar DOI, em lote, para o acervo já depositado (as ~1.950 teses e dissertações existentes).

**Fase 6 — Monitoramento.** Acompanhar, pelo Painel DAAD, a aparição progressiva das teses no OpenAlex, DataCite e OpenAIRE — evidência objetiva do retorno.

> **Piloto sugerido:** começar por **1 ou 2 PPGs** (Fases 1–4) antes de estender a todos e ao acervo retroativo (Fase 5).

## 7. Custos e recursos necessários

- **Adesão (IBICT/DataCite):** no modelo do consórcio nacional, o prefixo é obtido **sem custo de aquisição**, com pagamento **por DOI atribuído** (historicamente baixo, da ordem de poucos centavos a ~1 USD por DOI a depender do convênio). **Os valores vigentes devem ser confirmados diretamente com o IBICT.**
- **Recursos humanos:** equipe do Sistema de Bibliotecas (curadoria/operação) e do setor de TI (configuração e manutenção do DSpace). **Não há necessidade de software pago.**
- **Comparativo:** o custo total é muito inferior ao de ferramentas comerciais de análise (SciVal, Stela Experta), que o Painel DAAD já substitui parcialmente com dados abertos.

## 8. Governança sugerida

| Ator | Responsabilidade |
|---|---|
| **PROPPG** | Decisão, norma (resolução), articulação intersetorial |
| **Sistema de Bibliotecas (SIB)** | Gestão do prefixo, curadoria de metadados, operação da cunhagem |
| **TI / STI** | Configuração e manutenção do módulo DataCite no DSpace |
| **DAAD** | Diagnóstico, monitoramento de indicadores e demonstração de valor (Painel DAAD) |
| **Secretarias dos PPGs** | Garantir ORCID e metadados completos no momento do depósito |

## 9. Recomendação e encaminhamento

A DAAD recomenda que a **PROPPG institua o grupo de trabalho (Fase 0)** e inicie o **contato de adesão com o IBICT (Fase 1)** ainda neste semestre, com **piloto em 1–2 PPGs**. O investimento é baixo, a infraestrutura já existe, e o retorno — visibilidade internacional, mensurabilidade e alinhamento à Ciência Aberta — é alto e diretamente verificável pelo próprio Painel DAAD.

---

### Anexo — Fontes consultadas

- BDTD — Biblioteca Digital Brasileira de Teses e Dissertações (IBICT): https://bdtd.ibict.br
- IBICT — Solicitar prefixo DOI (Wiki): https://wiki.ibict.br/index.php/Solicitar_o_prefixo_DOI
- Rede Cariniana (IBICT) — contato `cariniana@ibict.br`: https://cariniana.ibict.br
- CNPq — Consórcio CoNCienciA (Ciência Aberta / DataCite): https://www.gov.br/cnpq
- Atribuição de DOI em Teses e Dissertações da UFU (relato de experiência) — Revista Ciência da Informação (IBICT): https://revista.ibict.br/ciinf/article/view/4854
- DataCite — agência de DOI para objetos de pesquisa: https://datacite.org

*Levantamento de dados (BDTD, OpenAlex, DataCite) realizado pela DAAD em junho/2026, reprodutível pelo coletor `fetch_bdtd.py` do Painel DAAD.*
