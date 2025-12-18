# Especificação: Mini-Jaeger Local para Conversas LLM Multi-turn

**Feature Branch**: `008-trace-visualizer`
**Created**: 2025-12-17
**Status**: Draft

## Visão Geral

O sistema fornece uma visualização local, leve e sem dependências externas para entender, depurar e analisar conversas multi-turn com LLMs, incluindo chamadas a ferramentas (tool calling).

Registra a execução como um **trace único**, composto por turns sequenciais e etapas internas, oferecendo navegação visual em **waterfall** com inspeção detalhada de conteúdo.

**Foco**: Desenvolvimento, debugging e pesquisa (não é ferramenta de produção).

---

## User Scenarios & Testing

### User Story 1 - Visualizar Conversa como Timeline (Priority: P1)

**Descrição**: Um desenvolvedor quer entender a sequência de uma conversa multi-turn visualizando-a como uma linha do tempo, não como logs de texto.

**Por quê esta prioridade**: Este é o core do produto. Sem visualização, não há valor. É requisito mínimo para MVP.

**Teste Independente**: Um desenvolverador consegue carregar um trace com 3+ turns e visualizar cada turn como uma barra no waterfall, com duração clara.

**Cenários de Aceitação**:

1. **Dado** um trace com 3 turns, **Quando** o desenvolvedor abre a visualização, **Então** vê 3 barras horizontais ordenadas por tempo, cada uma com rótulo do turn
2. **Dado** um turn com 5 etapas internas, **Quando** o desenvolvedor expande o turn, **Então** vê 5 sub-barras aninhadas, durações somam corretamente
3. **Dado** um trace carregado, **Quando** o desenvolvedor identifica a etapa mais lenta, **Então** consegue fazer isso em <10 segundos olhando apenas o waterfall

---

### User Story 2 - Inspecionar Detalhes de Etapas (Priority: P1)

**Descrição**: Desenvolvedor quer clicar em uma etapa e ver imediatamente o prompt, resposta, argumentos ou resultados associados.

**Por quê esta prioridade**: MVP requer capacidade de drill-down para entender "por quê" cada decisão foi tomada.

**Teste Independente**: Clique em uma etapa revela um painel lateral com todas as informações relevantes (prompt, resposta, args, resultado) em <1s.

**Cenários de Aceitação**:

1. **Dado** uma etapa de LLM call, **Quando** desenvolvedor clica, **Então** vê prompt, resposta e modelo em painel lateral
2. **Dado** uma etapa de tool call, **Quando** desenvolvedor clica, **Então** vê nome da tool, argumentos em JSON e resultado
3. **Dado** prompt com >500 chars, **Quando** exibido no painel, **Então** é truncado com opção de ver tudo
4. **Dado** um erro em uma etapa, **Quando** clicado, **Então** mensagem de erro é claramente visível em vermelho

---

### User Story 3 - Exportar e Compartilhar Traces (Priority: P2)

**Descrição**: Desenvolvedor quer compartilhar um trace com colega sem precisar recrear a conversa.

**Por quê esta prioridade**: Importante para colaboração e debugging remoto, mas não bloqueia MVP básico.

**Teste Independente**: Um trace pode ser exportado como arquivo `.trace.json`, enviado para outro desenvolvedor, e visualizado sem infraestrutura adicional.

**Cenários de Aceitação**:

1. **Dado** um trace carregado, **Quando** desenvolvedor clica "Exportar", **Então** arquivo `.trace.json` é salvo no disco
2. **Dado** um arquivo `.trace.json`, **Quando** desenvolvedor clica "Importar", **Então** trace é carregado e visualizado identicamente
3. **Dado** um arquivo `.trace.json`, **Quando** enviado para colega, **Então** colega consegue abrir sem Jaeger/Datadog/etc.

---

### User Story 4 - Cores Semânticas para Tipo de Etapa (Priority: P2)

**Descrição**: Desenvolvedor quer identificar rapidamente quais etapas são LLM calls, tool calls, ou erros apenas pela cor.

**Por quê esta prioridade**: Melhora legibilidade visual, mas não é crítico para MVP. Pode ser adicionado após core funcionar.

**Teste Independente**: Visualização waterfall mostra diferentes cores por tipo (LLM=Azul, Tool=Verde, Erro=Vermelho). Desenvolvedor identifica um erro apenas pela cor.

**Cenários de Aceitação**:

1. **Dado** um waterfall com múltiplos tipos de etapa, **Quando** desenvolvedor olha, **Então** cores são distintas e consistentes
2. **Dado** uma etapa de erro, **Quando** visualizada, **Então** é claramente vermelha e se destaca
3. **Dado** uma legenda de cores, **Quando** exibida, **Então** desenvolvedor sabe o que cada cor significa

---

### Edge Cases

- **O que acontece com traces muito grandes?** (100+ etapas) - Sistema deve permanecer responsivo (<2s para carregar)
- **E se uma tool executar por muito tempo?** (>30s) - Barra será muito longa, mas a hierarquia ainda fica clara
- **E se múltiplos turnos rodarem em paralelo?** (não esperado) - Sistema assume sequencial; comportamento indefinido
- **E se um trace não tiver metadados de tempo?** - Sistema usa timestamps relativos (0ms como baseline)
- **E se um arquivo .trace.json for corrompido?** - Mensagem clara: "Arquivo inválido, não pôde ser carregado"
- **E se o prompt/resposta for binário ou não-texto?** - Exibe "[Conteúdo binário]" ou hash resumido


## Requirements

### Functional Requirements

- **FR-001**: Sistema DEVE capturar automaticamente conversas multi-turn com timestamps e durações
- **FR-002**: Sistema DEVE apresentar traces em visualização waterfall (barras horizontais ordenadas por tempo)
- **FR-003**: Sistema DEVE permitir expansão/colapso de turns para exploração hierárquica
- **FR-004**: Sistema DEVE exibir duração de cada etapa visualmente (comprimento proporcional ao tempo)
- **FR-005**: Sistema DEVE permitir clique em etapa para abrir painel de detalhes (prompt, resposta, args, resultado)
- **FR-006**: Sistema DEVE truncar prompts/respostas longas (>500 chars) com opção de expandir
- **FR-007**: Sistema DEVE aplicar cores semânticas (LLM=Azul, Tool=Verde, Erro=Vermelho, Lógica=Amarelo)
- **FR-008**: Sistema DEVE exportar traces como arquivo JSON auto-contido
- **FR-009**: Sistema DEVE reimportar arquivos .trace.json para re-visualização
- **FR-010**: Sistema DEVE suportar árvore hierárquica (turns → etapas → sub-etapas aninhadas)
- **FR-011**: Sistema DEVE exibir argumentos de tools em formato JSON estruturado
- **FR-012**: Sistema DEVE mostrar resultado de tools com status (success/error) em cores apropriadas

### Key Entities

- **Trace**: Sessão lógica de interação, contém metadados (id, timestamps, duration) e array de Turns
- **Turn**: Iteração da conversa (input do usuário → processamento → output), contém array de Steps
- **Step**: Operação interna (LLM call, tool call, lógica), com tipo, timestamps, input/output, status
- **Metadata**: Timestamps (start/end), duration_ms, model (para LLM calls), tool_name (para tool calls), status

## Success Criteria

### Measurable Outcomes

- **SC-001**: Um desenvolvedor consegue explicar comportamento da conversa apenas observando o waterfall (sem ler logs)
- **SC-002**: Gargalos de tempo são identificáveis em <10 segundos de visualização
- **SC-003**: Sistema funciona sem infraestrutura externa (Jaeger, Datadog, etc.) - é totalmente local
- **SC-004**: Um trace compartilhado como arquivo .trace.json é visualizável por outro desenvolvedor imediatamente
- **SC-005**: Detalhes de uma etapa aparecem em <1 segundo após clique
- **SC-006**: Traces com até 100 etapas carregam e renderizam em <2 segundos
- **SC-007**: Cores semânticas são imediatamente distinguíveis (desenvolvedor diferencia tipos sem legenda)

## Assumptions

1. Formato JSON é adequado para transporte e armazenamento de traces
2. Sistema será usado para traces com até 100 etapas (limite prático para UI responsiva)
3. Não há suporte para concorrência (um desenvolvedor, um navegador, um trace por vez)
4. Visualização é web-based ou GUI local (não line-of-command)
5. Retenção: arquivos .trace.json ficam no disco; sem cleanup automático
6. Integração com synth-lab via SDK Python que registra eventos

## Out of Scope

- Observabilidade distribuída (Jaeger, Datadog, etc.)
- Armazenamento seguro ou anonimização de dados
- Agregação estatística ou alertas
- Suporte a múltiplos usuários simultaneamente
- Cálculo de tokens ou custo por etapa
