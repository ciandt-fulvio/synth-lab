# Research: Simulation-Driven Scenario Exploration

**Feature**: 024-llm-scenario-exploration
**Date**: 2025-12-31

## Research Summary

Este documento consolida as decisoes tecnicas tomadas durante a fase de pesquisa para a implementacao do sistema de exploracao de cenarios via LLM.

---

## 1. Pareto Dominance Implementation

**Decision**: Implementar dominancia de Pareto com 3 dimensoes fixas

**Rationale**:
- O problema de otimizacao multiobjetivo com 3 dimensoes (success_rate, complexity, risk) e bem definido
- Algoritmo de dominancia O(n^2) e suficiente para arvores de 15-25 nos
- Nao ha necessidade de algoritmos mais complexos (NSGA-II, MOEA/D) para este escopo

**Alternatives Considered**:
| Alternative | Why Rejected |
|-------------|--------------|
| NSGA-II | Over-engineering para arvores pequenas (<30 nos) |
| Weighted Sum | Perde informacao de trade-offs entre dimensoes |
| Epsilon-dominance | Complexidade desnecessaria, 3 dimensoes sao gerenciaveis |

**Implementation Notes**:
```python
def dominates(a: ScenarioNode, b: ScenarioNode) -> bool:
    """A domina B se A >= B em todas dimensoes E A > B em pelo menos uma."""
    a_better_or_equal = (
        a.success_rate >= b.success_rate and
        a.complexity <= b.complexity and
        a.risk <= b.risk
    )
    a_strictly_better = (
        a.success_rate > b.success_rate or
        a.complexity < b.complexity or
        a.risk < b.risk
    )
    return a_better_or_equal and a_strictly_better
```

---

## 2. Beam Search Strategy

**Decision**: Beam width K=3 (default), selecao por Δsuccess_rate

**Rationale**:
- K=3 balanceia exploracao vs custo (max 6 nos filhos por iteracao com 2 propostas/no)
- Criterio primario: maior Δsuccess_rate vs parent
- Criterio secundario (desempate): menor risk acumulado
- Criterio terciario: menor distancia do cenario inicial

**Alternatives Considered**:
| Alternative | Why Rejected |
|-------------|--------------|
| K=5 | Custo de LLM muito alto (10+ chamadas/iteracao) |
| K=1 (greedy) | Perde diversidade, pode ficar preso em otimos locais |
| Tournament selection | Adiciona aleatoriedade desnecessaria |

---

## 3. LLM Model Selection

**Decision**: gpt-4.1-mini como modelo inicial

**Rationale**:
- Custo mais baixo que gpt-4o (~10x mais barato por token)
- Qualidade suficiente para propostas estruturadas
- Suporte a JSON mode para output estruturado
- Latencia adequada (< 5s tipico)

**Alternatives Considered**:
| Alternative | Why Rejected |
|-------------|--------------|
| gpt-4o | Custo muito alto para exploracao iterativa |
| gpt-3.5-turbo | Qualidade de propostas pode ser inferior |
| Claude | Requer mudanca de SDK, nao alinhado com stack atual |

**Upgrade Path**: Configuravel via parametro, permitir gpt-4o para exploracoes criticas.

---

## 4. Async/Parallel Execution Pattern

**Decision**: asyncio.gather para execucao paralela de nos irmaos

**Rationale**:
- Nos irmaos (mesmo pai) sao independentes
- asyncio.gather permite execucao concorrente com tratamento de excecoes
- Timeout individual de 30s por chamada LLM
- Compativel com FastAPI async endpoints

**Implementation Pattern**:
```python
async def expand_frontier(self, nodes: list[ScenarioNode]) -> list[ScenarioNode]:
    """Expande todos os nos da fronteira em paralelo."""
    async with asyncio.timeout(120):  # timeout global de 2 min
        tasks = [self._expand_single_node(node) for node in nodes]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    children = []
    for node, result in zip(nodes, results):
        if isinstance(result, Exception):
            self._mark_expansion_failed(node, str(result))
        else:
            children.extend(result)
    return children
```

**Alternatives Considered**:
| Alternative | Why Rejected |
|-------------|--------------|
| ThreadPoolExecutor | Overhead de threads desnecessario para I/O bound |
| Sequential execution | Muito lento (30s * K nos = 90s+ por iteracao) |
| Celery tasks | Over-engineering, nao requer job queue distribuida |

---

## 5. Action Catalog Storage

**Decision**: JSON estatico em arquivo, carregado em memoria

**Rationale**:
- Catalogo e pequeno (5 categorias, ~50 acoes exemplo)
- Nao requer persistencia dinamica no MVP
- Facil de editar e versionar no repositorio
- Incluido no prompt do LLM como contexto

**File Structure**:
```json
{
  "categories": [
    {
      "id": "ux_interface",
      "name": "UX / Interface",
      "examples": [
        {"action": "Tooltip contextual", "typical_impacts": {"complexity": [-0.04, -0.01]}}
      ]
    }
  ]
}
```

**Location**: `data/action_catalog.json`

**Alternatives Considered**:
| Alternative | Why Rejected |
|-------------|--------------|
| PostgreSQL table | Over-engineering para dados estaticos |
| Python constants | Menos flexivel para editar |
| Configuravel por experimento | Complexidade prematura |

---

## 6. Exploration Persistence Strategy

**Decision**: Persistir em PostgreSQL com JSON fields para dados estruturados

**Rationale**:
- Consistente com arquitetura existente (synthlab.db)
- JSON1 extension permite queries em campos JSON se necessario
- Relacao simples: Exploration 1:N ScenarioNode
- Permite consulta de arvore completa ou caminho especifico

**Schema Design**:
- `explorations`: metadados da sessao
- `scenario_nodes`: nos da arvore com self-reference (parent_id)
- Indices em (exploration_id) e (exploration_id, node_status)

**Alternatives Considered**:
| Alternative | Why Rejected |
|-------------|--------------|
| Arvore em memoria apenas | Perde historico ao reiniciar |
| Neo4j | Stack diferente, over-engineering |
| JSON file per exploration | Dificil de consultar, nao transacional |

---

## 7. LLM Prompt Structure

**Decision**: Prompt estruturado com catalogo inline e output JSON schema

**Rationale**:
- Incluir catalogo no prompt ancora o LLM em acoes realistas
- JSON mode garante output parseavel
- System prompt define persona e regras
- User prompt contem contexto especifico do cenario

**Prompt Template**:
```
System: Voce e um Product & UX Strategist. Proponha ate 2 acoes incrementais...

User:
Cenario atual:
- Experimento: {name}
- Hipotese: {hypothesis}
- Parametros: complexity={c}, effort={e}, risk={r}, ttv={t}
- Resultados: success_rate={sr}, fail_rate={fr}, did_not_try={dnt}

Catalogo de acoes disponiveis:
{catalogo_json}

Output esperado (JSON):
[{"action": "...", "category": "...", "rationale": "...", "impacts": {...}}]
```

---

## 8. Error Handling Strategy

**Decision**: Graceful degradation com marcacao de nodes como expansion_failed

**Rationale**:
- Falha em um no nao deve parar toda exploracao
- Apos 3 falhas consecutivas, marca node como expansion_failed
- Continua com outros nos da fronteira
- Log detalhado para debugging

**Error Categories**:
| Error | Handling |
|-------|----------|
| LLM timeout | Retry 1x, depois marca expansion_failed |
| Invalid JSON response | Descarta proposta, loga erro |
| Validation failure (impacts fora de range) | Descarta proposta, loga warning |
| Simulation failure | Marca node expansion_failed, continua |

---

## 9. Reproducibility

**Decision**: Seed propagation para reproducibilidade 100%

**Rationale**:
- Permite re-executar exploracao e obter mesma arvore
- Seed inicial propagado para todas simulacoes
- LLM temperature=0 para determinismo

**Implementation**:
- ExplorationConfig inclui `seed: int | None`
- Se seed fornecido, usado para todas simulacoes e LLM calls
- Se None, gera seed aleatorio e persiste para referencia futura

---

## 10. Integration with Existing Analysis

**Decision**: Reutilizar AnalysisRun existente como baseline

**Rationale**:
- Nao duplica trabalho (analise baseline ja executada)
- Garante consistencia de parametros (n_synths, n_executions, sigma)
- scenario_id vem da analise baseline
- Resultados iniciais vem de aggregated_outcomes

**Flow**:
1. Usuario inicia exploracao informando experiment_id
2. Sistema busca primeira AnalysisRun do experimento (status=completed)
3. Extrai scorecard_params de Experiment.scorecard_data
4. Extrai simulation_results de AnalysisRun.aggregated_outcomes
5. Cria root node com esses dados

---

## Conclusion

Todas as decisoes tecnicas foram tomadas priorizando:
1. **Simplicidade**: Reutilizar componentes existentes
2. **Custo**: gpt-4.1-mini, beam_width=3
3. **Performance**: Execucao paralela de nos irmaos
4. **Reproducibilidade**: Seed propagation
5. **Resiliencia**: Graceful degradation em falhas

Nenhum item de NEEDS CLARIFICATION permanece pendente.
