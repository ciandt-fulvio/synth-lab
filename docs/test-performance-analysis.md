# Análise de Performance dos Testes Backend

## 📊 Situação Atual

### Total de Testes
- **98 arquivos de teste** identificados
- **~150+ testes individuais** (estimativa)
- Tempo médio de execução: **2-5 minutos** (sem E2E)

### Categorização por Uso de LLM

| Categoria | Quantidade | Status | Tempo Estimado |
|-----------|------------|--------|----------------|
| **Testes com chamadas REAIS a LLM** | 1 arquivo principal | 🔴 Lento | 5-10s cada |
| **Testes com MOCK de LLM** | 18 arquivos | ✅ Rápido | <0.5s cada |
| **Testes sem LLM** | 79 arquivos | ✅ Rápido | <0.5s cada |

## 🔴 Testes com Chamadas Reais a LLM

### 1. `tests/integration/test_avatar_generation.py`

**Classe**: `TestRealOpenAIIntegration`
- Marcado com `@pytest.mark.slow`
- Faz chamadas reais para OpenAI DALL-E
- **Custo**: ~$0.02 por execução
- **Tempo**: 5-10 segundos
- **Propósito**: Validar integração real com OpenAI (smoke test de API)

**Testes**:
```python
def test_real_api_single_block(...)  # Gera 9 avatares via DALL-E
def test_real_api_error_handling(...)  # Testa erro com API key inválida
```

**Problema**:
- Esses testes rodam em **TODA execução** se `OPENAI_API_KEY` estiver configurada
- Adicionam 10+ segundos ao tempo total
- Podem falhar por problemas de rede/quota da API

## ✅ Testes com Mock Correto (Exemplos)

### `tests/integration/services/test_ai_services.py`

**Padrão correto de mocking**:
```python
@pytest.mark.integration
class TestInterviewGuideGeneratorIntegration:
    @pytest.mark.asyncio
    async def test_generate_for_experiment_creates_guide(...):
        # Mock the LLM client's complete_json method
        with patch.object(service.llm, "complete_json") as mock_llm:
            mock_llm.return_value = json.dumps(mock_llm_response)
            guide = await service.generate_for_experiment(...)
            mock_llm.assert_called_once()
```

**Benefícios**:
- Teste rápido (<0.5s)
- Sem custo de API
- Sem dependência de rede
- Resultados determinísticos

### Outros arquivos com mock correto:
- `test_exploration_services.py`
- `test_research_services.py`
- `test_document_services.py`
- `test_materials_tool.py`
- `test_interview_with_materials.py`

## ⚠️ Testes Marcados como `@pytest.mark.slow` (Mas NÃO usam LLM)

Esses testes são lentos por outros motivos (não LLM):

| Arquivo | Motivo da Lentidão |
|---------|-------------------|
| `test_auth_flow.py` | OAuth flow completo + DB operations |
| `test_synth_group_ownership.py` | Operações complexas de permissões |
| `test_sharing.py` | Múltiplas operações de compartilhamento |
| `test_experiment_ownership.py` | Validações de ownership + DB |
| `test_permissions.py` | Verificações de permissões |

**Nota**: Esses testes NÃO precisam de mocking de LLM (não usam LLM).

## 📈 Impacto Estimado

### Cenário Atual (com chamadas reais a LLM)

```
Suite de testes backend completa:
├─> Testes rápidos (sem LLM): ~1-2 min
├─> Testes slow (auth, permissions): ~30-60s
└─> Testes com LLM real: ~10-20s
────────────────────────────────────
Total: ~2-4 minutos
```

### Cenário Proposto (com mocking de LLM)

```
Suite de testes backend completa:
├─> Testes rápidos (sem LLM): ~1-2 min
├─> Testes slow (auth, permissions): ~30-60s
├─> Testes com LLM mockado: ~5s
└─> 1 smoke test real de LLM: ~5s (opcional, só CI)
────────────────────────────────────
Total: ~2-3 minutos (15-30% mais rápido)
```

## 🎯 Recomendações

### 1. Converter Testes Reais para Mock (Prioridade Alta)

**Arquivo**: `tests/integration/test_avatar_generation.py`

**Ação**: Criar versão mockada dos testes:
```python
@pytest.mark.integration
class TestAvatarGenerationIntegration:
    """Integration tests with MOCKED OpenAI API."""

    @patch("synth_lab.gen_synth.avatar_generator.OpenAI")
    def test_avatar_generation_workflow(self, mock_openai, ...):
        # Mock OpenAI response
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_client.images.generate.return_value = mock_image_response

        # Test workflow
        result = generate_avatars(synths, ...)

        # Verify calls
        mock_client.images.generate.assert_called()
```

**Manter** teste real como smoke test:
- Mover para `tests/smoke/test_openai_integration.py`
- Executar apenas em CI (não localmente)
- Ou executar apenas quando explicitamente solicitado: `pytest -m slow`

### 2. Criar Fixture Centralizado para Mock de LLM

**Arquivo**: `tests/fixtures/llm_mocks.py`

```python
import pytest
from unittest.mock import MagicMock, AsyncMock

@pytest.fixture
def mock_llm_client():
    """Mock OpenAI client for fast testing."""
    mock = MagicMock()

    # Mock text completion
    mock.complete.return_value = "Mocked LLM response"

    # Mock JSON completion
    mock.complete_json.return_value = '{"key": "value"}'

    # Mock async methods
    mock.acomplete = AsyncMock(return_value="Async mocked response")

    return mock

@pytest.fixture
def mock_openai_image():
    """Mock OpenAI DALL-E image generation."""
    mock = MagicMock()
    mock.images.generate.return_value = MagicMock(
        data=[
            MagicMock(
                url="https://mocked-image.com/test.png",
                b64_json=None
            )
        ]
    )
    return mock
```

**Uso nos testes**:
```python
def test_with_mocked_llm(mock_llm_client):
    service = MyService(llm_client=mock_llm_client)
    result = service.generate_something()
    assert result is not None
    mock_llm_client.complete.assert_called_once()
```

### 3. Configurar Markers no pytest.ini

**Arquivo**: `pyproject.toml` (adicionar)

```toml
[tool.pytest.ini_options]
markers = [
    "slow: marks tests as slow (real API calls, deselect with '-m \"not slow\"')",
    "integration: marks integration tests",
    "smoke: marks smoke tests",
    "contract: marks contract tests",
    "schema: marks schema validation tests",
    "requires_postgres: marks tests requiring PostgreSQL",
    "real_api: marks tests that make real API calls (OpenAI, S3, etc)",
]
```

**Uso**:
```bash
# Rodar testes rápidos apenas (sem slow)
pytest -m "not slow"

# Rodar apenas testes de integração (sem chamadas reais)
pytest -m "integration and not real_api"

# Rodar apenas smoke tests de API real (CI)
pytest -m "smoke and real_api"
```

### 4. Estratégia de Testes de LLM

**Níveis de teste**:

1. **Unit tests** (sem LLM):
   - Testam lógica de negócio
   - Mock completo de LLM
   - Muito rápidos (<0.1s)

2. **Integration tests** (LLM mockado):
   - Testam fluxo completo
   - Mock de chamadas LLM
   - Rápidos (<0.5s)

3. **Smoke tests** (LLM real, opcional):
   - Validam integração real
   - Executam apenas em CI ou sob demanda
   - Lentos (5-10s)
   - Marcados com `@pytest.mark.real_api`

**Exemplo de smoke test mínimo**:
```python
@pytest.mark.slow
@pytest.mark.real_api
class TestOpenAISmoke:
    """Minimal smoke test for real OpenAI integration."""

    def test_openai_connection(self):
        """Verify OpenAI API is accessible with 'hello world'."""
        import os
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            pytest.skip("OPENAI_API_KEY not configured")

        from openai import OpenAI
        client = OpenAI(api_key=api_key)

        # Minimal test: just verify connection works
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Hi"}],
            max_tokens=5
        )

        assert response.choices[0].message.content is not None
```

## 🚀 Implementação Gradual

### Fase 1: Setup (30 min)
- [ ] Criar `tests/fixtures/llm_mocks.py`
- [ ] Adicionar markers ao `pyproject.toml`
- [ ] Criar `tests/smoke/test_openai_integration.py`

### Fase 2: Converter Testes (1-2h)
- [ ] Converter `test_avatar_generation.py` para usar mocks
- [ ] Mover testes reais para `tests/smoke/`
- [ ] Verificar outros testes de services que possam estar lentos

### Fase 3: Validação (30 min)
- [ ] Rodar suite completa e medir tempo: `time pytest`
- [ ] Rodar apenas testes rápidos: `pytest -m "not slow"`
- [ ] Rodar smoke tests: `pytest -m "slow and real_api"`

### Fase 4: Documentação (30 min)
- [ ] Atualizar README com instruções de testes
- [ ] Documentar estratégia de mocking no CLAUDE.md

## 📊 Métricas de Sucesso

| Métrica | Antes | Meta | Benefício |
|---------|-------|------|-----------|
| Tempo total de testes | 2-4 min | 1.5-2.5 min | 25-30% mais rápido |
| Testes com chamadas reais | 2+ | 0-1 (opcional) | Sem custo de API |
| Falhas por rede/quota | Ocasionais | Zero | Mais estável |
| Tempo de feedback dev | 2-4 min | 1.5-2.5 min | Iteração mais rápida |

## 🔗 Referências

- [pytest markers](https://docs.pytest.org/en/stable/example/markers.html)
- [unittest.mock](https://docs.python.org/3/library/unittest.mock.html)
- [Best practices for mocking](https://realpython.com/python-mock-library/)
