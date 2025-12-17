# Quickstart: Mini-Jaeger Local para Conversas LLM Multi-turn

**Feature**: 008-trace-visualizer | **Date**: 2025-12-17 | **Phase**: 1 (Design)

## Visão Geral

Este guia mostra como usar o trace visualizer para registrar e visualizar conversas multi-turn com LLMs.

**O que você vai fazer**:
1. Instrumentar código para registrar traces
2. Executar conversa e gerar arquivo `.trace.json`
3. Visualizar trace no navegador
4. Inspecionar detalhes de etapas (prompts, respostas, tool calls)

**Tempo estimado**: 10 minutos

---

## Instalação

O trace visualizer está incluído no synth-lab. Sem dependências externas.

```bash
# Já instalado se você tem synth-lab
uv pip install synth-lab
```

---

## Uso Básico: Registrar uma Conversa

### Passo 1: Importar o Tracer

```python
from synth_lab.trace_visualizer import Tracer
```

### Passo 2: Criar Trace e Instrumentar Código

```python
from synth_lab.trace_visualizer import Tracer, SpanType, SpanStatus

# Criar tracer para conversa
tracer = Tracer(trace_id="conv-weather-demo")

# Iniciar turn (iteração da conversa)
with tracer.start_turn(turn_number=1):

    # Registrar LLM call
    with tracer.start_span(SpanType.LLM_CALL, attributes={
        "prompt": "What is the weather in Paris?",
        "model": "claude-sonnet-4-5"
    }) as span:
        # Simular chamada LLM
        response = "Let me check the weather for you."
        span.set_attribute("response", response)
        span.set_attribute("tokens_input", 8)
        span.set_attribute("tokens_output", 10)

    # Registrar tool call
    with tracer.start_span(SpanType.TOOL_CALL, attributes={
        "tool_name": "get_weather",
        "arguments": {"city": "Paris"}
    }) as span:
        # Simular chamada tool
        result = {"temp": 15, "condition": "cloudy"}
        span.set_attribute("result", result)
        span.set_status(SpanStatus.SUCCESS)

    # Registrar resposta final
    with tracer.start_span(SpanType.LLM_CALL, attributes={
        "prompt": "Format weather response",
        "model": "claude-sonnet-4-5"
    }) as span:
        response = "The weather in Paris is 15°C and cloudy."
        span.set_attribute("response", response)

# Salvar trace
tracer.save_trace("data/traces/weather-demo.trace.json")
print("✅ Trace salvo em weather-demo.trace.json")
```

### Passo 3: Visualizar no Navegador

1. Abrir `logui/index.html` no navegador (Chrome, Firefox, Safari)
2. Clicar em "Load Trace" e selecionar `weather-demo.trace.json`
3. Explorar waterfall: ver timeline de execução
4. Clicar em etapas para ver detalhes (prompts, respostas, argumentos)

**Screenshot esperado**:
```
┌─────────────────────────────────────────────────┐
│ Turn 1                  ███████████████████████ │
│   ├─ LLM Call          ██                       │
│   ├─ Tool Call         ████████████████         │
│   └─ LLM Call          ██                       │
└─────────────────────────────────────────────────┘
```

---

## Exemplo Completo: Conversa Multi-Turn

```python
from synth_lab.trace_visualizer import Tracer, SpanType, SpanStatus
import time

# Criar tracer com metadata opcional
tracer = Tracer(
    trace_id="multi-turn-weather",
    metadata={"user_id": "demo-user", "session": "example"}
)

# Turn 1: Usuário pergunta sobre Paris
with tracer.start_turn(turn_number=1):
    with tracer.start_span(SpanType.LLM_CALL, attributes={
        "prompt": "What is the weather in Paris?",
        "model": "claude-sonnet-4-5"
    }) as span:
        time.sleep(0.5)  # Simular latência LLM
        span.set_attribute("response", "Let me check.")
        span.set_attribute("tokens_input", 8)
        span.set_attribute("tokens_output", 5)

    with tracer.start_span(SpanType.TOOL_CALL, attributes={
        "tool_name": "get_weather",
        "arguments": {"city": "Paris"}
    }) as span:
        time.sleep(1.0)  # Simular latência API
        span.set_attribute("result", {"temp": 15, "condition": "cloudy"})
        span.set_status(SpanStatus.SUCCESS)

# Turn 2: Usuário pergunta sobre previsão
with tracer.start_turn(turn_number=2):
    with tracer.start_span(SpanType.LLM_CALL, attributes={
        "prompt": "What about tomorrow?",
        "model": "claude-sonnet-4-5"
    }) as span:
        time.sleep(0.5)  # Simular latência LLM
        span.set_attribute("response", "I don't have forecast data.")

# Turn 3: Usuário tenta London (com erro)
with tracer.start_turn(turn_number=3):
    with tracer.start_span(SpanType.LLM_CALL, attributes={
        "prompt": "How about London?",
        "model": "claude-sonnet-4-5"
    }) as span:
        time.sleep(0.5)
        span.set_attribute("response", "Let me check London.")

    with tracer.start_span(SpanType.TOOL_CALL, attributes={
        "tool_name": "get_weather",
        "arguments": {"city": "London"}
    }) as span:
        time.sleep(1.0)
        # Simular erro
        span.set_status(SpanStatus.ERROR)
        span.set_attribute("error_message", "API timeout after 1000ms")

    # Registrar erro explicitamente
    with tracer.start_span(SpanType.ERROR, attributes={
        "error_type": "APITimeoutError",
        "error_message": "Weather API did not respond in time"
    }):
        pass

# Salvar e visualizar
tracer.save_trace("data/traces/multi-turn-demo.trace.json")
print(f"✅ Trace salvo: {tracer.trace.duration_ms}ms total")
print(f"   Turns: {len(tracer.trace.turns)}")
print(f"   Total steps: {sum(len(t.steps) for t in tracer.trace.turns)}")
```

**Output esperado**:
```
✅ Trace salvo: 4500ms total
   Turns: 3
   Total steps: 5
```

---

## API Reference Rápida

### Classe `Tracer`

**Construtor**:
```python
tracer = Tracer(
    trace_id="conversation-id",  # Opcional: auto-gerado se omitido
    metadata={"user_id": "123"}   # Opcional: metadados customizados
)
```

**Métodos**:

| Método | Descrição | Exemplo |
|--------|-----------|---------|
| `start_turn(turn_number)` | Inicia novo turn (context manager) | `with tracer.start_turn(1): ...` |
| `start_span(type, attributes)` | Inicia span (context manager) | `with tracer.start_span("llm_call", {...}): ...` |
| `save_trace(path)` | Salva trace em JSON | `tracer.save_trace("trace.json")` |

### Span Types

| Tipo | Quando Usar | Atributos Obrigatórios |
|------|-------------|------------------------|
| `llm_call` | Chamada LLM (prompt → response) | `prompt`, `response`, `model` |
| `tool_call` | Execução de ferramenta | `tool_name`, `arguments` |
| `logic` | Lógica de negócio | `operation` |
| `error` | Operação com erro | `error_type`, `error_message` |

### Span Attributes

**Configurar atributo durante criação**:
```python
with tracer.start_span("llm_call", attributes={"prompt": "..."}) as span:
    pass
```

**Configurar atributo durante execução**:
```python
with tracer.start_span("tool_call", attributes={...}) as span:
    result = call_tool()
    span.set_attribute("result", result)
    span.set_status("success")  # ou "error"
```

---

## Visualização no Navegador

### Abrir UI

1. Navegar até `logui/index.html` no navegador
2. Ou usar servidor local:
   ```bash
   cd ui
   python3 -m http.server 8000
   # Abrir http://localhost:8000
   ```

### Carregar Trace

1. Clicar em "Load Trace" (ou arrastar arquivo `.trace.json`)
2. Trace será renderizado em waterfall

### Navegação

- **Waterfall View**: Timeline horizontal mostrando duração de etapas
- **Expand/Collapse**: Clicar em turn para expandir/colapsar steps
- **Detail Panel**: Clicar em step para ver detalhes (sidebar à direita)
- **Cores**:
  - 🔵 **Azul**: LLM calls
  - 🟢 **Verde**: Tool calls
  - 🔴 **Vermelho**: Errors
  - 🟡 **Amarelo**: Logic/business logic

### Inspecionar Detalhes

Clicar em qualquer step abre painel lateral com:
- **Type**: Tipo da operação
- **Duration**: Tempo de execução
- **Status**: success/error
- **Attributes**: Prompt, response, args, resultado, etc.

**Exemplo - LLM Call**:
```
Type: llm_call
Duration: 3250ms
Status: success

Attributes:
  prompt: "What is the weather in Paris?"
  response: "Let me check the weather for you."
  model: "claude-sonnet-4-5"
```

**Exemplo - Tool Call (Error)**:
```
Type: tool_call
Duration: 1000ms
Status: error

Attributes:
  tool_name: "get_weather"
  arguments: {"city": "London"}
  error_message: "API timeout after 1000ms"
```

---

## Boas Práticas

### 1. Nomear Traces com Contexto

```python
# ✅ BOM: Identificador claro
tracer = Tracer(trace_id="user-123-weather-query")

# ❌ RUIM: Genérico
tracer = Tracer(trace_id="trace-001")
```

### 2. Usar Turns para Iterações

```python
# ✅ BOM: Cada pergunta do usuário = novo turn
with tracer.start_turn(turn_number=1):  # Primeira pergunta
    # ...

with tracer.start_turn(turn_number=2):  # Segunda pergunta
    # ...

# ❌ RUIM: Tudo no mesmo turn
with tracer.start_turn(turn_number=1):
    # ... múltiplas interações sem separação
```

### 3. Capturar Erros Explicitamente

```python
# ✅ BOM: Span de erro explícito
try:
    result = call_api()
except Exception as e:
    with tracer.start_span(
        span_type="error",
        attributes={
            "error_type": type(e).__name__,
            "error_message": str(e)
        }
    ):
        pass

# ❌ RUIM: Erro não registrado no trace
try:
    result = call_api()
except Exception:
    pass  # Erro invisível no trace
```

### 4. Adicionar Contexto em Attributes

```python
# ✅ BOM: Attributes informativos
with tracer.start_span(
    span_type="tool_call",
    attributes={
        "tool_name": "get_weather",
        "arguments": {"city": "Paris", "units": "celsius"},
        "api_endpoint": "https://weather.api/v1/current"
    }
) as span:
    result = get_weather("Paris")
    span.set_attribute("result", result)
    span.set_attribute("api_latency_ms", 1250)

# ❌ RUIM: Attributes mínimos
with tracer.start_span("tool_call", attributes={"tool_name": "tool"}):
    get_weather("Paris")
```

### 5. Truncar Prompts Longos (UI Automático)

UI trunca automaticamente prompts >500 chars (FR-006), mas você pode pré-truncar:

```python
prompt = "..." * 1000  # Muito longo
if len(prompt) > 1000:
    prompt_display = prompt[:1000] + "... [truncated]"
else:
    prompt_display = prompt

with tracer.start_span(
    "llm_call",
    attributes={"prompt": prompt_display}
):
    pass
```

---

## Troubleshooting

### Trace não aparece no UI

**Problema**: Carregou `.trace.json` mas waterfall está vazio.

**Solução**:
1. Verificar JSON válido: `python3 -m json.tool trace.json`
2. Verificar estrutura: pelo menos 1 turn, 1 step por turn
3. Abrir console do navegador (F12) para erros JavaScript

### Arquivo muito grande (>5MB)

**Problema**: Trace com muitas etapas causa lentidão no navegador.

**Solução**:
1. Dividir conversa em múltiplos traces menores
2. Limitar turns por trace (recomendado: <20 turns)
3. Truncar prompts/responses longos antes de salvar

### Timestamps incorretos

**Problema**: Duração de steps não bate com expectativa.

**Solução**:
1. Verificar que context managers (`with`) são usados corretamente
2. Verificar que `start_span` é chamado ANTES da operação
3. Timestamps são em UTC (ISO 8601)

### UI não carrega (CORS error)

**Problema**: `file://` protocol bloqueado pelo navegador.

**Solução**:
```bash
# Usar servidor local
cd ui
python3 -m http.server 8000
# Abrir http://localhost:8000
```

---

## Limitações Conhecidas

| Limitação | Impacto | Mitigação |
|-----------|---------|-----------|
| Máx. 100 steps por trace | Performance UI | Dividir conversas longas |
| Máx. 5MB por arquivo | Navegador pode travar | Truncar prompts/responses |
| Sem agregação estatística | Não vê médias/totais | Usar ferramenta externa (futuro) |
| Manual testing only (UI) | Sem testes automáticos | Seguir BDD checklist (spec.md) |

---

## Próximos Passos

1. ✅ **Leia**: [data-model.md](data-model.md) para entender estrutura JSON
2. ✅ **Experimente**: Rode exemplo completo acima
3. ✅ **Visualize**: Abra UI e explore trace gerado
4. ✅ **Instrumente**: Adicione tracer ao seu código LLM
5. ⏳ **Avançado**: Exportar/importar traces (P2 feature)

---

## Recursos Adicionais

- **Especificação**: [spec.md](spec.md) - Requisitos completos
- **Data Model**: [data-model.md](data-model.md) - Estrutura JSON detalhada
- **Implementation Plan**: [plan.md](plan.md) - Detalhes técnicos

---

## Feedback

Encontrou um bug ou tem sugestão? Abra issue no repositório synth-lab.
