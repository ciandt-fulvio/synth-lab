# Data Model: Analysis Tabs Refactor

**Feature**: 001-analysis-tabs-refactor
**Date**: 2025-12-29

## Overview

Esta feature usa entidades existentes do sistema. Não cria novos modelos de dados, apenas reorganiza a UI e adiciona uma nova operação de criação de entrevista automática.

## Existing Entities (No Changes)

### Synth
Representa uma persona sintética gerada para simulação de Monte Carlo.

**Attributes**:
- `id`: string - Identificador único
- `name`: string - Nome gerado
- `attributes`: dict - Capacidade, confiança, tolerância a fricção
- `outcomes`: list - Resultados de tentativas e sucessos
- `success_rate`: float - Taxa de sucesso calculada

### Interview
Sessão de perguntas e respostas com synths específicos.

**Attributes**:
- `id`: string - Identificador único
- `experiment_id`: string - ID do experimento associado
- `synth_ids`: list[string] - IDs dos synths entrevistados
- `num_turns`: int - Número de turnos de perguntas
- `status`: string - pending | in_progress | completed | failed
- `created_at`: datetime
- `completed_at`: datetime | null

### ExtremeCase
Representa casos extremos identificados (top/bottom performers).

**Attributes**:
- `synth_id`: string
- `success_rate`: float
- `category`: string - "top_performer" | "bottom_performer"
- `rank`: int - Posição no ranking (1-5)

### Outlier
Representa synths com comportamento estatisticamente anômalo.

**Attributes**:
- `synth_id`: string
- `anomaly_score`: float - Score de anomalia
- `method`: string - "zscore" | "isolation_forest"
- `features_contributing`: list[string] - Features que contribuem para anomalia

## New Operations (No New Entities)

### Auto-Interview Creation
**Input**:
```python
{
  "experiment_id": str,
  "synth_ids": list[str],  # 10 synths (5 top + 5 bottom)
  "num_turns": int = 4     # Fixed value
}
```

**Output**:
```python
{
  "interview_id": str,
  "status": "pending",
  "synth_count": 10,
  "created_at": datetime
}
```

**Business Rules**:
- MUST select exactly 5 top performers AND 5 bottom performers
- num_turns is FIXED at 4 (não configurável via UI)
- Interview creation is asynchronous (status starts as "pending")
- User receives link to interview detail page after creation

## Relationships

```
Experiment 1→* Synth
Experiment 1→* Interview
Experiment 1→* ExtremeCase
Experiment 1→* Outlier
Interview *→* Synth (via synth_ids)
```

## Notes

- Esta feature NÃO altera schemas de banco de dados
- Esta feature NÃO adiciona novos campos em entidades existentes
- Auto-interview usa lógica de criação de interview existente
- ExtremeCase e Outlier são queries/views sobre dados de Synth existentes
