# 🚀 Quick Start - Claude Code Test Hooks

## O Que São Estes Hooks?

Hooks do Claude Code que **automaticamente** lembram você de atualizar testes sempre que fizer mudanças no código.

---

## ⚡ Uso Rápido

### 1️⃣ Fazer um Commit

```bash
# Modifique código
vim src/synth_lab/services/my_service.py

# Add e commit
git add .
git commit -m "feat: add new feature"

# 🎯 Hook pre-commit será executado AUTOMATICAMENTE
# Claude mostrará checklist de testes necessários
```

**O que você verá:**
```
🧪 PRE-COMMIT TEST CHECK

Arquivos de código staged:
src/synth_lab/services/my_service.py

VERIFICAÇÃO OBRIGATÓRIA:
- [ ] Testes unitários criados/atualizados
- [ ] Testes de integração se necessário

Comandos:
pytest tests/unit/services/test_my_service.py
```

---

### 2️⃣ Fazer um Push

```bash
git push origin feature-branch

# 🎯 Hook pre-push será executado AUTOMATICAMENTE
# Claude verificará todos os commits e testes
```

**O que você verá:**
```
🧪 PRE-PUSH TEST CHECK

Commits a serem enviados:
abc1234 feat: add new feature

Arquivos de código modificados:
src/synth_lab/services/my_service.py

AÇÃO OBRIGATÓRIA:
Confirme que todos os testes foram executados e passam
```

---

### 3️⃣ Criar Pull Request

```bash
# Peça ao Claude
"Create a pull request for this feature"

# 🎯 Hook pull-request será executado AUTOMATICAMENTE
# Claude gerará checklist completa de PR
```

**O que você verá:**
```
🔍 PULL REQUEST TEST VALIDATION

Checklist para PR:
- [ ] Unit tests: pytest tests/unit/
- [ ] Integration tests: pytest tests/integration/
- [ ] E2E tests: npm run test:e2e
- [ ] Coverage: 80%+

Adicione esta checklist ao PR description
```

---

## 🎯 Workflow Completo (Exemplo)

### Cenário: Adicionar Nova Feature

```bash
# 1. Crie branch
git checkout -b feature/new-interview-type

# 2. Desenvolva (TDD recomendado)
# Escreva teste primeiro
vim tests/unit/services/test_interview_service.py

# Implemente feature
vim src/synth_lab/services/interview_service.py

# 3. Execute testes localmente
pytest tests/unit/services/test_interview_service.py
# ✅ All tests pass

# 4. Commit (hook pre-commit executará)
git add .
git commit -m "feat: add structured interview type"

# Claude mostrará checklist - confirme que testes estão OK

# 5. Execute todos os testes
pytest tests/
cd frontend && npm test && npm run test:e2e

# 6. Push (hook pre-push executará)
git push origin feature/new-interview-type

# Claude verificará novamente - confirme que tudo passou

# 7. Crie PR via Claude
"Create a pull request for the new interview type feature"

# Hook pull-request gerará checklist completa
# Copie a checklist para o PR description
```

---

## 📋 Checklists Geradas

### Pre-Commit (Básico)
```markdown
- [ ] Testes unitários criados
- [ ] Testes executados localmente
- [ ] Todos passando
```

### Pre-Push (Completo)
```markdown
- [ ] Unit tests: pytest tests/unit/
- [ ] Integration tests: pytest tests/integration/
- [ ] Frontend: npm test
- [ ] E2E: npm run test:e2e
- [ ] Coverage adequada
```

### Pull Request (Detalhado)
```markdown
## Test Plan

### Testes Executados
- [ ] Unit tests passando
- [ ] Integration tests passando
- [ ] E2E tests passando
- [ ] Smoke tests passando

### Cobertura
- [ ] Cobertura mínima: 80%
- [ ] Edge cases cobertos
- [ ] Error handling testado

### Resultados
- Test Coverage: ___%
- Tests Passing: ___/___
```

---

## 🔥 Dicas Pro

### 1. Commit Atômico
```bash
# ✅ BOM: Commita código + testes juntos
git add src/feature.py tests/test_feature.py
git commit -m "feat: add feature with tests"

# ❌ RUIM: Commita código sem testes
git add src/feature.py
git commit -m "feat: add feature"  # Hook alertará!
```

### 2. Execute Testes Antes do Commit
```bash
# Execute testes primeiro
pytest tests/unit/

# Se passar, commit
git commit -m "feat: add feature"

# Hook confirmará que você já testou
```

### 3. Use Coverage para Validar
```bash
# Veja coverage antes do commit
pytest --cov=src/synth_lab --cov-report=term-missing

# Mínimo: 80% para novo código
```

### 4. TDD - Test Driven Development
```bash
# 1. Red: Escreva teste (que falha)
vim tests/unit/test_new_feature.py
pytest tests/unit/test_new_feature.py  # ❌ Fail

# 2. Green: Implemente (passa)
vim src/synth_lab/new_feature.py
pytest tests/unit/test_new_feature.py  # ✅ Pass

# 3. Refactor: Melhore código
vim src/synth_lab/new_feature.py
pytest tests/unit/test_new_feature.py  # ✅ Still pass

# 4. Commit
git commit -m "feat: add new feature (TDD)"
```

---

## 🛠️ Comandos Úteis

### Backend (Python)
```bash
# Testes específicos
pytest tests/unit/services/test_my_service.py -v

# Por diretório
pytest tests/unit/ -v
pytest tests/integration/ -v

# Com coverage
pytest --cov=src/synth_lab --cov-report=html
open htmlcov/index.html

# Apenas um teste
pytest tests/unit/test_file.py::test_function -v
```

### Frontend (TypeScript/React)
```bash
cd frontend

# Todos os testes
npm test

# Watch mode (TDD)
npm test -- --watch

# E2E
npm run test:e2e

# E2E específico
npx playwright test tests/e2e/interviews/

# E2E com UI
npx playwright test --ui

# Coverage
npm run test:coverage
```

---

## ❓ FAQ

### Os hooks bloqueiam commits/pushes?
**Não!** Os hooks são **informativos**. Eles mostram avisos e checklists, mas não bloqueiam operações.

### Posso ignorar os avisos?
**Tecnicamente sim**, mas **não recomendado**. Os hooks existem para proteger a qualidade do código.

### Os hooks funcionam fora do Claude Code?
**Sim!** São scripts bash normais. Você verá os prompts no terminal mesmo sem Claude Code.

### Como desabilitar temporariamente?
```bash
# Desabilitar
chmod -x .claude/hooks/pre-commit

# Reabilitar
chmod +x .claude/hooks/pre-commit
```

### E se eu esquecer de criar testes?
Os hooks **sempre** vão lembrar você. Você verá avisos em:
- Pre-commit
- Pre-push
- Pull request

---

## 🎓 Recursos Adicionais

- **README Completo:** `.claude/hooks/README.md`
- **pytest docs:** https://docs.pytest.org/
- **Playwright docs:** https://playwright.dev/
- **Testing Library:** https://testing-library.com/

---

## 🎯 Objetivo Final

**Nenhum código sem testes adequados!**

Os hooks garantem que:
- ✅ Testes são sempre considerados
- ✅ Cobertura é mantida alta
- ✅ PRs incluem Test Plans
- ✅ Qualidade do código se mantém

---

**💪 Use os hooks, mantenha qualidade alta, ship com confiança!**
