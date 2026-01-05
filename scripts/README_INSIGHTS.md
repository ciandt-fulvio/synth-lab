# 🔄 Regenerate Insights Script

Script CLI para deletar e regenerar insights de análises quantitativas.

## 🎯 Casos de Uso

- ✅ Testar melhorias nos prompts sem rodar análise completa
- ✅ Corrigir insights que falharam na geração
- ✅ Regenerar insights após mudanças no modelo LLM
- ✅ Debug de prompts específicos

---

## 📋 Comandos Disponíveis

### 1. **Listar insights de um experimento**

```bash
uv run python scripts/regenerate_insights.py list exp_12345678
```

**Saída:**
```
┌────────────────────┬──────────┬─────────────────────────┬──────────────────────┐
│ Chart Type         │ Status   │ Summary                 │ Cache Key            │
├────────────────────┼──────────┼─────────────────────────┼──────────────────────┤
│ try_vs_success     │ ✅ completed │ A análise revela...  │ insight_try_vs_success│
│ shap_summary       │ ✅ completed │ Os atributos mais... │ insight_shap_summary │
│ pca_scatter        │ ⚠️  missing │ Not generated yet    │ insight_pca_scatter  │
│ radar_comparison   │ ✅ completed │ Comparando perfis... │ insight_radar_comparison│
│ extreme_cases      │ ❌ failed    │ Falha ao gerar...    │ insight_extreme_cases│
│ outliers           │ ✅ completed │ Foram identificados..│ insight_outliers     │
└────────────────────┴──────────┴─────────────────────────┴──────────────────────┘

Analysis ID: ana_87654321
Total insights: 5 / 6
```

---

### 2. **Regenerar um insight específico**

```bash
uv run python scripts/regenerate_insights.py regenerate exp_12345678 try_vs_success
```

**O que faz:**
1. Busca dados do gráfico no cache (`try_vs_success`)
2. Deleta insight antigo (se existir)
3. Gera novo insight via LLM
4. Salva no cache
5. Mostra o resultado

**Saída:**
```
🔄 Regenerating insight for try_vs_success...
✅ Insight regenerated successfully!

Summary:
A análise revela que 45% dos usuários (225/500) tentaram usar a feature,
mas apenas 28% obtiveram sucesso. O quadrante "Tentou mas Falhou" concentra
38% dos casos, indicando fricção significativa na experiência...
```

---

### 3. **Regenerar TODOS os insights em paralelo**

```bash
uv run python scripts/regenerate_insights.py regenerate-all exp_12345678
```

**O que faz:**
- Regenera os 6 insights em paralelo (mais rápido)
- Usa asyncio para chamadas LLM concorrentes
- Mostra progresso em tempo real

**Saída:**
```
🔄 Regenerating all 6 insights...

  → Generating try_vs_success...
  → Generating shap_summary...
  → Generating pca_scatter...
  → Generating radar_comparison...
  → Generating extreme_cases...
  → Generating outliers...
  ✅ try_vs_success completed
  ✅ shap_summary completed
  ⚠️  Skipping pca_scatter - no chart data in cache
  ✅ radar_comparison completed
  ✅ extreme_cases completed
  ✅ outliers completed

✅ All insights regenerated!
```

---

### 4. **Deletar um insight (sem regenerar)**

```bash
uv run python scripts/regenerate_insights.py delete exp_12345678 try_vs_success
```

**Útil para:**
- Limpar insights corrompidos
- Testar comportamento quando insight não existe

---

## 🔧 Exemplos de Workflow

### **Exemplo 1: Testar melhorias no prompt**

```bash
# 1. Editar prompt no código
vim src/synth_lab/services/insight_service.py

# 2. Regenerar insight para testar
uv run python scripts/regenerate_insights.py regenerate exp_12345678 try_vs_success

# 3. Ver resultado e iterar
```

---

### **Exemplo 2: Corrigir insight que falhou**

```bash
# 1. Listar insights e ver quais falharam
uv run python scripts/regenerate_insights.py list exp_12345678

# Saída mostra: extreme_cases → ❌ failed

# 2. Regenerar o que falhou
uv run python scripts/regenerate_insights.py regenerate exp_12345678 extreme_cases

# 3. Confirmar sucesso
uv run python scripts/regenerate_insights.py list exp_12345678
```

---

### **Exemplo 3: Regenerar tudo após mudança de modelo**

```bash
# 1. Mudar modelo no código (se necessário)
# INSIGHT_MODEL = "gpt-4.1-mini" → "gpt-4o"

# 2. Regenerar todos os insights
uv run python scripts/regenerate_insights.py regenerate-all exp_12345678

# 3. Verificar resultados
uv run python scripts/regenerate_insights.py list exp_12345678
```

---

## 📊 Chart Types Suportados

O script suporta regeneração dos seguintes insights:

| Chart Type | Descrição | Cache Key |
|------------|-----------|-----------|
| `try_vs_success` | Quadrantes tentativa vs sucesso | `try_vs_success` |
| `shap_summary` | Importância de features (SHAP) | `shap_summary` |
| `pca_scatter` | Segmentação de usuários (PCA) | `pca_scatter` |
| `radar_comparison` | Comparação de perfis de clusters | `radar_comparison` |
| `extreme_cases` | Casos extremos (outliers qualitativos) | `extreme_cases` |
| `outliers` | Outliers estatísticos (Isolation Forest) | `outliers` |

---

## ⚠️ Observações Importantes

### **Pré-requisitos:**
- ✅ Análise precisa estar completa (`status = "completed"`)
- ✅ Cache de gráficos precisa existir (gerado durante análise)
- ✅ `OPENAI_API_KEY` precisa estar configurada

### **Limitações:**
- ❌ Não regenera Executive Summary (use endpoint separado)
- ❌ Não regenera dados dos gráficos (só insights)
- ❌ Requer que a análise já tenha sido executada

### **Custos:**
- Regenerar 1 insight ≈ $0.002 (GPT-4.1-mini)
- Regenerar todos (6 insights) ≈ $0.012
- Executive Summary adicional ≈ $0.005

---

## 🐛 Troubleshooting

### **Erro: "No chart data in cache"**
```bash
⚠️  Skipping pca_scatter - no chart data in cache
```

**Solução:** O gráfico não foi pré-computado. Rode análise completa:
```bash
curl -X POST http://localhost:8000/api/experiments/exp_123/analysis
```

---

### **Erro: "Experiment not found"**
```bash
❌ Experiment exp_12345678 not found
```

**Solução:** Verifique o ID do experimento:
```bash
# Listar experimentos
curl http://localhost:8000/api/experiments
```

---

### **Erro: "Failed to generate insight"**
```bash
❌ Failed to regenerate insight: OpenAI API error
```

**Solução:** Verifique:
1. `OPENAI_API_KEY` está configurada
2. Você tem créditos na conta OpenAI
3. Logs do backend (`/tmp/synth-lab-backend.log`)

---

## 📚 Referências

- **Service:** `src/synth_lab/services/insight_service.py`
- **Prompts:** `insight_service.py:220-391`
- **API Router:** `src/synth_lab/api/routers/insights.py`
- **Spec:** `specs/023-quantitative-ai-insights/spec.md`

---

## 🎨 Customização

Para modificar prompts:
1. Edite métodos `_build_prompt_<chart_type>()` em `insight_service.py`
2. Teste com `regenerate` command
3. Valide resultado
4. Commit mudanças

**Exemplo:**
```python
# src/synth_lab/services/insight_service.py:220

def _build_prompt_try_vs_success(...):
    return f"""
    # CUSTOMIZE AQUI
    Analise de forma mais técnica/profunda/simples...
    """
```

Depois teste:
```bash
uv run python scripts/regenerate_insights.py regenerate exp_123 try_vs_success
```
