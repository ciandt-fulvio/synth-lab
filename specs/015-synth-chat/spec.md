# Feature Specification: Chat com Synth Entrevistado

**Feature Branch**: `015-synth-chat`
**Created**: 2025-12-23
**Status**: Draft
**Input**: User description: "quero poder fazer um chat com um synth entrevistado (tela de /interviews/{id}), no popup que sai dessa tela, talvez ao rolar a conversa até o fim tenha um botao tipo 'conversar com {nome do synth}'. a partir daí deve ser aberto um chat (tela simples, estilo o chat do ChatGPT). No titulo deve aparecer 'Conversando com {nome, idade}', o synth deve se lembrar da entrevista que fez e o histórico de perguntas/resposta, porém esse histórico não deve ser o historico da conversa atual, afinal agora o synth estará conversando comigo e não com o entrevistador."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Iniciar Chat com Synth Entrevistado (Priority: P1)

O usuário está visualizando o popup de transcrição de uma entrevista com um synth (ex: "Entrevista com Stephany, 56 anos"). Ao rolar até o final da conversa, encontra um botão "Conversar com Stephany" que permite iniciar uma conversa direta com o synth, mantendo o contexto da entrevista realizada.

**Why this priority**: Esta é a funcionalidade central da feature - sem ela, não existe chat. O botão de iniciar chat é o ponto de entrada obrigatório para toda a experiência.

**Independent Test**: Pode ser testado abrindo qualquer popup de entrevista concluída, rolando até o final e verificando que o botão aparece e abre a tela de chat.

**Acceptance Scenarios**:

1. **Given** um popup de transcrição de entrevista aberto, **When** o usuário rola até o final da conversa, **Then** um botão "Conversar com {nome do synth}" aparece visível
2. **Given** o botão de chat visível, **When** o usuário clica no botão, **Then** uma nova tela de chat é aberta com o título "Conversando com {nome}, {idade} anos"
3. **Given** uma entrevista não concluída, **When** o usuário visualiza o popup, **Then** o botão de chat NÃO aparece (apenas entrevistas concluídas permitem chat)

---

### User Story 2 - Enviar e Receber Mensagens no Chat (Priority: P1)

O usuário pode enviar mensagens de texto para o synth e receber respostas. A interface é simples e familiar, similar ao ChatGPT, com campo de input na parte inferior e histórico de mensagens acima.

**Why this priority**: Core da funcionalidade de chat - sem troca de mensagens, não há interação útil.

**Independent Test**: Pode ser testado enviando uma mensagem e verificando que a resposta do synth aparece na tela.

**Acceptance Scenarios**:

1. **Given** a tela de chat aberta, **When** o usuário digita uma mensagem e pressiona Enter ou clica em enviar, **Then** a mensagem aparece no histórico como mensagem do usuário
2. **Given** uma mensagem enviada pelo usuário, **When** o sistema processa a mensagem, **Then** uma resposta do synth é exibida no histórico
3. **Given** o synth processando uma resposta, **When** a resposta ainda não chegou, **Then** um indicador de "digitando..." ou loading é exibido
4. **Given** uma mensagem muito longa do synth, **When** a resposta é exibida, **Then** o texto é formatado corretamente com quebras de linha

---

### User Story 3 - Synth Mantém Contexto da Entrevista (Priority: P1)

O synth deve se comportar de forma consistente com sua persona e lembrar do conteúdo da entrevista que participou. Ele fala consigo mesmo como o entrevistado, não como um assistente.

**Why this priority**: A diferenciação desta feature é justamente o synth manter memória da entrevista. Sem isso, seria um chat genérico sem valor agregado.

**Independent Test**: Pode ser testado perguntando ao synth sobre algo que ele mencionou na entrevista e verificando que ele se lembra.

**Acceptance Scenarios**:

1. **Given** uma entrevista onde o synth falou sobre comprar uma panela de pressão na Amazon, **When** o usuário pergunta "Você ainda usa a panela?", **Then** o synth responde de forma contextualizada sobre a panela mencionada na entrevista
2. **Given** o chat iniciado, **When** o usuário pergunta sobre a experiência do synth, **Then** o synth responde em primeira pessoa como o entrevistado (não como assistente de IA)
3. **Given** a persona do synth com características específicas (idade, profissão, personalidade), **When** o synth responde, **Then** as respostas são consistentes com sua persona

---

### User Story 4 - Histórico de Chat Separado da Entrevista (Priority: P1)

O histórico da conversa atual (chat) é completamente separado do histórico da entrevista. A entrevista serve como contexto/memória do synth, mas as mensagens exibidas no chat são apenas as da conversa atual.

**Why this priority**: Essencial para a experiência do usuário - a separação clara entre entrevista e chat evita confusão e mantém a integridade dos dados originais.

**Independent Test**: Pode ser testado verificando que ao iniciar o chat, a tela começa vazia (sem mensagens da entrevista) e só mostra as mensagens trocadas no chat.

**Acceptance Scenarios**:

1. **Given** o chat recém-aberto, **When** a tela é renderizada, **Then** o histórico de mensagens está vazio (não mostra as mensagens da entrevista)
2. **Given** mensagens trocadas no chat, **When** o usuário fecha e reabre o chat, **Then** o histórico do chat é preservado separadamente
3. **Given** o chat aberto, **When** o usuário volta para o popup da entrevista, **Then** as mensagens originais da entrevista continuam intactas

---

### User Story 5 - Fechar e Voltar do Chat (Priority: P1)

O usuário pode fechar a tela de chat e voltar para o popup de transcrição da entrevista ou para a página de detalhes da pesquisa.

**Why this priority**: Navegação essencial para completar o fluxo de uso - sem ela o usuário ficaria preso na tela de chat.

**Independent Test**: Pode ser testado clicando no botão de fechar/voltar e verificando que retorna à tela anterior.

**Acceptance Scenarios**:

1. **Given** a tela de chat aberta, **When** o usuário clica no botão de fechar (X), **Then** o chat é fechado e o usuário volta ao popup da entrevista
2. **Given** o chat fechado, **When** o usuário clica novamente em "Conversar com {synth}", **Then** o chat reabre com o histórico preservado da sessão

---

### Edge Cases

- O que acontece quando a conexão é perdida durante o envio de mensagem? Sistema deve exibir erro e permitir reenvio.
- Como o sistema lida quando o synth não tem dados completos de persona? Usa valores padrão e continua funcionando.
- O que acontece se o usuário tentar iniciar chat com synth de entrevista em andamento? Botão não aparece até conclusão.
- Como lidar com múltiplas abas/sessões de chat simultâneas para o mesmo synth? Cada sessão mantém seu próprio histórico de chat.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Sistema DEVE exibir botão "Conversar com {nome}" ao final do popup de transcrição de entrevistas concluídas
- **FR-002**: Sistema DEVE abrir tela de chat dedicada ao clicar no botão de conversar
- **FR-003**: Tela de chat DEVE exibir título "Conversando com {nome}, {idade} anos"
- **FR-004**: Sistema DEVE permitir envio de mensagens via campo de texto com botão de envio e atalho Enter
- **FR-005**: Sistema DEVE exibir respostas do synth no histórico de chat
- **FR-006**: Sistema DEVE indicar visualmente quando o synth está processando uma resposta (loading/digitando)
- **FR-007**: Synth DEVE manter contexto da entrevista original ao responder (memória da conversa anterior)
- **FR-008**: Synth DEVE responder em primeira pessoa consistente com sua persona (idade, profissão, personalidade)
- **FR-009**: Histórico do chat DEVE ser independente do histórico da entrevista
- **FR-010**: Sistema DEVE preservar histórico do chat durante a sessão do usuário
- **FR-011**: Sistema DEVE permitir fechar o chat e retornar ao popup da entrevista
- **FR-012**: Botão de chat NÃO DEVE aparecer em entrevistas não concluídas

### Key Entities

- **ChatSession**: Representa uma sessão de chat entre usuário e synth, contendo: synth_id, exec_id (referência à entrevista), lista de mensagens, timestamps
- **ChatMessage**: Mensagem individual no chat, contendo: remetente (user/synth), texto, timestamp
- **InterviewContext**: Contexto da entrevista usado como memória do synth, incluindo: transcrição completa, dados da persona do synth

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Usuário consegue iniciar chat com synth em menos de 3 cliques a partir do popup de entrevista
- **SC-002**: Tempo de resposta do synth é inferior a 10 segundos para mensagens típicas
- **SC-003**: 100% das respostas do synth são consistentes com a persona definida
- **SC-004**: Synth demonstra memória da entrevista em pelo menos 90% das perguntas relacionadas ao conteúdo da entrevista
- **SC-005**: Interface de chat é intuitiva ao ponto de não requerer instruções para uso

## Assumptions

- A entrevista deve estar concluída para permitir chat (transcription_completed ou execution_completed)
- O histórico de chat é mantido apenas durante a sessão do navegador (não persiste entre sessões)
- O synth utiliza modelo de linguagem para gerar respostas contextualizadas
- A persona do synth já está definida e disponível no sistema
- O usuário interage em português brasileiro
