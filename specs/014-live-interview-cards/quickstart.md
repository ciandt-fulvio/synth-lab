# Guia Rápido: Cards de Entrevistas ao Vivo

**Funcionalidade**: 014-live-interview-cards
**Data**: 2025-12-21
**Versão**: 1.0.0

## Visão Geral

Os **Cards de Entrevistas ao Vivo** permitem monitorar múltiplas entrevistas simultâneas em tempo real através de uma grade de duas colunas. Cada card exibe a conversa conforme acontece, com rolagem automática para mostrar as mensagens mais recentes, identificação do synth entrevistado, e capacidade de expandir para visualização completa.

**Benefícios Principais**:

- 📊 **Monitoramento Paralelo**: Veja todas as entrevistas acontecendo ao mesmo tempo
- ⚡ **Atualizações em Tempo Real**: Mensagens aparecem instantaneamente conforme são geradas
- 🎯 **Identificação Rápida**: Avatar, nome e idade do synth em cada card
- 🔍 **Expansão Sem Perda de Contexto**: Clique para ver transcrição completa sem sair da visão de monitoramento

---

## Como Acessar

### 1. Navegar para Detalhes da Execução

A partir da lista de execuções de pesquisa, clique em qualquer card de execução para abrir a página de detalhes.

**Caminho de Navegação**:
```
Página Inicial → Lista de Entrevistas → [Clique em uma execução] → Detalhes da Entrevista
```

### 2. Visualizar Cards ao Vivo

Na página de detalhes da entrevista, você verá automaticamente:

- **Informações da Entrevista** (parte superior):
  - Nome do tópico
  - Status da execução ("Em Execução", "Concluído", etc.)
  - Horários de início e conclusão
  - Total de synths, bem-sucedidos e falhas

- **Cards de Entrevistas ao Vivo** (seção principal):
  - Grade de duas colunas com cards de 200px de altura
  - Cada card representa uma entrevista individual
  - Mensagens rolam automaticamente conforme chegam

- **Botões de Artefatos** (lateral direita):
  - "Gerar Summary" / "Visualizar Summary"
  - "Gerar PR/FAQ" / "Visualizar PR/FAQ"

---

## Anatomia de um Card ao Vivo

Cada card de entrevista ao vivo possui:

### Cabeçalho do Card

- **Avatar do Synth**: Foto do perfil do entrevistado
- **Título**: Formato "Entrevista com [Nome], [Idade] anos"
  - Exemplo: "Entrevista com Maria, 29 anos"
  - Se idade não disponível: "Entrevista com João"

### Área de Mensagens (Rolável)

- **Altura Fixa**: 200px com rolagem interna
- **Formato das Mensagens**:
  - **SynthLab** (azul #2563eb): Entrevistador fazendo perguntas
  - **Nome do Synth** (verde #16a34a): Respostas do entrevistado
  - Texto da mensagem em cinza para fácil leitura

**Exemplo de Conversa**:

```
SynthLab: Olá! Obrigado por participar — vou fazer algumas perguntas sobre suas experiências de compra online, especialmente na Amazon.

Maria: Oi! Tudo bem, pode perguntar.

SynthLab: Para começar, você pode me contar sobre a última vez que comprou algo na Amazon?

Maria: Comprei adubo e uma enxada na Amazon em agosto de 2023. Procurei os produtos no site, encontrei as opções, adicionei ao carrinho e finalizei a compra.
```

### Interação com o Card

- **Clique em Qualquer Lugar do Card**: Abre o popup de transcrição completa
- **Rolagem Manual**: Você pode rolar para cima para revisar mensagens anteriores
- **Rolagem Automática**: Se você estiver na parte inferior, novas mensagens rolam automaticamente

---

## Comportamentos de Rolagem Automática

### Quando Você Está na Parte Inferior

✅ **Rolagem Automática Ativa**: Novas mensagens aparecem automaticamente na parte inferior do card, mantendo você sincronizado com a conversa mais recente.

**Como Funciona**:
- Sistema detecta que você está a menos de 50px da parte inferior
- Quando nova mensagem chega, rola suavemente para mostrá-la
- Você sempre vê as respostas mais recentes sem precisar rolar manualmente

### Quando Você Rola para Cima (Revisando Mensagens Antigas)

⏸️ **Rolagem Automática Pausada**: Sistema detecta que você está revisando mensagens anteriores e não interrompe sua leitura.

**Como Funciona**:
- Você rola para cima para ler mensagens mais antigas
- Novas mensagens continuam chegando, mas não forçam rolagem
- Você mantém controle total da sua posição de leitura
- **Para Retomar Auto-Rolagem**: Basta rolar manualmente de volta para a parte inferior

---

## Expandir para Transcrição Completa

### Abrir Popup de Transcrição

**Como**:
1. Clique em qualquer lugar do card
2. Popup grande (70% largura, 80% altura) abre instantaneamente
3. Mostra transcrição completa da entrevista com o synth

**O Popup Inclui**:
- **Cabeçalho**: Avatar, nome e idade do synth (mesmo formato do card)
- **Transcrição Completa**: Todas as mensagens da conversa
- **Rolagem Ilimitada**: Sem limite de 200px, veja toda a conversa
- **Fechar**: Clique no X ou fora do popup para retornar aos cards ao vivo

### Cards Continuam Atualizando em Segundo Plano

✨ **Funcionalidade Importante**: Enquanto você está visualizando a transcrição completa de uma entrevista, os outros cards continuam recebendo e exibindo novas mensagens em tempo real.

**Benefício**: Você pode se aprofundar em uma conversa específica sem perder atualizações das outras entrevistas paralelas.

---

## Estados dos Cards

### Card Ativo (Entrevista em Andamento)

- **Aparência**: Mensagens aparecendo em tempo real
- **Comportamento**: Novas linhas de conversa a cada 10-30 segundos (varia conforme LLM)
- **Status**: Indica que a entrevista ainda está acontecendo

### Card Concluído (Entrevista Finalizada)

- **Aparência**: Mesma aparência visual que cards ativos
- **Comportamento**: Sem novas mensagens chegando
- **Status**: Conversa completa, todas as perguntas respondidas
- **Permanece Visível**: Você pode revisar a conversa completa mesmo após conclusão

### Card com Falha (Erro na Entrevista)

- **Aparência**: Similar aos outros cards
- **Comportamento**: Pode ter menos mensagens (interrompido por erro)
- **Status**: Indica que a entrevista encontrou um problema
- **Permanece Visível**: Você pode ver o que foi capturado antes da falha

---

## Layout Responsivo

### Desktop/Laptop (Padrão)

- **Duas Colunas**: Cards organizados em grade 2x N
- **Largura**: Cards ocupam ~50% da largura cada
- **Espaçamento**: Gap de 16px entre cards
- **Ordem**: Cards aparecem em ordem consistente (por synth_id ou tempo de início)

### Tablet/Mobile

- **Uma Coluna**: Cards empilhados verticalmente
- **Largura**: Cards ocupam 100% da largura disponível
- **Altura**: Mantém 200px de altura fixa
- **Rolagem**: Página inteira rola para ver todos os cards

---

## Entendendo os Indicadores de Status

### Informações da Entrevista (Parte Superior)

- **Status**: Badge colorido indicando estado da execução
  - "Em Execução" (azul): Entrevistas acontecendo agora
  - "Concluído" (verde): Todas as entrevistas finalizadas
  - "Falhou" (vermelho): Execução encontrou erro crítico

- **Total de Synths**: Número de entrevistas iniciadas
- **Bem-sucedidos**: Entrevistas completadas sem erros
- **Falhas**: Entrevistas que encontraram problemas

**Exemplo**:
```
Total de Synths: 10
Bem-sucedidos: 8
Falhas: 2
```
Significa que 8 entrevistas foram completadas com sucesso, 2 falharam, e você verá 10 cards no total (8 com conversas completas + 2 com conversas parciais).

---

## Dicas de Uso

### Monitoramento Eficiente

✅ **Deixe a Página Aberta Durante Execução**: As entrevistas podem levar 5-10 minutos para completar. Deixe a página aberta para ver o progresso em tempo real.

✅ **Identifique Padrões Rapidamente**: Com todas as conversas visíveis, você pode:
- Notar respostas similares entre synths diferentes
- Identificar insights interessantes conforme surgem
- Comparar comportamentos de compra em tempo real

✅ **Use Expansão Estrategicamente**: Quando ver uma resposta interessante em um card, clique para ler o contexto completo da conversa.

### Revisão de Mensagens Antigas

✅ **Role para Cima Sem Preocupação**: O sistema detecta que você está revisando e pausa a auto-rolagem. Você não será interrompido.

✅ **Retorne para Atualizações ao Vivo**: Basta rolar de volta para a parte inferior do card para retomar a auto-rolagem.

### Múltiplas Entrevistas

✅ **Acompanhe o Card Certo**: Use os avatars e nomes para distinguir rapidamente entre synths.

✅ **Não Precisa Ficar Alternando Tabs**: Diferente de visualizar uma entrevista por vez, você vê todas simultaneamente sem navegar.

---

## Casos de Uso Comuns

### Caso 1: Iniciar e Monitorar Novas Entrevistas

**Cenário**: Você acabou de criar uma nova execução de pesquisa com 10 synths.

**Passos**:
1. Clique no card da execução recém-criada
2. Você é levado para a página de detalhes
3. Veja os 10 cards aparecerem (inicialmente vazios ou com mensagens de saudação)
4. Acompanhe as conversas se desenrolando em tempo real
5. Identifique insights interessantes conforme surgem
6. Clique em cards específicos para ler conversas completas

**Duração Típica**: 5-10 minutos até todas as entrevistas completarem

---

### Caso 2: Revisar Execução Completada

**Cenário**: Você retorna a uma execução que já foi concluída ontem.

**Passos**:
1. Navegue para a execução na lista de entrevistas
2. Clique para abrir detalhes
3. Todos os cards aparecem imediatamente com conversas completas
4. Não há novas mensagens chegando (execução já concluída)
5. Role através dos cards para revisar diferentes conversas
6. Clique em cards específicos para análise detalhada
7. Use botões "Visualizar Summary" ou "Visualizar PR/FAQ" para insights consolidados

**Diferença**: Sem atualizações em tempo real, mas você ainda pode explorar todas as conversas lado a lado.

---

### Caso 3: Identificar Insight Durante Execução

**Cenário**: Você está monitorando entrevistas ao vivo e nota uma resposta particularmente interessante sobre problemas com entrega da Amazon.

**Passos**:
1. Você vê no card de "João, 45 anos" a resposta: "Tive problemas com atraso na entrega..."
2. Clique no card de João para abrir a transcrição completa
3. Leia o contexto completo da conversa sobre o problema de entrega
4. Feche o popup (clique no X ou fora)
5. Volte para a visão de cards ao vivo
6. Continue monitorando outras entrevistas enquanto procura padrões similares

**Benefício**: Você aprofunda em um insight específico sem perder visibilidade das outras conversas.

---

### Caso 4: Comparar Respostas Entre Synths

**Cenário**: Você quer ver como diferentes faixas etárias respondem sobre uso da Amazon.

**Passos**:
1. Identifique cards de synths mais jovens (20-30 anos) vs. mais velhos (50-60 anos)
2. Acompanhe as respostas lado a lado conforme chegam
3. Note padrões: jovens mencionam app mobile, mais velhos mencionam site desktop
4. Clique em exemplos representativos para ler conversas completas
5. Use "Gerar Summary" quando todas as entrevistas completarem para análise consolidada

**Benefício**: Visão imediata de diferenças demográficas sem precisar alternar entre páginas.

---

## Perguntas Frequentes (FAQ)

### Por que alguns cards não estão recebendo mensagens?

**Resposta**: Entrevistas podem estar em ritmos diferentes. O LLM leva tempo variável (5-30 segundos) para gerar cada resposta. É normal algumas entrevistas estarem adiantadas e outras atrasadas.

### Posso rolar manualmente sem perder novas mensagens?

**Resposta**: Sim! Role para cima para revisar mensagens antigas. O sistema pausa a auto-rolagem. Quando terminar, role de volta para a parte inferior e a auto-rolagem retoma automaticamente.

### O que acontece se eu fechar a página durante uma execução?

**Resposta**: As entrevistas continuam acontecendo no backend. Quando você retornar e abrir a página de detalhes novamente, todos os cards aparecerão com as mensagens geradas até aquele momento (histórico replay), e então você continuará vendo atualizações ao vivo para entrevistas ainda em andamento.

### Por que a transcrição completa (popup) mostra as mesmas mensagens do card?

**Resposta**: O popup é uma visão expandida do mesmo conteúdo. A diferença é que o popup não tem limite de 200px de altura, então você pode ver a conversa completa sem limitações de espaço. Útil para conversas mais longas.

### Posso exportar ou compartilhar as conversas?

**Resposta**: Atualmente não (fora do escopo desta funcionalidade). Para exportar ou compartilhar, use os artefatos "Summary" ou "PR/FAQ" que consolidam insights de todas as entrevistas.

### Quantas entrevistas posso monitorar simultaneamente?

**Resposta**: O sistema foi testado com até 20 entrevistas simultâneas sem degradação de performance. Execuções típicas têm 4-10 entrevistas.

### Os cards aparecem em alguma ordem específica?

**Resposta**: Sim, os cards aparecem em ordem consistente (por ID do synth ou tempo de início da primeira mensagem) para evitar reorganizações conforme novos cards aparecem.

---

## Solução de Problemas

### Cards não aparecem ou ficam vazios

**Problema**: Abri a página de detalhes mas não vejo nenhum card.

**Soluções**:
1. Verifique se a execução foi iniciada corretamente (status deve ser "Em Execução" ou "Concluído")
2. Aguarde alguns segundos - conexão SSE pode estar sendo estabelecida
3. Recarregue a página (F5 ou Cmd+R)
4. Verifique console do navegador para erros (F12 → Console)

### Mensagens não atualizam em tempo real

**Problema**: Cards aparecem mas não recebem novas mensagens.

**Soluções**:
1. Verifique conexão de internet
2. Verifique se a execução ainda está "Em Execução" (se estiver "Concluído", não haverá novas mensagens)
3. Abra console do navegador (F12) e veja se há erros de conexão SSE
4. Tente recarregar a página para restabelecer conexão

### Rolagem automática não funciona

**Problema**: Novas mensagens chegam mas card não rola automaticamente.

**Soluções**:
1. Verifique se você está na parte inferior do card (role manualmente até o fim)
2. Se estiver revisando mensagens antigas (rolado para cima), auto-rolagem está pausada propositalmente
3. Role de volta para a parte inferior para retomar auto-rolagem

### Popup de transcrição não abre

**Problema**: Clico no card mas o popup não aparece.

**Soluções**:
1. Certifique-se de clicar na área do card (não em elementos interativos como botões, se houver)
2. Verifique console do navegador para erros JavaScript
3. Tente outro card para ver se o problema é específico de um card ou geral
4. Recarregue a página

---

## Próximos Passos

Depois de usar os Cards de Entrevistas ao Vivo:

1. **Gerar Summary**: Clique em "Gerar Summary" para obter análise consolidada de todas as entrevistas
2. **Gerar PR/FAQ**: Clique em "Gerar PR/FAQ" para formato estruturado de perguntas e respostas
3. **Explorar Transcrições Individuais**: Clique em cards específicos para análise detalhada de conversas
4. **Criar Nova Execução**: Volte para lista de entrevistas e inicie nova pesquisa com outro tópico

---

## Resumo de Comandos Rápidos

| Ação | Como Fazer |
|------|------------|
| **Abrir Cards ao Vivo** | Clique em qualquer execução na lista de entrevistas |
| **Ver Transcrição Completa** | Clique em um card |
| **Fechar Transcrição** | Clique no X ou fora do popup |
| **Pausar Auto-Rolagem** | Role para cima no card |
| **Retomar Auto-Rolagem** | Role manualmente de volta para a parte inferior |
| **Identificar Synth** | Olhe para avatar e nome no cabeçalho do card |
| **Ver Status da Execução** | Olhe para badge de status na parte superior da página |

---

## Suporte

Para problemas não resolvidos por este guia:

- Verifique console do navegador (F12 → Console) para erros detalhados
- Relate bugs ou solicite funcionalidades através do sistema de issues do projeto
- Consulte documentação técnica em `specs/014-live-interview-cards/` para detalhes de implementação

**Versão do Guia**: 1.0.0 | **Última Atualização**: 2025-12-21
