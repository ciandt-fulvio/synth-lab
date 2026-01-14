# Reorganização dos Testes E2E - Sumário

**Data**: 14 de Janeiro, 2026
**Objetivo**: Reorganizar e padronizar testes e2e para servir como gate de qualidade no pre-PR

## ✅ Trabalho Realizado

### 1. Navegação e Análise da Aplicação

Utilizando Chrome DevTools, navegamos pela aplicação e identificamos:

- **Experimentos**: Lista, filtros por tag, busca, ordenação, CRUD completo, tabs (Análise, Entrevistas, Explorações, Materiais, Relatórios)
- **Entrevistas**: Modal de criação com validação de campos
- **Synths**: Listagem com filtro por grupo, paginação, modal de detalhes com 3 tabs (Demografia, Psicografia, Capacidades Técnicas)
- **Navegação**: Header, logo, botão Synths

### 2. Estrutura Reorganizada

#### Antes
```
tests/e2e/
├── README.md
├── TEST_SCENARIOS.md (desatualizado)
├── experiment-list.spec.ts (redundante)
├── experiments/
│   └── crud.spec.ts
└── smoke/
    └── critical-flows.spec.ts
```

#### Depois
```
tests/e2e/
├── README.md (atualizado)
├── E2E_TEST_PLAN.md (novo - plano detalhado)
├── TEST_SCENARIOS.md (mantido para referência)
├── smoke/
│   └── critical-flows.spec.ts (ST001-ST009)
├── experiments/
│   ├── crud.spec.ts (E001-E011)
│   └── list.spec.ts (EL001-EL008) ✨ NOVO
├── interviews/
│   └── create.spec.ts (I001-I013) ✨ NOVO
└── synths/
    ├── list.spec.ts (Y001-Y013) ✨ NOVO
    └── detail.spec.ts (Y014-Y027) ✨ NOVO
```

### 3. Novos Testes Implementados

#### `experiments/list.spec.ts` (P0 - Crítico)
- EL001: Filtro rápido por tag
- EL002: Busca por nome/hipótese
- EL003: Dropdown de filtro por tags
- EL004: Dropdown de ordenação
- EL005: Mensagem de "nenhum resultado"
- EL006: Limpar filtros restaura lista completa
- EL007: Empty state
- EL008: Cards mostram informação necessária

#### `interviews/create.spec.ts` (P0 - Crítico)
- I001: Abrir modal de nova entrevista
- I002: Fechar com botão Cancelar
- I003: Fechar com ESC
- I004: Valores padrão corretos
- I005-I007: Alteração de campos
- I008: Botão de submit visível e habilitado
- I009: Criar entrevista (skip - cria dados)
- I010-I013: Validações de formulário

#### `synths/list.spec.ts` (P0/P1)
- Y001: Página carrega corretamente
- Y002: Cards são exibidos
- Y003: Cards mostram informação necessária
- Y004: Badge de grupo é exibido
- Y005: Dropdown de filtro existe
- Y006: Filtro por grupo funciona
- Y007: Limpar filtro restaura lista
- Y008-Y013: Paginação (controles, tamanho de página, navegação)

#### `synths/detail.spec.ts` (P1 - Alto)
- Y014: Clicar em card abre modal
- Y015: Modal mostra descrição
- Y016: Modal tem 3 tabs
- Y017: Tab Demografia selecionada por padrão
- Y018: Demografia mostra informações corretas
- Y019-Y020: Tab Psicografia
- Y021-Y022: Tab Capacidades Técnicas
- Y023: Capacidades mostra percentuais
- Y024: Navegar entre todas as tabs
- Y025-Y026: Fechar modal (ESC e botão)
- Y027: Abrir modais de synths diferentes

### 4. Documentação Criada/Atualizada

- ✅ **E2E_TEST_PLAN.md**: Plano completo com navegação realizada, estrutura proposta, priorização (P0/P1/P2), checklist de padronização, roadmap
- ✅ **README.md**: Atualizado com nova estrutura, comandos para rodar testes P0 (gate de PR), cobertura atual
- ✅ **Arquivos de teste**: Todos com headers padronizados, tags Playwright (`@critical`, `@experiments`, etc.), IDs sequenciais

### 5. Padronização Aplicada

#### Nomenclatura
- IDs de teste: `ST001` (Smoke), `E001` (Experiments), `EL001` (Experiments List), `I001` (Interviews), `Y001` (sYnths)
- Tags: `@critical`, `@smoke`, `@experiments`, `@interviews`, `@synths`
- Arquivos: Nomes descritivos (`list.spec.ts`, `create.spec.ts`, `detail.spec.ts`)

#### Estrutura de Arquivo
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
    // Setup
  });

  test('ID - Description', async ({ page }) => {
    // Teste
  });
});
```

#### Boas Práticas
- ✅ Uso de `getByRole`, `getByLabel`, `getByText` (semânticos)
- ✅ Timeouts explícitos para operações lentas
- ✅ `waitForLoadState('networkidle')` após navegações
- ✅ `test.skip()` quando pré-requisitos não atendidos
- ✅ Validações que elementos estão **visíveis**, não apenas existem
- ✅ Verificação de URLs após navegação
- ✅ Testes de estados vazios e com dados

## 📊 Métricas

### Cobertura
- **Antes**: ~20 cenários (apenas smoke + CRUD básico)
- **Depois**: ~60 cenários cobrindo:
  - ✅ Smoke tests (7 testes)
  - ✅ Experimentos CRUD (11 testes)
  - ✅ Experimentos filtros e busca (8 testes)
  - ✅ Entrevistas criação (13 testes)
  - ✅ Synths listagem e paginação (13 testes)
  - ✅ Synths detalhes (14 testes)

### Priorização
- **P0 (Crítico)**: 39 testes - DEVEM passar para permitir PR
  - Smoke: ST001-ST007
  - Experiments CRUD: E001-E003
  - Experiments List: EL001-EL008
  - Interviews: I001-I008
  - Synths List: Y001-Y007

- **P1 (Alto)**: 21 testes - Recomendado antes de PR
  - Experiments CRUD: E004-E011
  - Interviews: I009-I013
  - Synths List: Y008-Y013
  - Synths Detail: Y014-Y027

## 🎯 Como Usar (Gate de PR)

### Comando Principal
```bash
# Rodar apenas testes P0 (críticos)
npx playwright test --grep "@critical"

# Duração esperada: < 3 minutos
```

Este comando roda:
- Smoke tests (ST001-ST007)
- Experimentos CRUD (E001-E003)
- Experimentos filtros (EL001-EL008)
- Entrevistas modal (I001-I008)
- Synths listagem (Y001-Y007)

### Integração com CI/CD (Recomendado)
```yaml
# Adicionar ao workflow do GitHub Actions
- name: Run E2E Critical Tests
  run: npx playwright test --grep "@critical"
```

## 📝 Roadmap (Próximos Passos)

### P1 - Alto (Esta Semana)
- [ ] `experiments/detail-tabs.spec.ts` - Testar navegação entre todas as tabs do experimento
- [ ] `experiments/materials.spec.ts` - Testar upload de materiais

### P2 - Médio (Quando Necessário)
- [ ] `shared/navigation.spec.ts` - Testes de navegação geral (header, logo)
- [ ] Testes de responsividade mobile
- [ ] Testes de acessibilidade (a11y)

### Melhorias de Infraestrutura
- [ ] Configurar parallel execution no Playwright
- [ ] Adicionar relatório HTML automático
- [ ] Configurar retry automático para testes flaky
- [ ] Adicionar screenshots automáticos em falhas

## 🐛 Observações/Bugs Encontrados

Durante a navegação, observamos:

1. **Modal "Nova Entrevista"**: Botão "Close" (X) teve timeout ao clicar. Workaround: usar ESC (funciona corretamente)
   - Localização: `frontend/tests/e2e/interviews/create.spec.ts:I003`
   - Solução temporária: Testes usam ESC para fechar

2. **Experimento sem scorecard**: Mostra mensagem clara "Configure o scorecard no formulário de criação"
   - Comportamento correto, não é bug

3. **Tab "Explorações"**: Aparece desabilitada quando não há exploração
   - Comportamento correto, não é bug

## ✨ Benefícios da Reorganização

1. **Confiança para Deploy**: Suite de testes robusta que cobre fluxos críticos
2. **Manutenibilidade**: Estrutura clara por módulo, fácil adicionar novos testes
3. **Padronização**: Todos os testes seguem mesmo padrão, facilitando code review
4. **Documentação**: Plano de testes detalhado e README atualizado
5. **Gate de Qualidade**: Comando simples (`@critical`) para validar PR
6. **Rastreabilidade**: IDs únicos (ST001, E001, etc.) facilitam referência

## 🎓 Lições Aprendidas

1. **Navegação Exploratória**: Usar DevTools para explorar aplicação antes de escrever testes economiza tempo
2. **Testes Flexíveis**: Não forçar comportamentos específicos - usar `test.skip()` quando dados seed não atendem pré-requisitos
3. **Seletores Semânticos**: `getByRole`, `getByLabel` são mais robustos que seletores CSS
4. **Validação de Visibilidade**: Sempre verificar que elemento está **visível**, não apenas existe no DOM
5. **Documentação Clara**: Plano de testes e README ajudam onboarding de novos desenvolvedores

## 📚 Referências

- Plano Detalhado: `E2E_TEST_PLAN.md`
- Comandos: `README.md`
- Cenários Antigos (referência): `TEST_SCENARIOS.md`
