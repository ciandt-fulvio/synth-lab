# SynthLab - Design Audit & Improvement Report

**Data**: 16/02/2026
**Escopo**: Auditoria completa via Chrome DevTools de todas as paginas, abas e modais
**Base**: React 18 + Tailwind CSS + shadcn/ui + Recharts

---

## Sumario Executivo

O SynthLab tem uma base solida com shadcn/ui e um design system (globals.css) bem estruturado. A aplicacao e funcional e apresenta dados complexos de forma razoavel. Porem, ha oportunidades significativas de melhoria em **hierarquia visual**, **densidade de informacao**, **navegacao**, **consistencia** e **polish geral** que elevariam a experiencia de um MVP funcional para um produto com presenca profissional.

---

## 1. Navegacao & Arquitetura de Informacao

### Problemas Identificados

**1.1 Navegacao global minimalista demais**
- O header so tem "SynthLab" (home) e "Synths" como navegacao. Nao ha indicacao visual de onde o usuario esta (breadcrumb, highlight no nav).
- Na pagina de detalhe do experimento, o header muda para "Detalhe do Experimento" como subtitle, mas nao ha breadcrumb clicavel (`Experimentos > pix via whatsapp`).
- No detalhe do grupo de synths, o header mostra "default" como subtitle, mas nao indica que e um grupo.

**1.2 Botao "Synths" descontextualizado**
- Na home (lista de experimentos), o botao "Synths" aparece no canto direito como um botao outline discreto. Ele se confunde com uma acao secundaria em vez de navegacao principal.
- Nas demais paginas (detalhe de experimento, grupos de synths), nao ha maneira direta de navegar entre Experimentos e Synths sem voltar ao home.

**1.3 Falta de "wayfinding" nas abas do experimento**
- As 5 abas (Analise Quanti, Simulacao, Entrevistas, Materiais, Relatorios) nao indicam progresso ou estado. O usuario nao sabe quais abas tem conteudo sem clicar em cada uma.
- As sub-abas dentro de Simulacao (Distribuicao, Segmentos, Sensibilidade) parecem visualmente identicas as abas principais, criando confusao hierarquica.

### Recomendacoes

- [ ] **Adicionar breadcrumbs** nas paginas de detalhe: `Experimentos / pix via whatsapp / Simulacao`
- [ ] **Converter navegacao global** em nav persistente (sidebar slim ou top nav com items destacados)
- [ ] **Diferenciar sub-abas visualmente** das abas principais (ex: usar botoes pill/toggle em vez de abas underline para sub-navegacao de Simulacao)
- [ ] **Indicar visualmente** quais abas tem conteudo (dot indicator, icone preenchido vs outline)

---

## 2. Layout & Espacamento

### Problemas Identificados

**2.1 Excesso de whitespace em listas com poucos items**
- A home com 1 experimento tem ~60% de tela vazia. O card de experimento ocupa ~1/3 da largura e o restante e vazio.
- A pagina de grupos de synths tem o mesmo problema com 1 grupo.

**2.2 Header do experimento ocupa espaco excessivo**
- O bloco superior (nome + badge grupo + hipotese + tags) ocupa ~280px de altura antes das abas. O campo "Adicionar tag..." com o botao "+" parece desproporcionalmente grande e vazio.
- A hipotese sendo apenas uma linha de texto ("pix via whatsapp") desperdiça o espaco alocado.

**2.3 Layout do DAG e Premissas Causais**
- A area do DAG (lado esquerdo) nao tem borda/card wrapper, criando assimetria visual com a lista de premissas (lado direito) que esta em um card.
- O DAG ocupa ~45% da largura, as premissas ~55%. Em telas menores isso pode comprimir demais.

**2.4 Secao Estatisticas do Grupo sem header contextual**
- A pagina de estatisticas do grupo pula direto para "Demografia" sem um resumo/header do grupo (nome, descricao, quando foi criado, quantos synths).

### Recomendacoes

- [ ] **Compactar o header do experimento**: Nome + grupo badge na mesma linha; hipotese como texto menor abaixo; tags inline ao lado do nome
- [ ] **Usar grid responsivo para listas**: Experimentar 2 ou 3 colunas para experiment cards quando ha poucos items, ou adicionar suggested actions/tips na area vazia
- [ ] **Wrappear o DAG em card**: Adicionar `rounded-xl border border-slate-200` no container do grafo, alinhando visualmente com o painel de premissas
- [ ] **Adicionar header do grupo**: Card resumo no topo da pagina de estatisticas com nome, descricao, data de criacao, total de synths

---

## 3. Hierarquia Visual & Tipografia

### Problemas Identificados

**3.1 Titulos e subtitulos sem diferenciacao clara**
- "Experimentos" (h2), "pix via whatsapp" (h3 do card), "Resultados da Simulacao" (h3 dentro da aba) usam tamanhos similares. A hierarquia nao e clara.
- Dentro da aba de Simulacao, "Resultados da Simulacao" e "Distribuicao/Segmentos/Sensibilidade" competem visualmente.

**3.2 Textos longos das premissas causais sem formatacao**
- Cada premissa e um bloco de texto corrido: "A respeito de quanto a Capacidade Digital e influenciada por Idade..." seguido de paragrafos longos de opcoes. Nao ha destaque visual para os termos-chave (ex: nomes das variaveis).

**3.3 Blocos de interpretacao sem destaque suficiente**
- Os blocos "INTERPRETACAO - DISTRIBUICAO/SEGMENTOS/SENSIBILIDADE" usam label all-caps mas o texto em si nao tem formatacao especial. Sendo o insight mais valioso da pagina, deveria ter mais destaque.

**3.4 Tabela de sensibilidade sem formatacao de dados**
- Valores numericos (2.80pp, 62.3%, etc.) aparecem em texto regular. Numeros sao dificeis de escanear sem alinhamento ou highlight.

### Recomendacoes

- [ ] **Aplicar sistema tipografico consistente**: Usar `.text-page-title` para titulos de pagina, `.text-section-title` para secoes, `.text-card-title` para sub-secoes
- [ ] **Destacar variaveis nas premissas**: Bold ou cor primaria nos nomes das variaveis (`Capacidade Digital`, `Idade`)
- [ ] **Redesenhar blocos de interpretacao**: Usar card com borda colorida lateral (border-left-4), icone de insight, e tipografia serif (Crimson Pro ja esta configurada) para diferenciar do conteudo tecnico
- [ ] **Formatar numeros na tabela**: Alinhamento a direita, font-mono para numeros, highlight condicional (verde para alto impacto, cinza para baixo)

---

## 4. Cor & Contraste

### Problemas Identificados

**4.1 Paleta moncromatica na simulacao**
- O histograma de distribuicao usa uma unica cor (indigo) para todas as barras. Nao ha diferenciacao visual das regioes P10-P90 vs outliers.
- O grafico tornado de sensibilidade usa tons de indigo quase identicos, tornando dificil distinguir barras adjacentes.

**4.2 Destaque verde nos segmentos sem legenda**
- Na aba de Segmentos, o card com maior % recebe borda verde, mas nao ha legenda explicando o que o verde significa ("melhor segmento" vs "significancia estatistica").

**4.3 Histogramas de sensibilidade no grupo (teal) sem contexto**
- Os 4 histogramas (Aversao ao Risco, etc.) usam barras teal que sao bonitas mas nao transmitem informacao. Nao ha gradiente de intensidade ou agrupamento visual.

**4.4 Badges de "ajustado" nas premissas sem explicacao**
- O badge verde "ajustado" aparece em algumas premissas mas nunca e explicado ao usuario o que significa ser "ajustado".

### Recomendacoes

- [ ] **Colorir histograma por regiao**: Barras abaixo de P10 e acima de P90 em tom mais claro; regiao P10-P90 em tom solido; barra contendo a media com accent diferente
- [ ] **Usar gradiente no tornado chart**: Da barra mais impactante (cor saturada) para a menos impactante (cor desaturada)
- [ ] **Adicionar legenda ao destaque verde** nos Segmentos: "Maior taxa de adocao" como tooltip ou label
- [ ] **Adicionar tooltip ao badge "ajustado"**: Explicar que o usuario ja respondeu essa premissa

---

## 5. Design de Componentes

### 5.1 Cards de Experimento

**Problema**: Card de experimento muito simples - mostra apenas nome, hipotese (repetida como titulo e descricao), contagem "0" de entrevistas e data.
**Melhoria**:
- [ ] Adicionar status visual do experimento (tag: "DAG gerado", "Simulado", "Entrevistado")
- [ ] Mostrar mini-sparkline ou indicador visual do resultado (ex: "Media: 62.1%")
- [ ] Incluir grupo de synths como badge no card

### 5.2 Cards de Synths (Grid)

**Problema**: Avatares com iniciais coloridas sao vibrantes mas o grid nao tem nenhum filtro ou busca. Com 500 synths em 12 paginas, encontrar um synth especifico e impossivel.
**Melhoria**:
- [ ] Adicionar busca por nome no topo da lista de synths
- [ ] Adicionar filtros por demografico (idade, genero, escolaridade)
- [ ] Considerar tabela com sort alternativa ao grid de cards

### 5.3 Modal de Synth Detail

**Problema**: O modal mostra informacoes uteis mas de forma muito plain - lista de campo: valor sem formatacao visual.
**Melhoria**:
- [ ] Usar layout de 2 colunas para demografia (campo a esquerda, valor a direita)
- [ ] Adicionar icones nos campos (localizar pin, moeda, etc.)
- [ ] As gauge bars de Sensibilidades sao boas, manter como estao

### 5.4 Modal de Novo Grupo de Synths

**Problema**: Este e o melhor modal em termos de UX - sliders interativos, preview visual com stacked bar. E bem executado.
**Melhoria menor**:
- [ ] A aba PcD e Conhecimento sao muito simples (apenas 1 dropdown cada). Considerar combina-las em uma unica aba "Outros"

### 5.5 Tabela de Sensibilidade

**Problema**: Headers da tabela ("Premissa", "Impacto", "Cenario Baixo", "Cenario Alto") sao claros, mas a tabela nao tem zebra striping e os valores nao sao faceis de escanear.
**Melhoria**:
- [ ] Adicionar zebra striping (bg-slate-50 em linhas pares)
- [ ] Usar `font-tabular-nums` ou `font-mono` nos numeros
- [ ] Considerar barras inline no valor de impacto (mini bar chart na celula)

---

## 6. Empty States

### Problemas Identificados

**6.1 Abas Entrevistas, Materiais e Relatorios**
- Todas mostram mensagem + icone generico. Funcional mas sem personalidade.
- "Relatorios serao gerados automaticamente apos analises e exploracoes" e informativo mas nao guia o usuario ao proximo passo.

**6.2 Lista de Experimentos com 1 item**
- Nao ha onboarding ou sugestao para usuarios novos.

### Recomendacoes

- [ ] **Entrevistas empty state**: Adicionar steps visuais ("1. Gere um roteiro 2. Configure a entrevista 3. Veja resultados") em vez de apenas texto
- [ ] **Materiais empty state**: O dropzone de upload e bom, mas poderia ter exemplos do que anexar ("Mockups, screenshots, documentos de referencia")
- [ ] **Relatorios**: Mostrar mini-preview de como sera o relatorio quando gerado (skeleton/mockup)
- [ ] **Home vazia**: Card de "Primeiros passos" ou "Como comecar" com 3-4 steps ilustrados

---

## 7. Interacao & Feedback

### Problemas Identificados

**7.1 Premissas causais sem indicacao de progresso**
- O badge "8/10 ajustadas" e bom, mas nao ha indicacao visual inline de quais premissas faltam ajustar. O usuario precisa expandir cada uma para descobrir.

**7.2 Botoes de acao ao final da pagina**
- "Gerar Resumo da Simulacao" e "Gerar roteiro de entrevista" ficam no fundo da pagina de Simulacao, apos scroll. Ações primarias nao deveriam exigir scroll para serem encontradas.

**7.3 Botao "Deletar" solitario no rodape**
- O botao vermelho "Deletar" fica isolado no final de todas as abas do experimento, muito distante do conteudo. E facil de clicar acidentalmente ao scrollar.

**7.4 Tag input sem feedback**
- O campo "Adicionar tag..." com botao "+" nao mostra tags existentes nem da feedback visual ao adicionar.

### Recomendacoes

- [ ] **Indicar premissas nao ajustadas**: Dot amarelo ou icone de alerta nas premissas que ainda nao foram respondidas
- [ ] **Sticky action bar**: Mover botoes de acao para um sticky footer bar ou floating action menu
- [ ] **Proteger botao Deletar**: Mover para menu dropdown (3 dots) no header, com confirmacao dialog
- [ ] **Melhorar UX de tags**: Mostrar tags como chips clicaveis acima do input; auto-suggest

---

## 8. Responsividade

### Problemas Identificados

**8.1 Layout fixo em max-w-7xl**
- O `max-w-7xl` (~80rem/1280px) funciona bem em desktop mas:
  - Em telas muito grandes (1920px+), ha muito espaco lateral desperdicado
  - Em tablets (~768px), o layout de 2 colunas (DAG + premissas) pode ficar apertado

**8.2 Grid de synths fixo em 3 colunas**
- Os cards de synths parecem usar grid fixo de 3 colunas. Em telas menores, os cards ficariam espremidos.

**8.3 Modal de Novo Grupo nao responsivo**
- O modal com sliders e graficos pode ser problematico em telas menores.

### Recomendacoes

- [ ] **Testar em tablet** (768px-1024px) e corrigir breakpoints do grid de synths (1 col mobile, 2 cols tablet, 3 cols desktop)
- [ ] **DAG + Premissas**: Stack vertical em telas < 1024px
- [ ] **Tabela de sensibilidade**: Considerar horizontal scroll em mobile ou layout de cards

---

## 9. Consistencia

### Problemas Identificados

**9.1 Texto com e sem acentos misturados**
- Alguns textos no modal "Novo Grupo" nao tem acentos: "Configure as distribuicoes demograficas", "Descricao", "Numero maximo de perguntas". Enquanto o resto do app usa acentos corretamente.

**9.2 Formato de data inconsistente**
- Cards de experimento: "ha 2 dias" (relativo)
- Simulacao: "14/02/2026, 13:30:26" (absoluto com hora)
- Nao ha padrao consistente

**9.3 Botoes de acao com estilo misto**
- "Novo Experimento" e "Novo Grupo" usam estilo `btn-primary` (gradiente roxo)
- "Nova Entrevista" usa estilo `btn-primary`
- "Ver Roteiro" usa estilo outline
- "Gerar Resumo da Simulacao" usa outline; "Gerar roteiro de entrevista" usa primary
- A hierarquia de importancia entre esses botoes nao e clara

**9.4 Modais com padding inconsistente**
- Modal "Novo Experimento" tem spacing generoso
- Modal "Nova Entrevista" e mais compacto
- Modal "Roteiro de Entrevista" tem padding completamente diferente (mais editorial)

### Recomendacoes

- [ ] **Corrigir acentuacao** em todos os textos do modal de Novo Grupo
- [ ] **Padronizar datas**: Usar relativo para listas ("ha 2 dias"), absoluto para detalhes ("14 fev 2026, 13:30")
- [ ] **Definir hierarquia de botoes**: Primary (CTA principal da pagina), Secondary (acoes secundarias), Ghost (acoes terciarias)
- [ ] **Padronizar padding de modais**: Definir padding base (p-6) e usa-lo em todos

---

## 10. Recomendacoes Priorizadas por Impacto

### Alta Prioridade (Quick Wins - Alto Impacto Visual)

| # | Melhoria | Esforco | Impacto |
|---|----------|---------|---------|
| 1 | Corrigir acentuacao nos textos sem acento | Baixo | Alto (profissionalismo) |
| 2 | Adicionar card/borda no container do DAG | Baixo | Medio (consistencia) |
| 3 | Mover botao Deletar para menu dropdown | Baixo | Alto (seguranca) |
| 4 | Zebra striping + font-mono na tabela de sensibilidade | Baixo | Medio (legibilidade) |
| 5 | Adicionar tooltip no badge "ajustado" das premissas | Baixo | Medio (clareza) |

### Media Prioridade (Melhorias Estruturais)

| # | Melhoria | Esforco | Impacto |
|---|----------|---------|---------|
| 6 | Breadcrumbs nas paginas de detalhe | Medio | Alto (navegacao) |
| 7 | Compactar header do experimento | Medio | Medio (espaco util) |
| 8 | Sticky action bar para botoes de geracao | Medio | Alto (descobribilidade) |
| 9 | Indicar premissas nao ajustadas visualmente | Medio | Alto (UX) |
| 10 | Busca/filtro na lista de synths | Medio | Alto (usabilidade) |

### Baixa Prioridade (Refinamentos de Longo Prazo)

| # | Melhoria | Esforco | Impacto |
|---|----------|---------|---------|
| 11 | Redesenhar blocos de interpretacao com tipografia serif | Medio | Medio (diferenciacao) |
| 12 | Colorir histograma por regiao P10/P90 | Alto | Medio (data viz) |
| 13 | Empty states com steps visuais | Medio | Medio (onboarding) |
| 14 | Diferenciar sub-abas de Simulacao das abas principais | Medio | Medio (hierarquia) |
| 15 | Layout responsivo para tablet | Alto | Baixo (base de usuarios) |

---

## Conclusao

O SynthLab tem uma fundacao tecnica excelente (shadcn/ui, design system em globals.css, boa separacao de componentes). As melhorias mais impactantes sao:

1. **Navegacao e wayfinding** - Breadcrumbs + indicadores de estado nas abas
2. **Polimento visual** - Acentos, padding consistente, hierarquia tipografica
3. **Acoes contextuais** - Sticky action bar, menu de acoes, protecao contra delete acidental
4. **Dados mais legíveis** - Formatacao de tabelas, coloracao de charts, destaque de insights

Nenhuma das melhorias requer reestruturacao arquitetural. Todas podem ser implementadas incrementalmente usando o design system existente.
