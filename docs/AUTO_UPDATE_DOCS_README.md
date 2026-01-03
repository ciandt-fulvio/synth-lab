# Auto-Update Docs - Guia Rápido

Sistema automático para manter documentação sincronizada com código usando Claude Code.

## 🚀 Quick Start

### Uso Automático (Recomendado)

Simplesmente commite código:

```bash
git add src/synth_lab/api/routers/research.py
git commit -m "feat: add GET /research/batch endpoint"

# Output do hook:
📚 SUGESTÃO: Atualizar documentação
...
Escolha (1/2/3): 1  # Executar agora
```

### Uso Manual

```bash
# Via Makefile (recomendado)
make update-docs

# Via script direto
./scripts/auto-update-docs.sh --last-commit
```

## 📋 O Que É Atualizado

| Código Mudou | Doc Atualizada | Conteúdo |
|--------------|----------------|----------|
| `src/synth_lab/api/routers/*.py` | `docs/api.md` | Endpoints, schemas, exemplos |
| `src/synth_lab/services/*.py` | `docs/arquitetura.md` | Services, responsabilidades |
| `src/synth_lab/models/orm/*.py` | `docs/database_model.md` | Tabelas, campos, tipos |
| `frontend/src/pages/*.tsx` | `docs/arquitetura_front.md` | Rotas, componentes |
| `frontend/src/hooks/*.ts` | `docs/arquitetura_front.md` | Hooks customizados |

## 🔧 Comandos

```bash
# Atualizar docs (analisa último commit)
make update-docs

# Ver prompts sem executar (dry-run)
./scripts/auto-update-docs.sh --last-commit --dry-run

# Auto-commit após atualização
./scripts/auto-update-docs.sh --last-commit --auto-commit

# Arquivo específico
./scripts/auto-update-docs.sh --file src/synth_lab/api/routers/research.py
```

## 🎯 Como Funciona

```
1. Você commita código
2. Git hook detecta mudanças
3. Script gera prompt específico
4. Claude Code atualiza doc
5. Você revisa e commita
```

## 📁 Arquivos do Sistema

```
scripts/
  auto-update-docs.sh          # Script principal

.claude/skills/
  update-docs/SKILL.md         # Templates de prompts

.githooks/
  post-commit                  # Hook que detecta mudanças

.github/workflows/
  docs-validation.yml          # CI/CD checks

.markdownlint.json             # Config de validação
```

## ⚙️ Configuração (Já Está Pronta)

Tudo já está configurado! Se precisar customizar:

1. **Editar prompts:** `.claude/skills/update-docs/SKILL.md`
2. **Ajustar detecção:** `scripts/auto-update-docs.sh` (funções `detect_*_changes`)
3. **Config markdown:** `.markdownlint.json`

## 📊 CI/CD (GitHub Actions)

Toda PR verifica automaticamente:

- ✅ Sintaxe markdown válida
- ✅ Links internos não quebrados
- ✅ Cobertura de API docs (>= 80%)
- ⚠️  Warning se código mudou mas docs não

## 💡 Dicas

**1. Sempre revise as mudanças:**
```bash
git diff docs/api.md
```

**2. Use dry-run para ver prompts:**
```bash
./scripts/auto-update-docs.sh --last-commit --dry-run
```

**3. Se prompt não ficou bom, ajuste template:**
Edite `.claude/skills/update-docs/SKILL.md`

**4. Desabilitar hook temporariamente:**
```bash
git commit --no-verify
```

## 🆘 Troubleshooting

**Hook não executa:**
```bash
# Verificar se hooks estão configurados
git config core.hooksPath
# Output esperado: .githooks

# Reconfigurar se necessário
make setup-hooks
```

**Script não encontrado:**
```bash
# Verificar permissão de execução
ls -la scripts/auto-update-docs.sh

# Adicionar se necessário
chmod +x scripts/auto-update-docs.sh
```

**Markdownlint não instalado:**
```bash
npm install -g markdownlint-cli
```

## 📚 Documentação Completa

Ver [DOCUMENTATION_MAINTENANCE.md](./DOCUMENTATION_MAINTENANCE.md) para:
- Arquitetura completa do sistema
- Detalhes de implementação
- Features avançadas planejadas
- Metadata tracking, coverage metrics, etc.

## 🔄 Comparação com Auto-Update Tests

Sistema análogo ao `auto-update-tests.sh`:

| Aspecto | Testes | Docs |
|---------|--------|------|
| **Script** | `auto-update-tests.sh` | `auto-update-docs.sh` |
| **Trigger** | Routers/Models/Services | Routers/Models/Services/Frontend |
| **Destino** | `tests/` | `docs/` |
| **Validação** | `pytest` | `markdownlint` |
| **Hook** | `post-commit` | `post-commit` |
| **Makefile** | `make test-fast` | `make update-docs` |

## ✅ Checklist Pós-Commit

Após Claude Code atualizar docs:

1. [ ] Revisar mudanças: `git diff docs/`
2. [ ] Verificar exemplos de código
3. [ ] Validar links internos
4. [ ] Rodar `markdownlint docs/**/*.md`
5. [ ] Commit: `git commit -m "docs: update documentation"`

---

**Status:** ✅ Sistema implementado e pronto para uso (2026-01-03)

**Próximo passo:** Faça um commit que mude um router/service e veja o sistema em ação! 🚀
