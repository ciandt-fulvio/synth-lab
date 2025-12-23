# Quickstart: Chat com Synth Entrevistado

**Feature**: 015-synth-chat
**Date**: 2025-12-23

## Visão Geral

Esta feature permite conversar diretamente com um synth após visualizar sua entrevista. O synth mantém memória da entrevista e responde consistente com sua persona.

## Pré-requisitos

- Backend rodando (`uv run uvicorn synth_lab.api.main:app --reload`)
- Frontend rodando (`cd frontend && npm run dev`)
- Pelo menos uma entrevista concluída no sistema

## Fluxo de Uso

### 1. Acessar Entrevista Concluída

1. Acesse a página de detalhes de uma pesquisa: `http://localhost:5173/interviews/{batch_id}`
2. Clique em um card de synth que tenha entrevista concluída
3. O popup de transcrição abrirá mostrando a conversa da entrevista

### 2. Iniciar Chat

1. Role até o final da transcrição no popup
2. Você verá um botão "Conversar com {nome do synth}"
3. Clique no botão para abrir a tela de chat

### 3. Conversar com o Synth

1. A tela de chat abrirá com título "Conversando com {nome}, {idade} anos"
2. Digite sua mensagem no campo de texto na parte inferior
3. Pressione Enter ou clique no botão de enviar
4. Aguarde a resposta do synth (indicador de loading aparecerá)
5. O synth responderá mantendo contexto da entrevista

### 4. Fechar Chat

1. Clique no botão X no canto superior direito
2. Você voltará ao popup da transcrição
3. Se clicar novamente em "Conversar", o histórico do chat será preservado

## Exemplos de Interação

### Exemplo 1: Pergunta sobre a Entrevista

**Contexto**: Entrevista onde synth falou sobre compra na Amazon

```
Usuário: Você ainda usa a panela que comprou?

Synth: Sim, uso quase todos os dias! Comprei ela em agosto, lembra?
Facilitou muito minha vida no restaurante, principalmente pra
preparar feijão e carne mais rápido. Foi uma das melhores compras
que fiz na Amazon.
```

### Exemplo 2: Pergunta sobre Preferências

**Contexto**: Synth com perfil de chef de restaurante

```
Usuário: O que você mais gosta de cozinhar?

Synth: Ah, adoro fazer pratos que levam tempo pra ficar bons,
sabe? Cozidos, assados de panela... A panela de pressão ajuda
muito quando o restaurante tá cheio e preciso agilizar. Mas nos
dias mais calmos, gosto de preparar uma moqueca caprichada.
```

### Exemplo 3: Pergunta Casual

```
Usuário: Como foi seu dia hoje?

Synth: Corrido como sempre! O restaurante tava cheio no almoço,
mas deu tudo certo. Agora tô aproveitando uma folguinha antes
do jantar começar. E você, tudo bem?
```

## API de Chat

### Endpoint

```
POST /api/synths/{synth_id}/chat
```

### Request

```json
{
  "exec_id": "batch_compra-amazon_20251223_085259",
  "message": "Você ainda usa a panela?",
  "chat_history": [
    {
      "role": "user",
      "content": "Oi!",
      "timestamp": "2025-12-23T10:25:00Z"
    },
    {
      "role": "synth",
      "content": "Olá! Prazer em conversar.",
      "timestamp": "2025-12-23T10:25:05Z"
    }
  ]
}
```

### Response

```json
{
  "message": "Sim, uso quase todos os dias!...",
  "timestamp": "2025-12-23T10:30:00Z"
}
```

## Testando via cURL

```bash
# Enviar mensagem para synth
curl -X POST http://localhost:8080/api/synths/synth_abc123/chat \
  -H "Content-Type: application/json" \
  -d '{
    "exec_id": "batch_compra-amazon_20251223_085259",
    "message": "Você ainda usa a panela?",
    "chat_history": []
  }'
```

## Limitações

- **Histórico de sessão**: O histórico do chat é mantido apenas durante a sessão do navegador. Ao fechar a aba, o histórico é perdido.
- **Entrevista concluída**: O chat só está disponível para entrevistas que foram concluídas. Entrevistas em andamento não mostram o botão de chat.
- **Tamanho da mensagem**: Mensagens são limitadas a 2000 caracteres.
- **Histórico de contexto**: Máximo de 50 mensagens no histórico enviado ao LLM.

## Troubleshooting

### Botão "Conversar" não aparece

- Verifique se a entrevista está concluída (status "Concluída" na página)
- Role completamente até o final da transcrição
- Recarregue a página se necessário

### Synth não responde

- Verifique se o backend está rodando
- Confira se a variável OPENAI_API_KEY está configurada
- Verifique os logs do backend para erros

### Resposta muito lenta

- Tempo esperado é < 10 segundos
- Se demorar mais, pode haver problema de rede ou com a API da OpenAI
- Verifique os logs do backend

## Arquivos Relacionados

### Backend
- `src/synth_lab/api/routers/chat.py` - Endpoint de chat
- `src/synth_lab/services/chat/service.py` - Lógica de geração de resposta
- `src/synth_lab/models/chat.py` - Modelos de dados

### Frontend
- `frontend/src/components/chat/SynthChatDialog.tsx` - Dialog do chat
- `frontend/src/components/shared/TranscriptDialog.tsx` - Botão de iniciar chat
- `frontend/src/hooks/use-synth-chat.ts` - Hook de gerenciamento do chat
