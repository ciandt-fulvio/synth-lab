# Research: Chat com Synth Entrevistado

**Feature**: 015-synth-chat
**Date**: 2025-12-23

## Decision 1: Arquitetura de Chat Backend

**Decision**: Utilizar endpoint REST síncrono para envio de mensagens, sem SSE para o chat.

**Rationale**:
- O chat é uma interação 1:1 simples (usuário envia mensagem, aguarda resposta)
- Diferente das entrevistas que têm múltiplos synths e eventos concorrentes
- Simplicidade de implementação: POST envia mensagem, resposta vem no corpo
- Frontend pode mostrar loading enquanto aguarda resposta (<10s conforme SC-002)

**Alternatives Considered**:
- SSE bidirectional: Complexidade desnecessária para interação 1:1
- WebSocket: Overhead de conexão persistente para chat ocasional
- Streaming response: Poderia ser adicionado futuramente se necessário

## Decision 2: Gerenciamento de Contexto/Memória do Synth

**Decision**: Enviar contexto completo em cada requisição (transcrição + histórico do chat).

**Rationale**:
- Padrão stateless simplifica backend e scaling
- Contexto é construído no frontend e enviado ao backend
- Transcrição da entrevista + mensagens do chat formam o contexto
- LLM recebe tudo e gera resposta contextualizada

**Alternatives Considered**:
- Sessão persistente no backend: Adiciona complexidade de gerenciamento de estado
- Cache de contexto: Premature optimization para volume esperado

## Decision 3: Estrutura do Prompt do Synth no Chat

**Decision**: Reutilizar `format_synth_profile()` existente + adicionar transcrição como memória.

**Rationale**:
- `format_synth_profile()` já formata persona completa do synth
- Adicionar seção "MEMÓRIA DA ENTREVISTA" com transcrição
- Adicionar seção "CONVERSA ATUAL" com histórico do chat
- Instruções claras: responder em primeira pessoa, como o entrevistado

**Format**:
```
VOCÊ É: {synth_profile}

MEMÓRIA DA ENTREVISTA:
{transcript_messages}

CONVERSA ATUAL:
{chat_messages}

INSTRUÇÕES: Você está conversando diretamente com um usuário.
Responda em primeira pessoa, mantendo sua persona e lembrando da entrevista.
```

## Decision 4: Armazenamento do Histórico de Chat

**Decision**: Histórico mantido apenas no estado do frontend (sessão do navegador).

**Rationale**:
- Spec define: "histórico de chat é mantido apenas durante a sessão do navegador"
- Simplifica implementação: sem nova tabela no banco
- Chat é exploratório, não precisa de auditoria/persistência
- Usuário pode fechar e reabrir, histórico preservado via React state

**Alternatives Considered**:
- Persistir no PostgreSQL: Adiciona complexidade sem valor claro
- LocalStorage: Poderia ser adicionado futuramente se necessário

## Decision 5: Interface do Chat (Frontend)

**Decision**: Criar componente `SynthChatDialog` que abre sobre o `TranscriptDialog`.

**Rationale**:
- Fluxo: TranscriptDialog → botão "Conversar" → SynthChatDialog
- Dialog sobre dialog mantém contexto visual
- Estilo ChatGPT: input fixo na parte inferior, mensagens scrolláveis acima
- Reutilizar padrões de UI existentes (shadcn/ui Dialog, Input, Button)

**UI Elements**:
- Header: "Conversando com {nome}, {idade} anos" + botão fechar (X)
- Body: Lista de mensagens (user à direita, synth à esquerda)
- Footer: Input + botão enviar + indicador de loading

## Decision 6: Detecção de Entrevista Concluída

**Decision**: Verificar campo `status` do execution ou presença de `transcription_completed` event.

**Rationale**:
- FR-012: Botão de chat NÃO deve aparecer em entrevistas não concluídas
- Status "completed" ou "transcription_completed" indica que entrevista terminou
- TranscriptDialog já recebe dados de transcript que só existem após conclusão

**Implementation**:
- Se `transcript.messages` existe e tem conteúdo → entrevista concluída
- Alternativa: verificar `execution.status === 'completed'`

## Decision 7: Modelo LLM para Respostas do Chat

**Decision**: Utilizar mesmo modelo configurado para entrevistas (gpt-4o-mini default).

**Rationale**:
- Consistência de comportamento entre entrevista e chat
- `LLMClient` já está configurado e testado
- Reutilizar infraestrutura de retry e token tracking

**Alternatives Considered**:
- Modelo diferente para chat: Sem justificativa clara para diferenciação

## Technical Stack Summary

| Component | Technology | Justification |
|-----------|------------|---------------|
| Backend API | FastAPI + Pydantic | Padrão do projeto |
| LLM Integration | OpenAI SDK via LLMClient | Reutiliza infraestrutura existente |
| Frontend State | React useState + useRef | Simples para estado de sessão |
| Data Fetching | React Query useMutation | Padrão para POST requests |
| UI Components | shadcn/ui Dialog, Input, Button | Consistência visual |
| Styling | Tailwind CSS | Padrão do projeto |

## API Design Preview

```
POST /api/synths/{synth_id}/chat
Request:
{
  "exec_id": "batch_xxx",
  "message": "Você ainda usa a panela?",
  "chat_history": [
    {"role": "user", "content": "Oi!"},
    {"role": "synth", "content": "Olá! Prazer em conversar."}
  ]
}

Response:
{
  "message": "Sim, uso quase todos os dias!...",
  "timestamp": "2025-12-23T10:30:00Z"
}
```

## Files to Create/Modify

### Backend (New)
- `src/synth_lab/api/routers/chat.py` - Novo router para chat
- `src/synth_lab/services/chat/` - Novo service para lógica de chat
- `src/synth_lab/models/chat.py` - Modelos Pydantic para chat

### Frontend (New)
- `frontend/src/components/chat/SynthChatDialog.tsx` - Dialog principal
- `frontend/src/components/chat/ChatMessage.tsx` - Componente de mensagem
- `frontend/src/components/chat/ChatInput.tsx` - Input de mensagem
- `frontend/src/hooks/use-synth-chat.ts` - Hook para gerenciar chat
- `frontend/src/services/chat-api.ts` - Cliente API

### Frontend (Modify)
- `frontend/src/components/shared/TranscriptDialog.tsx` - Adicionar botão "Conversar"
