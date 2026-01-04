# Synth-Lab: Acelerando Experimentação de Produto através de Pesquisa Sintética

## 1. Introduction

### O Paradoxo da Inovação Rápida

Vivemos um momento único: a IA reduziu o tempo de criação de POCs de meses para semanas. Startups podem testar 10 ideias no tempo que antes testavam uma. Porém, identificamos um paradoxo crítico: **embora possamos construir mais rápido, ainda demoramos semanas para validar se devemos construir**.

O processo tradicional de pesquisa com usuários — recrutamento, agendamento, entrevistas, análise — consome 2-4 semanas e custa R$ 20-80 mil por ciclo. Para análises quantitativas, amostras de 20-50 usuários oferecem poder estatístico limitado. **Resultado: 60-70% das features lançadas têm baixa adoção porque foram baseadas em hipóteses não validadas**.

### A Oportunidade: IA para Acelerar Investigação

Se a IA pode acelerar construção, **por que não pode acelerar investigação?**

Synth-Lab é uma plataforma brasileira de pesquisa sintética que permite equipes de produto executarem:
- **Entrevistas qualitativas** com 10 personas sintéticas em 20 minutos (vs 2 semanas recrutando usuários reais)
- **Simulações quantitativas** com 10.000 execuções probabilísticas em 2 minutos (vs 4 semanas para atingir significância estatística)
- **Explorações automatizadas** de cenários de produto usando IA para propor e simular melhorias

**Não buscamos substituir pesquisa real**, mas sim **reduzir 80% do tempo de preparação** e **direcionar melhor onde investir investigações profundas** com usuários.

### Tese de Mercado

**Mercado endereçável**: 2.000+ startups brasileiras Série A-B com equipes de produto (5-15 pessoas), que gastam coletivamente R$ 120-200 milhões/ano em research. Cada equipe executa 4-8 ciclos de validação/ano.

**Proposta de valor**: Reduzir custo de experimentação de R$ 20-80 mil → R$ 200, e tempo de 2-4 semanas → 4 horas. Isso permite equipes executarem **10-15x mais experimentos** com o mesmo budget, aumentando drasticamente a chance de encontrar product-market fit.

**Diferencial competitivo**:
1. **Dados brasileiros (IBGE)** — Única plataforma com personas baseadas em Censo 2022 e PNAD, capturando diversidade regional, desigualdade e barreiras digitais do Brasil
2. **Rigor científico** — Monte Carlo com 10K execuções + análises SHAP/PDP, não "pesquisas rápidas" de 20 respostas
3. **Open-source** — Transparência total de prompts e modelos probabilísticos gera confiança

---

## 2. Goals: Métricas de Sucesso

### Métricas North Star

| Métrica | Definição | Meta 2026 Q2 | Baseline Atual |
|---------|-----------|--------------|----------------|
| **Time-to-Insight** | Tempo da hipótese até insights acionáveis | **< 4 horas** | 2-4 semanas (tradicional) |
| **Cost per Experiment** | Custo total de um ciclo de validação | **< R$ 200** | R$ 20-80 mil (tradicional) |
| **Iteration Velocity** | Experimentos executados por equipe/trimestre | **> 15** | 1-2 (tradicional) |

### Métricas de Produto

| Métrica | Meta 2026 Q2 |
|---------|--------------|
| **Synth Diversity Score** (Shannon Entropy) | > 4.5 bits |
| **Research Completion Rate** (% entrevistas sem falhas) | > 95% |
| **Simulation Accuracy** (correlação com outcomes reais) | > 0.70 (Pearson r) |
| **Exploration Success Rate** (% que melhora baseline) | > 60% |

### Métricas de Negócio

| Métrica | Meta 2026 Q4 |
|---------|--------------|
| **Active Teams** (≥ 1 experimento/mês) | 10 equipes |
| **Experiments Executed** | 500 experimentos |
| **Features De-risked** (validadas antes de desenvolvimento) | 150 features |
| **Roadmap Impact** (% decisões influenciadas) | > 40% |

**Critério de Sucesso Qualitativo**: PMs usam Synth-Lab **antes** de escrever specs; executivos citam simulações em decisões de go/no-go.

---

## 3. Tenets: Princípios de Negócio

### 1. Simulação Direciona, Não Substitui
**"Synths aceleram investigação, mas decisões finais exigem validação com humanos reais."**

- Tratamos simulações como sinalizadores de risco, não verdades absolutas
- Sempre recomendamos validação com usuários reais antes de grandes investimentos
- Transparência sobre limitações: synths não capturam toda complexidade humana
- **Trade-off aceito**: Direcionar bem 80% das investigações > 100% de precisão em 20%

### 2. Dados Brasileiros, Personas Brasileiras
**"A diversidade do Brasil não cabe em modelos genéricos de outros países."**

- Todas distribuições demográficas baseadas em IBGE (Censo 2022, PNAD Contínua)
- Arquétipos refletem realidades regionais: desigualdade, diversidade cultural, barreiras digitais
- Viés explícito: priorizamos representatividade brasileira sobre generalizações globais
- **Trade-off aceito**: Menor aplicabilidade internacional em favor de precisão local

### 3. Velocidade com Rigor
**"Insights em horas, mas com metodologia científica."**

- Monte Carlo com 1.000-10.000 execuções (não 10-20 como em testes A/B prematuros)
- Análises estatísticas completas: SHAP, PDP, clustering, outlier detection
- Rastreabilidade: todo resultado rastreável até prompts, seeds, parâmetros
- **Trade-off aceito**: Latência de minutos para garantir robustez estatística

### 4. IA Aumenta, Não Automatiza Decisões
**"LLMs propõem, humanos decidem."**

- Explorações oferecem múltiplas alternativas (beam search), não uma única resposta
- Insights de charts são hipóteses para investigação, não conclusões definitivas
- PMs mantêm controle total: podem rejeitar, ajustar ou refinar qualquer sugestão
- **Trade-off aceito**: Mais interação humana necessária, mas melhor alinhamento estratégico

### 5. Código Aberto, Transparência Total
**"Confiança vem de entender como resultados são gerados."**

- Prompts de LLM visíveis no código-fonte
- Modelos probabilísticos documentados e auditáveis
- Rastreamento OpenTelemetry de todas chamadas LLM (Arize Phoenix)
- **Trade-off aceito**: Possibilidade de cópia por concorrentes, mas ganho em confiabilidade

---

## 4. State of the Business: Situação Atual

### 4.1 Componentes Core (Produção)

| Componente | Capacidade | Propósito |
|------------|------------|-----------|
| **Geração de Synths** | 1.800 personas/segundo, 80+ atributos IBGE, avatares visuais | População sintética representativa do Brasil com demografia, psicografia, deficiências |
| **Entrevistas Qualitativas** | Sistema de 2 agentes LLM (entrevistador + synth), streaming em tempo real | Simular entrevistas de UX Research, gerar transcritos, resumos e PR-FAQs |
| **Simulação Quantitativa** | Monte Carlo 10.000 execuções em ~2min, cache de resultados | Prever outcomes probabilísticos (success/failure/did-not-try) de features |
| **Análise Estatística** | SHAP, PDP, clustering, outlier detection, 12 tipos de charts | Explicar drivers de sucesso/falha, identificar perfis de usuários, detectar anomalias |
| **Exploração de Cenários** | Beam search com LLM, filtragem Pareto, até 5 níveis | IA propõe melhorias de produto, simula cada proposta, identifica caminho vencedor |
| **Gestão de Documentos** | Summaries, PR-FAQs, executive reports, export PDF | Persistir insights, compartilhar resultados, integrar com workflow de produto |
| **Observabilidade** | Phoenix/OpenTelemetry tracing de todas chamadas LLM | Rastrear custos, latências, qualidade de outputs de IA |

### 4.2 Casos de Uso Validados (Internos)

Executamos **8 experimentos internos** para validar a plataforma antes de lançamento:

| Experimento | Insight Principal | Tempo | Outcome |
|-------------|-------------------|-------|---------|
| **Onboarding Gamificado** | Synths com baixa escolaridade rejeitaram mecânicas complexas → simplificar tutorial | 3h | ✅ Redesign aceito |
| **Checkout em 1 Clique** | Simulação mostrou 18% abandono por falta de confiança em segurança | 1.5h | ✅ Adicionado selo de segurança |
| **Dashboard de Analytics** | Exploração propôs remover 40% das métricas + tour guiado → sucesso 28% → 41% | 4h | ✅ Implementado |
| **Feature de Compartilhamento** | Entrevistas revelaram preocupação com privacidade em 7/10 synths | 2h | ✅ Adicionado controle granular |
| **Modo Offline** | SHAP mostrou que latência de rede (não complexidade UI) prediz abandono | 2.5h | ✅ Priorizou cache |
| **Notificações Push** | Exploração sugeria opt-in agressivo, mas UX interviews mostraram rejeição | 5h | ✅ Mudou para opt-in suave |
| **Sistema de Recomendação** | Clustering identificou 4 perfis distintos, cada um precisa de lógica diferente | 3h | ✅ Personalização por perfil |
| **Wizard Multi-Step** | Exploração reduziu scorecard de complexidade de 8.5 → 4.2 em 5 níveis | 4h | ✅ Simplificação radical |

**Taxa de Sucesso**: 7/8 experimentos geraram insights acionáveis que mudaram decisões de produto (**87.5%**)

**Custo Real por Experimento**: < R$ 20 (LLM API costs)

---

## 5. Lessons Learned

### O Que Funcionou Bem

**1. LLMs como Entrevistadores São Surpreendentemente Eficazes**
- Em testes cegos, 3 UX researchers não distinguiram transcritos de synths vs. humanos em 6/10 casos
- Structured outputs + function calling garantem profundidade comparável a entrevistadores juniores
- **Aprendizado**: Qualidade depende do script — roteiros vagos geram entrevistas rasas

**2. Monte Carlo Revela Padrões Invisíveis**
- Experimento "Modo Offline": SHAP revelou efeito multiplicativo de latência × idade > 55 (não-linear)
- 10.000 execuções cobrem cauda longa da distribuição que 20-50 usuários nunca mostrariam
- **Aprendizado**: Explicabilidade (SHAP/PDP) é tão importante quanto o resultado bruto

**3. Beam Search com LLM Supera Busca Exaustiva**
- Exploração dirigida (beam width = 3) encontra soluções 40% melhores em 1/10 do tempo
- Experimento "Dashboard": 15 nós explorados vs. 200+ combinações possíveis
- **Aprendizado**: Largura do beam (3-5) importa mais que profundidade (> 5 níveis tem retorno decrescente)

**4. Dados IBGE São Suficientes para Diversidade**
- 80+ atributos geram 10.000+ arquétipos distintos (Shannon Entropy = 4.7 bits)
- Deficiências (visual, auditiva, motora) e vieses cognitivos são diferenciadores-chave
- **Aprendizado**: Sem esses atributos, synths ficam genéricos e pouco realistas

### O Que Não Funcionou

**1. Scorecards Automáticos por LLM São Inconsistentes**
- Mesma feature recebia scores variando ±30% entre execuções (mesmo com seed fixo)
- **Solução adotada**: Scorecards agora são input manual do PM, com sugestão LLM opcional
- **Aprendizado**: LLMs são melhores em comparações relativas que avaliações absolutas

**2. Entrevistas com > 10 Turnos Ficam Repetitivas**
- Turnos 11-20 eram variações superficiais, sem novos insights (recency bias do LLM)
- **Solução adotada**: Limite padrão = 6 turnos, máximo 10 para casos específicos
- **Aprendizado**: Múltiplas entrevistas curtas > 1 entrevista longa

**3. Frontend com Server-Side Rendering Foi Abandonado**
- Latências de 5-30s de LLM tornavam UX insuportável com SSR (spinners intermináveis)
- **Solução adotada**: Client-Side SPA + TanStack Query + Server-Sent Events para streaming
- **Aprendizado**: Para IA com latências longas, CSR + streaming > SSR

### Surpresas Positivas

- **PMs usam explorações para negociar com stakeholders** — Simulações dão "cobertura objetiva" para decisões de descope
- **Entrevistas geram hipóteses não planejadas** — 5/8 experimentos tiveram insights fora do escopo original
- **SHAP charts > tabelas** — Visualizações receberam 3× mais compartilhamentos internos (24 vs. 8 no Slack)

---

## 6. Strategic Priorities: Próximos 6 Meses

### Prioridade 1: Validar Product-Market Fit (Jan-Mar 2026)

**Objetivo**: Provar que Synth-Lab muda comportamento de decisão em organizações reais.

**Táticas**:
- Recrutar **3 equipes piloto** (startups Série A-B, 5-15 pessoas de produto)
- Implementar **sistema de feedback in-app** (thumbs up/down em insights)
- Instrumentar **funil de adoção** (experimento criado → simulação → visualização → decisão)
- Conduzir **6 entrevistas de validação** para identificar gaps de valor

**Critério de Sucesso (Go/No-Go)**:
- ≥ 2/3 equipes executaram 5+ experimentos
- ≥ 1 equipe relata mudança concreta de roadmap devido a Synth-Lab
- Taxa de insights úteis > 60%

---

### Prioridade 2: Escalar Capacidade de Insights (Jan-Abr 2026)

**Objetivo**: Reduzir Time-to-Insight de 4h → 1h através de automação.

**Táticas**:
- **Paralelizar análises de charts** (12 × 15s → 20s via asyncio.gather)
- **Cache inteligente** (invalidação seletiva, evita 50% de re-simulações)
- **Simulações incrementais** (adicionar synths sem reprocessar todos)
- **Otimizar prompts de LLM** (2K → 800 tokens, mantendo qualidade)

**Critério de Sucesso**:
- Time-to-Insight mediano < 90min
- Custo por experimento < R$ 15
- Latency p95 de endpoints de IA < 10s

---

### Prioridade 3: Feedback Loop com Validação Real (Mar-Jun 2026)

**Objetivo**: Provar correlação entre insights de synths e comportamento de usuários reais.

**Táticas**:
- Feature **"Marcar para Validação"** (checklist de pesquisa real)
- **Coleta de ground truth** (10 experimentos com research real pós-synth)
- **Modelo de confiança** (badges 🟢🟡🔴 baseados em precision histórica)

**Critério de Sucesso**:
- ≥ 10 experimentos com validação real completada
- ≥ 1 case study publicável sobre correlação synths vs. humanos
- Sistema de badges implementado e visível no UI

---

### Prioridade 4: Posicionamento e Go-to-Market (Jan-Jun 2026)

**Objetivo**: Definir ICP, pricing e canais de aquisição.

**Táticas**:
- **Análise de ICP** (15 entrevistas com PMs/UX Researchers)
- **Teste de pricing** (Van Westendorp com 50+ respondentes)
- **Conteúdo educacional** (3 blog posts, 1 webinar, 1 case study)
- **Parcerias** com comunidades de produto (Product Oversee, WomenTech, UXCONF)

**Critério de Sucesso**:
- ICP documentado e validado
- Modelo de pricing testado e definido
- ≥ 100 usuários únicos testaram produto
- ≥ 1 case study publicado

---

### Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|--------------|---------|-----------|
| **Equipes piloto não executam experimentos** | 🟡 Média | 🔴 Alto | Onboarding dedicado 1h/semana, templates prontos |
| **Insights de IA têm baixa qualidade (< 50%)** | 🟡 Média | 🔴 Alto | A/B testing de prompts, human review antes de GA |
| **Validação real contradiz synths** | 🟢 Baixa | 🔴 Alto | Study com 10 experimentos antes de claims públicos |
| **Custos de LLM excedem budget** | 🟡 Média | 🟡 Médio | Otimização de prompts, cache agressivo |
| **Concorrente lança produto similar** | 🟡 Média | 🟡 Médio | Foco em dados IBGE (moat local), open-source |

---

### Recursos Necessários (6 meses)

**Time**:
- 1.0 FTE Backend Engineer (paralelização, cache, multi-tenancy)
- 0.5 FTE Frontend Engineer (UI de feedback, dashboards)
- 0.3 FTE Product Manager (roadmap, entrevistas ICP)
- 0.2 FTE UX Researcher consultor (validation studies)

**Budget**: R$ 15.600 total (~R$ 2.600/mês)
- LLM API: R$ 3.000
- Infra (PostgreSQL, compute): R$ 2.000
- Ferramentas (analytics, monitoring): R$ 1.500
- Recrutamento para validation studies: R$ 4.000
- Marketing de conteúdo: R$ 2.500
- Contingência 20%: R$ 2.600

---

**Documento preparado em**: 04 de Janeiro de 2026
**Próxima revisão**: 01 de Abril de 2026 (pós-validação com equipes piloto)
**Responsável**: Fulvio (Product Lead, Synth-Lab)
**Versão**: 2.0 (Executiva)
