# Feature Specification: SynthLab CLI

**Feature Branch**: `002-synthlab-cli`
**Created**: 2025-12-15
**Status**: Draft
**Input**: User description: "Criar um CLI chamado synthlab com help, version e comando gensynth baseado em scripts/gen_synth.py. Mover gen_synth.py para src/synth_lab/gen_synth/ e modularizar em múltiplos arquivos por semântica. Saída com cores para facilitar a TUI."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generate Synthetic Personas (Priority: P1)

Um usuário deseja gerar uma ou mais personas sintéticas brasileiras usando o comando `synthlab gensynth`. O CLI deve processar os argumentos, gerar os synths com dados coerentes baseados em distribuições IBGE, e exibir feedback visual colorido indicando progresso e sucesso.

**Why this priority**: Esta é a funcionalidade principal do CLI - sem ela, não há valor de uso. É o MVP que entrega valor imediato.

**Independent Test**: Pode ser testado executando `synthlab gensynth -n 5` e verificando que 5 arquivos JSON válidos são criados em data/synths/.

**Acceptance Scenarios**:

1. **Given** o CLI está instalado, **When** usuário executa `synthlab gensynth -n 3`, **Then** 3 synths são gerados com progresso colorido e salvos em data/synths/
2. **Given** o CLI está instalado, **When** usuário executa `synthlab gensynth`, **Then** 1 synth é gerado (valor padrão)
3. **Given** o CLI está instalado, **When** usuário executa `synthlab gensynth -n 100 -q`, **Then** 100 synths são gerados silenciosamente com apenas resumo final

---

### User Story 2 - Validate Synth Files (Priority: P2)

Um usuário deseja validar arquivos de synth existentes contra o JSON Schema para garantir conformidade e integridade dos dados.

**Why this priority**: Validação é essencial para garantir qualidade dos dados gerados, mas depende da geração funcionar primeiro.

**Independent Test**: Pode ser testado executando `synthlab gensynth --validate-all` com synths existentes e verificando output de validação.

**Acceptance Scenarios**:

1. **Given** existem synths em data/synths/, **When** usuário executa `synthlab gensynth --validate-all`, **Then** cada arquivo é validado com feedback colorido (verde=válido, vermelho=inválido)
2. **Given** existe um arquivo synth específico, **When** usuário executa `synthlab gensynth --validate-file <path>`, **Then** o arquivo é validado individualmente

---

### User Story 3 - Analyze Distribution (Priority: P3)

Um usuário deseja analisar a distribuição demográfica dos synths gerados comparando com dados do IBGE para verificar representatividade.

**Why this priority**: Análise é útil para validar qualidade estatística, mas é secundária à geração e validação básica.

**Independent Test**: Pode ser testado executando `synthlab gensynth --analyze all` com synths existentes.

**Acceptance Scenarios**:

1. **Given** existem synths gerados, **When** usuário executa `synthlab gensynth --analyze region`, **Then** tabela colorida mostra distribuição regional vs IBGE
2. **Given** existem synths gerados, **When** usuário executa `synthlab gensynth --analyze age`, **Then** tabela colorida mostra distribuição etária vs IBGE

---

### User Story 4 - CLI Help and Version (Priority: P1)

Um usuário novo deseja entender como usar o CLI e verificar a versão instalada.

**Why this priority**: Help e version são funcionalidades fundamentais de qualquer CLI - necessárias para onboarding de usuários.

**Independent Test**: Pode ser testado executando `synthlab --help` e `synthlab --version`.

**Acceptance Scenarios**:

1. **Given** o CLI está instalado, **When** usuário executa `synthlab --help`, **Then** exibe descrição do programa e lista de comandos disponíveis
2. **Given** o CLI está instalado, **When** usuário executa `synthlab --version`, **Then** exibe versão atual do pacote
3. **Given** o CLI está instalado, **When** usuário executa `synthlab gensynth --help`, **Then** exibe todas as opções do comando gensynth

---

### Edge Cases

- O que acontece quando quantidade é 0 ou negativa? Erro com mensagem clara.
- O que acontece quando diretório de output não existe? Criar automaticamente.
- O que acontece quando arquivo de validação não existe? Erro com mensagem clara.
- O que acontece quando config files estão ausentes? Erro explicativo listando arquivos faltantes.
- O que acontece quando terminal não suporta cores? Fallback para output sem cores (auto-detectado).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Sistema DEVE prover comando `synthlab` como entry point principal do CLI
- **FR-002**: Sistema DEVE suportar subcomando `gensynth` para geração de synths
- **FR-003**: Sistema DEVE exibir help com `--help` ou `-h` em qualquer nível
- **FR-004**: Sistema DEVE exibir versão com `--version` ou `-V`
- **FR-005**: Sistema DEVE usar cores ANSI para output (verde=sucesso, vermelho=erro, amarelo=aviso, azul=info)
- **FR-006**: Sistema DEVE detectar automaticamente se terminal suporta cores
- **FR-007**: Sistema DEVE manter compatibilidade com todas as flags existentes do gen_synth.py
- **FR-008**: Sistema DEVE organizar código em módulos separados por responsabilidade semântica:
  - `demographics.py` - geração de dados demográficos (idade, gênero, localização, ocupação)
  - `psychographics.py` - geração de dados psicográficos (Big Five, valores, interesses)
  - `behavior.py` - geração de comportamentos (consumo, tecnologia, mídia)
  - `disabilities.py` - geração de deficiências
  - `tech_capabilities.py` - geração de capacidades tecnológicas
  - `biases.py` - geração de vieses comportamentais
  - `derivations.py` - funções de derivação (arquétipo, estilo de vida, descrição)
  - `validation.py` - validação de synths contra schema
  - `analysis.py` - análise de distribuições
  - `storage.py` - persistência de synths (save, load)
  - `config.py` - carregamento de configurações
  - `utils.py` - funções utilitárias (gerar_id, weighted_choice, etc.)
- **FR-009**: Sistema DEVE manter função `assemble_synth()` como orquestrador principal
- **FR-010**: Sistema DEVE preservar todas as regras de coerência entre campos

### Key Entities

- **Synth**: Persona sintética completa com id, nome, arquétipo, descrição, demografia, psicografia, comportamento, deficiências, capacidades tecnológicas e vieses
- **Config**: Conjunto de configurações carregadas dos arquivos JSON (IBGE, occupations, interests_hobbies)
- **ValidationResult**: Resultado de validação com status (válido/inválido) e lista de erros
- **DistributionAnalysis**: Análise comparativa de distribuição gerada vs esperada (IBGE)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Usuários podem gerar 100 synths em menos de 10 segundos
- **SC-002**: 100% dos synths gerados passam na validação contra JSON Schema
- **SC-003**: Output colorido funciona em 95% dos terminais modernos (com fallback)
- **SC-004**: Código modularizado com nenhum arquivo excedendo 300 linhas
- **SC-005**: 100% das funcionalidades existentes do gen_synth.py preservadas
- **SC-006**: Usuários conseguem entender todas as opções do CLI apenas lendo o help
