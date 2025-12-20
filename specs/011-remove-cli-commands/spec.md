# Feature Specification: Remover Comandos CLI Obsoletos

**Feature Branch**: `011-remove-cli-commands`
**Created**: 2025-12-20
**Status**: Draft
**Input**: User description: "vamos eliminar uma serie de comandos CLI: uv run synthlab listsynth, uv run synthlab research, uv run synthlab research-batch, uv run synthlab topic-guide, uv run synthlab research-prfaq. MANTENHA OS SERVICOS QUE SEJAM USADOS PELA API, mas elimine tudo que ficar obsoleto ao eliminar esses comandos."

## User Scenarios & Testing

### User Story 1 - Simplificar Interface CLI Mantendo API Funcional (Priority: P1)

Como desenvolvedor ou administrador do sistema, eu quero que a interface CLI seja simplificada removendo comandos duplicados que já estão disponíveis via API REST, para que a manutenção seja mais fácil e os usuários sejam direcionados para a API moderna.

**Why this priority**: Este é o cenário principal - eliminar complexidade desnecessária mantendo toda funcionalidade acessível via API REST. A API já oferece todos esses recursos de forma mais moderna e escalável.

**Independent Test**: Pode ser totalmente testado verificando que (1) os comandos CLI removidos não estão mais disponíveis, (2) todas as funcionalidades correspondentes continuam acessíveis via endpoints da API REST, e (3) o comando `synthlab --help` não mostra mais os comandos removidos.

**Acceptance Scenarios**:

1. **Given** o sistema está instalado com os comandos CLI removidos, **When** usuário executa `uv run synthlab listsynth`, **Then** o sistema retorna erro informando que o comando não existe e sugere usar a API REST endpoint `/synths/list`

2. **Given** o sistema está instalado com os comandos CLI removidos, **When** usuário executa `uv run synthlab research`, **Then** o sistema retorna erro informando que o comando não existe e sugere usar a API REST endpoint `/research/execute`

3. **Given** o sistema está instalado com os comandos CLI removidos, **When** usuário executa `uv run synthlab research-batch`, **Then** o sistema retorna erro informando que o comando não existe e sugere usar a API REST endpoint `/research/execute`

4. **Given** o sistema está instalado com os comandos CLI removidos, **When** usuário executa `uv run synthlab topic-guide`, **Then** o sistema retorna erro informando que o comando não existe e sugere usar a API REST endpoints `/topics/*`

5. **Given** o sistema está instalado com os comandos CLI removidos, **When** usuário executa `uv run synthlab research-prfaq`, **Then** o sistema retorna erro informando que o comando não existe e sugere usar a API REST endpoint `/prfaq/*`

6. **Given** o sistema está instalado com os comandos CLI removidos, **When** usuário executa `uv run synthlab --help`, **Then** o sistema mostra apenas os comandos CLI mantidos (`gensynth`) sem mencionar os comandos removidos

---

### User Story 2 - Serviços da API Continuam Funcionais (Priority: P1)

Como desenvolvedor de API ou usuário da API REST, eu quero que todos os serviços (SynthService, ResearchService, TopicService, ReportService) continuem funcionando normalmente, para que a API REST não seja afetada pela remoção dos comandos CLI.

**Why this priority**: Crítico - os serviços são compartilhados entre CLI e API. Devemos garantir que a remoção de comandos CLI não afete a API REST de forma alguma.

**Independent Test**: Pode ser totalmente testado executando todos os endpoints da API REST e verificando que continuam retornando respostas corretas.

**Acceptance Scenarios**:

1. **Given** os comandos CLI foram removidos, **When** usuário faz GET request para `/synths/list`, **Then** a API retorna lista de synths com status 200

2. **Given** os comandos CLI foram removidos, **When** usuário faz POST request para `/research/execute`, **Then** a API inicia research execution com streaming SSE

3. **Given** os comandos CLI foram removidos, **When** usuário faz GET request para `/topics/list`, **Then** a API retorna lista de topics com status 200

4. **Given** os comandos CLI foram removidos, **When** usuário faz GET request para `/prfaq/list`, **Then** a API retorna lista de PR-FAQs com status 200

5. **Given** os comandos CLI foram removidos, **When** usuário executa todos os 17 endpoints da API REST, **Then** todos retornam respostas corretas sem erros

---

### User Story 3 - Limpeza de Código Obsoleto (Priority: P2)

Como mantenedor do código, eu quero que todo código relacionado exclusivamente aos comandos CLI removidos seja eliminado, para reduzir a superfície de código a manter e evitar confusão futura.

**Why this priority**: Importante para manutenibilidade de longo prazo, mas secundário à funcionalidade principal.

**Independent Test**: Pode ser testado verificando que arquivos e imports relacionados apenas aos comandos removidos não existem mais no código.

**Acceptance Scenarios**:

1. **Given** os comandos CLI foram removidos, **When** desenvolvedor busca por imports de módulos CLI removidos, **Then** não encontra referências no código ativo

2. **Given** os comandos CLI foram removidos, **When** desenvolvedor verifica estrutura de diretórios, **Then** arquivos específicos de CLI removidos (como `query/cli.py`, `research/cli.py`) foram deletados

3. **Given** os comandos CLI foram removidos, **When** desenvolvedor executa linter/type checker, **Then** não há warnings sobre imports não utilizados

---

### User Story 4 - Documentação Atualizada (Priority: P2)

Como usuário do synth-lab, eu quero que toda documentação (README, docs/cli.md) reflita os comandos disponíveis, para não tentar usar comandos que não existem mais.

**Why this priority**: Importante para UX, mas pode ser feito após a remoção técnica dos comandos.

**Independent Test**: Pode ser testado verificando que a documentação não menciona mais os comandos removidos.

**Acceptance Scenarios**:

1. **Given** os comandos CLI foram removidos, **When** usuário lê README.md, **Then** não vê menções aos comandos removidos (listsynth, research, research-batch, topic-guide, research-prfaq)

2. **Given** os comandos CLI foram removidos, **When** usuário lê docs/cli.md, **Then** a documentação mostra apenas o comando `gensynth` e direciona para a API REST para outras funcionalidades

3. **Given** os comandos CLI foram removidos, **When** usuário busca exemplos de uso, **Then** encontra apenas exemplos usando API REST ou o comando `gensynth`

---

### Edge Cases

- O que acontece se um script ou automação existente tentar usar os comandos removidos? (Deve falhar com mensagem clara direcionando para a API)
- Como lidar com código de testes que usa os comandos CLI removidos? (Deve ser atualizado para usar API REST ou removido)
- O que acontece com módulos que eram importados apenas pelos comandos removidos? (Devem ser removidos se não usados pela API)
- Como garantir que serviços compartilhados (SynthService, etc.) não são afetados? (Testes de integração da API devem continuar passando)

## Requirements

### Functional Requirements

- **FR-001**: Sistema NÃO DEVE mais aceitar o comando `uv run synthlab listsynth`
- **FR-002**: Sistema NÃO DEVE mais aceitar o comando `uv run synthlab research`
- **FR-003**: Sistema NÃO DEVE mais aceitar o comando `uv run synthlab research-batch`
- **FR-004**: Sistema NÃO DEVE mais aceitar o comando `uv run synthlab topic-guide`
- **FR-005**: Sistema NÃO DEVE mais aceitar o comando `uv run synthlab research-prfaq`
- **FR-006**: Sistema DEVE retornar mensagem de erro clara quando usuário tentar usar comandos removidos, sugerindo uso da API REST
- **FR-007**: Sistema DEVE manter comando `uv run synthlab gensynth` totalmente funcional
- **FR-008**: Sistema DEVE manter todos os serviços (SynthService, ResearchService, TopicService, ReportService) 100% funcionais
- **FR-009**: API REST DEVE continuar oferecendo todos os 17 endpoints sem alterações
- **FR-010**: Sistema DEVE remover arquivos de código relacionados exclusivamente aos comandos CLI removidos:
  - `src/synth_lab/query/cli.py`
  - `src/synth_lab/research/cli.py`
  - `src/synth_lab/research_agentic/cli.py` (se existir)
  - `src/synth_lab/topic_guides/cli.py` (se existir)
  - `src/synth_lab/research_prfaq/cli.py` (se existir)
- **FR-011**: Sistema DEVE remover imports e registros dos comandos removidos no entry point principal (`__main__.py` ou arquivo de CLI principal)
- **FR-012**: Sistema DEVE atualizar `synthlab --help` para mostrar apenas comandos disponíveis
- **FR-013**: Documentação DEVE ser atualizada para não mencionar comandos removidos:
  - README.md
  - docs/cli.md
  - Qualquer outro arquivo de documentação que mencione os comandos
- **FR-014**: Sistema DEVE preservar toda lógica de negócio nos services que é usada pela API REST
- **FR-015**: Testes existentes da API REST DEVEM continuar passando sem modificações

### Key Entities

Nenhuma entidade de dados é criada ou modificada nesta feature - apenas remoção de código.

### Componentes Afetados

- **CLI Entry Point**: Arquivo principal que registra comandos Typer (provavelmente `__main__.py`)
- **Módulos CLI**: Arquivos `cli.py` nos módulos `query/`, `research/`, `topic_guides/`, `research_prfaq/`
- **Documentação**: README.md, docs/cli.md
- **Serviços (NÃO REMOVER)**: SynthService, ResearchService, TopicService, ReportService devem ser preservados intactos
- **Repositórios (NÃO REMOVER)**: Todos os repositories devem ser preservados
- **API REST (NÃO TOCAR)**: Nenhuma alteração na camada API

## Success Criteria

### Measurable Outcomes

- **SC-001**: Usuário que tenta executar `uv run synthlab listsynth` recebe erro claro em menos de 1 segundo
- **SC-002**: Usuário que tenta executar qualquer dos 5 comandos removidos recebe mensagem sugerindo o endpoint REST correspondente
- **SC-003**: Todos os 17 endpoints da API REST continuam funcionando com 100% de sucesso rate
- **SC-004**: Execução de `uv run synthlab --help` mostra apenas o comando `gensynth` disponível
- **SC-005**: Código base reduzido em aproximadamente 200-500 linhas (estimativa baseada em remoção de 5 arquivos CLI)
- **SC-006**: Zero warnings de imports não utilizados após remoção dos comandos
- **SC-007**: 100% dos testes de integração da API REST continuam passando
- **SC-008**: Documentação atualizada não menciona nenhum dos 5 comandos removidos

## Assumptions

1. **API REST completamente funcional**: Assumimos que a API REST já oferece todas as funcionalidades dos comandos CLI sendo removidos
2. **Serviços desacoplados**: Assumimos que os services (SynthService, etc.) são usados tanto por CLI quanto por API, portanto devem ser mantidos
3. **Apenas CLI gensynth é mantido**: Assumimos que o comando `gensynth` é o único comando CLI que deve permanecer (geração de synths e avatares)
4. **Sem migração de dados**: Nenhuma migração de dados é necessária, apenas remoção de código
5. **Usuários migraram para API**: Assumimos que usuários que usavam CLI podem migrar para API REST sem problemas

## Out of Scope

- Adicionar novos comandos CLI
- Modificar comportamento da API REST
- Alterar lógica de negócio nos services
- Criar ferramentas de migração para scripts existentes
- Adicionar autenticação ou outros recursos na API
- Modificar o comando `gensynth` que permanece

## Dependencies

- API REST deve estar totalmente funcional e testada
- Documentação da API deve estar completa (já existe em docs/api.md)
- Testes de integração da API devem estar implementados

## Risks

1. **Risco**: Scripts ou automações existentes podem depender dos comandos removidos
   **Mitigação**: Mensagens de erro claras direcionando para API REST, documentar breaking change no CHANGELOG

2. **Risco**: Remoção acidental de código compartilhado com API
   **Mitigação**: Revisar cuidadosamente dependencies antes de deletar, executar todos os testes da API

3. **Risco**: Usuários confusos sobre onde encontrar funcionalidades
   **Mitigação**: Documentação clara, mensagens de erro com sugestões de endpoints REST
