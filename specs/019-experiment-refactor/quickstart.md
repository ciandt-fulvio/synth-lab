# Quickstart: Modelo Experimento-Análise-Entrevista

## Visão Geral

Este guia explica como usar o novo modelo de dados onde:
- **Experimento** é o hub central com scorecard embutido
- **Análise Quantitativa** é única por experimento (1:1)
- **Entrevistas** podem ser múltiplas por experimento (N:1)

## Fluxo Típico de Uso

```
1. Criar Experimento (com nome, hipótese, descrição)
        ↓
2. Preencher Scorecard (manual ou via "Estimar com IA")
        ↓
3. Executar Análise Quantitativa
        ↓
4. Analisar Resultados (ver regiões de alto risco)
        ↓
5. Disparar Entrevistas (com synths sugeridos ou manuais)
        ↓
6. Acompanhar Entrevistas em Tempo Real (SSE)
        ↓
7. Gerar Resumo e Insights
```

## Exemplos de Uso

### 1. Criar Experimento com Scorecard

```bash
# Criar experimento básico
curl -X POST http://localhost:8000/api/experiments \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Novo Checkout Mobile",
    "hypothesis": "Simplificar o checkout aumentará conversão em 20%",
    "description": "Redesign do fluxo de checkout para dispositivos móveis com menos etapas"
  }'

# Resposta: { "id": "exp_a1b2c3d4", ... }
```

### 2. Estimar Scorecard com IA

```bash
# Estimar dimensões baseado na descrição
curl -X POST http://localhost:8000/api/experiments/exp_a1b2c3d4/estimate-scorecard

# Resposta com dimensões estimadas:
# {
#   "complexity": { "score": 0.35, "rules_applied": ["mobile-first", "fewer-steps"] },
#   "initial_effort": { "score": 0.4 },
#   "perceived_risk": { "score": 0.25 },
#   "time_to_value": { "score": 0.7 },
#   "justification": "Feature de baixa complexidade com alto potencial de impacto...",
#   "impact_hypotheses": ["Redução de abandono de carrinho", ...]
# }
```

### 3. Salvar Scorecard no Experimento

```bash
# Atualizar experimento com scorecard
curl -X PUT http://localhost:8000/api/experiments/exp_a1b2c3d4/scorecard \
  -H "Content-Type: application/json" \
  -d '{
    "feature_name": "Checkout Mobile Simplificado",
    "description_text": "Fluxo de checkout em 3 etapas para mobile",
    "complexity": { "score": 0.35 },
    "initial_effort": { "score": 0.4 },
    "perceived_risk": { "score": 0.25 },
    "time_to_value": { "score": 0.7 }
  }'
```

### 4. Executar Análise Quantitativa

```bash
# Executar análise (substitui análise anterior se existir)
curl -X POST http://localhost:8000/api/experiments/exp_a1b2c3d4/analysis \
  -H "Content-Type: application/json" \
  -d '{
    "n_synths": 500,
    "n_executions": 100
  }'

# Resposta:
# {
#   "id": "ana_e5f6g7h8",
#   "status": "running",
#   "started_at": "2025-12-27T10:00:00Z"
# }
```

### 5. Verificar Resultados da Análise

```bash
# Obter análise (aguardar status "completed")
curl http://localhost:8000/api/experiments/exp_a1b2c3d4/analysis

# Resposta quando completa:
# {
#   "id": "ana_e5f6g7h8",
#   "status": "completed",
#   "aggregated_outcomes": {
#     "did_not_try_rate": 0.15,
#     "failed_rate": 0.25,
#     "success_rate": 0.60
#   }
# }
```

### 6. Obter Sugestões de Entrevista

```bash
# Synths sugeridos baseado em regiões de alto risco
curl http://localhost:8000/api/experiments/exp_a1b2c3d4/analysis/interview-suggestions

# Resposta:
# {
#   "suggestions": [
#     { "synth_id": "syn_123", "synth_name": "Maria", "reason": "Alta taxa de falha", "failure_rate": 0.8 },
#     { "synth_id": "syn_456", "synth_name": "João", "reason": "Baixa literacia digital", "failure_rate": 0.7 }
#   ]
# }
```

### 7. Disparar Entrevistas

```bash
# Criar rodada de entrevistas com synths sugeridos
curl -X POST http://localhost:8000/api/experiments/exp_a1b2c3d4/interviews \
  -H "Content-Type: application/json" \
  -d '{
    "topic_name": "usabilidade-checkout",
    "synth_ids": ["syn_123", "syn_456"],
    "max_turns": 6
  }'

# Resposta:
# {
#   "exec_id": "res_i9j0k1l2",
#   "status": "running"
# }
```

### 8. Acompanhar Entrevistas via SSE

```javascript
// Frontend: Conectar ao stream SSE
const eventSource = new EventSource('/api/research/res_i9j0k1l2/stream');

eventSource.addEventListener('message', (event) => {
  const data = JSON.parse(event.data);
  console.log(`[${data.speaker}] ${data.text}`);
});

eventSource.addEventListener('interview_completed', (event) => {
  const data = JSON.parse(event.data);
  console.log(`Entrevista com ${data.synth_id} finalizada (${data.total_turns} turnos)`);
});

eventSource.addEventListener('transcription_completed', (event) => {
  const data = JSON.parse(event.data);
  console.log(`Todas entrevistas finalizadas: ${data.successful_count} sucesso, ${data.failed_count} falhas`);
});

eventSource.addEventListener('execution_completed', () => {
  console.log('Processamento completo!');
  eventSource.close();
});
```

### 9. Gerar Resumo

```bash
# Gerar resumo das entrevistas
curl -X POST http://localhost:8000/api/research/res_i9j0k1l2/summary

# Obter resumo
curl http://localhost:8000/api/research/res_i9j0k1l2/summary

# Resposta:
# {
#   "content": "## Resumo das Entrevistas\n\n### Principais Descobertas\n..."
# }
```

## Diferenças do Modelo Anterior

| Aspecto | Antes | Agora |
|---------|-------|-------|
| Scorecard | Entidade separada (`feature_scorecards`) | Embutido no experimento (`scorecard_data`) |
| Simulações | Múltiplas por experimento | Uma análise por experimento (1:1) |
| Nomenclatura | "Simulação" | "Análise Quantitativa" |
| Sugestões | Manual | Baseada em regiões de alto risco |
| SSE | Disponível | Disponível (verificar conexão frontend) |

## Terminologia

| Termo | Descrição |
|-------|-----------|
| **Experimento** | Hub central que agrupa scorecard, análise e entrevistas |
| **Scorecard** | Dimensões que descrevem complexidade, esforço, risco e valor |
| **Análise Quantitativa** | Simulação Monte Carlo que estima taxas de adoção |
| **Entrevista** | Conversa com synths para entender barreiras qualitativas |
| **Synth** | Persona sintética gerada para representar usuários |
| **SSE** | Server-Sent Events para streaming em tempo real |

## Troubleshooting

### SSE não conecta

1. Verificar URL: deve ser `/api/research/{exec_id}/stream`
2. Verificar CORS: backend deve permitir origem do frontend
3. Verificar proxy Vite: deve redirecionar `/api` para backend
4. Usar DevTools Network para ver conexão SSE

### Análise não executa

1. Verificar se experimento tem scorecard preenchido
2. Verificar se não há análise já em execução (`status: running`)

### Entrevistas sem streaming

1. Verificar se `status` é `running` (não `completed`)
2. Se já completou, mensagens vêm como replay no início do stream
