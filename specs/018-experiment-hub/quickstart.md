# Quickstart: Experiment Hub

**Feature**: 018-experiment-hub
**Date**: 2025-12-27

## Visão Geral

O Experiment Hub reorganiza a navegação do SynthLab para centralizar o conceito de **Experimento** como container principal. Cada experimento representa uma feature ou hipótese a ser testada, contendo simulações (análise quantitativa) e entrevistas (análise qualitativa).

## Pré-requisitos

- Backend rodando: `uv run uvicorn synth_lab.api.main:app --reload`
- Frontend rodando: `cd frontend && npm run dev`
- Banco de dados inicializado (cria automaticamente na primeira execução)

---

## Fluxo Básico

### 1. Criar Experimento

**Via API:**
```bash
curl -X POST http://localhost:8000/experiments \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Novo Fluxo de Checkout",
    "hypothesis": "Reduzir etapas do checkout aumentará conversão em 15%",
    "description": "Baseado em feedback de usuários e análise de abandono"
  }'
```

**Resposta:**
```json
{
  "id": "exp_a1b2c3d4",
  "name": "Novo Fluxo de Checkout",
  "hypothesis": "Reduzir etapas do checkout aumentará conversão em 15%",
  "description": "Baseado em feedback de usuários...",
  "simulation_count": 0,
  "interview_count": 0,
  "created_at": "2025-12-27T10:30:00Z",
  "updated_at": null,
  "simulations": [],
  "interviews": []
}
```

**Via Frontend:**
1. Acesse a home (`/`)
2. Clique em **"+ Novo Experimento"**
3. Preencha nome e hipótese
4. Clique em **"Criar"**

---

### 2. Listar Experimentos

**Via API:**
```bash
curl "http://localhost:8000/experiments/list?limit=10&offset=0"
```

**Resposta:**
```json
{
  "data": [
    {
      "id": "exp_a1b2c3d4",
      "name": "Novo Fluxo de Checkout",
      "hypothesis": "Reduzir etapas...",
      "simulation_count": 2,
      "interview_count": 1,
      "created_at": "2025-12-27T10:30:00Z"
    }
  ],
  "pagination": {
    "total": 1,
    "limit": 10,
    "offset": 0,
    "has_next": false,
    "has_prev": false
  }
}
```

**Via Frontend:**
A home (`/`) exibe automaticamente a lista de experimentos em cards.

---

### 3. Criar Simulação no Experimento

**Via API:**
```bash
curl -X POST http://localhost:8000/experiments/exp_a1b2c3d4/scorecards \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "feature_name": "Novo Checkout",
      "dimensions": [...]
    }
  }'
```

**Via Frontend:**
1. Acesse o detalhe do experimento (`/experiments/exp_a1b2c3d4`)
2. Na seção **"Simulações"**, clique em **"+ Nova Simulação"**
3. Configure o scorecard e execute

---

### 4. Criar Entrevista no Experimento

**Via API:**
```bash
curl -X POST http://localhost:8000/experiments/exp_a1b2c3d4/interviews \
  -H "Content-Type: application/json" \
  -d '{
    "topic_name": "checkout-experience",
    "synth_count": 15,
    "model": "gpt-5-mini",
    "max_turns": 6
  }'
```

**Via Frontend:**
1. Acesse o detalhe do experimento (`/experiments/exp_a1b2c3d4`)
2. Na seção **"Entrevistas"**, clique em **"+ Nova Entrevista"**
3. Selecione tópico e configure parâmetros

---

### 5. Ver Detalhe do Experimento

**Via API:**
```bash
curl http://localhost:8000/experiments/exp_a1b2c3d4
```

**Resposta:**
```json
{
  "id": "exp_a1b2c3d4",
  "name": "Novo Fluxo de Checkout",
  "hypothesis": "Reduzir etapas...",
  "description": "Baseado em feedback...",
  "simulation_count": 2,
  "interview_count": 1,
  "created_at": "2025-12-27T10:30:00Z",
  "simulations": [
    {
      "id": "sim_xyz789",
      "scenario_id": "base",
      "status": "completed",
      "has_insights": true,
      "score": 72.5
    }
  ],
  "interviews": [
    {
      "exec_id": "exec_abc123",
      "topic_name": "checkout-experience",
      "status": "completed",
      "synth_count": 15,
      "has_summary": true,
      "has_prfaq": false
    }
  ]
}
```

---

## Synth Groups

### Listar Grupos

```bash
curl http://localhost:8000/synth-groups
```

### Criar Grupo (Manual)

```bash
curl -X POST http://localhost:8000/synth-groups \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Geração Dezembro 2025",
    "description": "Synths para testes de checkout"
  }'
```

### Gerar Synths com Grupo

```bash
curl -X POST http://localhost:8000/synths/generate \
  -H "Content-Type: application/json" \
  -d '{
    "count": 50,
    "synth_group_id": "grp_a1b2c3d4"
  }'
```

Se `synth_group_id` não for fornecido, um novo grupo será criado automaticamente.

---

## Navegação (Frontend)

### Rotas Disponíveis

| Rota | Página | Descrição |
|------|--------|-----------|
| `/` | ExperimentList | Lista de todos os experimentos |
| `/experiments/:id` | ExperimentDetail | Detalhe com simulações e entrevistas |
| `/experiments/:id/simulations/:simId` | SimulationDetail | Detalhe da simulação |
| `/experiments/:id/interviews/:execId` | InterviewDetail | Detalhe da entrevista |
| `/synths` | SynthCatalog | Catálogo de synths (menu secundário) |

### Navegação por Cliques

```
Home (/)
   |
   +-- [Card de Experimento] --> /experiments/:id
           |
           +-- [Card de Simulação] --> /experiments/:id/simulations/:simId
           |
           +-- [Card de Entrevista] --> /experiments/:id/interviews/:execId

Header: [Synths icon] --> /synths
```

---

## Verificação

### Testar API

```bash
# Health check
curl http://localhost:8000/health

# Listar experimentos (deve retornar lista vazia ou com dados)
curl http://localhost:8000/experiments/list

# Criar experimento
curl -X POST http://localhost:8000/experiments \
  -H "Content-Type: application/json" \
  -d '{"name": "Teste", "hypothesis": "Hipótese de teste"}'

# Verificar que foi criado
curl http://localhost:8000/experiments/list
```

### Testar Frontend

1. Acesse `http://localhost:8080/`
2. Verifique que a home mostra a lista de experimentos
3. Clique em **"+ Novo Experimento"** e crie um
4. Clique no card do experimento para ver o detalhe
5. Verifique que o ícone de Synths no header leva para `/synths`

---

## Troubleshooting

### Erro 404 ao acessar experimento
- Verifique se o ID existe: `curl http://localhost:8000/experiments/list`
- O formato do ID deve ser `exp_` + 8 caracteres hex

### Simulação/Entrevista sem experiment_id
- Todas as simulações e entrevistas devem ser criadas via `/experiments/:id/scorecards` ou `/experiments/:id/interviews`
- Endpoints antigos diretos requerem `experiment_id` no body

### Synths sem grupo
- Synths existentes antes da migração precisam ser associados a um grupo
- Use a query: `UPDATE synths SET synth_group_id = 'grp_default' WHERE synth_group_id IS NULL`
