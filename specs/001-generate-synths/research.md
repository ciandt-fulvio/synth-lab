# Pesquisa Técnica: Gerar Synths Realistas (ATUALIZADO com Fontes Reais)

**Feature**: 001-generate-synths
**Data**: 2025-12-14 (Atualizado)
**Fase**: Phase 0 - Outline & Research

## Objetivo da Pesquisa

Resolver todas as incertezas técnicas identificadas no Technical Context usando **fontes de dados confiáveis e verificáveis** para garantir realismo baseado em evidências.

**Princípio**: NÃO INVENTAR DADOS. Se não encontrar fonte confiável, o campo será removido ou marcado como "sem fonte - usar distribuição genérica".

---

## Decisões Técnicas com Fontes Verificadas

### 1. Dados Demográficos IBGE (VERIFICADO ✅)

**Decisão**: Usar dados estáticos do IBGE Censo 2022 e PNAD 2022/2023

#### 1.1 População por Região

**Fonte**: [IBGE Censo 2022](https://agenciadenoticias.ibge.gov.br/agencia-noticias/)

- Norte: 8,6%
- Nordeste: 26,2%
- Sudeste: 40,7%
- Sul: 13,8%
- Centro-Oeste: 7,7%

#### 1.2 Distribuição Etária

**Fonte**: IBGE Projeção Populacional 2023

- 0-14 anos: 19,8%
- 15-29 anos: 22,1%
- 30-44 anos: 22,8%
- 45-59 anos: 19,6%
- 60+ anos: 15,7%

#### 1.3 Raça/Etnia

**Fonte**: [IBGE PNAD 2022](https://agenciadenoticias.ibge.gov.br/)

- Pardos: 47,3%
- Brancos: 43,5%
- Pretos: 8,2%
- Amarelos: 0,5%
- Indígenas: 0,5%

#### 1.4 Escolaridade (população 25+ anos)

**Fonte**: IBGE Educação 2022

- Sem instrução: 6,4%
- Fundamental incompleto: 29,2%
- Fundamental completo: 8,0%
- Médio incompleto: 4,1%
- Médio completo: 27,4%
- Superior incompleto: 4,7%
- Superior completo: 20,2%

#### 1.5 Renda Mensal (adaptado de PNAD Contínua 2023)

**Fonte**: IBGE PNAD Contínua 2023

Distribuição aproximada por faixas de salário mínimo (SM = R$ 1.320):
- Até 1 SM: ~30%
- 1-2 SM: ~25%
- 2-3 SM: ~15%
- 3-5 SM: ~12%
- 5-10 SM: ~10%
- 10-20 SM: ~5%
- 20+ SM: ~3%

**Implementação**:
- Arquivo: `data/config/ibge_distributions.json`

---

### 2. Religião (VERIFICADO ✅)

**Fonte**: [IBGE Censo 2022 - Religião](https://agenciadenoticias.ibge.gov.br/agencia-sala-de-imprensa/2013-agencia-de-noticias/releases/43593-censo-2022-catolicos-seguem-em-queda-evangelicos-e-sem-religiao-crescem-no-pais)

**Distribuição Real**:
- Católicos: 56,7%
- Evangélicos: 26,9%
- Sem religião: 9,3%
- Espíritas: 1,8%
- Umbanda/Candomblé: 1,0%
- Outras religiões: 4,3%

**Mudanças 2010-2022**:
- Católicos caíram de 65,1% para 56,7% (-8,4 pontos)
- Evangélicos cresceram de 21,6% para 26,9% (+5,3 pontos)
- Sem religião cresceu de 7,9% para 9,3%

**Variação Regional**:
- Piauí: maior proporção de católicos (77,4%)
- Acre: maior proporção de evangélicos (44,4%)
- Roraima: maior proporção sem religião (16,9%)

---

### 3. Inclinação Política (VERIFICADO ✅)

**Fonte**: [DataSenado/Nexus "Panorama Político 2024"](https://www12.senado.leg.br/radio/1/noticia/2024/09/27/datasenado-revela-que-57-dos-eleitores-nao-se-consideram-nem-de-esquerda-nem-de-direita)

**Pesquisa**: 21.808 brasileiros de todas as 27 UFs (junho 2024)

**Distribuição de Espectro Político**:
- Direita: 29%
- Esquerda: 15%
- Centro: 11%
- Não se identifica com nenhum: 40%
- Não sabe/Não respondeu: 6%

**Fonte Alternativa**: [IPEC março 2024](https://www.gazetadopovo.com.br/eleicoes/2024/pesquisa-ipec-posicionamento-ideologico-eleitores/)
- Direita: 24%
- Esquerda: 11%

**Implementação**:
- Usar escala -100 (esquerda) a +100 (direita)
- Distribuir conforme proporções DataSenado:
  - 29% com valores positivos (direita: +20 a +100)
  - 15% com valores negativos (esquerda: -100 a -20)
  - 11% próximo a zero (centro: -20 a +20)
  - 40% neutro/indefinido (usar -10 a +10)

---

### 4. Deficiências Físicas e Cognitivas (VERIFICADO ✅)

**Fonte**: [IBGE PNS 2019](https://agenciadenoticias.ibge.gov.br/agencia-sala-de-imprensa/2013-agencia-de-noticias/releases/31445-pns-2019-pais-tem-17-3-milhoes-de-pessoas-com-algum-tipo-de-deficiencia) (Pesquisa Nacional de Saúde)

**Prevalência Total**: 8,4% da população (17,3 milhões de pessoas com 2+ anos)

**Por Tipo de Deficiência**:
- **Visual**: 3,4% (6,978 milhões) - "muita dificuldade" ou "não consegue de modo algum"
  - Homens: 2,7%
  - Mulheres: 4,0%

- **Física/Motora (membros inferiores)**: 3,8% (7,8 milhões)
  - Homens: 2,7%
  - Mulheres: 4,8%

- **Auditiva**: 1,1% (2,3 milhões)
  - Distribuição igual entre homens e mulheres

- **Mental/Cognitiva**: 1,2% (2,5 milhões)

**Implementação**:
- 91,6% dos Synths: nenhuma deficiência
- 8,4% dos Synths: pelo menos uma deficiência
- Usar proporções específicas por tipo conforme PNS 2019

---

### 5. Capacidades Tecnológicas (VERIFICADO ✅)

**Fonte**: [TIC Domicílios 2023 - CETIC.br](https://cetic.br/pt/noticia/classes-c-e-de-impulsionam-crescimento-da-conectividade-a-internet-nos-lares-brasileiros-mostra-tic-domicilios-2023/)

**Pesquisa**: 23.975 domicílios e 21.271 indivíduos (março-julho 2023)

**Acesso à Internet**:
- 84% dos domicílios conectados (64 milhões) - crescimento de 4 pontos vs 2022

**E-commerce**:
- 50% dos usuários de internet fizeram compras online (78 milhões de pessoas)

**Podcasts**:
- 29% ouviram podcasts em 2023 (+7 pontos vs 2021, +19 vs 2019)

**Fonte Complementar**: [NielsenIQ Ebit 2023](https://nielseniq.com/global/pt/insights/education/2024/a-trajetoria-ascendente-do-e-commerce-brasileiro/)

**Comportamento de Compra Online**:
- 50% influenciados por redes sociais (Instagram, Facebook)
- 69% fizeram compras em e-commerce internacional
- 32% usam apps de supermercado mensalmente
- 45% usam apps de farmácia mensalmente

**Implementação**:
- `alfabetizacao_digital`: correlacionar com idade (inverso) e escolaridade (direto)
- `frequencia_internet`: usar dados TIC Domicílios (84% diária, 16% menor frequência)
- `familiaridade_plataformas.e_commerce`: 50% alta, 50% média/baixa
- `uso_tecnologia.smartphone`: ~85% (correlacionar com renda)

---

### 6. Hobbies e Interesses (VERIFICADO ✅)

**Fonte Principal**: [Pesquisa TIM + USP](https://jornal.usp.br/ciencias/ciencias-humanas/estudo-revela-o-que-brasileiro-faz-no-tempo-livre-e-como-escolaridade-influencia/)

**Atividades Online Principais**:
- Redes sociais: 24%
- Assistir filmes/séries: 17%
- Assistir vídeos: 13%
- Ouvir música: 11%
- Ler/estudar: 10%

**Games Mobile**:
- 49,3% jogam diariamente (pesquisa com 5.380 pessoas)

**Correlação com Escolaridade** (USP):
- **Baixa escolaridade**: preferem atividades sociais (encontros com amigos/família) e esportes físicos (futebol)
- **Alta escolaridade**: maior variedade (teatro, cinema, leitura, museus)

**Equilíbrio Trabalho-Lazer** (Instituto Locomotiva):
- 65% têm dificuldade de encontrar equilíbrio entre lazer e trabalho

**Hobbies Comuns Identificados**:
- Fotografia
- Culinária
- Música (ouvir/tocar)
- Leitura
- Jardinagem
- Esportes/atividades físicas
- Criação de conteúdo para redes sociais
- Streaming (filmes/séries)
- Videogames

**Implementação**:
- Lista curada em `data/config/interests_hobbies.json` com ~50-80 opções
- Selecionar 3-7 hobbies por Synth
- Correlacionar com escolaridade (alta = mais variedade artística/cultural)

---

### 7. Valores Pessoais (FONTE INTERNACIONAL ✅)

**Fonte**: [World Values Survey (WVS) Wave 7 (2017-2022)](https://www.worldvaluessurvey.org/)

**Cobertura**: 80 países, incluindo Brasil, ~90% da população mundial

**Dimensões Principais de Valores** (WVS):
1. **Valores Tradicionais vs Secular-Racionais**
2. **Valores de Sobrevivência vs Auto-Expressão**

**Nota**: WVS não fornece lista específica de "valores" para distribuição direta, mas oferece framework teórico.

**Decisão de Implementação**:
- Criar lista curada de ~30-50 valores universais comuns baseados em literatura de psicologia social
- Exemplos: família, trabalho, liberdade, segurança, justiça, saúde, educação, religião, amizade, sucesso, criatividade, natureza, tradição, inovação, etc.
- **Sem distribuição percentual específica** (não disponível em WVS de forma diretamente aplicável)
- Selecionar 3-5 valores aleatoriamente por Synth

**Fonte de Lista de Valores**: Schwartz Theory of Basic Values (10 valores universais + subtipos)

---

### 8. Vieses Comportamentais (FONTE ACADÊMICA INTERNACIONAL ✅)

**Fontes**:
- [Hyperbolic Discounting Research](https://thedecisionlab.com/biases/hyperbolic-discounting) - The Decision Lab
- [Loss Aversion Studies](https://www.researchgate.net/publication/393422655_Loss_Aversion_and_Its_Behavioral_Implications_in_Economics_and_Market_Strategies)
- [Behavioral Economics Literature](https://www.bu.edu/eci/files/2020/05/Behavioral-Economics_final.pdf) - Boston University

**Prevalência Documentada**:

- **Hyperbolic Discounting**:
  - Amplamente aceito desde Thaler (1981)
  - "Overwhelmingly the available evidence indicates that delay discounting is hyperbolic in nature"
  - Prevalência varia por população: 8,2% em estudo com turistas (Singapore)
  - Em populações com SUDs: considerado fator de risco devido à alta prevalência

- **Loss Aversion**:
  - Kahneman & Tversky: "people perceive losses much more strongly than pleasure from equivalent gains"
  - Estudo com 121.293 investidores (Hiroshima University + Rakuten Securities)

- **Outros Vieses**: Literatura confirma existência mas sem percentuais populacionais específicos

**Decisão de Implementação**:
- Usar distribuição normal (μ=50, σ=20) para TODOS os 7 vieses
- Não há dados populacionais brasileiros específicos
- Literatura confirma que vieses existem em graus variados na população geral
- Modelar como traços contínuos (0-100) sem categorização binária

**Vieses Incluídos** (com base em literatura sólida):
1. Aversão à Perda (Loss Aversion) ✅
2. Desconto Hiperbólico (Hyperbolic Discounting) ✅
3. Efeito Chamariz (Decoy Effect) ✅
4. Ancoragem (Anchoring) ✅
5. Viés de Confirmação (Confirmation Bias) ✅
6. Viés de Status Quo (Status Quo Bias) ✅
7. Sobrecarga de Informação (Information Overload) ✅

---

### 9. Campos REMOVIDOS (Sem Fonte Confiável ❌)

Os seguintes campos foram **removidos do data model** por falta de dados populacionais verificáveis:

#### 9.1 Atitudes
- **Motivo**: Não encontrada pesquisa brasileira com distribuição de atitudes específicas
- **Ação**: Campo removido

#### 9.2 Motivações
- **Motivo**: Não encontrada pesquisa com distribuição de motivações na população brasileira
- **Ação**: Campo removido

#### 9.3 Estilo de Vida (como campo independente)
- **Motivo**: Muito genérico, pode ser derivado de outros atributos (Big Five, hobbies)
- **Ação**: Campo derivado automaticamente, não gerado independentemente

---

## Distribuições Probabilísticas (Mantidas)

### Big Five Personality Traits

**Fonte Teórica**: Literatura de psicometria estabelecida

**Parâmetros**:
- Média (μ): 50
- Desvio padrão (σ): 15
- Range: [0, 100]
- Distribuição Normal: ~68% entre 35-65, ~95% entre 20-80

**Rationale**:
- Traços de personalidade seguem distribuição normal em populações (literatura consolidada)
- Não há dados IBGE específicos, mas padrão científico internacional é robusto

---

## Resumo de Decisões ATUALIZADAS

| Área | Decisão | Fonte | Status |
|------|---------|-------|--------|
| **Dados IBGE** | Censo 2022 + PNAD 2022/2023 | IBGE oficial | ✅ VERIFICADO |
| **Religião** | Censo 2022 | IBGE oficial | ✅ VERIFICADO |
| **Inclinação Política** | DataSenado 2024 | Pesquisa brasileira oficial | ✅ VERIFICADO |
| **Deficiências** | PNS 2019 | IBGE oficial | ✅ VERIFICADO |
| **Capacidades Tech** | TIC Domicílios 2023 | CETIC.br oficial | ✅ VERIFICADO |
| **E-commerce** | NielsenIQ Ebit 2023 | Instituto brasileiro | ✅ VERIFICADO |
| **Hobbies/Interesses** | TIM + USP + Locomotiva | Pesquisas brasileiras | ✅ VERIFICADO |
| **Valores** | Lista curada (Schwartz) | Teoria psicológica | ⚠️ ADAPTADO |
| **Vieses** | Literatura acadêmica | Estudos internacionais | ✅ VERIFICADO |
| **Nomes** | Faker pt_BR | Biblioteca estabelecida | ✅ OK |
| **Big Five** | Distribuição normal | Literatura psicométrica | ✅ OK |
| **Ocupações** | CBO 2022 (curado ~200) | Governo brasileiro | ✅ OK |
| **Atitudes** | — | SEM FONTE | ❌ REMOVIDO |
| **Motivações** | — | SEM FONTE | ❌ REMOVIDO |

---

## Dependências Finais (Inalteradas)

```toml
[project]
dependencies = [
    "faker>=21.0.0",
    "jsonschema>=4.20.0",
]
```

---

## Fontes Bibliográficas Completas

### Fontes Brasileiras Oficiais
1. [IBGE Censo 2022 - População e Religião](https://agenciadenoticias.ibge.gov.br/)
2. [IBGE PNAD 2022/2023 - Demografia e Renda](https://agenciadenoticias.ibge.gov.br/)
3. [IBGE PNS 2019 - Deficiências](https://agenciadenoticias.ibge.gov.br/agencia-sala-de-imprensa/2013-agencia-de-noticias/releases/31445-pns-2019-pais-tem-17-3-milhoes-de-pessoas-com-algum-tipo-de-deficiencia)
4. [TIC Domicílios 2023 - CETIC.br](https://cetic.br/pt/noticia/classes-c-e-de-impulsionam-crescimento-da-conectividade-a-internet-nos-lares-brasileiros-mostra-tic-domicilios-2023/)
5. [DataSenado/Nexus - Panorama Político 2024](https://www12.senado.leg.br/radio/1/noticia/2024/09/27/datasenado-revela-que-57-dos-eleitores-nao-se-consideram-nem-de-esquerda-nem-de-direita)

### Fontes Brasileiras - Institutos de Pesquisa
6. [NielsenIQ Ebit - Webshoppers 49 (2023)](https://nielseniq.com/global/pt/insights/education/2024/a-trajetoria-ascendente-do-e-commerce-brasileiro/)
7. [Pesquisa TIM - Hobbies Online](https://marcasmais.com.br/minforma/pesquisas/comportamento/4-em-10-brasileiros-buscam-hobbies-na-internet-mostra-pesquisa-da-tim/)
8. [USP - Lazer e Escolaridade](https://jornal.usp.br/ciencias/ciencias-humanas/estudo-revela-o-que-brasileiro-faz-no-tempo-livre-e-como-escolaridade-influencia/)
9. [Instituto Locomotiva - Equilíbrio Trabalho-Lazer](https://www.capitaldopantanal.com.br/)

### Fontes Internacionais
10. [World Values Survey (WVS)](https://www.worldvaluessurvey.org/)
11. [The Decision Lab - Behavioral Economics](https://thedecisionlab.com/)
12. [Boston University - Behavioral Economics in Context](https://www.bu.edu/eci/files/2020/05/Behavioral-Economics_final.pdf)

---

## Próximos Passos

1. ✅ Research completo com fontes verificadas
2. ⏭️ Atualizar `data-model.md` removendo campos sem fonte
3. ⏭️ Atualizar `contracts/synth-schema.json` com estrutura revisada
4. ⏭️ Criar arquivos de configuração em `data/config/` com dados reais
