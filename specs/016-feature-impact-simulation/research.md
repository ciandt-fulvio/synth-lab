# Research: Sistema de Simulacao de Impacto de Features

**Date**: 2025-12-23
**Feature**: 016-feature-impact-simulation

## 1. Monte Carlo Simulation com NumPy

### Decision
Usar **NumPy com `default_rng()`** para geração de números aleatórios e operações vetorizadas, sem necessidade de SciPy para o MVP.

### Rationale

1. **NumPy é suficiente para distribuições Beta**:
   - `np.random.Generator.beta(a, b, size=N)` gera amostras eficientemente
   - Implementação em C garante performance para 50k iterações

2. **Performance para 500 synths × 100 execuções**:
   - Operações vetorizadas são 100-1000x mais rápidas que loops Python
   - Padrão recomendado:
     ```python
     rng = np.random.default_rng(seed=42)
     # Gera todas as amostras de uma vez
     samples = rng.beta(a=2.0, b=4.0, size=(500, 100))
     ```

3. **Reprodutibilidade**:
   - Usar `np.random.default_rng(seed=N)` em vez de `np.random.seed()` (legado)
   - Evitar estado global - instanciar generator e passar entre funções
   - Para processamento paralelo: usar `rng.spawn()` para criar geradores filhos

4. **Pitfalls a evitar**:
   - Selecionar distribuições Beta apropriadas por contexto (ex: Beta(2,4) para skew baixo)
   - Verificar convergência com erro padrão ∝ 1/√n
   - Rodar múltiplas simulações com seeds diferentes para calcular intervalos de confiança

### Alternatives Considered

| Abordagem | Prós | Contras | Quando usar |
|-----------|------|---------|-------------|
| NumPy Vectorized (escolhido) | Mais rápido, nativo Python | Funções estatísticas limitadas | Caso padrão |
| SciPy Stats | Funções ricas (PDF, CDF, PPF) | Overhead maior | Se precisar análises avançadas |
| Numba JIT | Velocidade próxima a C | Requer reescrita de código | Se vetorização for insuficiente |

---

## 2. Análise de Regiões do Espaço de Synths

### Decision
Usar **DecisionTreeClassifier do sklearn** com profundidade limitada (max_depth=3-4) para identificar grupos com altas taxas de falha e extrair regras interpretáveis.

### Rationale

1. **Por que Decision Tree**:
   - Naturalmente produz regras interpretáveis ("capability < 0.48 AND trust < 0.4 → failure")
   - Funciona bem com datasets pequenos (< 1000 samples)
   - Não requer normalização de features
   - Feature importance built-in

2. **Configuração recomendada para 500 synths**:
   ```python
   from sklearn.tree import DecisionTreeClassifier

   clf = DecisionTreeClassifier(
       max_depth=4,           # Evita overfitting
       min_samples_leaf=20,   # Mínimo 4% da população por folha
       min_samples_split=40,  # Pelo menos 8% para dividir
       class_weight='balanced'  # Compensa desbalanceamento
   )
   ```

3. **Extração de regras**:
   - Usar `sklearn.tree.export_text()` para formato textual
   - Ou percorrer a árvore manualmente para regras customizadas
   - Filtrar por folhas com alta taxa de falha (> 50%)

4. **Validação**:
   - Cross-validation com k=5 para evitar overfitting
   - Verificar que regras fazem sentido do ponto de vista de domínio

### Alternatives Considered

| Abordagem | Prós | Contras | Quando usar |
|-----------|------|---------|-------------|
| Decision Tree (escolhido) | Regras interpretáveis, robusto | Pode overfit | Caso padrão |
| RIPPER (rule extraction) | Regras diretas | Menos comum em Python | Se precisar regras mais precisas |
| K-Means clustering | Identifica grupos | Sem regras interpretáveis | Exploração inicial |
| SHAP/LIME | Explicações detalhadas | Mais complexo | Análise avançada |

---

## 3. Análise de Sensibilidade (OAT)

### Decision
Implementar **One-At-a-Time (OAT)** com cálculo de delta normalizado e visualização via Tornado diagram.

### Rationale

1. **Metodologia OAT padrão**:
   - Variar uma dimensão por vez (±0.05, ±0.10) mantendo outras em baseline
   - Todas as comparações referenciam mesmo ponto central
   - Atribuição clara: qualquer delta é causado pela dimensão variada

2. **Cálculo de delta/impacto**:
   ```python
   # Delta absoluto
   delta_abs = output(baseline + Δ) - output(baseline)

   # Delta relativo
   delta_rel = (output(baseline + Δ) - output(baseline)) / output(baseline) * 100

   # Índice de sensibilidade
   sensitivity_index = (% mudança output) / (% mudança input)
   ```

3. **Complexidade computacional**:
   - O(n) em vez de O(2^n) para factorial design
   - Para 4 dimensões com ±0.05 e ±0.10: baseline + 16 avaliações (vs 256 para full factorial)

4. **Visualização**:
   - **Tornado diagram** (primário): barras horizontais ranqueadas por magnitude de impacto
   - **Response curves** (secundário): gráficos 2D mostrando relação input-output por dimensão
   - **Tabela de dados**: valores exatos para análise detalhada

### Alternatives Considered

| Abordagem | Prós | Contras | Quando usar |
|-----------|------|---------|-------------|
| OAT (escolhido) | Simples, interpretável, eficiente | Ignora interações | Análise inicial |
| Morris Method | Cobre mais espaço de parâmetros | Mais complexo | Validação pós-OAT |
| Sobol Indices (GSA) | Captura interações | 100-1000x mais execuções | Análise avançada |
| Factorial Design | Mede interações | Explosão combinatória | Quando interações são críticas |

---

## 4. Dependências a Adicionar

### pyproject.toml changes

```toml
# Adicionar ao [project.dependencies]
"numpy>=1.26.0",
"scikit-learn>=1.4.0",
```

### Justificativa

| Dependência | Uso | Tamanho | Alternativa |
|-------------|-----|---------|-------------|
| numpy | Beta distributions, Monte Carlo | Core library | Nenhuma (essencial) |
| scikit-learn | Decision tree for region analysis | 25MB | Implementar manualmente (não vale a pena) |

---

## 5. Schema Extension para Synths

### Novos atributos em simulation_attributes

```json
{
  "simulation_attributes": {
    "observables": {
      "digital_literacy": 0.35,
      "similar_tool_experience": 0.42,
      "motor_ability": 0.85,
      "time_availability": 0.28,
      "domain_expertise": 0.55
    },
    "latent_traits": {
      "capability_mean": 0.42,
      "trust_mean": 0.39,
      "friction_tolerance_mean": 0.35,
      "exploration_prob": 0.38
    }
  }
}
```

### Integração com gensynth

1. Gerar observáveis via distribuições Beta durante `assemble_synth()`
2. Calcular latentes via fórmulas de derivação
3. Traduzir `digital_literacy` para `alfabetizacao_digital` (escala 0-100)
4. Derivar `motor_ability` de `deficiencias.motora.tipo`

---

## 6. Performance Benchmarks Esperados

| Operação | Target | Abordagem |
|----------|--------|-----------|
| Simulação 500×100 | < 30s | NumPy vetorizado |
| Análise de regiões | < 5s | sklearn Decision Tree |
| Sensibilidade (4 dims) | < 10s | OAT com 16 avaliações |
| Geração de synth + attrs | < 100ms | Inline no assemble_synth |

---

## Fontes

- [NumPy Random Generator Best Practices](https://blog.scientific-python.org/numpy/numpy-rng/)
- [NEP 19: Random Number Generator Policy](https://numpy.org/neps/nep-0019-rng-policy.html)
- [sklearn DecisionTreeClassifier](https://scikit-learn.org/stable/modules/tree.html)
- [Sensitivity Analysis - JASSS](https://www.jasss.org/19/1/5.html)
- [Tornado Diagrams](https://en.wikipedia.org/wiki/Tornado_diagram)
