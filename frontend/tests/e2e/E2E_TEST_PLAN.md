# Plano de Testes E2E - SynthLab

## Objetivo
Criar uma suite de testes e2e que dê tranquilidade para deploy em produção, servindo como gate no pre-PR.

## Navegação Realizada

Durante a exploração da aplicação (Jan 14, 2026), foram identificados os seguintes fluxos:

### 1. Experimentos
- ✅ Lista de experimentos
- ✅ Criação de experimento (com formulário multi-step)
- ✅ Detalhe do experimento
- ✅ Navegação entre tabs: Análise, Entrevistas, Explorações, Materiais, Relatórios
- 🆕 Filtros rápidos por tag (botões "checkout", "teste")
- 🆕 Busca por nome ou hipótese
- 🆕 Filtro por dropdown de tags
- 🆕 Ordenação (dropdown "Recentes")
- ✅ Botão voltar (navegação)
- 🆕 Tab "Materiais" com upload de arquivos
- 🆕 Tab "Relatórios" (estado vazio)

### 2. Entrevistas
- 🆕 Modal "Nova Entrevista"
- 🆕 Campos: Contexto Adicional (textarea), Quantidade de Synths (spinner 1-50), Máximo de Turnos (spinner 1-20)
- 🆕 Botões: Cancelar, Iniciar Entrevista
- 🆕 Fechar modal com ESC ou botão X

### 3. Synths
- 🆕 Página de listagem de synths (/synths)
- 🆕 Filtro por grupo (dropdown "Todos os grupos")
- 🆕 Cards com avatar, nome, descrição e badge do grupo
- 🆕 Modal de detalhes do synth (ao clicar no card)
- 🆕 Tabs no modal: Demografia, Psicografia, Capacidades Técnicas
- 🆕 Paginação (mostrando 1-45 de 420 synths)

### 4. Navegação Geral
- ✅ Header com logo e link para home
- ✅ Botão "Synths" no header
- ✅ Badge "Beta"

## Estrutura Atual vs. Proposta

### Estrutura Atual
```
tests/e2e/
├── README.md
├── TEST_SCENARIOS.md (documentação extensa, mas desatualizada)
├── experiment-list.spec.ts (teste básico, redundante com experiments/crud)
├── experiments/
│   └── crud.spec.ts (testes completos de CRUD)
└── smoke/
    └── critical-flows.spec.ts (smoke tests)
```

### Estrutura Proposta
```
tests/e2e/
├── README.md (manter, atualizar comandos)
├── E2E_TEST_PLAN.md (este arquivo - plano de ação)
├── smoke/
│   └── critical-flows.spec.ts (P0: smoke tests para production)
├── experiments/
│   ├── list.spec.ts (listagem, filtros, busca, ordenação)
│   ├── crud.spec.ts (criar, visualizar, deletar)
│   ├── detail-tabs.spec.ts (navegação entre tabs)
│   └── materials.spec.ts (upload de materiais)
├── interviews/
│   └── create.spec.ts (modal de criação, validação)
├── synths/
│   ├── list.spec.ts (listagem, filtro, paginação)
│   └── detail.spec.ts (modal de detalhes, tabs)
└── shared/
    └── navigation.spec.ts (navegação geral, header)
```

## Priorização de Implementação

### P0 - Crítico (Gate para PR)
**Estes testes DEVEM passar para permitir merge**

1. ✅ `smoke/critical-flows.spec.ts` - já existe, revisar
   - ST001: App carrega
   - ST002: Lista de experimentos carrega
   - ST003: API responde
   - ST004: Navegação básica funciona
   - ST005: Detalhe de experimento carrega
   - ST006: Sem erros visíveis
   - ST007: Sem erros no console

2. ✅ `experiments/crud.spec.ts` - já existe, revisar
   - E001: Criar experimento
   - E002: Listar experimentos
   - E003: Ver detalhes

3. 🆕 `experiments/list.spec.ts` - NOVO
   - Filtros rápidos por tag funcionam
   - Busca por nome/hipótese funciona
   - Dropdown de tags funciona
   - Ordenação funciona

4. 🆕 `interviews/create.spec.ts` - NOVO
   - Modal abre e fecha
   - Validação de campos
   - Criação de entrevista

5. 🆕 `synths/list.spec.ts` - NOVO
   - Listagem carrega
   - Filtro por grupo funciona
   - Paginação funciona

### P1 - Alto (Recomendado antes de PR)

6. 🆕 `experiments/detail-tabs.spec.ts` - NOVO
   - Navegação entre todas as tabs
   - Conteúdo correto em cada tab

7. 🆕 `synths/detail.spec.ts` - NOVO
   - Modal abre ao clicar
   - Tabs funcionam (Demografia, Psicografia, Capacidades)

8. 🆕 `experiments/materials.spec.ts` - NOVO
   - Upload de arquivo (pode ser mock)
   - Validação de tipos de arquivo

### P2 - Médio (Opcional)

9. 🆕 `shared/navigation.spec.ts` - NOVO
   - Header sempre visível
   - Logo leva para home
   - Botão Synths funciona

## Checklist de Padronização

### Nomenclatura
- [ ] Usar nomes descritivos: `list.spec.ts`, `create.spec.ts`, `detail.spec.ts`
- [ ] IDs de teste: `ST001`, `E001`, `I001`, `Y001` (Smoke, Experiments, Interviews, sYnths)
- [ ] Tags Playwright: `@smoke`, `@critical`, `@experiments`, `@interviews`, `@synths`

### Estrutura de Arquivo
```typescript
/**
 * E2E Tests - [Módulo] [Funcionalidade]
 *
 * [Descrição breve]
 *
 * Run: npm run test:e2e [caminho]
 */
import { test, expect } from '@playwright/test';

test.describe('[Módulo] - [Funcionalidade] @tag1 @tag2', () => {
  test.beforeEach(async ({ page }) => {
    // Setup comum
  });

  test('ID - Description', async ({ page }) => {
    // Teste
  });
});
```

### Boas Práticas
- [ ] Usar `getByRole`, `getByLabel`, `getByText` ao invés de seletores CSS quando possível
- [ ] Timeouts explícitos para operações lentas (API, modal abrir)
- [ ] `waitForLoadState('networkidle')` após navegações
- [ ] Mensagens de `expect` claras
- [ ] `test.skip()` quando pré-requisitos não atendidos (dados de seed)

### Validações Importantes
- [ ] Não apenas verificar que elemento existe, mas que está visível
- [ ] Verificar URLs após navegação
- [ ] Verificar estados vazios e com dados
- [ ] Não forçar comportamentos - usar `test.skip()` quando apropriado

## Ações Necessárias

### Fase 1: Reorganização (hoje)
1. ✅ Criar este documento de planejamento
2. [ ] Remover `experiment-list.spec.ts` (redundante)
3. [ ] Atualizar `TEST_SCENARIOS.md` ou removê-lo (desatualizado)
4. [ ] Revisar e padronizar `smoke/critical-flows.spec.ts`
5. [ ] Revisar e padronizar `experiments/crud.spec.ts`

### Fase 2: Novos Testes P0 (hoje/amanhã)
6. [ ] Implementar `experiments/list.spec.ts`
7. [ ] Implementar `interviews/create.spec.ts`
8. [ ] Implementar `synths/list.spec.ts`

### Fase 3: Testes P1 (esta semana)
9. [ ] Implementar `experiments/detail-tabs.spec.ts`
10. [ ] Implementar `synths/detail.spec.ts`
11. [ ] Implementar `experiments/materials.spec.ts`

### Fase 4: Integração CI/CD
12. [ ] Atualizar README.md com comandos atualizados
13. [ ] Configurar comando para rodar apenas P0 (gate de PR)
14. [ ] Documentar tempo de execução esperado

## Métricas de Sucesso

- **Cobertura**: 80% dos fluxos críticos testados
- **Tempo de execução**: < 3 minutos para P0
- **Confiabilidade**: 95% de taxa de sucesso (não flaky)
- **Manutenibilidade**: Testes fáceis de entender e atualizar

## Comandos Úteis

```bash
# Rodar apenas P0 (gate de PR)
npm run test:e2e -- --grep "@critical"

# Rodar por módulo
npm run test:e2e experiments/
npm run test:e2e synths/
npm run test:e2e interviews/

# Rodar smoke tests
npm run test:e2e smoke/

# Modo UI (desenvolvimento)
npm run test:e2e:ui

# Headed (ver browser)
npm run test:e2e:headed
```

## Notas da Navegação

### Estado Atual da Aplicação
- Há experimentos seed (incluindo "Test Experiment" sem scorecard)
- Tags: "checkout", "teste"
- 420 synths no total
- Grupos de synths: "Default", "Aposentados 60+"
- Paginação mostrando 45 synths por página

### Bugs/Observações Encontrados
- Modal "Nova Entrevista": botão "Close" (X) teve timeout ao clicar - usar ESC funciona
- Experimento sem scorecard mostra mensagem clara: "Configure o scorecard no formulário de criação"
- Tab "Explorações" aparece desabilitada quando não há exploração
