# Auto-Update Tests - Guia Rápido

## 🎯 Problema Resolvido

**Antes:**
```bash
# Você cria endpoint
vim src/synth_lab/api/routers/experiments.py

# Commit
git commit -m "Add clone endpoint"

# ❌ Esquece de criar contract test
# ❌ Problema só descobre em prod
```

**Agora:**
```bash
# Você cria endpoint
vim src/synth_lab/api/routers/experiments.py

# Commit
git commit -m "Add clone endpoint"

# 🤖 Hook post-commit AUTOMÁTICO:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🤖 SUGESTÃO: Atualizar testes automaticamente
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Você modificou routers.
Quer que Claude Code gere contract tests automaticamente?

Opções:
  1) Sim, executar agora (interativo)    ← Recomendado
  2) Sim, executar e auto-commit
  3) Não, farei manualmente

Escolha (1/2/3): 1

# 🤖 Claude Code é chamado AUTOMATICAMENTE com prompt já montado:
"Atualizar tests/contract/test_api_contracts.py para cobrir o router 'experiments'.

Endpoints encontrados:
- /experiments/{id}/clone

Para cada endpoint, crie contract test que valide:
- Status code esperado
- Estrutura de resposta
- Tipos de dados corretos
..."

# ✅ Claude Code gera o teste
# ✅ Script valida que teste passa
# ✅ Você só revisa e commita

# 🎉 Teste sincronizado com código!
```

## 🔄 Como Funciona

### 1. Análise Automática (GitHub Actions)

**Quando:** Toda segunda 9am + após merge em main

**O que faz:**
- Analisa gaps de cobertura
- Cria/atualiza issue no GitHub com relatório
- Sugere comandos Claude Code prontos

**Resultado:**
```
Issue #123: 📊 Test Coverage Gaps - Weekly Report

📡 Endpoints: 15/30 testados (50.0%)
   Faltam: /api/documents/upload, ...

💡 COMANDOS PRONTOS:
   claude code --prompt "Criar contract tests para: /api/documents/upload, ..."
```

### 2. Atualização Automática (Git Hook Post-Commit)

**Quando:** Após cada commit que muda router/model/service

**O que faz:**
1. **Detecta** arquivos modificados
2. **Gera prompts** específicos para Claude Code
3. **Executa** Claude Code automaticamente
4. **Valida** que testes passam
5. **Oferece** auto-commit

**Fluxo:**
```
git commit
   ↓
Hook post-commit detecta: router mudou
   ↓
Pergunta: "Gerar testes automaticamente?"
   ↓
Você: "1" (sim, interativo)
   ↓
Script monta prompt e chama Claude Code
   ↓
Claude Code gera contract test
   ↓
Script roda: make test-fast
   ↓
✅ Passou! Mostra diff para você revisar
   ↓
Você: git commit -m "test: add contract test"
```

### 3. Manual Quando Necessário

```bash
# Para commit específico
./scripts/auto-update-tests.sh --last-commit

# Para arquivo específico
./scripts/auto-update-tests.sh --file src/synth_lab/api/routers/experiments.py

# Ver o que seria feito (sem executar)
./scripts/auto-update-tests.sh --last-commit --dry-run

# Executar e auto-commit tudo
./scripts/auto-update-tests.sh --last-commit --auto-commit
```

## 📋 Respostas às Suas Perguntas

### 1. Quem monta o prompt do Claude Code?

**R:** O script `auto-update-tests.sh` monta AUTOMATICAMENTE.

**Exemplo:**
```bash
# Você modificou: src/synth_lab/api/routers/experiments.py
# Script detecta e gera automaticamente:

Prompt gerado:
"Atualizar tests/contract/test_api_contracts.py para cobrir o router 'experiments'.

Endpoints encontrados:
- POST /experiments/{id}/clone
- GET /experiments/search

Para cada endpoint, crie contract test que valide:
- Status 200
- Response.id existe
- Response tem campos obrigatórios

Use padrão existente em test_api_contracts.py."

# Você NÃO precisa escrever isso manualmente!
```

### 2. Os passos seguintes são automáticos?

**R:** Parcialmente. Você escolhe o nível de automação:

**Opção 1: Interativo (Recomendado)**
```bash
# Você escolhe: "1) Sim, executar agora (interativo)"

# Script faz:
1. ✅ Detecta mudanças         (automático)
2. ✅ Gera prompt             (automático)
3. ✅ Chama Claude Code       (automático)
4. ✅ Roda testes             (automático)
5. ⏸️  Mostra diff            (você revisa)
6. 👤 Você faz commit         (manual)
```

**Opção 2: Totalmente Automático**
```bash
# Você escolhe: "2) Sim, executar e auto-commit"

# Script faz:
1. ✅ Detecta mudanças         (automático)
2. ✅ Gera prompt             (automático)
3. ✅ Chama Claude Code       (automático)
4. ✅ Roda testes             (automático)
5. ✅ Commita se passou       (automático)

# Tudo 100% automático!
```

**Opção 3: Manual**
```bash
# Você escolhe: "3) Não, farei manualmente"

# Script não faz nada
# Você roda depois:
./scripts/auto-update-tests.sh --last-commit
```

### 3. Análise de Gaps é automática?

**R:** SIM! Roda no GitHub Actions.

**Configuração:**
- ✅ Toda segunda 9am (cron)
- ✅ Após merge em main
- ✅ Manualmente via botão no GitHub

**Resultado:**
- Cria/atualiza issue automaticamente
- Issue tem comandos prontos para copiar/colar

## 🚀 Fluxo Completo Real

### Cenário: Você adiciona endpoint de clone

```bash
# 1. Desenvolve
vim src/synth_lab/api/routers/experiments.py
# Adiciona: POST /experiments/{id}/clone

# 2. Commit
git commit -m "Add clone endpoint"

# 3. Hook post-commit (AUTOMÁTICO):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🤖 SUGESTÃO: Atualizar testes automaticamente
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Arquivos modificados:
  - src/synth_lab/api/routers/experiments.py

📡 Routers modificados detectados

Opções:
  1) Sim, executar agora (interativo)
  2) Sim, executar e auto-commit
  3) Não, farei manualmente

Escolha (1/2/3): 1

# 4. Script monta prompt automaticamente (você NÃO escreve isso):
════════════════════════════════════════
Prompt 1/1 - Tipo: contract
════════════════════════════════════════

Atualizar tests/contract/test_api_contracts.py para cobrir o router 'experiments'.

Endpoints encontrados:
- POST /experiments/{id}/clone

Para cada endpoint, crie/atualize contract test que valide:
- Status code esperado (200, 201, 404, etc)
- Estrutura de resposta (campos obrigatórios)
- Tipos de dados corretos
- Valores válidos para enums/constantes

Use o padrão existente em test_api_contracts.py como referência.

# 5. Script executa Claude Code (AUTOMÁTICO)
🤖 Executando Claude Code...
✅ Claude Code executado com sucesso

# 6. Script valida testes (AUTOMÁTICO)
🧪 Validando testes...
Running: make test-fast
✅ Contract tests passaram

# 7. Você revisa e commita
git diff tests/contract/test_api_contracts.py  # Revisa
git add tests/contract/
git commit -m "test: add contract test for clone endpoint"

# 🎉 Pronto! Teste criado e validado automaticamente.
```

## ⚙️ Configuração

**Tudo já está configurado!**

```bash
# Hooks estão em:
.githooks/post-commit              # Pergunta se quer gerar testes

# Scripts:
scripts/auto-update-tests.sh       # Gera prompts e chama Claude Code

# GitHub Actions:
.github/workflows/test-coverage-analysis.yml  # Análise semanal
```

## 💡 Dicas

**Para começar:**
```bash
# Teste com último commit
./scripts/auto-update-tests.sh --last-commit --dry-run

# Veja o que seria gerado (sem executar)
```

**Para desenvolver:**
- Escolha opção **1 (interativo)** - você revisa antes de commitar
- Use opção **2 (auto-commit)** apenas para mudanças triviais

**Para manutenção:**
- GitHub Actions cria issue semanalmente
- Copie os comandos da issue e execute

## 🎓 Comparação

| Antes | Depois |
|-------|--------|
| Você escreve endpoint | Você escreve endpoint |
| ❌ Esquece contract test | ✅ Hook pergunta se quer gerar |
| ❌ Quebra em prod | ✅ Claude Code gera automaticamente |
| | ✅ Script valida que teste passa |
| | ✅ Você só revisa e commita |

---

**Dúvidas?** Rode: `./scripts/auto-update-tests.sh --help`
