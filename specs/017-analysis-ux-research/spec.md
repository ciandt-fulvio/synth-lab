# Feature Specification: Sistema de Análise para UX Research
**Feature Branch**: `017-analysis-ux-research`
**Created**: 2025-12-26
**Status**: Draft
**Input**: User description: "Sistema de Análise para UX Research com visualizações de dados, clustering de personas, detecção de outliers e geração de insights via LLM"
**Dependency**: 016-feature-impact-simulation
---
## Contexto
Este sistema fornece ferramentas de análise quantitativa para UX Researchers que executaram simulações de feature impact. A jornada do researcher segue 6 fases: Visão Geral → Localização → Segmentação → Casos Especiais → Explicação Profunda → Insights LLM.
---
## User Scenarios & Testing *(mandatory)*
### User Story 1 - Visão Geral da Simulação (Priority: P1)
O UX Researcher quer ter uma visão rápida e abrangente dos resultados da simulação para entender "o que aconteceu" antes de aprofundar a análise.
**Why this priority**: Esta é a primeira etapa da jornada de análise. Sem uma visão geral clara, o researcher não consegue priorizar onde investigar mais profundamente. É o ponto de entrada obrigatório para todas as outras análises.
**Acceptance Scenarios**:
1. **Given** uma simulação finalizada com resultados de synths, **When** o researcher solicita o gráfico Try vs Success, **Then** o sistema retorna todos os synths posicionados nos 4 quadrantes (low_value, usability_issue, discovery_issue, ok) com contagens agregadas.
2. **Given** uma simulação com 500 synths, **When** o researcher solicita o Outcome Distribution, **Then** o sistema retorna a proporção de did_not_try, failed e success para cada synth, ordenados conforme parâmetro.
---
### User Story 2 - Localização de Problemas (Priority: P1)
O UX Researcher precisa identificar "onde exatamente a experiência quebra" - quais combinações de atributos de usuário resultam em maior taxa de falha.
**Why this priority**: Localizar problemas é essencial para direcionar esforços de melhoria do produto. Sem esta análise, o researcher não consegue identificar quais segmentos de usuários precisam de atenção prioritária.
**Independent Test**: Pode ser testado verificando se o heatmap de falhas identifica corretamente células críticas com base em combinações de atributos latentes.
**Acceptance Scenarios**:
1. **Given** uma simulação com synths contendo atributos latentes (capability, trust, etc.), **When** o researcher solicita o Failure Heatmap com capability_mean x trust_mean, **Then** o sistema retorna uma matriz 5x5 (bins configuráveis) com taxa de falha média por célula e identificação de células críticas.
2. **Given** resultados de region_analysis existentes, **When** o researcher solicita o Box Plot por Região, **Then** o sistema retorna estatísticas de quartis, outliers e baseline para cada região identificada.
3. **Given** atributos latentes e outcomes de synths, **When** o researcher solicita o Scatter de correlação (trust vs success), **Then** o sistema retorna pontos, coeficiente de Pearson, p-value, R² e linha de tendência.
4. **Given** uma análise de sensibilidade já executada, **When** o researcher solicita o Tornado Diagram, **Then** o sistema retorna barras ordenadas por sensitivity_index mostrando impacto positivo e negativo de cada dimensão do scorecard.
---
### User Story 3 - Segmentação de Personas (Priority: P2)
O UX Researcher quer agrupar synths em clusters para identificar "quem são esses usuários" - personas naturais baseadas em atributos e comportamentos.
**Why this priority**: A segmentação permite ao researcher comunicar insights de forma mais efetiva para stakeholders, usando personas ao invés de dados granulares. É um passo de abstração que facilita a tomada de decisão.
**Independent Test**: Pode ser testado executando K-Means com diferentes valores de K e verificando se os clusters gerados têm perfis distintivos e labels sugeridos.
**Acceptance Scenarios**:
1. **Given** synths com atributos latentes normalizados, **When** o researcher solicita clustering K-Means com K=4, **Then** o sistema retorna 4 clusters com centroid, size, high/low traits, avg_success_rate e suggested_label (ex: "Power Users", "Strugglers").
2. **Given** uma simulação, **When** o researcher solicita dados do Elbow Method, **Then** o sistema retorna inertia e silhouette_score para K de 2 a 10, permitindo escolher o K ideal.
3. **Given** clustering executado, **When** o researcher solicita Radar Chart de comparação, **Then** o sistema retorna perfil multidimensional de cada cluster com baseline para referência.
4. **Given** synths com atributos, **When** o researcher solicita Hierarchical Clustering, **Then** o sistema retorna linkage matrix e pontos de corte sugeridos baseados em gaps de distância.
---
### User Story 4 - Identificação de Casos Especiais (Priority: P2)
O UX Researcher quer identificar "quem devemos entrevistar primeiro" - synths extremos ou anômalos que podem revelar insights qualitativos únicos.
**Why this priority**: Casos especiais são candidatos prioritários para entrevistas qualitativas. Identificá-los automaticamente economiza tempo e aumenta a probabilidade de descobrir insights valiosos.
**Independent Test**: Pode ser testado verificando se o sistema identifica corretamente os 10 synths com maior taxa de falha e os outliers detectados pelo Isolation Forest.
**Acceptance Scenarios**:
1. **Given** uma simulação com outcomes variados, **When** o researcher solicita Extreme Cases Table, **Then** o sistema retorna top N synths nas categorias: worst_failures, best_successes, most_unstable e unexpected, com profile_summary e interview_questions sugeridas.
2. **Given** features de synths (atributos + outcomes), **When** o researcher solicita detecção de outliers via Isolation Forest, **Then** o sistema retorna synths com anomaly_score, classificação de tipo (unexpected_failure, unexpected_success, atypical_profile) e desvio da média.
---
### User Story 5 - Explicação Profunda (Priority: P3)
O UX Researcher quer entender "por que esse synth específico falhou" com explicações baseadas em contribuições de cada atributo para o resultado.
**Why this priority**: Explicações profundas são valiosas para pesquisas avançadas, mas dependem de modelos treinados e são computacionalmente mais custosas. É uma análise sob demanda para casos específicos.
**Independent Test**: Pode ser testado verificando se SHAP values explicam corretamente a diferença entre a predição baseline e a predição para um synth específico.
**Acceptance Scenarios**:
1. **Given** um modelo preditivo treinado com dados da simulação, **When** o researcher solicita SHAP explanation para um synth específico, **Then** o sistema retorna contribuição de cada feature (positive/negative), base_value, predicted_value e texto explicativo.
2. **Given** um modelo treinado, **When** o researcher solicita SHAP summary, **Then** o sistema retorna feature_importance global ordenada e top positive/negative contributors.
3. **Given** um modelo treinado, **When** o researcher solicita Partial Dependence Plot para uma feature, **Then** o sistema retorna curva de efeito marginal, tipo de efeito (monotônico, não-linear, flat) e strength.
---
### User Story 6 - Insights Gerados por LLM (Priority: P3)
O UX Researcher quer legendas curtas e insights explicativos gerados automaticamente para cada gráfico, facilitando a comunicação com stakeholders não-técnicos.
**Why this priority**: LLM insights agregam valor comunicativo mas não são essenciais para a análise. São um "nice-to-have" que melhora a experiência mas pode ser implementado após as funcionalidades core.
**Independent Test**: Pode ser testado verificando se captions geradas são factuais, curtas (≤20 tokens) e focadas no insight mais importante do gráfico.
**Acceptance Scenarios**:
1. **Given** dados de um gráfico Try vs Success, **When** o researcher solicita caption, **Then** o sistema retorna legenda factual de no máximo 20 tokens destacando a métrica mais importante (ex: "42% dos synths têm problema de usabilidade").
2. **Given** dados de um gráfico e sua caption, **When** o researcher solicita insight completo, **Then** o sistema retorna explicação de até 200 tokens com 2-3 evidências numéricas e sugestão de ação quando relevante.
---
### Edge Cases
- **Simulação sem resultados**: Sistema retorna erro claro indicando que a simulação precisa ser executada primeiro.
- **Poucos synths para clustering**: Se N < 10 synths, sistema sugere usar análise individual ao invés de clustering.
- **Sensitivity analysis não executada**: Tornado Diagram retorna erro indicando que sensitivity analysis é pré-requisito.
- **Modelo SHAP não treinado**: Sistema treina modelo automaticamente na primeira requisição de SHAP, informando o usuário sobre tempo de processamento.
- **Clustering com K > N synths**: Sistema ajusta K automaticamente e notifica o usuário.
- **LLM indisponível**: Caption/Insight endpoints retornam erro gracioso com sugestão de usar dados brutos.
---
## Requirements *(mandatory)*
### Functional Requirements
#### FASE 1 - Visão Geral
- **FR-001**: Sistema DEVE fornecer gráfico Try vs Success com todos os synths posicionados por attempt_rate (X) e success_rate (Y), classificados em 4 quadrantes configuráveis.
- **FR-002**: Sistema DEVE fornecer Outcome Distribution mostrando proporção de did_not_try, failed e success por synth, com suporte a ordenação e limite de resultados.
#### FASE 2 - Localização
- **FR-004**: Sistema DEVE fornecer Failure Heatmap 2D com eixos configuráveis (qualquer par de atributos latentes), número de bins ajustável e identificação de células críticas.
- **FR-005**: Sistema DEVE fornecer Box Plot por Região usando dados de region_analysis existente, incluindo baseline para comparação.
- **FR-006**: Sistema DEVE fornecer Scatter de correlação entre qualquer atributo e outcome, com cálculo de Pearson, p-value, R² e linha de tendência.
- **FR-007**: Sistema DEVE fornecer Tornado Diagram usando dados de sensitivity_result, mostrando impacto de cada dimensão do scorecard.
#### FASE 3 - Segmentação
- **FR-008**: Sistema DEVE executar K-Means clustering com normalização, retornando clusters com centroid, size, high/low traits e suggested_label.
- **FR-009**: Sistema DEVE calcular silhouette_score e inertia para diferentes valores de K (Elbow Method).
- **FR-010**: Sistema DEVE gerar Radar Chart para cada cluster e permitir comparação sobreposta.
- **FR-011**: Sistema DEVE executar Hierarchical Clustering e retornar linkage matrix com pontos de corte sugeridos.
- **FR-012**: Sistema DEVE permitir "cortar" dendrograma em N clusters específico.
#### FASE 4 - Casos Especiais
- **FR-013**: Sistema DEVE identificar extreme cases nas categorias: worst_failures, best_successes, most_unstable e unexpected.
- **FR-014**: Sistema DEVE incluir profile_summary e interview_questions para cada extreme case.
- **FR-015**: Sistema DEVE executar Isolation Forest para detecção de outliers com contamination configurável.
- **FR-016**: Sistema DEVE classificar outliers por tipo (unexpected_failure, unexpected_success, atypical_profile).
#### FASE 5 - Explicabilidade
- **FR-017**: Sistema DEVE treinar modelo preditivo internamente para cálculo de SHAP values.
- **FR-018**: Sistema DEVE calcular SHAP explanation para synth específico com contribuições ordenadas por magnitude.
- **FR-019**: Sistema DEVE gerar texto explicativo legível a partir de SHAP values.
- **FR-020**: Sistema DEVE calcular Partial Dependence Plot para qualquer feature, classificando tipo de efeito.
- **FR-021**: Sistema DEVE permitir comparação de PDP entre múltiplas features.
#### FASE 6 - Insights LLM
- **FR-022**: Sistema DEVE gerar caption (≤20 tokens) para qualquer tipo de gráfico, factual e com números.
- **FR-023**: Sistema DEVE gerar insight (≤200 tokens) com evidências numéricas e sugestão de ação.
- **FR-024**: Sistema DEVE cachear resultados de LLM para evitar re-chamadas desnecessárias.
---
### Key Entities
- **TryVsSuccessChart**: Representa scatter plot com synths nos 4 quadrantes (attempt_rate x success_rate). Contém pontos, contagens por quadrante e thresholds configuráveis.
- **FailureHeatmapChart**: Representa matriz 2D com taxa de falha por combinação de atributos. Contém células com failure_rate, synth_count e identificação de células críticas.
- **ClusterResult**: Representa resultado de clustering (K-Means ou Hierarchical). Contém profiles de clusters com centroid, size, traits distintivas e suggested_label.
- **OutlierResult**: Representa synths detectados como anômalos pelo Isolation Forest. Contém anomaly_score, tipo de outlier e comparação com "normais".
- **ShapExplanation**: Representa explicação de predição para um synth. Contém contribuições de cada feature, base_value, predicted_value e texto explicativo.
- **PDPResult**: Representa efeito marginal de uma feature no outcome. Contém pontos da curva, tipo de efeito (monotônico, não-linear, flat) e strength.
- **ChartCaption**: Representa legenda curta gerada por LLM. Contém caption (≤20 tokens), key_metric e confidence.
- **ChartInsight**: Representa insight completo gerado por LLM. Contém explanation (≤200 tokens), evidências e recomendação.
---
## Assumptions
1. **Dependência de simulação**: Todas as análises requerem uma simulação previamente executada com synth_outcomes populados.
2. **Dados normalizados**: Atributos latentes (capability_mean, trust_mean, etc.) estão sempre no intervalo [0, 1].
3. **Análises opcionais já executadas**: Tornado Diagram assume que sensitivity_analysis já foi executada; Box Plot por Região assume que region_analysis existe.
4. **LLM disponível**: Endpoints de caption/insight assumem acesso a modelo LLM configurado no sistema.
5. **Volume de dados**: Clustering assume ao menos 10 synths; análises são otimizadas para até 10.000 synths.
6. **Threshold padrão**: Quadrantes do Try vs Success usam threshold 0.5 por padrão; heatmap usa 5 bins por padrão.
---
## Success Criteria *(mandatory)*
### Measurable Outcomes
- **SC-001**: UX Researcher obtém visão geral completa (3 gráficos da Fase 1) em menos de 5 minutos após simulação.
- **SC-002**: Researcher identifica as 3 principais zonas de problema usando Failure Heatmap em menos de 2 minutos.
- **SC-003**: Sistema gera clusters com silhouette_score ≥ 0.3, indicando separação significativa entre grupos.
- **SC-004**: 90% dos extreme cases identificados são considerados "relevantes para entrevista" por researchers.
- **SC-005**: SHAP explanations são gerados em menos de 30 segundos para synth individual.
- **SC-006**: Captions geradas são factuais (0 erros numéricos) e respeitam limite de 20 tokens.
- **SC-007**: 80% dos insights gerados recebem avaliação "útil" ou "muito útil" por researchers.
- **SC-008**: Researcher completa jornada completa de análise (6 fases) em menos de 2 horas.
