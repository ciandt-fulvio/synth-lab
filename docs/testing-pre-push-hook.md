# Testando o Pre-Push Hook

## ✅ Teste Confirmado

O pre-push hook **ESTÁ funcionando corretamente** e É disparado quando você faz push para main.

## 🧪 Resultado do Teste

```bash
# Teste executado: git push origin HEAD:main --dry-run
✅ PRE-PUSH HOOK FOI DISPARADO!
```

## 📋 Como o Fluxo Deveria Funcionar

### Cenário 1: Merge + Push (SEU CASO)

```bash
# 1. Você está em uma feature branch
git checkout feature-branch
git commit -m "minhas mudanças"

# 2. Faz merge para main (NENHUM hook roda aqui!)
git checkout main
git merge feature-branch
# ☝️ O merge em si NÃO dispara hooks

# 3. Faz push para remote (PRE-PUSH HOOK RODA AQUI! ✅)
git push origin main
# ☝️ Aqui o hook deveria rodar:
#    - Build de imagens Docker
#    - make test (testes unitários)
#    - make test-e2e (testes E2E)
#    - Push de imagens para GHCR
```

### Cenário 2: Push Direto de Feature Branch para Main

```bash
# Você está em feature-branch
git push origin feature-branch:main
# ☝️ PRE-PUSH HOOK RODA AQUI! ✅
```

## 🔍 Por Que Pode Parecer Que Não Está Funcionando?

### 1. Hook Pode Estar Sendo Bypassado

```bash
# ❌ Isso pula o hook
git push origin main --no-verify

# ✅ Use sem --no-verify
git push origin main
```

### 2. Push Pode Não Estar Acontecendo

```bash
# Apenas fazer merge NÃO dispara o hook
git checkout main
git merge feature-branch
# ☝️ NADA acontece ainda - você só mergeou localmente

# Você PRECISA fazer push depois
git push origin main
# ☝️ AQUI o hook roda!
```

### 3. Branch Pode Não Ser Main

```bash
# Hook só roda se você estiver fazendo push para MAIN
git push origin feature-branch  # ❌ Hook não roda
git push origin main            # ✅ Hook roda
```

## 🧪 Teste Manual - Faça Você Mesmo

Execute este teste para ver o hook funcionando:

```bash
# 1. Crie uma branch de teste
git checkout -b test-pre-push-hook

# 2. Faça uma mudança trivial
echo "# Test" >> README.md
git add README.md
git commit -m "test: verify pre-push hook"

# 3. Tente fazer push para main (dry-run, não faz push de verdade)
git push origin test-pre-push-hook:main --dry-run

# ☝️ Você deveria ver:
#    [1/5] 🐳 Building Docker images...
#    [2/5] 🧪 Running full test suite...
#    [3/5] 🎭 Running E2E tests...
#    [4/5] 📦 Pushing images to GHCR...
#    [5/5] 📋 Summary

# 4. Limpar
git checkout main
git branch -D test-pre-push-hook
```

## 🚨 Se o Hook NÃO Rodar

Verifique estas configurações:

```bash
# 1. Verificar se o Git está usando .githooks
git config core.hooksPath
# Deveria retornar: .githooks

# 2. Se não estiver configurado, configure:
git config core.hooksPath .githooks

# 3. Verificar se o hook tem permissão de execução
ls -la .githooks/pre-push
# Deveria mostrar: -rwxr-xr-x (com 'x' de executável)

# 4. Se não tiver permissão, adicione:
chmod +x .githooks/pre-push
```

## 📊 Diagnóstico Rápido

Execute este script para diagnosticar:

```bash
#!/bin/bash
echo "🔍 Diagnóstico do Pre-Push Hook"
echo ""
echo "Git hooks path: $(git config core.hooksPath)"
echo "Current branch: $(git branch --show-current)"
echo "Hook exists: $(test -f .githooks/pre-push && echo 'YES' || echo 'NO')"
echo "Hook executable: $(test -x .githooks/pre-push && echo 'YES' || echo 'NO')"
echo ""
echo "Testando hook com push dry-run para main..."
git push origin HEAD:refs/heads/main --dry-run 2>&1 | grep -E "(Building|Running|Pushing|Pre-Push|skipping)" || echo "Hook não foi disparado!"
```

## ✅ Conclusão

O pre-push hook **está configurado corretamente** e **é disparado** quando você faz push para main.

Se você está fazendo merge mas não vê o hook rodando, provavelmente você:
1. Não está fazendo push depois do merge (apenas mergeou localmente)
2. Está usando `--no-verify` para pular o hook
3. Está fazendo push para uma branch diferente de main

**Solução**: Sempre faça `git push origin main` depois de fazer merge para main.
