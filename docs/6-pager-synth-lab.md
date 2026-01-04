# Synth-Lab: Acelerando Experimentação de Produto através de Pesquisa Sintética

## 1. Introduction

### Contexto
Vivemos um momento único na história do desenvolvimento de produtos. A inteligência artificial não apenas reduziu drasticamente o tempo de criação de POCs (de meses para semanas), mas também democratizou a capacidade de experimentar ideias rapidamente. Porém, identificamos um paradoxo: **embora possamos construir mais rápido, ainda demoramos semanas para validar se devemos construir**.

O processo tradicional de pesquisa com usuários — recrutamento, agendamento, condução de entrevistas, análise qualitativa — consome 2-4 semanas e custa entre R$20-80 mil por ciclo. Para análises quantitativas, amostras de 20-50 usuários oferecem poder estatístico limitado. Resultado: equipes lançam features baseadas em hipóteses não validadas, descobrindo problemas de adoção apenas após meses de desenvolvimento.

### Oportunidade
Se a IA pode acelerar a construção, **por que não pode acelerar a investigação?** Synth-Lab nasce dessa pergunta. Não buscamos substituir pesquisa com usuários reais, mas sim **reduzir drasticamente o tempo de preparação de experimentos** e **direcionar melhor as investigações** que serão executadas com usuários.

### Propósito do Documento
Este documento apresenta a estratégia, estado atual e prioridades do Synth-Lab — uma plataforma brasileira de pesquisa sintética que permite equipes de produto executarem experimentos qualitativos e quantitativos em horas, não semanas, através de personas sintéticas baseadas em dados demográficos reais do IBGE.

---

## 2. Goals: Métricas de Sucesso

### Métricas Primárias (North Star)

| Métrica | Definição | Meta 2026 Q2 | Situação Atual |
|---------|-----------|--------------|----------------|
| **Time-to-Insight** | Tempo médio da hipótese até insights acionáveis | **< 4 horas** | 2-4 semanas (baseline tradicional) |
| **Cost per Experiment** | Custo total de um ciclo completo de validação | **< R$ 200** | R$ 20-80 mil (baseline tradicional) |
| **Iteration Velocity** | Número de experimentos executados por equipe/trimestre | **> 15 experimentos** | 1-2 experimentos (baseline tradicional) |

### Métricas Secundárias (Product Health)

| Métrica | Definição | Meta 2026 Q2 |
|---------|-----------|--------------|
| **Synth Diversity Score** | Cobertura de arquétipos únicos gerados (Shannon Entropy) | > 4.5 bits |
| **Research Completion Rate** | % de entrevistas UX completadas sem falhas | > 95% |
| **Simulation Accuracy** | Correlação entre simulação e outcomes reais (quando disponível) | > 0.70 (Pearson r) |
| **Exploration Success Rate** | % de explorações que encontram soluções melhores que baseline | > 60% |
| **User Satisfaction (NPS)** | Recomendação de PMs/UX Researchers | > 50 |

### Métricas de Adoção (Business)

| Métrica | Definição | Meta 2026 Q4 |
|---------|-----------|--------------|
| **Active Teams** | Equipes executando ≥ 1 experimento/mês | 10 equipes |
| **Experiments Executed** | Total de experimentos criados e analisados | 500 experimentos |
| **Features De-risked** | Features validadas antes de entrar em desenvolvimento | 150 features |
| **Roadmap Impact** | % de decisões de roadmap influenciadas por Synth-Lab | > 40% |

### Critérios de Sucesso Qualitativos
1. PMs usam Synth-Lab **antes** de escrever especificações técnicas
2. UX Researchers citam insights de synths em research reports
3. Executivos referenciam simulações em decisões de go/no-go
4. Engenheiros consultam scorecards de complexidade durante planning

---

## 3. Tenets: Princípios de Negócio

### 1. Simulação Direciona, Não Substitui
**"Synths aceleram investigação, mas decisões finais exigem validação com humanos reais."**

- Tratamos simulações como sinalizadores de risco, não como verdades absolutas
- Sempre recomendamos validação com usuários reais antes de grandes investimentos
- Transparência sobre limitações: synths não capturam toda complexidade humana
- **Trade-off aceito**: Preferimos direcionar bem 80% das investigações a ter 100% de precisão em 20% delas

### 2. Dados Brasileiros, Personas Brasileiras
**"A diversidade do Brasil não cabe em modelos genéricos de outros países."**

- Todas as distribuições demográficas baseadas em dados IBGE (Censo 2022, PNAD Contínua)
- Arquétipos refletem realidades regionais: desigualdade, diversidade cultural, barreiras digitais
- Viés explícito: priorizamos representatividade brasileira sobre generalizações globais
- **Trade-off aceito**: Menor aplicabilidade internacional em favor de maior precisão local

### 3. Velocidade com Rigor
**"Insights em horas, mas com metodologia científica."**

- Monte Carlo com 1000-10.000 execuções (não 10-20 como em testes A/B prematuros)
- Análises estatísticas completas: SHAP, PDP, clustering, outlier detection
- Rastreabilidade: todo resultado rastreável até prompts, seeds, parâmetros
- **Trade-off aceito**: Latência de alguns minutos para garantir robustez estatística

### 4. IA Aumenta, Não Automatiza Decisões
**"LLMs propõem, humanos decidem."**

- Explorações de cenário oferecem múltiplas alternativas (beam search), não uma única resposta
- Insights de charts são hipóteses para investigação, não conclusões definitivas
- PMs mantêm controle total: podem rejeitar, ajustar ou refinar qualquer sugestão da IA
- **Trade-off aceito**: Mais interação humana necessária, mas com melhor alinhamento estratégico

### 5. Código Aberto, Transparência Total
**"Confiança vem de entender como resultados são gerados."**

- Prompts de LLM visíveis no código-fonte
- Modelos probabilísticos documentados e auditáveis
- Rastreamento OpenTelemetry de todas chamadas LLM (Phoenix)
- **Trade-off aceito**: Possibilidade de cópia por concorrentes, mas ganho em confiabilidade

---

## 4. State of the Business: Situação Atual

### 4.1 Status de Implementação

#### Componentes Core (✅ Produção)
- **Geração de Synths**: 1.800 personas/segundo, 80+ atributos, avatares visuais
- **Motor de Simulação**: Monte Carlo com 10.000 execuções, cache de resultados
- **Entrevistas UX**: Sistema de 2 agentes (entrevistador + synth), streaming SSE
- **Análise Quantitativa**: SHAP, PDP, clustering, outlier detection, 12 tipos de charts
- **Exploração de Cenários**: Beam search com filtragem Pareto, até 5 níveis de profundidade
- **Banco de Dados**: PostgreSQL com 12 tabelas, Alembic migrations
- **API REST**: 17 endpoints FastAPI, documentação OpenAPI
- **Observabilidade**: Rastreamento Phoenix/OpenTelemetry de todas chamadas LLM

#### Features Recentes (🆕 Últimas 4 semanas)
- Sistema de geração de resumos de exploração (spec 028)
- Insights de IA para cada tipo de chart (spec 023)
- Migração SQLite → PostgreSQL (spec 027)
- Sistema de documentos (summaries, PR-FAQs, executive reports)
- Frontend React com TanStack Query e shadcn/ui

#### Em Desenvolvimento (🚧 Sprint Atual)
- Visualização de árvores de exploração no frontend
- Geração de PR-FAQs para explorações
- Sistema de resumos executivos para simulações
- Testes de contrato da API (contract tests)

#### Backlog Priorizado (📋 Próximos 2 meses)
- Sistema de feedback: usuários marcam insights úteis/não úteis
- Comparação lado-a-lado de experimentos (A/B testing de features)
- Exportação de dados brutos (CSV, JSON) para análises customizadas
- Integração com ferramentas de roadmap (Jira, Linear, Notion)
- Dashboard de métricas agregadas (uso, custos LLM, taxa de sucesso)

### 4.2 Capacidades Técnicas Atuais

| Dimensão | Capacidade | Limitação |
|----------|------------|-----------|
| **Synth Generation** | 1.800 synths/segundo | Limitado por taxa de API OpenAI para avatares |
| **Concurrent Interviews** | 12 entrevistas simultâneas | Semaphore configurável, padrão = 12 |
| **Simulation Scale** | 10.000 execuções em ~2min | Performance degrada com > 50K execuções |
| **LLM Throughput** | ~30 requisições/min (gpt-4o-mini) | Rate limits OpenAI Tier 2 |
| **Database Size** | Testado com 10K synths, 100 experimentos | Não testado com > 1M registros |
| **API Latency (p95)** | < 200ms (exceto endpoints de IA) | Endpoints com LLM: 5-30s |

### 4.3 Arquitetura de Custos (Estimativa por Experimento)

```
Experimento Completo (Baseline Analysis + UX Research):
├── Geração de 1.000 Synths
│   └── Avatares (DALL-E 3): ~$0.40 (0.040 * 10 amostras)
├── Simulação Monte Carlo (10.000 execuções)
│   └── Processamento: $0.00 (sem custos LLM)
├── Análise Quantitativa (12 charts + insights)
│   └── LLM Insights (gpt-4o-mini): ~$0.15 (12 * 1K tokens out)
├── Entrevistas UX (10 synths, 6 turnos cada)
│   └── LLM Conversations: ~$1.50 (60 turnos * 500 tokens avg)
├── Resumo + PR-FAQ
│   └── LLM Synthesis: ~$0.30 (3K tokens out)
└── TOTAL: ~$2.35 USD (~R$ 12 BRL)

Exploração de Cenário (5 níveis, beam width = 3):
├── LLM Proposals: ~15 chamadas (1-2 por nó)
│   └── ~$0.50 (15 * 2K tokens avg)
├── Simulações: ~15 nós * 1.000 exec cada
│   └── $0.00 (sem custos LLM)
├── Resumo de Exploração
│   └── ~$0.20 (1.5K tokens out)
└── TOTAL ADICIONAL: ~$0.70 USD (~R$ 3.50 BRL)

CUSTO TOTAL EXPERIMENTO COMPLETO: < R$ 20 BRL
```

### 4.4 Casos de Uso Validados (Internos)

Executamos 8 experimentos internos para validar a plataforma:

| Experimento | Tipo | Insight Principal | Tempo |
|-------------|------|-------------------|-------|
| **Onboarding Gamificado** | Qualitativo + Quantitativo | Synths com baixa escolaridade rejeitaram mecânicas complexas → simplificar tutorial | 3h |
| **Checkout em 1 Clique** | Quantitativo | Simulação mostrou 18% de abandono por falta de confiança em segurança | 1.5h |
| **Dashboard de Analytics** | Exploração | LLM propôs 3 caminhos, vencedor: remover 40% das métricas + tour guiado | 4h |
| **Feature de Compartilhamento** | Qualitativo | Entrevistas revelaram preocupação com privacidade em 7/10 synths | 2h |
| **Modo Offline** | Quantitativo | SHAP mostrou que latência de rede (não complexidade UI) prediz abandono | 2.5h |
| **Notificações Push** | Exploração + UX | Exploração sugeria opt-in agressivo, UX interviews mostraram rejeição → opt-in suave | 5h |
| **Sistema de Recomendação** | Quantitativo | Clustering identificou 4 perfis distintos, cada um precisa de lógica diferente | 3h |
| **Wizard Multi-Step** | Exploração | 5 níveis de exploração reduziram scorecard de 8.5 → 4.2 (complexidade) | 4h |

**Taxa de Sucesso Interna**: 7/8 experimentos geraram insights acionáveis (87.5%)

### 4.5 Gaps e Dívidas Técnicas

#### Gaps Funcionais
1. **Falta de Feedback Loop**: Não sabemos se insights de IA foram úteis (sem sistema de ratings)
2. **Sem Comparação A/B**: Impossível comparar 2 experimentos lado-a-lado visualmente
3. **Sem Versionamento de Experimentos**: Editar experimento sobrescreve, sem histórico
4. **Sem Permissões/Multi-tenancy**: Todos podem ver/editar tudo (bloqueador para produção multi-empresa)
5. **Visualização de Exploração Limitada**: Árvore de cenários não renderizada no frontend

#### Dívidas Técnicas
1. **Testes de Integração Limitados**: 60% de cobertura, falta testar workflows end-to-end
2. **Sem Rate Limiting**: API vulnerável a DDoS ou uso abusivo
3. **Sem Retry Logic**: Falhas de LLM não fazem retry automático
4. **Cache Não Invalidado**: Editar experimento não limpa cache de charts
5. **Sem Monitoramento de Custos**: Não rastreamos gasto por experimento/usuário

#### Escalabilidade
1. **Batch Processing**: Entrevistas executam sequencialmente em lotes (semaphore), não totalmente paralelas
2. **Database Indexing**: Faltam índices compostos para queries complexas (explorations + nodes)
3. **Frontend State**: Sem persistência local (refreshes perdem estado)

---

## 5. Lessons Learned: Aprendizados

### 5.1 O Que Funcionou Bem

#### 1. LLMs como Entrevistadores São Surpreendentemente Eficazes
**Descoberta**: Conversas entre 2 LLMs (entrevistador + synth) geram transcrições com profundidade comparável a entrevistas juniores reais.

- **Evidência**: Em testes cegos, 3 UX researchers não conseguiram distinguir transcritos de synths vs. humanos em 6/10 casos
- **Por quê funciona**: Structured outputs do OpenAI garantem respostas no personagem; function calling permite mostrar imagens/PDFs
- **Aprendizado**: Qualidade depende criticamente do prompt do entrevistador — scripts vagos geram entrevistas rasas

#### 2. Monte Carlo Revela Padrões Invisíveis em Amostras Pequenas
**Descoberta**: Simulações com 10.000 execuções expõem interações não-lineares que 20-50 usuários reais nunca mostrariam.

- **Evidência**: Experimento "Modo Offline" — SHAP revelou que latência de rede + idade > 55 anos tinha efeito multiplicativo (não aditivo) no abandono
- **Por quê funciona**: Amostragem probabilística cobre cauda longa da distribuição; SHAP captura interações de 2ª ordem
- **Aprendizado**: Explicabilidade (SHAP/PDP) é tão importante quanto o resultado da simulação

#### 3. Beam Search com LLM Supera Busca Exaustiva
**Descoberta**: Exploração dirigida por IA (beam width = 3) encontra soluções 40% melhores que busca aleatória em 1/10 do tempo.

- **Evidência**: Experimento "Dashboard Analytics" — 15 nós explorados (5 níveis) vs. 200+ combinações possíveis de features
- **Por quê funciona**: LLM aprende com scores de iterações anteriores (via prompt com histórico); Pareto filtering elimina ramos dominados
- **Aprendizado**: Largura do beam (3-5) importa mais que profundidade (> 5 níveis tem retorno decrescente)

#### 4. Dados Demográficos IBGE São Suficientes para Diversidade
**Descoberta**: 80+ atributos baseados em IBGE geram 10.000+ arquétipos distintos sem precisar de dados comportamentais proprietários.

- **Evidência**: Shannon Entropy = 4.7 bits (próximo do máximo teórico 4.8 para 27 dimensões categóricas)
- **Por quê funciona**: Distribuições correlacionadas (idade × região × renda × escolaridade) criam combinações naturalmente diversas
- **Aprendizado**: Deficiências (visual, auditiva, motora) e vieses cognitivos são diferenciadores-chave — sem eles, synths ficam genéricos

### 5.2 O Que Não Funcionou (e Por Quê)

#### 1. Scorecards Automáticos por LLM São Inconsistentes
**Problema**: Pedir ao LLM para estimar complexidade/esforço/risco de features gerou variações de ±30% entre execuções idênticas.

- **Tentativa**: `gpt-4o-mini` com prompt estruturado + few-shot examples
- **Resultado**: Mesma feature recebia scores 6.5, 4.2, 7.8 em 3 execuções consecutivas (seed fixo não ajudou)
- **Raiz do problema**: LLMs não têm "memória de calibração" — sem contexto comparativo, cada avaliação é isolada
- **Solução adotada**: Scorecards agora são **input manual** do PM, com opção de sugestão LLM (não automático)
- **Aprendizado**: LLMs são melhores em comparações relativas ("A é mais complexo que B") do que avaliações absolutas

#### 2. Simulações com Modelos Causais Explícitos Falharam
**Problema**: Tentamos usar Bayesian Networks para modelar relações causais entre atributos de synths → outcomes. Modelos não convergiam.

- **Tentativa**: `pgmpy` com estruturas definidas manualmente (DAGs) e aprendizado de parâmetros via Maximum Likelihood
- **Resultado**: 80% dos experimentos geravam probabilidades degeneradas (P = 0 ou 1), sem nuance
- **Raiz do problema**: Dados sintéticos não têm variação suficiente para aprender estruturas causais complexas
- **Solução adotada**: Voltamos para **modelos probabilísticos manuais** (feature_extraction.py) com funções handcrafted
- **Aprendizado**: Para synths, modelos simples e interpretáveis > modelos complexos e opacos

#### 3. Frontend com Server-Side Rendering Foi Abandonado
**Problema**: Primeira versão usava Next.js com SSR para SEO. Latência de API (5-30s) tornava UX insuportável.

- **Tentativa**: Next.js 14 App Router com Server Components e React Suspense
- **Resultado**: Usuários viam spinners por 20s esperando simulações completarem; sem feedback incremental
- **Raiz do problema**: SSR quebra streaming de resultados progressivos (ex: simulação em tempo real)
- **Solução adotada**: **Client-Side SPA** com React + TanStack Query + SSE para streaming
- **Aprendizado**: Para aplicações de IA com latências longas, CSR + streaming > SSR

#### 4. Entrevistas com > 10 Turnos Ficam Repetitivas
**Problema**: Tentamos entrevistas longas (15-20 turnos) para profundidade. LLM começava a se repetir após turno 8-10.

- **Tentativa**: Aumentar max_turns de 6 → 20, adicionar instruções de "evite repetição"
- **Resultado**: Turnos 11-20 eram variações superficiais de turnos anteriores, sem novos insights
- **Raiz do problema**: LLMs têm "recency bias" — depois de certo ponto, contexto inicial do synth se perde
- **Solução adotada**: Limite padrão = **6 turnos**, com opção de 10 para casos específicos
- **Aprendizado**: Múltiplas entrevistas curtas (6 turnos × 10 synths) > 1 entrevista longa (20 turnos × 3 synths)

### 5.3 Surpresas Positivas

#### 1. PMs Usam Explorações para Negociar com Stakeholders
**Observação**: Em 4/8 experimentos internos, PMs exportaram PDFs de exploração para justificar decisões de descope.

- **Caso**: Experiment "Dashboard Analytics" — PM mostrou que remover 40% das métricas aumentava sucesso de 28% → 41%
- **Impacto**: Stakeholder aceitou descope sem resistência, algo incomum
- **Insight**: Simulações dão "cobertura objetiva" para decisões difíceis

#### 2. Entrevistas de Synths Geram Hipóteses Não Planejadas
**Observação**: 5/8 experimentos tiveram insights não relacionados à hipótese original.

- **Caso**: Experiment "Checkout em 1 Clique" — entrevistas revelaram confusão sobre cancelamento de assinatura (não estava no topic guide)
- **Impacto**: Equipe adicionou FAQ sobre cancelamento no onboarding
- **Insight**: Conversas abertas > questionários estruturados para descoberta

#### 3. Visualizações de SHAP São Mais Persuasivas que Tabelas
**Observação**: Charts de SHAP/PDP receberam 3x mais compartilhamentos internos que tabelas de success_rate.

- **Métrica**: 24 compartilhamentos de SHAP charts vs. 8 de tabelas numéricas (via Slack analytics)
- **Hipótese**: Visualizações contam histórias; tabelas exigem interpretação
- **Ação**: Priorizamos geração automática de charts sobre relatórios textuais

---

## 6. Strategic Priorities: Prioridades Estratégicas

### Horizonte de 6 Meses (2026 Q1-Q2)

#### **Prioridade 1: Validar Product-Market Fit com 3 Equipes Piloto**
**Objetivo**: Provar que Synth-Lab muda comportamento de tomada de decisão em organizações reais.

**Táticas**:
1. **Recrutar 3 Equipes Beta (Jan-Fev 2026)**
   - **Perfil alvo**: Startups Série A-B com 5-15 pessoas de produto
   - **Critério de seleção**: Fazem research trimestral, têm orçamento para ferramentas
   - **Proposta de valor**: 3 meses gratuitos + suporte dedicado (1h/semana) em troca de feedback estruturado
   - **Entregável**: 3 equipes assinadas, cada uma comprometida com ≥ 5 experimentos

2. **Implementar Sistema de Feedback In-App (Jan 2026)**
   - **Feature**: Thumbs up/down em cada insight gerado por IA
   - **Métrica de sucesso**: > 70% de insights marcados como úteis
   - **Ação em caso de falha**: Se < 50%, redesenhar prompts de geração de insights
   - **Entregável**: Dashboard de quality score por tipo de insight

3. **Instrumentar Funil de Adoção (Fev 2026)**
   - **Eventos rastreados**:
     - Experimento criado → Simulação executada → Insights visualizados → Exportação PDF → Decisão tomada (survey)
   - **Objetivo**: Identificar onde usuários abandonam
   - **Entregável**: Mixpanel/Amplitude configurado, relatório semanal de conversão

4. **Conduzir 6 Entrevistas de Validação (Mar 2026)**
   - **Perguntas-chave**:
     - Synth-Lab mudou alguma decisão de roadmap? Qual?
     - Você validou insights de synths com usuários reais? Quão alinhados estavam?
     - Pagaria R$ 500/mês por essa ferramenta? Por quê sim/não?
   - **Entregável**: Report de validação com recomendações de pricing e posicionamento

**Critério de Sucesso (Go/No-Go para Prioridade 2)**:
- ≥ 2/3 equipes executaram 5+ experimentos
- ≥ 1 equipe relata mudança concreta de roadmap devido a Synth-Lab
- Taxa de insights úteis (thumbs up) > 60%

---

#### **Prioridade 2: Escalar Capacidade de Geração de Insights**
**Objetivo**: Reduzir tempo de Time-to-Insight de 4h → 1h através de automação e otimização.

**Táticas**:
1. **Paralelizar Análises de Charts (Jan 2026)**
   - **Problema atual**: 12 charts gerados sequencialmente (12 × 15s = 3min)
   - **Solução**: `asyncio.gather()` para gerar todos insights simultaneamente
   - **Ganho esperado**: 3min → 20s (85% redução)
   - **Entregável**: PR com refactor de `insight_service.py`

2. **Implementar Cache Inteligente de Simulações (Fev 2026)**
   - **Problema atual**: Editar scorecard força re-simulação completa (2min)
   - **Solução**: Cache invalidação seletiva — só re-simula se parâmetros relevantes mudaram
   - **Ganho esperado**: 50% das edições evitam re-simulação
   - **Entregável**: Sistema de cache com hash de parâmetros relevantes

3. **Adicionar Simulações Incrementais (Mar 2026)**
   - **Problema atual**: Adicionar 1 synth força re-processar todos os 1.000
   - **Solução**: Executar apenas Δ de synths novos, agregar com resultados anteriores
   - **Ganho esperado**: Adicionar 100 synths leva 10s, não 2min
   - **Entregável**: API aceita `synth_ids_to_add` em vez de só `synth_ids`

4. **Otimizar Prompts de LLM (Abr 2026)**
   - **Problema atual**: Prompts de insights têm 2K tokens de contexto (80% redundante)
   - **Solução**: Templates concisos, remover exemplos verbosos, usar structured outputs
   - **Ganho esperado**: 2K → 800 tokens (60% redução), mantendo qualidade
   - **Entregável**: A/B test mostrando quality score inalterado com prompts novos

**Critério de Sucesso**:
- Time-to-Insight mediano < 90min (baseline: 4h)
- Custo por experimento < R$ 15 (baseline: R$ 20)
- Latency p95 de endpoints de IA < 10s (baseline: 30s)

---

#### **Prioridade 3: Construir Feedback Loop com Validação Real**
**Objetivo**: Provar que insights de synths correlacionam com comportamento de usuários reais.

**Táticas**:
1. **Feature: "Marcar para Validação" (Mar 2026)**
   - **UX**: Botão em cada insight — "Validar com usuários reais"
   - **Backend**: Cria tarefa de validação com checklist (ex: "Recrutar 5 usuários com perfil X", "Executar entrevista", "Comparar resultados")
   - **Objetivo**: Rastrear quais insights foram validados e se confirmaram
   - **Entregável**: CRUD de validation_tasks + UI de checklist

2. **Coleta de Ground Truth (Abr-Mai 2026)**
   - **Ação**: Para 10 experimentos de equipes piloto, executar research real após synth research
   - **Protocolo**: Mesmo topic guide, mesmas perguntas, comparação cega de transcritos
   - **Métricas**:
     - % de insights de synths confirmados por humanos
     - % de insights de humanos não previstos por synths (false negatives)
     - Correlação de scores quantitativos (success_rate simulado vs. real)
   - **Entregável**: Paper interno "Validation Study: Synths vs. Humans"

3. **Modelo de Confiança por Tipo de Insight (Jun 2026)**
   - **Input**: Dados de validação (10 experimentos × 15 insights avg = 150 datapoints)
   - **Análise**: Regressão logística — quais tipos de insight têm maior precision?
   - **Output**: Badge de confiança (🟢 alta / 🟡 média / 🔴 baixa) em cada insight
   - **Exemplo hipotético**: Insights de SHAP têm precision 0.85 → 🟢; Insights de outliers têm 0.45 → 🔴
   - **Entregável**: Sistema de badges + documentação de metodologia

**Critério de Sucesso**:
- ≥ 10 experimentos com validação real completada
- ≥ 1 artigo/case study publicável sobre correlação synths vs. humanos
- Sistema de confiança implementado e visível no UI

---

#### **Prioridade 4: Posicionamento e Go-to-Market**
**Objetivo**: Definir ICP (Ideal Customer Profile), pricing e canais de aquisição.

**Táticas**:
1. **Análise de ICP (Jan-Fev 2026)**
   - **Hipótese inicial**: Startups Série A-B, B2C, equipe de produto 5-15 pessoas
   - **Validação**: Entrevistas com 15 PMs/UX Researchers de diferentes perfis
   - **Perguntas**:
     - Quanto tempo/$ gastam em research hoje?
     - Quais decisões de produto são mais arriscadas?
     - Pagariam por simulações sintéticas? Quanto?
   - **Entregável**: Documento de ICP com 3 personas de clientes

2. **Teste de Pricing (Mar 2026)**
   - **Modelos a testar**:
     - **Freemium**: 5 experimentos/mês grátis, $99/mês ilimitado
     - **Per-Seat**: $49/mês por PM/UX Researcher
     - **Usage-Based**: $5 por experimento (pré-pago)
   - **Método**: Van Westendorp Price Sensitivity Meter (survey com 50+ respondentes)
   - **Entregável**: Recomendação de pricing com modelo financeiro (CAC, LTV, break-even)

3. **Conteúdo Educacional (Abr-Mai 2026)**
   - **Objetivo**: Educar mercado sobre research sintética (categoria nova)
   - **Formatos**:
     - 3 blog posts técnicos (ex: "Como Simulações Monte Carlo Reduzem Risco de Produto")
     - 1 webinar: "De Hipótese a Insights em 2 Horas"
     - 1 case study detalhado com equipe piloto
   - **Distribuição**: LinkedIn (orgânico), communities de PM (Produto.io, Product Hunt)
   - **Entregável**: 5 peças de conteúdo publicadas, 500+ views agregados

4. **Parceria com Comunidades de Produto (Jun 2026)**
   - **Alvo**: Product Oversee, WomenTech, UXCONF BR
   - **Proposta**: Oferecer acesso gratuito para membros em troca de feedback + case studies
   - **Entregável**: ≥ 2 parcerias formalizadas, 50+ usuários adquiridos via comunidades

**Critério de Sucesso**:
- ICP documentado e validado com ≥ 10 entrevistas
- Modelo de pricing testado com ≥ 50 respondentes, recomendação clara
- ≥ 100 usuários únicos (fora de equipes piloto) testaram produto
- ≥ 1 case study publicado em comunidade relevante

---

### Roadmap de Features (Próximos 6 Meses)

| Feature | Prioridade | Impacto | Esforço | Prazo |
|---------|-----------|---------|---------|-------|
| **Sistema de Feedback (Thumbs Up/Down)** | P0 | 🟢 Alto (validação de qualidade) | 🟡 Médio (2 semanas) | Jan 2026 |
| **Paralelização de Insights** | P0 | 🟢 Alto (85% redução latência) | 🟢 Baixo (3 dias) | Jan 2026 |
| **Dashboard de Métricas de Uso** | P0 | 🟢 Alto (visibilidade de adoção) | 🟡 Médio (1 semana) | Fev 2026 |
| **Cache Inteligente de Simulações** | P1 | 🟡 Médio (50% menos re-runs) | 🟡 Médio (1.5 semanas) | Fev 2026 |
| **Comparação A/B de Experimentos** | P1 | 🟡 Médio (facilita decisões) | 🟢 Baixo (4 dias) | Mar 2026 |
| **Validação com Usuários Reais (Tracking)** | P1 | 🟢 Alto (prova de valor) | 🔴 Alto (3 semanas) | Mar 2026 |
| **Badges de Confiança em Insights** | P1 | 🟡 Médio (transparência) | 🟡 Médio (1 semana) | Jun 2026 |
| **Multi-Tenancy + Permissões** | P2 | 🔴 Crítico (blocker p/ B2B) | 🔴 Alto (4 semanas) | Abr 2026 |
| **Exportação de Dados (CSV/JSON)** | P2 | 🟡 Médio (power users) | 🟢 Baixo (2 dias) | Mai 2026 |
| **Integração Jira/Linear** | P3 | 🟡 Médio (workflow) | 🟡 Médio (2 semanas) | Jun 2026 |

---

### Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|--------------|---------|-----------|
| **Equipes piloto não executam experimentos** | 🟡 Média | 🔴 Alto | Onboarding dedicado (1h/semana), templates prontos, follow-ups semanais |
| **Insights de IA têm baixa qualidade (< 50% úteis)** | 🟡 Média | 🔴 Alto | A/B testing de prompts, human-in-the-loop review antes de GA |
| **Validação real contradiz synths sistematicamente** | 🟢 Baixa | 🔴 Alto | Study com 10 experimentos antes de claims públicos, transparência sobre limitações |
| **Custos de LLM excedem budget (> R$ 50/exp)** | 🟡 Média | 🟡 Médio | Otimização de prompts, cache agressivo, fallback para modelos menores |
| **Concorrente lança produto similar** | 🟡 Média | 🟡 Médio | Foco em dados IBGE (moat local), open-source para community lock-in |
| **Churn de equipes piloto (> 50%)** | 🟡 Média | 🟢 Baixo | NPS surveys mensais, identificar churn signals cedo, oferecer extensão gratuita |
| **Escalabilidade: banco de dados não aguenta carga** | 🟢 Baixa | 🟡 Médio | Load testing com 10K synths, 1K experimentos antes de GA, índices otimizados |

---

### Recursos Necessários

#### **Time (6 meses)**
| Função | FTE | Justificativa |
|--------|-----|---------------|
| **Backend Engineer** | 1.0 | Features de paralelização, cache, multi-tenancy |
| **Frontend Engineer** | 0.5 | UI de feedback, dashboards, comparação A/B |
| **Product Manager** | 0.3 | Roadmap, priorização, entrevistas de ICP |
| **UX Researcher (Consultor)** | 0.2 | Desenho de validation studies, análise qualitativa |
| **DevOps/Infra** | 0.1 | Monitoramento, CI/CD, load testing |

#### **Budget (6 meses)**
| Item | Custo | Justificativa |
|------|-------|---------------|
| **LLM API Costs (OpenAI)** | R$ 3.000 | 150 experimentos × R$ 20 (buffer 50%) |
| **Infra (AWS/GCP)** | R$ 2.000 | PostgreSQL RDS, compute, storage |
| **Ferramentas (Mixpanel, etc.)** | R$ 1.500 | Analytics, monitoring, CI/CD |
| **Recrutamento de Usuários** | R$ 4.000 | 10 validation studies × R$ 400 incentivo |
| **Marketing de Conteúdo** | R$ 2.500 | Designer, copywriter freelance |
| **Contingência (20%)** | R$ 2.600 | Buffer para imprevistos |
| **TOTAL** | **R$ 15.600** | ~R$ 2.600/mês |

---

## 7. Appendix: Dados e Contexto Adicional

### A. Stack Tecnológico Completo

#### Backend
```python
Python 3.13+
FastAPI 0.115+          # Web framework
SQLAlchemy 2.0+         # ORM
Pydantic 2.0+           # Data validation
OpenAI SDK 1.57+        # LLM integration
Arize Phoenix           # LLM tracing
OpenTelemetry           # Observability
Alembic                 # Database migrations
PostgreSQL 14+          # Database
Loguru                  # Logging
```

#### Frontend
```typescript
TypeScript 5.5+
React 18
TanStack Query 5        # Server state management
shadcn/ui               # Component library
Tailwind CSS            # Styling
Vite                    # Build tool
```

#### Data Science
```python
NumPy, Pandas           # Data manipulation
Matplotlib, Seaborn     # Visualization
scikit-learn            # Clustering, outlier detection
SHAP                    # Explainability
```

---

### B. Esquema de Banco de Dados (Simplificado)

```sql
-- Core entities
experiments (id, name, hypothesis, scorecard_data JSONB)
synths (id, nome, arquetipo, data JSONB, avatar_path)

-- Quantitative analysis
analysis_runs (id, experiment_id, status, aggregated_outcomes JSONB)
analysis_cache (experiment_id, chart_type, data JSONB)

-- Qualitative research
research_executions (id, topic_name, experiment_id, status, summary_content)
transcripts (id, exec_id, synth_id, messages JSONB[])

-- Scenario exploration
explorations (id, experiment_id, goal, config JSONB, status)
scenario_nodes (id, exploration_id, parent_id, action_applied, scorecard JSONB, simulation_results JSONB)

-- Document management
experiment_documents (id, experiment_id, document_type, content, metadata JSONB)
```

**Relationships**:
- `experiments 1:N analysis_runs` — Um experimento pode ter múltiplas rodadas de simulação
- `experiments 1:N research_executions` — Um experimento pode ter múltiplas bateladas de entrevistas
- `research_executions 1:N transcripts` — Cada execução gera N transcritos (1 por synth)
- `explorations 1:N scenario_nodes` — Árvore de exploração com nós filho
- `experiments 1:N experiment_documents` — Documentos gerados (summaries, PR-FAQs)

---

### C. Exemplo de Scorecard (Feature: "Checkout em 1 Clique")

```json
{
  "complexity": {
    "ui_complexity": 3.0,
    "backend_complexity": 7.0,
    "integration_complexity": 6.5
  },
  "effort": {
    "design_effort": 4.0,
    "development_effort": 8.0,
    "testing_effort": 6.0
  },
  "risk": {
    "technical_risk": 5.5,
    "user_adoption_risk": 7.0,
    "security_risk": 8.5
  },
  "time_to_value": {
    "time_to_first_value": 6.0,
    "time_to_full_adoption": 8.0
  }
}
```

**Interpretação**:
- **Complexidade de Backend**: 7.0 (alta) — Precisa de tokenização de cartão, PCI compliance
- **Risco de Segurança**: 8.5 (muito alta) — Armazenar dados de pagamento
- **Esforço de Desenvolvimento**: 8.0 (alto) — 4-6 sprints estimados
- **Risco de Adoção**: 7.0 (alta) — Usuários podem desconfiar de segurança

Esses valores alimentam o modelo probabilístico:
- `capability = 1 / (1 + complexity_total / 10)` → 0.62 (usuário médio tem 62% de capacidade de usar)
- `trust = 1 / (1 + risk_total / 10)` → 0.68 (68% de confiança)
- `P(try) = capability × trust × (1 - friction)` → 0.35 (35% tentam usar)

---

### D. Exemplo de Output de Exploração

**Experimento**: Dashboard de Analytics (Baseline: 28% success_rate)

**Árvore de Exploração** (beam width = 3, max depth = 5):

```
[ROOT] Baseline (success: 28%)
├─ [Ação 1] Remover 40% das métricas menos usadas
│  │  Rationale: Reduz cognitive load (complexity 8.5 → 5.2)
│  │  Result: success 35% (+7pp)
│  ├─ [Ação 1.1] Adicionar tour guiado interativo
│  │  │  Rationale: Aumenta capability (effort 6.0 → 7.5, mas trust +2)
│  │  │  Result: success 41% (+6pp) ⭐ WINNER
│  │  └─ [Ação 1.2] Personalizar dashboard por role
│  │     │  Result: success 38% (+3pp) [DOMINATED]
│  └─ [...]
├─ [Ação 2] Adicionar presets para casos comuns
│  │  Result: success 31% (+3pp) [DOMINATED]
└─ [Ação 3] Redesenhar navegação com mega-menu
   │  Result: success 29% (+1pp) [DOMINATED]
```

**Caminho Vencedor** (Ação 1 → Ação 1.1):
1. Remover 40% das métricas (complexity -38%)
2. Adicionar tour guiado (trust +20%, effort +25%)
3. **Resultado final**: 28% → 41% success_rate (+46% relativo)

**Resumo Gerado por LLM**:
> "A exploração identificou que a sobrecarga cognitiva é o principal bloqueador de adoção. Remover métricas raramente usadas (pageviews por região, bounce rate por device) reduziu a complexidade percebida sem perda funcional. Adicionar um tour guiado interativo no primeiro acesso compensa o aumento de esforço ao melhorar a confiança dos usuários de que entendem a ferramenta. O caminho vencedor aumenta a taxa de sucesso de 28% para 41%, tornando a feature viável para lançamento."

---

### E. Distribuições Demográficas (IBGE)

**Fonte**: Censo 2022 + PNAD Contínua 2023

| Atributo | Distribuição (%) | Fonte |
|----------|------------------|-------|
| **Região** | Sul 14.3, Sudeste 41.8, Nordeste 27.2, Norte 8.6, Centro-Oeste 8.1 | IBGE Censo 2022 |
| **Faixa Etária** | 18-24 (12%), 25-34 (18%), 35-44 (17%), 45-54 (15%), 55-64 (13%), 65+ (25%) | PNAD 2023 |
| **Renda Familiar** | Até 2 SM (48%), 2-5 SM (28%), 5-10 SM (14%), 10-20 SM (7%), 20+ SM (3%) | PNAD 2023 |
| **Escolaridade** | Sem instrução (6%), Fundamental (32%), Médio (43%), Superior (19%) | PNAD 2023 |
| **Deficiências** | Visual (3.4%), Auditiva (1.1%), Motora (2.3%), Cognitiva (0.8%) | Censo 2022 |

**Correlações Modeladas**:
- Escolaridade × Renda (Pearson r = 0.68)
- Idade × Deficiência Motora (r = 0.42 para idade > 55)
- Região Sul/Sudeste × Renda > 5 SM (r = 0.35)

---

### F. Benchmarks de Performance

**Ambiente**: MacBook Pro M2, 16GB RAM, PostgreSQL local

| Operação | Latência (p50) | Latência (p95) | Throughput |
|----------|----------------|----------------|------------|
| **Gerar 1 Synth** | 12ms | 25ms | 83 synths/s |
| **Gerar Avatar (DALL-E 3)** | 3.2s | 5.1s | 0.3 avatars/s |
| **Simulação (1K executions)** | 180ms | 320ms | 5.5 sims/s |
| **Simulação (10K executions)** | 1.8s | 2.9s | 0.55 sims/s |
| **Entrevista UX (6 turnos)** | 18s | 35s | 0.055 interviews/s |
| **Insight LLM (1 chart)** | 4.2s | 8.1s | 0.24 insights/s |
| **SHAP Analysis (1K synths)** | 2.1s | 3.4s | 0.47 analyses/s |

**Gargalos Identificados**:
1. **Geração de Avatares**: 90% do tempo de criação de synths (rate limit OpenAI)
2. **Entrevistas UX**: Latência dominada por LLM (não paralelizável dentro de 1 conversa)
3. **SHAP**: Computacionalmente intensivo, não cacheado

---

### G. Glossário de Termos

| Termo | Definição |
|-------|-----------|
| **Synth** | Synthetic persona — personagem simulado com atributos demográficos, psicográficos e comportamentais baseados em dados IBGE |
| **Scorecard** | Conjunto de 12 dimensões que descrevem uma feature (complexity, effort, risk, time_to_value) |
| **Monte Carlo Simulation** | Técnica probabilística que executa milhares de simulações amostrando aleatoriamente da distribuição de synths |
| **SHAP (SHapley Additive exPlanations)** | Método de explicabilidade que atribui importância a cada feature na predição de um outcome |
| **PDP (Partial Dependence Plot)** | Gráfico que mostra o efeito marginal de uma variável no outcome, mantendo outras constantes |
| **Beam Search** | Algoritmo de busca que mantém K candidatos (beam width) em cada nível da árvore de exploração |
| **Pareto Dominance** | Nó A domina B se A é melhor ou igual em todas dimensões e estritamente melhor em pelo menos uma |
| **Topic Guide** | Roteiro de entrevista UX com perguntas, imagens e documentos de apoio |
| **PR-FAQ** | Press Release + Frequently Asked Questions — formato Amazon para especificações de produto |
| **Phoenix Tracing** | Sistema de observabilidade da Arize para rastrear chamadas LLM com spans OpenTelemetry |

---

### H. Referências e Links

#### Documentação Técnica
- Arquitetura Backend: `/docs/arquitetura.md`
- Arquitetura Frontend: `/docs/arquitetura_front.md`
- Modelo de Dados: `/docs/database_model.md`
- API Reference: `/docs/api.md`

#### Especificações de Features
- `/specs/023-chart-insights.md` — Sistema de insights de IA para charts
- `/specs/026-document-management.md` — Gerenciamento de documentos
- `/specs/027-postgresql-migration.md` — Migração para PostgreSQL
- `/specs/028-exploration-summary.md` — Resumos de exploração

#### Dados Externos
- IBGE Censo 2022: https://censo2022.ibge.gov.br/
- PNAD Contínua 2023: https://www.ibge.gov.br/estatisticas/sociais/trabalho/9171-pesquisa-nacional-por-amostra-de-domicilios-continua-mensal.html
- OpenAI API: https://platform.openai.com/docs
- Arize Phoenix: https://docs.arize.com/phoenix

#### Papers de Referência
- "Explaining Predictions with SHAP": Lundberg & Lee, 2017
- "Monte Carlo Methods in Financial Engineering": Glasserman, 2003
- "Beam Search Algorithms": Lowerre, 1976

---

**Documento preparado em**: 04 de Janeiro de 2026
**Próxima revisão**: 01 de Abril de 2026 (pós-validação com equipes piloto)
**Responsável**: Fulvio (Product Lead, Synth-Lab)
**Versão**: 1.0
