# synth-lab - Documentação de Funcionalidades

> Documentação completa de todas as funcionalidades da plataforma synth-lab

**Última atualização**: 2026-01-13

---

## Visão Geral

O **synth-lab** é uma plataforma de pesquisa e experimentação que utiliza personas sintéticas (synths) para testar hipóteses sobre features, produtos e ideias. A plataforma combina simulação quantitativa, entrevistas qualitativas com IA e exploração automatizada de cenários.

### Stack Tecnológico
- **Backend**: Python 3.13+, FastAPI, SQLAlchemy 2.0+, PostgreSQL 14+
- **Frontend**: TypeScript 5.5+, React 18, TanStack Query, shadcn/ui, Tailwind CSS
- **IA**: OpenAI SDK, OpenAI Agents SDK, Arize Phoenix (tracing)
- **Storage**: PostgreSQL (metadata), S3-compatible (arquivos)

---

## 1. GESTÃO DE SYNTHES (Personas Sintéticas)

### 1.1 Listar Synths
- **Endpoint**: `GET /synths/list`
- **Descrição**: Lista todas as personas sintéticas disponíveis com paginação, filtros e seleção de campos
- **Parâmetros**:
  - `limit` (1-200, padrão: 50)
  - `offset` (padrão: 0)
  - `sort_by` (nome do campo)
  - `sort_order` (asc/desc)
  - `fields` (lista de campos a retornar)
  - `synth_group_id` (filtrar por grupo)
- **Retorno**: Lista paginada de `SynthSummary` (ID, nome, arquétipo, descrição)
- **Frontend**: `Synths.tsx` (página catálogo)

### 1.2 Obter Detalhes de um Synth
- **Endpoint**: `GET /synths/{synth_id}`
- **Descrição**: Retorna perfil completo de uma persona sintética incluindo:
  - Demografia (idade, gênero, localização, etc.)
  - Psicografia (valores, comportamentos, atitudes)
  - Capacidades técnicas
  - Histórico comportamental
- **Retorno**: `SynthDetail` com todos os dados aninhados

### 1.3 Obter Avatar de um Synth
- **Endpoint**: `GET /synths/{synth_id}/avatar`
- **Descrição**: Retorna imagem PNG do avatar do synth
- **Comportamento**:
  - Tenta carregar arquivo local primeiro
  - Se não existir, redireciona para `link_photo` dinâmico

### 1.4 Campos Disponíveis de Synth
- **Endpoint**: `GET /synths/fields`
- **Descrição**: Retorna metadata de todos os campos disponíveis para query e seleção
- **Retorno**: Lista de `SynthFieldInfo` (nome, tipo, descrição, nullable)
- **Uso**: Interface dinâmica de filtros e seleção de campos

### 1.5 Buscar Synths
- **Endpoint**: `POST /synths/search`
- **Descrição**: Busca avançada com cláusulas WHERE customizadas ou queries SQL
- **Parâmetros**:
  - `where_clause` (string SQL para filtro)
  - `query` (query SQL completa - apenas SELECT permitido)
  - Paginação (limit, offset)
- **Segurança**: Queries são validadas para prevenir SQL injection
- **Componentes**: `SynthRepository.search()`

---

## 2. GESTÃO DE GRUPOS DE SYNTHS

### 2.1 Listar Grupos de Synths
- **Endpoint**: `GET /synth-groups/list`
- **Descrição**: Lista todos os grupos de synths disponíveis com paginação
- **Retorno**: Lista de `SynthGroupSummary` (id, name, description, synth_count)
- **Frontend**: `Synths.tsx` (Synth Groups Panel)

### 2.2 Criar Grupo de Synths
- **Endpoint**: `POST /synth-groups`
- **Descrição**: Cria novo grupo customizado de synths
- **Campos**:
  - `name` (obrigatório)
  - `description` (opcional)
  - `synth_ids` (lista de IDs dos synths)
  - `config` (configuração JSONB - distribuições, critérios)
- **Grupo Padrão**: `grp_00000001` (todos os synths)
- **Entidade**: `SynthGroup` em `domain/entities/synth_group.py`

### 2.3 Obter Detalhes de Grupo
- **Endpoint**: `GET /synth-groups/{group_id}`
- **Descrição**: Retorna grupo completo com lista de synths associados
- **Retorno**: `SynthGroupDetailResponse` com:
  - Metadata do grupo
  - `synth_count` (total de synths)
  - Lista de synths do grupo

### 2.4 Deletar Grupo
- **Endpoint**: `DELETE /synth-groups/{group_id}`
- **Descrição**: Remove grupo de synths
- **Status**: 204 No Content
- **Restrição**: Não pode deletar grupo padrão

---

## 3. CHAT COM SYNTHS (Pós-Entrevista)

### 3.1 Chat Simples
- **Endpoint**: `POST /synths/{synth_id}/chat`
- **Descrição**: Enviar mensagem e receber resposta de um synth específico
- **Campos**:
  - `message` (string)
  - `interview_id` (opcional - para contexto)
  - `history` (opcional - histórico de mensagens)
- **Funcionalidade**:
  - Mantém contexto de entrevista anterior
  - Persona do synth é preservada
  - Histórico de mensagens
- **Componentes**: `services/chat/service.py`

### 3.2 Chat com Streaming
- **Endpoint**: `POST /synths/{synth_id}/chat/stream`
- **Descrição**: Chat com resposta em tempo real via Server-Sent Events (SSE)
- **Retorno**: Streaming de tokens com headers SSE apropriados
- **Uso**: Experiência real-time token-by-token no frontend
- **Headers**: `text/event-stream`, `Cache-Control: no-cache`

---

## 4. EXPERIMENTOS (Feature Testing Hub)

### 4.1 Criar Experimento
- **Endpoint**: `POST /experiments`
- **Descrição**: Cria novo experimento para testar uma feature, produto ou hipótese
- **Campos**:
  - `name` (max 100 caracteres)
  - `hypothesis` (max 500 caracteres)
  - `description` (max 2000 caracteres)
  - `synth_group_id` (padrão: grp_00000001)
  - `scorecard_data` (opcional, embedded)
- **Side Effects**:
  - Inicia geração assíncrona de interview guide
  - Gera ID no formato `exp_[a-f0-9]{8}`
- **Frontend**: `Index.tsx` (ExperimentForm dialog)
- **Entidade**: `Experiment` em `domain/entities/experiment.py`

### 4.2 Listar Experimentos
- **Endpoint**: `GET /experiments/list`
- **Descrição**: Lista todos os experimentos com paginação, busca e filtros
- **Parâmetros**:
  - `limit`, `offset` (paginação)
  - `search` (busca por nome/hipótese)
  - `tag` (filtrar por tag)
  - `sort_by`, `sort_order`
- **Retorno**: `PaginatedExperimentSummary` com:
  - Metadata do experimento
  - `interview_count` (número de entrevistas)
  - Flags de análise (has_analysis, analysis_status)
- **Frontend**: `Index.tsx` (ExperimentCard grid)

### 4.3 Obter Detalhes de Experimento
- **Endpoint**: `GET /experiments/{experiment_id}`
- **Descrição**: Experimento completo com todas as informações aninhadas
- **Retorno**: `ExperimentDetail` incluindo:
  - Metadata básica
  - Scorecard data (4 dimensões)
  - Analysis summary (simulation results)
  - Interviews list
  - Explorations list
  - Documents availability
  - Tags associadas
- **Frontend**: `ExperimentDetail.tsx` (view read-only com tabs)

### 4.4 Atualizar Experimento
- **Endpoint**: `PUT /experiments/{experiment_id}`
- **Descrição**: Atualiza informações básicas do experimento
- **Campos Atualizáveis**: `name`, `hypothesis`, `description`
- **Nota**: Scorecard deve ser atualizado via endpoint separado

### 4.5 Deletar Experimento
- **Endpoint**: `DELETE /experiments/{experiment_id}`
- **Descrição**: Remove experimento e todos os dados associados
- **Cascata**: Remove análises, entrevistas, documentos, materiais
- **Status**: 204 No Content

### 4.6 Scorecard - Estimar via IA
- **Endpoints**:
  - `POST /experiments/estimate-scorecard` (global - sem experimento)
  - `POST /experiments/{experiment_id}/estimate-scorecard` (para experimento específico)
- **Descrição**: Usa OpenAI para estimar automaticamente as 4 dimensões do scorecard
- **Campos de Entrada**:
  - `name`, `hypothesis`, `description` (para global)
  - Usa dados do experimento (para específico)
- **4 Dimensões Estimadas**:
  - **Complexity**: Complexidade técnica da implementação
  - **Initial Effort**: Esforço inicial necessário
  - **Perceived Risk**: Risco percebido pelos usuários
  - **Time to Value**: Tempo até usuário perceber valor
- **Componentes**: `scorecard_estimator.py` com tracing OpenTelemetry
- **Retorno**: `ScorecardEstimateResponse` com:
  - Scores (0-100) para cada dimensão
  - Bounds (min, max) estimados
  - Reasoning (justificativa)

### 4.7 Scorecard - Atualizar
- **Endpoint**: `PUT /experiments/{experiment_id}/scorecard`
- **Descrição**: Atualiza ou cria scorecard embedded no experimento
- **Campos**: 4 dimensões do tipo `ScorecardDimension`:
  - `value` (0-100)
  - `label` (nome da dimensão)
  - `description` (opcional)
- **Entidade**: `ScorecardData` em `domain/entities/experiment.py`

---

## 5. ENTREVISTAS / RESEARCH EXECUTIONS

### 5.1 Executar Entrevista
- **Endpoint**: `POST /research/execute`
- **Descrição**: Inicia batch de entrevistas com synths sobre um tópico específico
- **Parâmetros**:
  - `topic_name` (nome do tópico/feature a investigar)
  - `synth_ids` (lista específica) OU `synth_count` (número aleatório)
  - `experiment_id` (opcional - para linkar experimento)
  - `max_turns` (padrão: 6 - número de perguntas)
  - `generate_summary` (padrão: true)
  - `additional_context` (opcional)
- **Componentes**:
  - Router: `research.py`
  - Serviço: `research_service.py`
  - Executor: `services/research_agentic/runner.py` (OpenAI Agents SDK)
- **Retorno**: `ResearchExecuteResponse` com:
  - `exec_id` (ID da execução)
  - Status inicial (pending/running)
- **Execução**: Assíncrona com message broker para updates em tempo real
- **Frontend**: `InterviewDetail.tsx` (com LiveInterviewGrid)

### 5.2 Listar Execuções de Research
- **Endpoint**: `GET /research/list`
- **Descrição**: Lista todas as execuções de research (entrevistas)
- **Parâmetros**: Paginação padrão (limit, offset, sort)
- **Retorno**: `PaginatedResponse[ResearchExecutionSummary]` com:
  - exec_id, topic_name, status
  - synth_count, completed_count
  - has_summary flag
  - Timestamps

### 5.3 Obter Detalhes de Execução
- **Endpoint**: `GET /research/{exec_id}`
- **Descrição**: Status completo da execução de research
- **Retorno**: `ResearchExecutionDetail` com:
  - Status da execução
  - Contagens (total synths, completados, falhados)
  - Flags de documentos disponíveis
  - Linked experiment (se houver)

### 5.4 Obter Transcrições
- **Endpoint**: `GET /research/{exec_id}/transcripts`
- **Descrição**: Lista transcrições de cada synth entrevistado
- **Parâmetros**: Paginação padrão
- **Retorno**: `PaginatedResponse[TranscriptSummary]` com:
  - synth_id, synth_name
  - Status (pending/running/completed/failed)
  - Turn count, message count

### 5.5 Obter Transcrição Específica
- **Endpoint**: `GET /research/{exec_id}/transcripts/{synth_id}`
- **Descrição**: Transcrição completa com todas as mensagens da entrevista
- **Retorno**: `TranscriptDetail` com:
  - Metadata (synth, status, counts)
  - `messages` array (pergunta/resposta com timestamps)
  - Summary da entrevista individual (se gerada)

### 5.6 Stream de Mensagens em Tempo Real
- **Endpoint**: `GET /research/{exec_id}/stream`
- **Descrição**: SSE endpoint para monitoramento live das entrevistas
- **Eventos SSE**:
  - `message`: Mensagem individual de entrevista
  - `interview_completed`: Uma entrevista finalizou
  - `transcription_completed`: Todas as entrevistas finalizadas
  - `execution_completed`: Processamento completo (incluindo summary)
- **Comportamento**:
  - Replay histórico (mensagens já enviadas)
  - Streaming live de novas mensagens
- **Componentes**:
  - Backend: `message_broker.py` (in-memory queues)
  - Frontend: `LiveInterviewGrid` em `InterviewDetail.tsx`

### 5.7 Entrevista Automática com Casos Extremos
- **Endpoint**: `POST /experiments/{experiment_id}/interviews/auto`
- **Descrição**: Cria automaticamente entrevista com 10 synths extremos selecionados da análise
- **Seleção**: 5 melhores (top performers) + 5 piores (worst performers)
- **Validação**: Requer:
  - Experimento com interview guide gerado
  - Análise prévia executada
- **Uso**: Investigação qualitativa de casos extremos identificados quantitativamente

### 5.8 Criar Entrevista para Experimento
- **Endpoint**: `POST /experiments/{experiment_id}/interviews`
- **Descrição**: Cria entrevista linkedada diretamente ao experimento
- **Parâmetros**:
  - `additional_context` (contexto extra)
  - `synth_ids` (específicos) OU `synth_count` (aleatórios)
  - `max_turns` (padrão: 6)
  - `generate_summary` (padrão: true)
- **Pré-requisito**: Experimento deve ter interview guide gerado
- **Uso**: Interview guide é automaticamente usado como base

---

## 6. DOCUMENTOS GERADOS (Research Summary, PRFAQ, Executive Summary)

### 6.1 Gerar Sumário de Research
- **Endpoints**:
  - `POST /research/{exec_id}/documents/summary/generate` (novo)
  - `POST /research/{exec_id}/summary/generate` (legacy, deprecated)
- **Descrição**: Gera sumário narrativo consolidado a partir das transcrições de entrevistas
- **Componentes**:
  - Serviço: `research_summary_generator_service.py`
  - LLM: OpenAI com prompts estruturados
  - Tracing: OpenTelemetry spans
- **Pré-requisitos**:
  - Execução completa
  - Transcripts disponíveis
  - Linked a experimento
- **Retorno**: `DocumentDetailResponse` com:
  - document_id
  - document_type (RESEARCH_SUMMARY)
  - markdown_content
  - Status (generating/completed/failed)

### 6.2 Obter Sumário de Research
- **Endpoint**: `GET /research/{exec_id}/documents/summary`
- **Descrição**: Recupera sumário gerado (ou null se não existe)
- **Retorno**: `DocumentDetailResponse` ou null

### 6.3 Deletar Sumário
- **Endpoint**: `DELETE /research/{exec_id}/documents/summary`
- **Descrição**: Remove sumário gerado
- **Status**: 204 No Content

### 6.4 Gerar PRFAQ (Press Release / FAQ)
- **Endpoint**: `POST /research/{exec_id}/documents/prfaq/generate`
- **Descrição**: Gera documento no formato Amazon PRFAQ a partir do sumário
- **Componentes**: `research_prfaq_generator_service.py`
- **Pré-requisitos**: Sumário deve existir
- **Estrutura PRFAQ**:
  - Press Release (anúncio fictício)
  - FAQ (perguntas frequentes)
  - Baseado em insights das entrevistas

### 6.5 Obter/Deletar PRFAQ
- **Endpoints**:
  - `GET /research/{exec_id}/documents/prfaq`
  - `DELETE /research/{exec_id}/documents/prfaq`
- **Descrição**: Recupera ou remove documento PRFAQ

### 6.6 Listar/Obter Documentos do Experimento
- **Endpoints**:
  - `GET /experiments/{experiment_id}/documents` - Lista todos os documentos
  - `GET /experiments/{experiment_id}/documents/availability` - Checa quais existem
- **Tipos de Documentos**:
  - RESEARCH_SUMMARY
  - RESEARCH_PRFAQ
  - EXPLORATION_SUMMARY
  - EXPLORATION_PRFAQ
  - EXECUTIVE_SUMMARY
- **Componentes**: `DocumentsList.tsx` no frontend
- **Documentação**: `/docs/template_feat_scorecard.md`

---

## 7. ANALYSIS (Simulação e Quantificação)

### 7.1 Executar Análise
- **Endpoint**: `POST /experiments/{experiment_id}/analysis/run`
- **Descrição**: Executa simulação do experimento com synths e gera outcomes quantitativos
- **Componentes**:
  - Router: `analysis.py`
  - Serviço: `services/analysis/analysis_service.py`
  - Executor: `services/analysis/analysis_execution_service.py`
  - Engine: `services/simulation/engine.py`
- **Parâmetros**:
  - `config` (opcional - configurações de simulação)
  - `n_executions` (número de runs)
- **Processo**:
  1. Simula comportamento de cada synth
  2. Calcula métricas (try rate, success rate, adoption)
  3. Gera insights e visualizações
- **Retorno**: `AnalysisResponse` com simulation_id

### 7.2 Obter Resultado de Analysis
- **Endpoint**: `GET /experiments/{experiment_id}/analysis`
- **Descrição**: Retorna status e resultados agregados da análise
- **Retorno**: `AnalysisResponse` com:
  - simulation_id
  - Status (running/completed/failed)
  - execution_time
  - Aggregated outcomes (try_rate, success_rate, etc.)
  - Available charts
  - Timestamps

### 7.3 Charts/Visualizações de Analysis

#### 7.3.1 Outcome Distribution
- **Endpoint**: `GET /experiments/{experiment_id}/analysis/{simulation_id}/charts/outcome-distribution`
- **Tipo**: `OutcomeDistributionChart`
- **Descrição**: Distribuição de outcomes (sucesso/falha/não-tentou)
- **Dados**: Contagens e percentuais por categoria
- **Frontend**: Gráfico de barras ou pizza

#### 7.3.2 Try vs Success
- **Endpoint**: `GET /experiments/{experiment_id}/analysis/{simulation_id}/charts/try-vs-success`
- **Tipo**: `TryVsSuccessChart`
- **Descrição**: Scatter plot relacionando taxa de tentativa vs taxa de sucesso
- **Eixos**: X = try rate, Y = success rate
- **Insights**: Identifica synths que tentam mas não conseguem

#### 7.3.3 Failure Heatmap
- **Endpoint**: `GET /experiments/{experiment_id}/analysis/{simulation_id}/charts/failure-heatmap`
- **Tipo**: `FailureHeatmapChart`
- **Descrição**: Matriz de correlação entre atributos dos synths e falhas
- **Visualização**: Heatmap mostrando onde falhas se concentram
- **Uso**: Identificar características problemáticas

#### 7.3.4 Scatter Correlation
- **Endpoint**: `GET /experiments/{experiment_id}/analysis/{simulation_id}/charts/scatter-correlation`
- **Tipo**: `ScatterCorrelationChart`
- **Descrição**: Correlação entre dois atributos específicos
- **Parâmetros**: feature_x, feature_y

#### 7.3.5 Sankey Flow
- **Endpoint**: `GET /experiments/{experiment_id}/analysis/{simulation_id}/charts/sankey-flow`
- **Tipo**: `SankeyFlowChart`
- **Descrição**: Fluxo de estados (try → success/failed → outcomes)
- **Visualização**: Diagrama Sankey mostrando transições

### 7.4 Segmentação (Clustering)

#### 7.4.1 K-Means Clustering
- **Endpoint**: `POST /experiments/{experiment_id}/analysis/{simulation_id}/clustering/kmeans`
- **Descrição**: Agrupa synths por similaridade de comportamento/outcomes
- **Parâmetros**:
  - `n_clusters` (número de clusters)
  - `features` (atributos para clustering)
- **Retorno**: `KMeansResult` com:
  - cluster_assignments (synth_id → cluster_id)
  - centroids
  - inertia (qualidade do clustering)

#### 7.4.2 Hierarchical Clustering (Dendrogram)
- **Endpoint**: `POST /experiments/{experiment_id}/analysis/{simulation_id}/clustering/hierarchical`
- **Descrição**: Clustering hierárquico para visualização em dendrogram
- **Parâmetros**: linkage method, features
- **Retorno**: `HierarchicalResult` com:
  - linkage_matrix
  - dendrogram_data

#### 7.4.3 Cortar Dendrogram
- **Endpoint**: `POST /experiments/{experiment_id}/analysis/{simulation_id}/clustering/cut`
- **Descrição**: Corta dendrogram em altura específica para formar clusters
- **Parâmetros**: `CutDendrogramRequest` (height ou n_clusters)
- **Retorno**: Cluster assignments

#### 7.4.4 PCA Scatter
- **Endpoint**: `GET /experiments/{experiment_id}/analysis/{simulation_id}/charts/pca-scatter`
- **Tipo**: `PCAScatterChart`
- **Descrição**: Redução dimensional (PCA) dos dados para visualização 2D/3D
- **Uso**: Visualizar separação natural dos synths
- **Dados**: 2-3 componentes principais + variance explained

#### 7.4.5 Radar Chart (Cluster Profile)
- **Endpoint**: `GET /experiments/{experiment_id}/analysis/{simulation_id}/charts/radar/{cluster_id}`
- **Tipo**: `RadarChart`
- **Descrição**: Perfil médio de atributos de um cluster específico
- **Visualização**: Radar/spider chart com múltiplas dimensões
- **Uso**: Comparar perfis de diferentes clusters

### 7.5 Casos Extremos (Outlier Analysis)

#### 7.5.1 Extreme Cases
- **Endpoint**: `GET /experiments/{experiment_id}/analysis/{simulation_id}/outliers`
- **Descrição**: Identifica synths com comportamento extremo (muito positivo ou negativo)
- **Algoritmo**: Detecção de outliers por distância estatística
- **Retorno**: `OutlierResult` com:
  - top_performers (5 melhores)
  - worst_performers (5 piores)
  - outlier_scores

#### 7.5.2 Tabela de Casos Extremos
- **Endpoint**: `GET /experiments/{experiment_id}/analysis/{simulation_id}/outliers/table`
- **Descrição**: Tabela formatada com synths extremos e suas características
- **Retorno**: `ExtremeCasesTable` com:
  - synth_ids
  - scores (success, try, adoption)
  - Key attributes
- **Uso**: Input para entrevista automática (endpoint 5.7)

### 7.6 Explainabilidade (SHAP, PDP)

#### 7.6.1 SHAP Summary
- **Endpoint**: `GET /experiments/{experiment_id}/analysis/{simulation_id}/explainability/shap-summary`
- **Descrição**: Feature importance via SHAP (SHapley Additive exPlanations)
- **Retorno**: `ShapSummary` com:
  - feature_names
  - importance_scores (impacto médio de cada feature)
  - sorted_features

#### 7.6.2 SHAP Explanation (Feature)
- **Endpoint**: `GET /experiments/{experiment_id}/analysis/{simulation_id}/explainability/shap/{feature}`
- **Descrição**: Explicação detalhada do impacto de uma feature específica
- **Retorno**: `ShapExplanation` com:
  - shap_values (contribuição individual por synth)
  - base_value
  - Visualização data

#### 7.6.3 PDP (Partial Dependence Plot)
- **Endpoint**: `GET /experiments/{experiment_id}/analysis/{simulation_id}/explainability/pdp/{feature}`
- **Descrição**: Como outcome muda conforme feature varia (mantendo outras constantes)
- **Retorno**: `PDPResult` com:
  - feature_values (grid de valores testados)
  - predictions (outcome médio para cada valor)

#### 7.6.4 PDP Comparison
- **Endpoint**: `GET /experiments/{experiment_id}/analysis/{simulation_id}/explainability/pdp-comparison`
- **Descrição**: Comparação de PDPs de múltiplas features lado a lado
- **Parâmetros**: Lista de features
- **Retorno**: `PDPComparison` com array de PDPResults

### 7.7 Insights com IA

#### 7.7.1 Gerar Insight para Chart
- **Endpoint**: `POST /experiments/{experiment_id}/analysis/insights/{chart_type}`
- **Descrição**: Gera insight narrativo interpretando um chart específico via LLM
- **Parâmetros**:
  - `chart_type` (outcome-distribution, try-vs-success, etc.)
  - Chart data (do endpoint correspondente)
- **Componentes**: `insight_service.py` com prompts especializados
- **Retorno**: `ChartInsight` com:
  - chart_type
  - narrative (texto interpretativo)
  - key_findings (bullet points)
  - recommendations

#### 7.7.2 Listar Todos os Insights
- **Endpoint**: `GET /experiments/{experiment_id}/analysis/insights`
- **Descrição**: Todos os insights gerados + executive summary + estatísticas
- **Retorno**: `AllInsightsResponse` com:
  - insights (array de ChartInsight)
  - executive_summary (overview consolidado)
  - stats (contagens, scores)

### 7.8 Executive Summary
- **Endpoint**: `GET /experiments/{experiment_id}/analysis/executive-summary`
- **Descrição**: Sumário narrativo executivo de toda a análise
- **Componentes**: `executive_summary_service.py`
- **Conteúdo**:
  - Overview dos resultados
  - Key findings principais
  - Recomendações estratégicas
  - Risk assessment
- **Retorno**: `ExecutiveSummary` com markdown_content

---

## 8. EXPLORAÇÃO (LLM-Assisted Scenario Exploration)

### 8.1 Criar Exploração
- **Endpoint**: `POST /explorations`
- **Descrição**: Inicia exploração automatizada de cenários com LLM propondo melhorias iterativas
- **Componentes**:
  - Router: `exploration.py`
  - Serviço: `services/exploration/exploration_service.py`
  - Entidade: `Exploration` em `domain/entities/exploration.py`
  - Frontend: `ExplorationDetail.tsx` com ExplorationTreeFlow
- **Parâmetros**:
  - `experiment_id` (experimento base)
  - `goal` (métrica + operador + valor alvo)
  - `max_depth` (profundidade máxima da árvore)
  - `max_iterations` (limite de iterações)
  - `initial_context` (opcional)
- **Processo**:
  1. Analisa resultados atuais do experimento
  2. LLM propõe ações para melhorar
  3. Simula cada ação proposta
  4. Escolhe melhor resultado e repete
- **Behavior**: Execução assíncrona com updates via message broker

### 8.2 Obter Exploração
- **Endpoint**: `GET /explorations/{exploration_id}`
- **Descrição**: Status e metadata da exploração
- **Retorno**: `ExplorationResponse` com:
  - exploration_id, experiment_id
  - goal (métrica alvo)
  - status (pending/running/completed/failed)
  - best_success_rate (melhor resultado encontrado)
  - node_count (número de cenários testados)
  - Timestamps

### 8.3 Árvore de Cenários
- **Endpoint**: `GET /explorations/{exploration_id}/tree`
- **Descrição**: Estrutura completa de nós e edges para visualização em React Flow
- **Componentes**:
  - Frontend: ExplorationTreeFlow, NodeDetailsPanel
  - Biblioteca: React Flow
- **Retorno**: `ExplorationTreeResponse` com:
  - `nodes` (array de ScenarioNode)
    - node_id, parent_id
    - action_applied (ação que levou a este nó)
    - metrics (success_rate, try_rate, etc.)
    - is_winner (melhor caminho)
  - `edges` (conexões entre nós)

### 8.4 Winning Path
- **Endpoint**: `GET /explorations/{exploration_id}/winning-path`
- **Descrição**: Sequência de ações que levou ao melhor resultado
- **Retorno**: `WinningPathResponse` com:
  - path (array ordenado de nodes)
  - final_metrics
  - actions_sequence (lista de ações aplicadas)
- **Uso**: Entender quais modificações geraram maior impacto

### 8.5 Executar/Continuar Exploração
- **Endpoint**: `POST /explorations/{exploration_id}/run`
- **Descrição**: Resume exploração de um ponto parado ou reexecuta
- **Uso**: Continuar exploração que foi pausada ou falhou

### 8.6 Sumário de Exploração
- **Endpoint**: `POST /explorations/{exploration_id}/documents/summary/generate`
- **Descrição**: Gera sumário narrativo consolidando resultados da exploração
- **Componentes**: `exploration_summary_generator_service.py`
- **Conteúdo**:
  - Objetivo da exploração
  - Cenários testados
  - Melhor caminho encontrado
  - Insights e recomendações

### 8.7 PRFAQ de Exploração
- **Endpoint**: `POST /explorations/{exploration_id}/documents/prfaq/generate`
- **Descrição**: Gera documento PRFAQ baseado nos resultados da exploração
- **Uso**: Comunicar recomendações no formato Amazon PRFAQ

### 8.8 Catálogo de Ações
- **Endpoint**: `GET /explorations/catalog/actions`
- **Descrição**: Lista de todas as ações disponíveis para proposição pelo LLM
- **Retorno**: `ActionCatalogResponse` com:
  - categories (categorias de ações)
  - actions (por categoria)
  - examples (casos de uso)
- **Tipos de Ações**:
  - Feature modifications
  - UX improvements
  - Pricing changes
  - Targeting adjustments
  - etc.

---

## 9. MATERIAIS (Imagens, Vídeos, Documentos)

### 9.1 Fazer Upload de Material
- **Endpoint**: `POST /experiments/{experiment_id}/materials`
- **Descrição**: Upload de arquivo (imagem, vídeo, documento) para experimento
- **Componentes**:
  - Router: `materials.py`
  - Serviço: `material_service.py`
  - Storage: S3-compatible (via `infrastructure/storage_client.py`)
  - Frontend: `MaterialUpload.tsx`
- **Tipos Suportados**:
  - IMAGE (png, jpg, jpeg, gif, webp)
  - VIDEO (mp4, webm, mov)
  - DOCUMENT (pdf, doc, docx)
- **Limites**:
  - Por material: configurável via env
  - Por experimento: quota total
- **Campos**:
  - `file` (multipart upload)
  - `material_type` (IMAGE/VIDEO/DOCUMENT)
  - `description` (opcional)
- **Retorno**: `MaterialUploadResponse` com material_id

### 9.2 Listar Materiais
- **Endpoint**: `GET /experiments/{experiment_id}/materials`
- **Descrição**: Lista todos os materiais do experimento
- **Retorno**: `MaterialListResponse` com array de `MaterialSummaryResponse`:
  - material_id, filename, material_type
  - file_size, upload_timestamp
  - thumbnail_url (presigned URL)
  - description, status
- **Frontend**: `MaterialGallery.tsx` (grid de thumbnails)

### 9.3 Obter Detalhes de Material
- **Endpoint**: `GET /experiments/{experiment_id}/materials/{material_id}`
- **Descrição**: Detalhes completo de um material específico
- **Retorno**: `MaterialDetailResponse` com:
  - Metadata completa
  - view_url (presigned URL para visualização)
  - download_url (presigned URL para download)

### 9.4 Gerar Descrição IA
- **Endpoint**: `POST /experiments/{experiment_id}/materials/{material_id}/describe`
- **Descrição**: Usa Vision API (GPT-4 Vision) para descrever imagens automaticamente
- **Processo**:
  1. Faz upload de imagem para OpenAI
  2. Gera descrição via modelo de visão
  3. Atualiza status: PENDING → COMPLETED/FAILED
- **Retorno**: Descrição gerada
- **Uso**: Auto-descrição de screenshots, mockups, wireframes

### 9.5 Confirmar Descrição
- **Endpoint**: `POST /experiments/{experiment_id}/materials/{material_id}/confirm-description`
- **Descrição**: Confirma ou edita descrição gerada por IA
- **Campos**: `description` (editada ou confirmada)
- **Uso**: Validação humana da descrição automática

### 9.6 Reordenar Materiais
- **Endpoint**: `POST /experiments/{experiment_id}/materials/reorder`
- **Descrição**: Atualiza ordem de apresentação dos materiais
- **Parâmetros**: `material_ids` (array ordenado)
- **Uso**: Interface de drag-and-drop no frontend

### 9.7 Deletar Material
- **Endpoint**: `DELETE /experiments/{experiment_id}/materials/{material_id}`
- **Descrição**: Remove material do experimento e do storage
- **Cascata**: Deleta arquivo do S3 + metadata do DB
- **Status**: 204 No Content

---

## 10. TAGS (Tagging de Experiments)

### 10.1 Listar Tags
- **Endpoint**: `GET /tags`
- **Descrição**: Lista todas as tags disponíveis no sistema
- **Retorno**: `List[TagResponse]` com:
  - tag_name
  - usage_count (número de experimentos)
  - created_at

### 10.2 Criar Tag
- **Endpoint**: `POST /tags`
- **Descrição**: Cria nova tag (ou retorna existente se nome duplicado)
- **Campos**: `tag_name` (único, lowercase)
- **Componentes**:
  - Router: `tags.py`
  - Repository: `tag_repository.py`
- **Validação**: Nome deve ser alfanumérico + hífens/underscores

### 10.3 Adicionar Tag a Experimento
- **Endpoint**: `POST /experiments/{experiment_id}/tags`
- **Descrição**: Associa tag existente a um experimento
- **Campos**: `tag_name`
- **Idempotente**: Não falha se já associada
- **Uso**: Organização e filtro de experimentos

### 10.4 Remover Tag de Experimento
- **Endpoint**: `DELETE /experiments/{experiment_id}/tags/{tag_name}`
- **Descrição**: Remove associação entre tag e experimento
- **Status**: 204 No Content

---

## 11. INTERVIEW GUIDE (Geração Automática)

### 11.1 Geração Automática de Interview Guide
- **Trigger**: Criação de experimento (via background task)
- **Componentes**:
  - Serviço: `interview_guide_generator_service.py`
  - Prompts: LLM-based com tracing OpenTelemetry
  - Storage: Database (interview_guide table)
- **Processo**:
  1. Recebe name, hypothesis, description do experimento
  2. LLM gera questions apropriadas
  3. Cria context_examples e context_definition
  4. Persiste no DB linkedado ao experimento
- **Estrutura**:
  - `questions` (array de perguntas para entrevista)
  - `context_definition` (definição do conceito)
  - `context_examples` (exemplos para synths)
- **Uso**: Base automática para research executions do experimento

---

## 12. FRONTEND - PÁGINAS PRINCIPAIS

### 12.1 Index (Home - Experiment List)
- **Arquivo**: `frontend/src/pages/Index.tsx`
- **URL**: `/`
- **Funcionalidades**:
  - Grid de experiment cards com:
    - Nome, hipótese (truncada)
    - Tags (colored badges)
    - Interview count, analysis status
    - Created at timestamp
  - Search por nome/hipótese (live)
  - Filter por tags (dropdown)
  - Sort por created_at ou name (asc/desc)
  - Dialog para criar novo experimento
  - Empty state com onboarding
- **Componentes**:
  - `ExperimentCard` (card individual)
  - `ExperimentForm` (dialog de criação)
  - `TagFilter` (filtro)

### 12.2 ExperimentDetail
- **Arquivo**: `frontend/src/pages/ExperimentDetail.tsx`
- **URL**: `/experiments/{experiment_id}`
- **Tabs**:

  #### Tab: Overview
  - Scorecard sliders (read-only - 4 dimensões)
  - Status badges
  - Timestamps (created, updated)
  - Linked synth group
  - Actions: Edit, Delete, Tag Management

  #### Tab: Analysis
  - **6 Fases Iterativas** (workflow guiado):
    1. **PhaseOverview**:
       - Outcome distribution chart
       - Try vs success scatter
       - KPIs principais
    2. **PhaseLocation**:
       - Failure heatmap
       - Region analysis
       - Where problems occur
    3. **PhaseSegmentation**:
       - K-means clustering
       - Hierarchical clustering
       - PCA scatter
       - Radar charts por cluster
    4. **PhaseEdgeCases**:
       - Extreme cases table
       - Outlier analysis
       - Top/bottom performers
    5. **PhaseInsights**:
       - AI-generated insights por chart
       - Key findings consolidados
    6. **PhaseSummary**:
       - Executive summary
       - Recommendations
       - Export results
  - Actions: Run Analysis, Generate Insights

  #### Tab: Interviews
  - Lista de research executions com:
    - Topic name, status
    - Synth count, completed count
    - Turns, has summary flag
    - Link para InterviewDetail
  - Actions: Create Interview, Auto Interview (extreme cases)

  #### Tab: Explorations
  - Lista de explorations com:
    - Goal metric e target
    - Status, progress
    - Best success rate
    - Node count
    - Link para ExplorationDetail
  - Actions: Create Exploration

  #### Tab: Materials
  - Upload de imagens/vídeos/documentos
  - Galeria com thumbnails
  - Drag-and-drop para reordenar
  - Auto-descrição via Vision API
  - Actions: Upload, Describe, Delete

  #### Tab: Documents
  - Research Summary (de interviews)
  - PRFAQ (de interviews)
  - Exploration Summary
  - Exploration PRFAQ
  - Executive Summary (de analysis)
  - Actions: Generate, View, Delete

- **Componentes**:
  - `PhaseOverview.tsx`, `PhaseLocation.tsx`, etc. (fases de análise)
  - `DocumentsList.tsx` (lista de documentos)
  - `MaterialGallery.tsx` (galeria de materiais)
  - `InterviewsList.tsx` (lista de entrevistas)

### 12.3 InterviewDetail
- **Arquivo**: `frontend/src/pages/InterviewDetail.tsx`
- **URL**: `/research/{exec_id}`
- **Seções**:

  #### Live Interview Grid
  - Grid responsivo (3 colunas em desktop)
  - Card por synth com:
    - Avatar, nome, arquétipo
    - Status badge (pending/running/generating/completed/failed)
    - Turn count atual
    - Últimas 2 mensagens
  - Real-time updates via SSE (`/research/{exec_id}/stream`)
  - Auto-scroll to active interviews

  #### Transcript Viewer
  - Seleção de synth específico
  - Thread completa de perguntas/respostas
  - Timestamps por mensagem
  - Syntax highlighting para melhor leitura
  - Download transcript

  #### Documents Section
  - Summary card (se disponível)
  - PRFAQ card (se disponível)
  - Actions: Generate, View

- **Componentes**:
  - `LiveInterviewGrid` (monitoramento real-time)
  - `TranscriptViewer` (visualizador de transcrição)
  - `InterviewProgress` (barra de progresso)

### 12.4 ExplorationDetail
- **Arquivo**: `frontend/src/pages/ExplorationDetail.tsx`
- **URL**: `/explorations/{exploration_id}`
- **Seções**:

  #### Exploration Tree Flow
  - Visualização com React Flow
  - Nós representam cenários testados
  - Edges mostram ações aplicadas
  - Color coding:
    - Verde: winning path
    - Amarelo: explorado mas não vencedor
    - Cinza: não explorado
  - Layout hierárquico (top-down)
  - Zoom, pan, fit view

  #### Node Details Panel
  - Mostra detalhes do nó selecionado:
    - Action applied (ação que levou a este nó)
    - Metrics (success_rate, try_rate, etc.)
    - Parent node
    - Children nodes
  - Actions: Expand node (continuar exploração daqui)

  #### Exploration Progress
  - Status (pending/running/completed)
  - Goal metric e target
  - Best success rate encontrada
  - Node count (cenários testados)
  - Depth atual vs max_depth

  #### Documents Section
  - Exploration Summary card
  - Exploration PRFAQ card
  - Actions: Generate, View

- **Componentes**:
  - `ExplorationTreeFlow` (React Flow wrapper)
  - `NodeDetailsPanel` (detalhes do nó)
  - `ExplorationProgress` (progress bar)

### 12.5 Synths (Catalog + Groups)
- **Arquivo**: `frontend/src/pages/Synths.tsx`
- **URL**: `/synths`
- **Layout**: 2 painéis (Split View)

  #### Synth List Panel (esquerda)
  - Grid de synth cards com:
    - Avatar thumbnail
    - Nome, arquétipo
    - Descrição curta
    - Demographic highlights (idade, profissão)
  - Filtros:
    - Por grupo (dropdown)
    - Por arquétipo
    - Search por nome
  - Paginação
  - Click para ver detalhes

  #### Synth Groups Panel (direita)
  - Lista de grupos disponíveis
  - Card por grupo com:
    - Nome do grupo
    - Description
    - Synth count
    - Created at
  - Actions:
    - Create new group (modal)
    - View synths in group
    - Edit group
    - Delete group

  #### Synth Group Detail View
  - Quando grupo selecionado, mostra:
    - Lista de synths do grupo
    - Distribution chart (demografia)
    - Actions: Add/Remove synths

  #### Create Synth Group Modal
  - Name (required)
  - Description (optional)
  - Synth selection (multi-select)
  - Config (JSONB - avançado)

- **Componentes**:
  - `SynthList.tsx` (lista de synths)
  - `SynthGroupList.tsx` (lista de grupos)
  - `SynthGroupDetailView.tsx` (detalhes do grupo)
  - `CreateSynthGroupModal.tsx` (modal de criação)

---

## 13. COMPONENTES DE DOMÍNIO (Entidades de Negócio)

### Domain Entities (em `src/synth_lab/domain/entities/`)

| Entidade | Arquivo | Propósito |
|----------|---------|-----------|
| **Experiment** | `experiment.py` | Experimento principal + ScorecardData + ScorecardDimension |
| **SynthGroup** | `synth_group.py` | Agrupamento de synths (padrão + custom) |
| **Exploration** | `exploration.py` | Sessão de exploração LLM + Goal |
| **ScenarioNode** | `scenario_node.py` | Nó na árvore de exploração |
| **ActionProposal** | `action_proposal.py` | Ação proposta pelo LLM para melhorar cenário |
| **AnalysisRun** | `analysis_run.py` | Resultado de simulação/análise |
| **AnalysisCache** | `analysis_cache.py` | Cache de análises computadas (performance) |
| **SynthOutcome** | `synth_outcome.py` | Resultado de synth específico em simulação |
| **ClusterResult** | `cluster_result.py` | Resultado de clustering (kmeans, hierarchical) |
| **OutlierResult** | `outlier_result.py` | Casos extremos identificados |
| **ChartData** | `chart_data.py` | Dados para diferentes tipos de charts |
| **ChartInsight** | `chart_insight.py` | Insight narrativo gerado por LLM |
| **ExecutiveSummary** | `executive_summary.py` | Sumário executivo da análise |
| **ExplainabilityResult** | `explainability.py` | Resultados de SHAP, PDP, feature importance |
| **ExperimentDocument** | `experiment_document.py` | Summary, PRFAQ, Executive Summary |
| **ExperimentMaterial** | `experiment_material.py` | Imagens, vídeos, documentos uploadados |
| **Tag** | `tag.py` | Tag para organização de experimentos |
| **SimulationRun** | `simulation_run.py` | Execução de simulação |
| **SimulationContext** | `simulation_context.py` | Contexto de simulação |
| **SimulationAttributes** | `simulation_attributes.py` | Atributos simulados |

---

## 14. OBSERVABILIDADE & INFRAESTRUTURA

### 14.1 Tracing com Phoenix/OpenTelemetry
- **Componente**: `infrastructure/phoenix_tracing.py`
- **Framework**: Arize Phoenix (observabilidade para LLMs)
- **Coverage**: Todas as LLM calls envolvidas em traces com `_tracer.start_as_current_span()`
- **Collector**: Phoenix Collector (configurável via `PHOENIX_COLLECTOR_ENDPOINT`)
- **Spans**: Incluem:
  - Prompts enviados
  - Respostas recebidas
  - Latência
  - Tokens consumidos
  - Atributos OpenInference
- **Dashboard**: Phoenix UI para visualização de traces

### 14.2 Logging
- **Framework**: loguru
- **Configuração**: Via `infrastructure/config.py`
- **Níveis**: DEBUG, INFO, WARNING, ERROR
- **Arquivo**: `/tmp/synth-lab-backend.log` (desenvolvimento)
- **Formato**: Timestamp + Level + Module + Message

### 14.3 Message Broker
- **Propósito**: Real-time updates para SSE streams
- **Implementação**: `services/message_broker.py` (in-memory queues)
- **Uso**:
  - Research executions (interview updates)
  - Exploration updates
  - Long-running tasks
- **Padrão**: Pub/Sub com topics por exec_id/exploration_id

---

## 15. AUTENTICAÇÃO & CONFIGURAÇÃO

### 15.1 Variáveis de Ambiente
```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost/synthlab
DATABASE_TEST_URL=postgresql://user:pass@localhost/synthlab_test

# AI
OPENAI_API_KEY=sk-...

# Observability
PHOENIX_COLLECTOR_ENDPOINT=http://localhost:6006
PHOENIX_ENABLED=true  # ou false para desabilitar

# Storage (S3-compatible)
S3_ENDPOINT_URL=...
S3_ACCESS_KEY_ID=...
S3_SECRET_ACCESS_KEY=...
S3_BUCKET_NAME=...
S3_REGION=...

# Application
ENV=development  # ou production
DEBUG=true  # ou false
```

### 15.2 CORS
- **Configuração**: `api/main.py`
- **Origins**: `["*"]` em desenvolvimento (configurável para produção)
- **Methods**: Todos
- **Headers**: Todos

### 15.3 Health Check
- **Endpoint**: `GET /health` (suporta GET e HEAD)
- **Resposta**:
  ```json
  {
    "status": "healthy",
    "service": "synth-lab-api",
    "version": "1.0.0"
  }
  ```
- **Uso**: Load balancers, monitoring, CI/CD

---

## 16. PADRÕES E CONVENÇÕES

### 16.1 Paginação Padrão
- **Parâmetros**:
  - `limit` (1-200, padrão: 50)
  - `offset` (padrão: 0)
  - `sort_by` (campo para ordenação)
  - `sort_order` (asc/desc, padrão: desc)
- **Resposta**:
  ```json
  {
    "data": [...],
    "pagination": {
      "total": 100,
      "limit": 50,
      "offset": 0,
      "has_next": true
    }
  }
  ```

### 16.2 IDs Gerados
- **Experiments**: `exp_[a-f0-9]{8}` (e.g., `exp_a1b2c3d4`)
- **Explorations**: `expl_[a-f0-9]{8}` (e.g., `expl_f3e4d5c6`)
- **Synth Groups**: `grp_[a-f0-9]{8}` (e.g., `grp_b7c8d9e0`)
- **Grupo Padrão**: `grp_00000001` (todos os synths)
- **Formato**: Prefixo + 8 caracteres hexadecimais

### 16.3 Real-time Streaming (SSE)
- **Research**: `/research/{exec_id}/stream`
- **Chat**: `/synths/{synth_id}/chat/stream`
- **Headers**:
  ```
  Content-Type: text/event-stream
  Cache-Control: no-cache
  Connection: keep-alive
  ```
- **Eventos**:
  - `message`: Dados incrementais
  - `interview_completed`: Interview finalizada
  - `transcription_completed`: Todas transcriptions prontas
  - `execution_completed`: Execução completa

### 16.4 LLM Tracing
- **Padrão**: Todas as chamadas OpenAI envolvidas em traces
- **Atributos**: OpenInference standard (prompts, responses, tokens)
- **Serviços com prompts**:
  - `scorecard_estimator.py`
  - `research_summary_generator_service.py`
  - `research_prfaq_generator_service.py`
  - `insight_service.py`
  - `executive_summary_service.py`
  - `exploration_summary_generator_service.py`
  - `interview_guide_generator_service.py`
- **Wrapper**: `_tracer.start_as_current_span()` em todos os LLM calls

---

## 17. RESUMO DE MÓDULOS PRINCIPAIS

| Módulo | Responsabilidade | Arquivos Principais |
|--------|------------------|---------------------|
| **Synths** | Personas sintéticas + listagem + search | `api/routers/synths.py`, `services/synth_service.py` |
| **Experiments** | Hub central de feature testing | `api/routers/experiments.py`, `services/experiment_service.py` |
| **Research** | Entrevistas qualitativas com synths | `api/routers/research.py`, `services/research_agentic/runner.py` |
| **Analysis** | Simulação e quantificação | `api/routers/analysis.py`, `services/simulation/engine.py` |
| **Exploration** | Otimização LLM de cenários | `api/routers/exploration.py`, `services/exploration/` |
| **Documents** | Geração de sumários e PRFAQ | `api/routers/documents.py`, `services/research_summary_generator_service.py` |
| **Materials** | Upload e gerenciamento de mídia | `api/routers/materials.py`, `services/material_service.py` |
| **Insights** | IA para interpretação de resultados | `api/routers/insights.py`, `services/insight_service.py` |
| **Tags** | Organização de experimentos | `api/routers/tags.py`, `repositories/tag_repository.py` |
| **Chat** | Conversas pós-entrevista com synths | `api/routers/chat.py`, `services/chat/service.py` |

---

## 18. FLUXO TÍPICO DE USO

### Workflow Completo: Teste de Feature

1. **Criar Experimento**
   - POST `/experiments` com name, hypothesis, description
   - Interview guide é gerado automaticamente em background

2. **Estimar Scorecard (opcional)**
   - POST `/experiments/{id}/estimate-scorecard`
   - Ajustar manualmente via PUT `/experiments/{id}/scorecard`

3. **Upload de Materiais (opcional)**
   - POST `/experiments/{id}/materials` (imagens, vídeos, docs)
   - POST `/experiments/{id}/materials/{id}/describe` (auto-descrição)

4. **Executar Análise Quantitativa**
   - POST `/experiments/{id}/analysis/run`
   - GET `/experiments/{id}/analysis` (polling status)
   - Navegar pelas 6 fases de análise no frontend

5. **Gerar Insights**
   - POST `/experiments/{id}/analysis/insights/{chart_type}` (por chart)
   - GET `/experiments/{id}/analysis/insights` (todos os insights)

6. **Criar Entrevista Qualitativa**
   - POST `/experiments/{id}/interviews/auto` (casos extremos)
   - OU POST `/experiments/{id}/interviews` (custom)
   - GET `/research/{exec_id}/stream` (monitorar live)

7. **Gerar Documentos**
   - POST `/research/{exec_id}/documents/summary/generate`
   - POST `/research/{exec_id}/documents/prfaq/generate`
   - GET `/experiments/{id}/analysis/executive-summary`

8. **Exploração Automatizada (opcional)**
   - POST `/explorations` com goal metric
   - GET `/explorations/{id}/tree` (visualizar cenários)
   - POST `/explorations/{id}/documents/summary/generate`

9. **Decisão**
   - Revisar todos os documentos gerados
   - Analisar insights e recomendações
   - Decidir: prosseguir, iterar, ou descartar feature

---

## APÊNDICE A: Comandos de Desenvolvimento

### Backend
```bash
# Iniciar servidor
uv run uvicorn synth_lab.api.main:app --reload

# Rodar testes
pytest tests/

# Rodar linter
ruff check . && ruff format .

# Migrations (Alembic)
alembic revision --autogenerate -m "description"
alembic upgrade head
```

### Frontend
```bash
cd frontend

# Iniciar dev server
npm run dev

# Build para produção
npm run build

# Linter
npm run lint

# Type check
npm run type-check
```

### Observabilidade
```bash
# Phoenix (Arize)
# Dashboard disponível em http://localhost:6006
# (configurar PHOENIX_COLLECTOR_ENDPOINT no .env)
```

---

## APÊNDICE B: Documentação Adicional

- **Arquitetura Backend**: `/docs/arquitetura.md`
- **Arquitetura Frontend**: `/docs/arquitetura_front.md`
- **Template Scorecard**: `/docs/template_feat_scorecard.md`
- **CHANGELOG**: `/docs/CHANGELOG.md`

---

**Fim da Documentação de Funcionalidades**
