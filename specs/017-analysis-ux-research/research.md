# Research: Sistema de Análise para UX Research

**Feature Branch**: `017-analysis-ux-research`
**Created**: 2025-12-26

---

## Resumo das Decisões

Este documento consolida a pesquisa técnica realizada para definir as escolhas de tecnologia e padrões de implementação.

---

## 1. Bibliotecas de Machine Learning

### 1.1 Clustering (K-Means e Métricas)

**Decisão**: scikit-learn >= 1.4.0

**Rationale**:
- Padrão da indústria para ML em Python
- API estável e bem documentada
- `KMeans`, `StandardScaler`, `silhouette_score` disponíveis nativamente
- Compatível com numpy arrays existentes no projeto
- Mantido ativamente pela comunidade

**Alternativas avaliadas**:
| Biblioteca | Prós | Contras | Decisão |
|------------|------|---------|---------|
| scikit-learn | Padrão, estável, completo | - | ✅ Escolhido |
| HDBSCAN | Melhor para clusters não-esféricos | Dependência adicional, mais complexo | ❌ |
| kmeans-pytorch | GPU acceleration | Overkill para 10k pontos | ❌ |

**Documentação**: https://scikit-learn.org/stable/modules/clustering.html

---

### 1.2 Hierarchical Clustering

**Decisão**: scipy.cluster.hierarchy

**Rationale**:
- `linkage()`, `fcluster()`, `dendrogram()` são funções maduras
- Retorna matriz de linkage no formato padrão (compatível com visualização)
- scipy já é dependência transitiva do projeto (via numpy/scikit-learn)
- Suporta múltiplos métodos de linkage (ward, complete, average, single)

**Alternativas avaliadas**:
| Biblioteca | Prós | Contras | Decisão |
|------------|------|---------|---------|
| scipy.cluster.hierarchy | Completo, dendrograma | - | ✅ Escolhido |
| sklearn AgglomerativeClustering | API sklearn | Não retorna dendrograma | ❌ |
| fastcluster | Mais rápido | Dependência adicional, menos features | ❌ |

**Documentação**: https://docs.scipy.org/doc/scipy/reference/cluster.hierarchy.html

---

### 1.3 Detecção de Outliers (Isolation Forest)

**Decisão**: sklearn.ensemble.IsolationForest

**Rationale**:
- Implementação eficiente e bem testada
- Parâmetro `contamination` intuitivo (% esperado de outliers)
- Retorna `score_samples()` para visualização contínua
- Já incluído no scikit-learn

**Alternativas avaliadas**:
| Biblioteca | Prós | Contras | Decisão |
|------------|------|---------|---------|
| sklearn IsolationForest | Padrão, integrado | - | ✅ Escolhido |
| PyOD | Especializado em outliers, muitos algoritmos | Dependência adicional, overkill | ❌ |
| Local Outlier Factor | Bom para densidade variável | Mais lento, menos interpretável | ❌ |

**Documentação**: https://scikit-learn.org/stable/modules/outlier_detection.html

---

### 1.4 SHAP Values

**Decisão**: shap >= 0.44.0

**Rationale**:
- Única biblioteca oficial para SHAP (SHapley Additive exPlanations)
- `TreeExplainer` otimizado para modelos tree-based (GradientBoosting)
- Gera visualizações prontas (opcional, mas útil para debug)
- Integração nativa com scikit-learn

**Modelo para treinar**:
- `GradientBoostingRegressor` (sklearn)
- Suportado por TreeExplainer (O(n) ao invés de O(2^n))
- Boa capacidade preditiva sem tuning extensivo

**Alternativas avaliadas**:
| Biblioteca | Prós | Contras | Decisão |
|------------|------|---------|---------|
| shap | Oficial, TreeExplainer rápido | - | ✅ Escolhido |
| LIME | Mais simples | Menos preciso, diferente interpretação | ❌ |
| ELI5 | Fácil de usar | Não implementa SHAP | ❌ |

**Documentação**: https://shap.readthedocs.io/en/latest/

---

### 1.5 Partial Dependence Plots

**Decisão**: sklearn.inspection.partial_dependence

**Rationale**:
- Integrado ao scikit-learn
- Compatível com qualquer estimator sklearn
- Retorna grid_values e valores médios para plotar
- Sem dependências adicionais

**Documentação**: https://scikit-learn.org/stable/modules/partial_dependence.html

---

## 2. Cálculos Estatísticos

### 2.1 Correlação de Pearson

**Decisão**: scipy.stats.pearsonr

**Rationale**:
- Retorna coeficiente r e p-value em uma chamada
- Eficiente para datasets médios (< 100k pontos)
- scipy já é dependência do projeto

**Uso**:
```python
from scipy.stats import pearsonr

r, p_value = pearsonr(x_values, y_values)
r_squared = r ** 2
```

**Documentação**: https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html

---

### 2.2 Linha de Tendência (Linear Regression)

**Decisão**: numpy.polyfit ou sklearn.linear_model.LinearRegression

**Rationale**:
- numpy.polyfit é mais simples para regressão linear
- Retorna coeficientes diretamente
- Já disponível no projeto

**Uso**:
```python
import numpy as np

slope, intercept = np.polyfit(x_values, y_values, 1)
trendline_y = slope * x_values + intercept
```

---

## 3. LLM para Insights

### 3.1 Cliente LLM

**Decisão**: OpenAI SDK (já existente em infrastructure/llm_client.py)

**Rationale**:
- Infraestrutura já configurada no projeto
- Tracing com Phoenix já funciona
- Consistência com resto do projeto
- Modelo configurável via environment

**Uso existente**: Verificar `src/synth_lab/infrastructure/llm_client.py`

---

### 3.2 Cache de Insights

**Decisão**: Cache em memória (dicionário por simulation_id + chart_type)

**Rationale**:
- Simples de implementar
- Suficiente para escopo atual (insights não mudam frequentemente)
- Evita dependência de Redis/Memcached
- Invalidado quando simulação é re-executada

**Implementação**:
```python
class InsightService:
    def __init__(self):
        self._cache: dict[str, ChartInsight] = {}

    def _cache_key(self, simulation_id: str, chart_type: str) -> str:
        return f"{simulation_id}:{chart_type}"

    def get_cached(self, simulation_id: str, chart_type: str) -> ChartInsight | None:
        return self._cache.get(self._cache_key(simulation_id, chart_type))

    def set_cache(self, simulation_id: str, chart_type: str, insight: ChartInsight):
        self._cache[self._cache_key(simulation_id, chart_type)] = insight
```

**Alternativas consideradas**:
| Estratégia | Prós | Contras | Decisão |
|------------|------|---------|---------|
| In-memory dict | Simples, sem deps | Perde em restart | ✅ Escolhido |
| SQLite | Persistente | Mais complexo | ❌ (futuro) |
| Redis | Distribuído, TTL | Infra adicional | ❌ |

---

## 4. Dependências Novas

### pyproject.toml additions

```toml
[project]
dependencies = [
    # ... existing deps ...
    "scikit-learn>=1.4.0",
    "shap>=0.44.0",
]
```

### Verificações necessárias

1. **scipy**: Já é dependência transitiva. Verificar versão >= 1.10.0 para `cluster.hierarchy`
2. **numpy**: Já existente. Compatível com sklearn 1.4+
3. **joblib**: Dependência do sklearn para cache de modelos (automático)

---

## 5. Padrões de Implementação

### 5.1 Extração de Features

Todas as análises ML precisam extrair features dos synth_outcomes. Criar helper compartilhado:

```python
def extract_features(
    outcomes: list[dict],
    features: list[str],
    include_outcomes: bool = False
) -> tuple[np.ndarray, list[str]]:
    """
    Extrai matriz de features dos outcomes.

    Returns:
        X: numpy array (n_samples, n_features)
        synth_ids: lista de IDs na mesma ordem
    """
    X = []
    synth_ids = []

    for o in outcomes:
        row = []
        attrs = o.get("synth_attributes", {}).get("latent_traits", {})

        for f in features:
            if f in attrs:
                row.append(attrs[f])
            elif f in o:  # outcome fields
                row.append(o[f])
            else:
                row.append(0.0)  # fallback

        if include_outcomes:
            row.extend([o.get("success_rate", 0), o.get("failed_rate", 0)])

        X.append(row)
        synth_ids.append(o["synth_id"])

    return np.array(X), synth_ids
```

### 5.2 Normalização

K-Means e outros algoritmos requerem features normalizadas:

```python
from sklearn.preprocessing import StandardScaler

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)
```

### 5.3 Lazy Training para SHAP

O modelo para SHAP é treinado na primeira requisição e cacheado:

```python
class ExplainabilityService:
    def __init__(self):
        self._models: dict[str, tuple] = {}  # simulation_id -> (model, explainer, X)

    def _get_or_train_model(self, simulation_id: str, outcomes: list[dict]):
        if simulation_id not in self._models:
            # Train model
            X, y, feature_names = self._prepare_data(outcomes)
            model = GradientBoostingRegressor(n_estimators=100, max_depth=4)
            model.fit(X, y)
            explainer = shap.TreeExplainer(model)
            self._models[simulation_id] = (model, explainer, X, feature_names)

        return self._models[simulation_id]
```

---

## 6. Riscos e Mitigações

| Risco | Impacto | Probabilidade | Mitigação |
|-------|---------|---------------|-----------|
| SHAP lento para muitos synths | Performance degradada | Média | Limitar a 1000 synths para SHAP summary |
| Clustering com poucos synths | Resultados ruins | Alta | Validar n >= 10 antes de executar |
| LLM indisponível | Insights não funcionam | Baixa | Retornar erro gracioso, usar dados brutos |
| Cache memory leak | OOM em produção | Baixa | Limitar cache a 100 simulações, LRU |

---

## 7. Referências

- [scikit-learn User Guide](https://scikit-learn.org/stable/user_guide.html)
- [SHAP Documentation](https://shap.readthedocs.io/en/latest/)
- [scipy.cluster.hierarchy](https://docs.scipy.org/doc/scipy/reference/cluster.hierarchy.html)
- [Isolation Forest Paper](https://cs.nju.edu.cn/zhouzh/zhouzh.files/publication/icdm08b.pdf)
