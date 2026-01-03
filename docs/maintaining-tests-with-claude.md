# Mantendo Testes Atualizados com Claude Code

## 🎯 Estratégia em 3 Camadas

### 1. **Automático (Git Hooks)** - Alertas em Tempo Real

Quando você faz commit/push, recebe alertas automáticos:

```bash
git commit -m "Add new router"

✅ Pre-commit tests passed!

⚠️  ATENÇÃO: Você pode precisar atualizar testes!

  📝 Router mudou → Considere atualizar tests/contract/test_api_contracts.py
     Comando: claude code --prompt 'Atualizar contract tests para os routers modificados'
```

**Configuração:** Já está ativo em `.githooks/check-test-coverage.sh`

---

### 2. **Periódico (Semanal)** - Análise de Gaps

Execute semanalmente para ver gaps de cobertura:

```bash
make test-coverage-analysis
```

**Output:**
```
📊 ANÁLISE DE COBERTURA DE TESTES
============================================================

📡 Endpoints (Contract Tests)
   15/30 testados (50.0%)
   ⚠️  15 endpoints sem contract tests:
      - /api/documents/upload
      - /api/exploration/nodes/{id}
      - /api/research/execute
      ...

🗄️  ORM Models (Schema Tests)
   8/12 testados (66.7%)
   ⚠️  4 models sem schema tests:
      - ExplorationNode
      - ResearchDocument
      ...

⚙️  Services (Integration Tests)
   4/18 testados (22.2%)
   ⚠️  14 services sem integration tests:
      - document_service
      - research_service
      ...

============================================================
💡 SUGESTÕES DE PROMPTS PARA CLAUDE CODE
============================================================

📝 Para Contract Tests:
   claude code --prompt "Criar contract tests para os endpoints: /api/documents/upload, /api/exploration/nodes/{id}, /api/research/execute"

📝 Para Schema Tests:
   claude code --prompt "Adicionar validação de schema para os models: ExplorationNode, ResearchDocument"

📝 Para Integration Tests:
   claude code --prompt "Criar integration tests para os services: document_service, research_service"
```

---

### 3. **On-Demand** - Comandos Claude Code

Use Claude Code quando precisar:

## 📋 Comandos Claude Code Úteis

### Atualizar Contract Tests

```bash
# Quando adicionar/modificar endpoint
claude code --prompt "
Analisei o router em src/synth_lab/api/routers/experiments.py
e vi que há um novo endpoint POST /experiments/batch-create.
Atualize tests/contract/test_api_contracts.py para validar:
- Schema de request
- Schema de response
- Campos obrigatórios
- Tipos corretos
"

# Verificar se contract tests estão completos
claude code --prompt "
Liste todos os endpoints em src/synth_lab/api/routers/
que NÃO têm contract tests correspondentes em tests/contract/
"
```

### Atualizar Schema Tests

```bash
# Quando criar/modificar ORM model
claude code --prompt "
Criei um novo ORM model 'ScenarioNode' em src/synth_lab/models/orm/exploration.py.
Adicione validação de schema em tests/schema/test_db_schema_validation.py para:
- Tabela 'scenario_nodes' existe
- Colunas obrigatórias presentes
- Tipos corretos
- Foreign keys
"

# Verificar sincronização com DB
claude code --prompt "
Analise se há divergências entre ORM models em src/synth_lab/models/orm/
e os schema tests em tests/schema/test_db_schema_validation.py
"
```

### Criar Integration Tests

```bash
# Para novo service
claude code --prompt "
Crie integration test para DocumentService em src/synth_lab/services/document_service.py
que valide o fluxo completo:
1. Upload de documento
2. Processamento
3. Salvamento de metadados no DB
4. Verificação que dados foram persistidos corretamente
"

# Para fluxo crítico
claude code --prompt "
Crie integration test que valide o fluxo completo:
Criar experimento → Gerar avatares → Rodar simulação → Gerar análise → Criar insights
Valide que cada etapa persiste dados corretamente no DB
"
```

### Criar E2E Tests

```bash
# Para novo fluxo de usuário
claude code --prompt "
Crie E2E test com Playwright em frontend/tests/e2e/ que valide:
1. Usuário clica em 'Novo Experimento'
2. Preenche form com nome e hipótese
3. Adiciona scorecard data
4. Clica em 'Criar'
5. É redirecionado para página de detalhes
6. Vê experimento criado
"
```

### Análise e Manutenção

```bash
# Análise geral
claude code --prompt "
Analise a suíte de testes completa e identifique:
1. Testes duplicados
2. Testes desatualizados (baseados em código que não existe mais)
3. Gaps críticos de cobertura
4. Padrões inconsistentes
Sugira melhorias
"

# Atualizar testes quebrados
claude code --prompt "
Rode pytest -m contract e analise falhas.
Atualize os contract tests para refletir mudanças recentes na API.
"

# Refatorar testes
claude code --prompt "
Refatore tests/integration/test_experiment_flows.py para:
1. Usar fixtures compartilhadas
2. Reduzir duplicação
3. Melhorar nomes de testes
4. Adicionar docstrings
Mantenha funcionalidade idêntica
"
```

## 🔄 Workflow Recomendado

### Desenvolvimento Diário

```bash
# 1. Antes de começar a trabalhar
make test-fast

# 2. Desenvolve feature X (ex: novo endpoint)
# ...

# 3. Atualiza testes JUNTO com código
claude code --prompt "Criar contract test para o endpoint que acabei de criar"

# 4. Commit (git hook alerta se esqueceu algo)
git commit -m "Add new endpoint"

# 5. Push (git hook roda testes rápidos)
git push
```

### Manutenção Semanal

```bash
# Segunda-feira de manhã (10min)

# 1. Analisa gaps
make test-coverage-analysis

# 2. Prioriza top 3 gaps mais críticos
# Ex: endpoints de pagamento sem contract tests

# 3. Usa Claude Code para gerar testes
claude code --prompt "Criar contract tests para endpoints: /api/payments/..."

# 4. Valida que testes passam
make test-fast

# 5. Commit
git commit -m "chore: add missing contract tests for payment endpoints"
```

### Review de PR

```bash
# Antes de aprovar PR de colega

# 1. Verifica se PR tem testes adequados
claude code --prompt "
Analise o PR #123 e verifique:
- Novos endpoints têm contract tests?
- Novos models têm schema validation?
- Novos services têm integration tests?
Se algo faltar, sugira os testes necessários
"

# 2. Se faltar testes, comenta no PR
# "Faltam contract tests para o endpoint X. Use: claude code --prompt '...'"
```

## 📊 Métricas de Sucesso

Acompanhe mensalmente:

```bash
# Gera relatório
make test-coverage-analysis > coverage-report-$(date +%Y-%m).txt

# Metas:
# - Contract tests: 80%+ dos endpoints
# - Schema tests: 100% das tabelas principais
# - Integration tests: 60%+ dos services
# - E2E tests: 50%+ dos fluxos críticos
```

## 🎓 Boas Práticas

### ✅ FAÇA

- **Atualize testes JUNTO com código** - não deixe para depois
- **Use Claude Code para gerar boilerplate** - economiza tempo
- **Rode `make test-fast` frequentemente** - feedback rápido
- **Execute `make test-coverage-analysis` semanalmente** - visibilidade
- **Priorize testes de fluxos críticos** - maior ROI

### ❌ NÃO FAÇA

- **Não ignore alertas dos git hooks** - eles existem para ajudar
- **Não pule validação manual** - sempre rode testes após gerar com Claude
- **Não gere testes em batch sem validar** - pode criar testes ruins
- **Não delete testes sem entender** - pode ter lógica importante
- **Não confie 100% em testes gerados** - sempre revise

## 🚀 Atalhos Rápidos

```bash
# Análise rápida
make test-coverage-analysis

# Gera contract tests para endpoint específico
claude code --prompt "Contract test para GET /api/experiments/{id}"

# Gera schema test para model específico
claude code --prompt "Schema test para model Experiment"

# Gera integration test para service específico
claude code --prompt "Integration test para ExperimentService.create_experiment()"

# Atualiza testes quebrados
claude code --prompt "Conserta testes falhando em tests/contract/test_api_contracts.py"

# Lista gaps críticos
claude code --prompt "Liste top 5 gaps mais críticos de testes que devemos priorizar"
```

## 📖 Recursos

- **Skill:** `.claude/skills/update-tests.md` - Templates e padrões
- **Script:** `scripts/analyze_test_coverage.py` - Análise de gaps
- **Hook:** `.githooks/check-test-coverage.sh` - Alertas automáticos
- **Docs:** `tests/README.md` - Guia completo de testes

## 💡 Exemplo Completo

**Cenário:** Você adiciona um novo endpoint `POST /api/experiments/{id}/clone`

```bash
# 1. Implementa o endpoint
vim src/synth_lab/api/routers/experiments.py

# 2. Roda testes (tudo passa pois não quebrou nada)
make test-fast

# 3. Commit
git commit -m "Add clone experiment endpoint"

# Git hook alerta:
# ⚠️  Router mudou → Considere atualizar contract tests

# 4. Usa Claude Code para gerar teste
claude code --prompt "
Criar contract test em tests/contract/test_api_contracts.py para:
POST /api/experiments/{id}/clone

Valide:
- Status 200
- Response tem campo 'id' do novo experimento
- Response tem campo 'name' com '(Clone)' no final
- Experimento original não foi modificado
"

# 5. Claude gera o teste, você valida
make test-fast

# 6. Commit do teste
git commit -m "test: add contract test for clone endpoint"

# 7. Push
git push

# ✅ CI passa, PR aprovado!
```

---

**Dúvidas?** Execute:
```bash
make help
claude code --help
```
