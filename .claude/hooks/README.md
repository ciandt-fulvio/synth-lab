# Claude Code Hooks - Test Validation

Este diretório contém hooks do Claude Code que garantem que os testes sejam atualizados sempre que código é modificado.

## 📋 Hooks Disponíveis

### 1. `pre-commit` 🔍
**Quando executa:** Antes de cada commit

**O que faz:**
- Analisa arquivos staged (que serão commitados)
- Identifica se há código novo/modificado
- Solicita ao Claude que verifique e atualize testes
- Lista tipos de teste necessários baseado nos arquivos modificados

**Exemplo de uso:**
```bash
git add src/synth_lab/services/new_feature.py
git commit -m "feat: add new feature"

# Hook pre-commit será executado e mostrará checklist de testes
```

---

### 2. `pre-push` 🚀
**Quando executa:** Antes de fazer push para remote

**O que faz:**
- Analisa todos os commits que serão enviados
- Lista arquivos modificados em todos os commits
- Verifica se há gaps de cobertura de testes
- Solicita confirmação de que testes foram executados

**Exemplo de uso:**
```bash
git push origin feature-branch

# Hook pre-push será executado antes do push
```

---

### 3. `pull-request` 📝
**Quando executa:** Ao criar Pull Request via Claude

**O que faz:**
- Analisa todas as mudanças no branch
- Gera checklist completa de testes para PR
- Sugere descrição de PR com seção de Test Plan
- Lista comandos de teste a executar

**Exemplo de uso:**
```bash
# Ao pedir ao Claude para criar PR:
"Create a pull request for this feature"

# Hook será executado e mostrará checklist completa
```

---

## 🎯 Tipos de Teste Verificados

### Backend (Python)
- ✅ **Unit Tests** - `pytest tests/unit/`
- ✅ **Integration Tests** - `pytest tests/integration/`
- ✅ **Contract Tests** - APIs/endpoints
- ✅ **Smoke Tests** - `pytest tests/smoke/`

### Frontend (TypeScript/React)
- ✅ **Unit Tests** - `npm test`
- ✅ **Integration Tests** - Components interagindo
- ✅ **E2E Tests** - `npm run test:e2e` (Playwright)
- ✅ **Smoke Tests** - Fluxos críticos

---

## 🔧 Como Funciona

### 1. Detecção Automática
Os hooks analisam automaticamente:
- Arquivos modificados (`.py`, `.ts`, `.tsx`, `.js`, `.jsx`)
- Tipo de código (API, Service, Component, Page, etc.)
- Testes existentes relacionados

### 2. Prompt Inteligente
Baseado nos arquivos modificados, o Claude recebe um prompt com:
- Lista de arquivos modificados
- Tipos de teste necessários
- Comandos para executar
- Checklist para validar

### 3. Não-Bloqueante
Os hooks **não bloqueiam** commits/pushes, mas:
- Mostram avisos claros
- Instruem o Claude a verificar testes
- Criam um registro no terminal

---

## 📊 Exemplo de Output

### Pre-Commit Hook
```
🧪 PRE-COMMIT TEST CHECK

Arquivos de código staged:
src/synth_lab/services/interview_service.py
frontend/src/components/InterviewCard.tsx

VERIFICAÇÃO OBRIGATÓRIA:

### Backend (Python)
- [ ] Testes unitários criados/atualizados para novas funções
- [ ] Testes de integração se houver interação entre componentes
- [ ] Testes de serviço se houver lógica de negócio nova/modificada

### Frontend (TypeScript/React)
- [ ] Testes unitários para componentes novos/modificados
- [ ] Testes E2E atualizados se fluxos de UI foram modificados

Comandos:
pytest tests/unit/
cd frontend && npm test && npm run test:e2e
```

---

## 🚦 Workflow Recomendado

### 1. Durante Desenvolvimento
```bash
# Desenvolva a feature
vim src/synth_lab/services/new_service.py

# Crie os testes
vim tests/unit/services/test_new_service.py

# Execute testes
pytest tests/unit/services/test_new_service.py

# Commit (hook pre-commit será executado)
git add .
git commit -m "feat: add new service"
```

### 2. Antes de Push
```bash
# Execute todos os testes
pytest tests/
cd frontend && npm test && npm run test:e2e

# Push (hook pre-push será executado)
git push origin feature-branch
```

### 3. Ao Criar PR
```bash
# Peça ao Claude para criar PR
# Hook pull-request será executado automaticamente

# Adicione a checklist gerada ao PR description
```

---

## ⚙️ Configuração

### Ativar Hooks
Os hooks estão automaticamente ativos se você está usando Claude Code. Não há configuração adicional necessária.

### Desativar Temporariamente
Se precisar desativar temporariamente (não recomendado):
```bash
# Desativa hook específico
chmod -x .claude/hooks/pre-commit

# Reativa
chmod +x .claude/hooks/pre-commit
```

---

## 📚 Padrões de Teste

### Backend (Python)

#### Estrutura de Diretórios
```
tests/
├── unit/              # Testes unitários (funções isoladas)
│   ├── services/
│   ├── repositories/
│   └── domain/
├── integration/       # Testes de integração
│   ├── api/
│   └── services/
├── smoke/            # Testes de smoke (fluxos críticos)
└── fixtures/         # Fixtures compartilhadas
```

#### Exemplo de Teste Unitário
```python
# tests/unit/services/test_interview_service.py
import pytest
from synth_lab.services.interview_service import InterviewService

def test_create_interview():
    service = InterviewService()
    result = service.create(experiment_id="exp_123")
    assert result.id is not None
    assert result.status == "pending"
```

### Frontend (TypeScript/React)

#### Estrutura de Diretórios
```
frontend/
├── src/
│   └── components/
│       └── InterviewCard.tsx
└── tests/
    ├── unit/
    │   └── components/
    │       └── InterviewCard.test.tsx
    └── e2e/
        └── interviews/
            └── interview-flow.spec.ts
```

#### Exemplo de Teste de Component
```typescript
// InterviewCard.test.tsx
import { render, screen } from '@testing-library/react';
import { InterviewCard } from './InterviewCard';

test('renders interview card with title', () => {
  render(<InterviewCard title="Test Interview" />);
  expect(screen.getByText('Test Interview')).toBeInTheDocument();
});
```

---

## 🎓 Melhores Práticas

### 1. **Write Tests First (TDD)**
```bash
# 1. Escreva o teste (Red)
vim tests/unit/test_new_feature.py

# 2. Implemente a feature (Green)
vim src/synth_lab/new_feature.py

# 3. Refatore (Refactor)
```

### 2. **Commit Atômico com Testes**
```bash
# Sempre commite código E testes juntos
git add src/synth_lab/services/new_service.py
git add tests/unit/services/test_new_service.py
git commit -m "feat: add new service with tests"
```

### 3. **Cobertura Mínima**
- Novo código: **80%+**
- Código crítico (pagamento, auth): **100%**
- Componentes UI: **80%+**
- Utils/helpers: **100%**

### 4. **Tipos de Teste por Camada**
- **API**: Contract tests + Integration tests
- **Service**: Unit tests + Integration tests
- **Repository**: Integration tests (com banco real)
- **Domain**: Unit tests
- **Components**: Unit tests + Integration tests
- **Pages**: E2E tests

---

## 🔍 Troubleshooting

### Hook não está executando
```bash
# Verifique se hooks têm permissão de execução
ls -la .claude/hooks/

# Torne executável
chmod +x .claude/hooks/*
```

### Hook mostra erro
```bash
# Verifique sintaxe do hook
bash -n .claude/hooks/pre-commit

# Execute manualmente para debug
.claude/hooks/pre-commit
```

### Claude não está vendo os prompts
- Certifique-se de estar usando Claude Code CLI
- Verifique se os hooks estão no diretório `.claude/hooks/`
- Verifique se os hooks têm permissão de execução

---

## 📖 Documentação Adicional

- [Claude Code Hooks Documentation](https://docs.anthropic.com/claude/docs/claude-code-hooks)
- [pytest Documentation](https://docs.pytest.org/)
- [Playwright Testing](https://playwright.dev/)
- [React Testing Library](https://testing-library.com/react)

---

## 🤝 Contribuindo

Se você adicionar novos tipos de teste ou modificar os hooks:

1. Atualize este README
2. Teste os hooks localmente
3. Documente mudanças no commit

---

## 📝 Changelog

### 2026-01-14
- ✅ Criados hooks `pre-commit`, `pre-push`, `pull-request`
- ✅ Suporte para Python (backend) e TypeScript (frontend)
- ✅ Detecção automática de tipos de arquivo
- ✅ Checklists específicas por tipo de mudança

---

**🎯 Objetivo:** Garantir que nenhum código seja commitado ou enviado sem testes adequados.
