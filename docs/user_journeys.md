# synth-lab - Jornadas de Usuário

> Documentação das principais jornadas de uso da plataforma synth-lab

**Última atualização**: 2026-01-13

---

## Visão Geral

Este documento descreve as principais jornadas de usuário na plataforma **synth-lab**, mostrando como diferentes perfis de usuários interagem com o sistema para atingir seus objetivos.

### Personas de Usuário

1. **Product Manager (PM)**: Valida hipóteses de produto, toma decisões sobre features, executa análises quantitativas
2. **UX Researcher**: Conduz pesquisas qualitativas, analisa comportamentos, gerencia grupos de synths
3. **Product Designer**: Testa conceitos visuais, valida usabilidade

---

## JORNADA 1: Validação Completa de Feature (PM)

**Objetivo**: Validar se uma nova feature deve ser implementada

**Persona**: Product Manager

**Contexto**: O PM tem uma hipótese sobre uma nova feature e precisa decidir se deve investir desenvolvimento

### Passo 1: Criar Experimento
1. Acessa página **Index** (`/`)
2. Clica em "New Experiment" (dialog)
3. Preenche **ExperimentForm**:
   - Nome: "Dark Mode Toggle"
   - Hipótese: "Usuários preferem tema escuro para uso noturno"
   - Descrição: Contexto detalhado da feature
4. Submete formulário
5. Sistema gera **Interview Guide** automaticamente em background

**Resultado**: Experimento `exp_a1b2c3d4` criado

### Passo 2: Configurar Scorecard
1. Navega para **ExperimentDetail** (`/experiments/exp_a1b2c3d4`)
2. Tab **Overview**
3. Clica em "Estimate Scorecard" (IA)
4. Revisa estimativas automáticas:
   - Complexity: 30/100
   - Initial Effort: 40/100
   - Perceived Risk: 20/100
   - Time to Value: 60/100
5. Ajusta manualmente se necessário
6. Salva scorecard

**Resultado**: Feature quantificada nas 4 dimensões

### Passo 3: Adicionar Materiais (Opcional)
1. Tab **Materials**
2. Upload de:
   - Mockups da interface (PNG)
   - Protótipo interativo (vídeo MP4)
   - Especificação técnica (PDF)
3. Clica em "Describe" para auto-descrição via Vision API
4. Confirma/edita descrições geradas

**Resultado**: Contexto visual disponível para entrevistas

### Passo 4: Executar Análise Quantitativa
1. Tab **Analysis**
2. Clica em "Run Analysis"
3. Aguarda processamento (polling de status)
4. Navega pelas **6 Fases**:

   **Fase 1: Overview**
   - Vê outcome distribution chart
   - Analisa try rate: 72%
   - Analisa success rate: 65%
   - Identifica adoption potential: 47%

   **Fase 2: Location**
   - Examina failure heatmap
   - Identifica: Usuários 60+ têm alta taxa de falha
   - Nota: Usuários mobile têm baixa taxa de tentativa

   **Fase 3: Segmentation**
   - Executa K-means clustering (4 clusters)
   - Identifica perfis:
     - "Tech Enthusiasts": Alta adoção
     - "Resistant Traditionalists": Baixa tentativa
     - "Struggling Adopters": Tentam mas falham
     - "Neutral Middle": Média performance
   - Visualiza PCA scatter

   **Fase 4: Edge Cases**
   - Vê extreme cases table:
     - Top 5 performers: Jovens tech-savvy
     - Bottom 5 performers: Seniors, low tech literacy
   - Decide: Precisa investigar qualitativamente

   **Fase 5: Insights**
   - Gera AI insights para cada chart
   - Lê key findings consolidados
   - Nota recomendação: "Simplificar onboarding para seniors"

   **Fase 6: Summary**
   - Lê Executive Summary completo
   - Exporta relatório

**Resultado**: Compreensão quantitativa completa

### Passo 5: Entrevista com Casos Extremos
1. Tab **Interviews**
2. Clica em "Auto Interview" (extreme cases)
3. Sistema seleciona automaticamente:
   - 5 top performers
   - 5 worst performers
4. Navega para **InterviewDetail** (`/research/exec_12345`)
5. Monitora **LiveInterviewGrid** em tempo real:
   - Vê cards de 10 synths
   - Acompanha perguntas/respostas streaming
   - Nota status: pending → running → generating → completed
6. Seleciona synth específico para ler transcrição completa
7. Identifica insights qualitativos:
   - Seniors: "Não entendo onde está o botão"
   - Tech enthusiasts: "Deveria ter atalho de teclado"

**Resultado**: Contexto qualitativo dos extremos

### Passo 6: Gerar Documentos
1. Volta para **InterviewDetail**
2. Seção **Documents**
3. Clica em "Generate Summary"
4. Aguarda processamento
5. Lê **Research Summary** (narrativa consolidada)
6. Clica em "Generate PRFAQ"
7. Lê **PRFAQ** (formato Amazon)
8. Volta para **ExperimentDetail** > Tab **Analysis**
9. Já possui **Executive Summary** gerado

**Resultado**: 3 documentos narrativos prontos para decisão

### Passo 7: Decisão Final
1. Revisa todos os documentos:
   - Executive Summary: Recomenda implementação COM ajustes
   - Research Summary: Destaca problemas de usabilidade para seniors
   - PRFAQ: Mostra visão de produto final
2. Decisão: **Aprovar feature COM modificações**:
   - Adicionar tutorial step-by-step
   - Melhorar contraste do toggle
   - Adicionar atalho de teclado (Ctrl+Shift+D)
3. Adiciona tag "approved-with-changes"
4. Compartilha documentos com time de desenvolvimento

**Resultado**: Decisão informada com roadmap claro

**Tempo Total**: ~2-3 horas (incluindo processamentos assíncronos)

---

## JORNADA 2: Exploração de Cenários Alternativos (PM/Designer)

**Objetivo**: Encontrar a melhor variação de uma feature para maximizar adoção

**Persona**: Product Manager + Product Designer

**Contexto**: A análise inicial mostrou 47% de adoção, mas o PM quer explorar melhorias

### Passo 1: Criar Exploração
1. Em **ExperimentDetail** > Tab **Explorations**
2. Clica em "New Exploration"
3. Preenche formulário:
   - Goal: `success_rate > 75`
   - Max Depth: 3
   - Max Iterations: 10
4. Submete

**Resultado**: Exploração `expl_f3e4d5c6` iniciada

### Passo 2: Monitorar Árvore de Cenários
1. Navega para **ExplorationDetail** (`/explorations/expl_f3e4d5c6`)
2. Visualiza **Exploration Tree Flow** (React Flow):
   - Nó raiz: Cenário original (success_rate: 65%)
   - Ramificações: LLM propõe 3 ações:
     - "Adicionar tooltip explicativo"
     - "Mudar localização do toggle"
     - "Adicionar preview antes de aplicar"
3. Aguarda simulações de cada ação
4. Vê resultados:
   - Tooltip: 68% (melhora pequena)
   - Mudar localização: 71% (melhora moderada)
   - Preview: 78% (ATINGE META!)
5. Sistema escolhe "Preview" e continua explorando a partir dele

### Passo 3: Analisar Winning Path
1. Aguarda exploração completar
2. Clica em "View Winning Path"
3. Vê sequência de ações vencedoras:
   1. Adicionar preview antes de aplicar (65% → 78%)
   2. Adicionar tutorial contextual (78% → 82%)
   3. Melhorar mensagem de confirmação (82% → 85%)
4. Final success rate: **85%** (meta: 75%)

**Resultado**: Roadmap de melhorias com impacto quantificado

### Passo 4: Gerar Documentos de Exploração
1. Clica em "Generate Exploration Summary"
2. Lê sumário narrativo com:
   - Objetivo da exploração
   - Cenários testados (15 no total)
   - Melhor caminho encontrado
   - Insights e recomendações
3. Clica em "Generate PRFAQ"
4. Lê PRFAQ da versão melhorada

**Resultado**: Documentação completa da versão otimizada

### Passo 5: Comunicação com Time
1. Exporta documentos
2. Compartilha com designers e devs
3. Adiciona tag "optimized-version"
4. Atualiza descrição do experimento com as melhorias

**Resultado**: Time alinhado com versão final

**Tempo Total**: ~1-2 horas (incluindo processamento)

---

## JORNADA 3: Pesquisa Qualitativa Focada (UX Researcher)

**Objetivo**: Entender em profundidade as motivações e barreiras de um segmento específico

**Persona**: UX Researcher

**Contexto**: A análise identificou um cluster "Struggling Adopters" e o researcher quer investigar

### Passo 1: Criar Entrevista Customizada
1. Em **ExperimentDetail**
2. Tab **Interviews**
3. Clica em "New Interview"
4. Preenche:
   - Additional context: "Foco em barreiras de usabilidade para usuários 55+"
   - Synth IDs: Cola lista de 8 synths
   - Max turns: 8 (entrevista mais longa)
   - Generate summary: true
5. Submete

**Resultado**: Entrevista `exec_78901` iniciada

### Passo 2: Acompanhar Entrevistas ao Vivo
1. Navega para **InterviewDetail** (`/research/exec_78901`)
2. **LiveInterviewGrid**:
   - 8 cards atualizando em tempo real
   - Foca em padrões emergentes:
     - "Não vejo o botão"
     - "Tenho medo de errar"
     - "Não sei se salvou"
3. Anota temas recorrentes

**Resultado**: Padrões identificados durante execução

### Passo 3: Análise Detalhada de Transcrições
1. Seção **Transcript Viewer**
2. Seleciona cada synth individualmente
3. Lê thread completa
4. Anota quotes relevantes:
   - synth_001: "O contraste é muito baixo, não consigo ver"
   - synth_005: "Prefiro que perguntasse antes de mudar tudo"
   - synth_007: "Não sei como voltar se não gostar"
5. Download de todas as transcrições

**Resultado**: Quotes e insights categorizados

### Passo 4: Gerar e Enriquecer Summary
1. Clica em "Generate Summary"
2. Lê **Research Summary** gerado
3. Identifica 3 temas principais:
   - Visibilidade (contraste, localização)
   - Controle (confirmação, reversão)
   - Confiança (feedback, guidance)
4. Exporta para apresentação

**Resultado**: Relatório de pesquisa pronto

### Passo 5: Compartilhar Insights
1. Adiciona tag "ux-research"
2. Compartilha summary com time de design
3. Agenda workshop para discutir soluções

**Resultado**: Insights acionáveis para design

**Tempo Total**: ~1-2 horas

---

## JORNADA 4: Chat Pós-Entrevista com Synth (UX Researcher)

**Objetivo**: Aprofundar em tópico específico com um synth após entrevista

**Persona**: UX Researcher

**Contexto**: Durante revisão de transcrição, identifica ponto que precisa clarificação

### Passo 1: Identificar Synth e Contexto
1. Em **InterviewDetail**
2. **Transcript Viewer**: Lê transcrição de synth_042
3. Identifica fala: "Não consigo ver o botão"
4. Quer entender: O que especificamente dificulta a visualização?

**Resultado**: Tópico para aprofundar

### Passo 2: Iniciar Chat
1. Clica em "Chat with Synth" (na card do synth)
2. Sistema abre dialog de chat
3. Contexto de entrevista é mantido automaticamente

**Resultado**: Chat iniciado com contexto

### Passo 3: Conversa Contextual
1. Envia: "Você mencionou que não consegue ver o botão. Pode descrever o que torna difícil visualizá-lo?"
2. Synth responde (mantendo persona):
   - "O contraste entre o botão e o fundo é muito baixo"
   - "Meus olhos não são mais tão bons quanto antes"
   - "Prefiro interfaces com alto contraste"
3. Envia follow-up: "Que nível de contraste seria ideal para você?"
4. Synth responde:
   - "Algo como texto preto em fundo branco"
   - "Ou botões com bordas bem definidas"

**Resultado**: Insight específico sobre contraste

### Passo 4: Documentar Aprendizado
1. Copia quotes do chat
2. Adiciona a notas de pesquisa
3. Identifica padrão: Problema de acessibilidade (não apenas usabilidade)

**Resultado**: Recomendação de design atualizada

**Tempo Total**: ~15-30 minutos

---

## JORNADA 5: Criar e Gerenciar Grupos de Synths (UX Researcher)

**Objetivo**: Criar grupo customizado de synths para pesquisa específica

**Persona**: UX Researcher

**Contexto**: Precisa entrevistar apenas "Usuários Enterprise B2B"

### Passo 1: Explorar Catálogo de Synths
1. Acessa **Synths** (`/synths`)
2. Painel **Synth List**:
   - Filtro por arquétipo: "Enterprise User"
   - Filtro por job: "Manager", "Director", "VP"
   - Filtro por company size: "1000+"
3. Identifica 25 synths relevantes

**Resultado**: Lista de candidatos

### Passo 2: Criar Grupo Customizado
1. Painel **Synth Groups** (direita)
2. Clica em "Create New Group"
3. **CreateSynthGroupModal**:
   - Name: "Enterprise B2B Users"
   - Description: "Usuários de empresas grandes, decisores"
   - Synth selection: Marca os 25 synths identificados
   - Config (opcional): `{"min_company_size": 1000}`
4. Submete

**Resultado**: Grupo `grp_b7c8d9e0` criado

### Passo 3: Visualizar Grupo
1. Clica no grupo recém-criado
2. **SynthGroupDetailView**:
   - Lista de 25 synths
   - Distribution chart:
     - Idade média: 42 anos
     - 68% homens, 32% mulheres
     - 80% tech literacy: High
     - Jobs: 40% Managers, 35% Directors, 25% VPs
3. Confirma: Distribuição alinhada com target

**Resultado**: Grupo validado

### Passo 4: Usar Grupo em Experimento
1. Volta para **Index**
2. Clica em "New Experiment"
3. Preenche formulário:
   - Nome: "Enterprise Dashboard Redesign"
   - Hipótese: "Dashboards mais customizáveis aumentam engajamento"
   - **Synth Group**: Seleciona "Enterprise B2B Users"
4. Submete

**Resultado**: Experimento com target específico

### Passo 5: Executar Entrevista com Grupo
1. Em **ExperimentDetail** > Tab **Interviews**
2. Clica em "New Interview"
3. **Synth Group** já está selecionado automaticamente
4. Escolhe: "Interview all synths in group" (25 entrevistas)
5. Submete

**Resultado**: Pesquisa focada em target

**Tempo Total**: ~30-45 minutos

---

## FLUXOS ALTERNATIVOS E CASOS DE USO

### Caso 1: Análise Falhou - Reintentar
**Situação**: Análise iniciada, mas falhou por timeout

1. **ExperimentDetail** > Tab **Analysis**
2. Vê status: "Failed"
3. Clica em "Retry Analysis"
4. Sistema reprocessa
5. Sucesso na segunda tentativa

**Resultado**: Análise completada

### Caso 2: Entrevista Parcialmente Completa
**Situação**: 8 de 10 synths completaram, 2 falharam

1. **InterviewDetail**
2. **LiveInterviewGrid**: 8 cards "completed", 2 cards "failed"
3. Clica em synth falhado para ver erro
4. Decide: "Generate Summary" mesmo assim (8/10 é suficiente)
5. Summary é gerado com nota: "Based on 8 of 10 interviews"

**Resultado**: Pesquisa parcial aproveitada

### Caso 3: Exploração Não Atingiu Meta
**Situação**: Exploração completou mas não atingiu success_rate > 75%

1. **ExplorationDetail**
2. Vê: Best success rate: 68% (meta: 75%)
3. Analisa **Winning Path**: Sequência de 3 melhorias aplicadas
4. Decisões:
   - Opção A: Aceitar 68% como suficiente
   - Opção B: Continuar exploração (aumentar max_depth)
   - Opção C: Ajustar meta para 65%
5. Escolhe Opção B: Clica em "Continue Exploration"
6. Sistema continua a partir do melhor nó

**Resultado**: Exploração estendida

### Caso 4: Modificar Experimento Após Análise
**Situação**: Análise revelou problema, precisa ajustar hipótese

1. **ExperimentDetail** > Tab **Overview**
2. Clica em "Edit"
3. Atualiza:
   - Hipótese: Adiciona "especialmente para usuários jovens"
   - Descrição: Inclui insights da análise
4. **Scorecard**: Ajusta Perceived Risk (aumenta)
5. Salva
6. Tab **Analysis**: Clica em "Re-run Analysis" (opcional)

**Resultado**: Experimento refinado

### Caso 5: Deletar Material Errado
**Situação**: Upload de arquivo errado, precisa remover

1. **ExperimentDetail** > Tab **Materials**
2. **MaterialGallery**: Vê thumbnail do arquivo errado
3. Clica no material
4. Clica em "Delete"
5. Confirma deleção
6. Sistema remove do S3 e DB

**Resultado**: Material removido

### Caso 6: Compartilhar Resultados Externamente
**Situação**: Stakeholder externo (sem acesso ao sistema) precisa ver resultados

1. **ExperimentDetail** > Tab **Documents**
2. Clica em "View" no Executive Summary
3. Copia markdown renderizado
4. Cola em Google Docs ou exporta como PDF
5. Compartilha link/arquivo

**Resultado**: Resultados compartilhados

---

## INTEGRAÇÕES ENTRE JORNADAS

### Fluxo Típico: Quantitativo → Qualitativo → Exploração

1. **PM** cria experimento (Jornada 1, Passos 1-2)
2. **PM** executa análise (Jornada 1, Passo 4)
3. **PM** identifica clusters problemáticos na análise
4. **UX Researcher** cria grupo customizado (Jornada 5)
5. **UX Researcher** conduz entrevista focada (Jornada 3)
6. **UX Researcher** identifica soluções
7. **PM** inicia exploração para validar soluções (Jornada 2)
8. **PM** toma decisão final (Jornada 1, Passo 7)

### Fluxo Alternativo: Exploração → Validação Qualitativa

1. **PM** cria experimento com baixa performance
2. **PM** inicia exploração (Jornada 2)
3. **PM** encontra winning path com melhorias
4. **UX Researcher** entrevista synths sobre as melhorias propostas
5. **UX Researcher** valida se melhorias fazem sentido qualitativamente
6. **PM** decide implementar

---

## PONTOS DE ATENÇÃO E DICAS

### Para Product Managers
- ✅ Sempre preencha scorecard (mesmo que estimado) - ajuda priorização
- ✅ Use exploração quando success rate < 70% - pode encontrar melhorias
- ✅ Gere TODOS os documentos antes de decidir - evita viés
- ⚠️ Não confie apenas em métricas - qualitativo é essencial
- ⚠️ Não delete experimentos - histórico é valioso

### Para UX Researchers
- ✅ Use grupos customizados para pesquisas focadas
- ✅ Chat pós-entrevista é excelente para follow-ups
- ✅ Leia transcrições completas, não apenas summary
- ⚠️ Não entreviste apenas casos extremos - inclua "mainstream"
- ⚠️ Não confie 100% em quotes - são personas sintéticas

---

## ATALHOS E PRODUTIVIDADE

### Navegação Rápida
- **Index** → **ExperimentDetail**: Click no card
- **ExperimentDetail** → **InterviewDetail**: Click no interview da lista
- **InterviewDetail** → **Chat**: Click no synth card
- **ExperimentDetail** → **ExplorationDetail**: Click no exploration da lista

### Ações Comuns
- **Criar experimento**: Index > "New Experiment"
- **Run analysis**: ExperimentDetail > Tab Analysis > "Run Analysis"
- **Auto interview**: ExperimentDetail > Tab Interviews > "Auto Interview"
- **Generate summary**: InterviewDetail > Documents > "Generate Summary"
- **Start exploration**: ExperimentDetail > Tab Explorations > "New Exploration"

### Status Indicators
- 🟢 **Green badge**: Completed/Success
- 🟡 **Yellow badge**: Running/Generating
- 🔴 **Red badge**: Failed/Error
- ⚪ **Gray badge**: Pending/Not Started

---

**Fim do Documento de Jornadas de Usuário**
