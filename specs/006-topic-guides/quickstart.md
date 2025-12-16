# Guia Rápido: Topic Guides

**Funcionalidade**: Guias de Tópicos com Contexto Multi-Modal
**Versão**: 1.0.0
**Data**: 2025-12-16

## Visão Geral

Topic Guides permitem organizar materiais de contexto (imagens, PDFs, documentos) em diretórios estruturados e gerar descrições automáticas com IA para cada arquivo. Os synths podem acessar esses materiais durante entrevistas de pesquisa UX para fornecer respostas contextualizadas.

## Instalação

Os topic guides fazem parte do synth-lab. Nenhuma instalação adicional é necessária além das dependências do projeto:

```bash
# Instalar dependências
pip install -e .

# Verificar instalação
synthlab topic-guide --help
```

## Primeiros Passos

### 1. Criar um Topic Guide

Crie um novo topic guide para organizar seus materiais de contexto:

```bash
synthlab topic-guide create --name amazon-ecommerce
```

**Saída**:
```
✓ Topic guide 'amazon-ecommerce' criado com sucesso
  Caminho: /Users/user/synth-lab/data/topic_guides/amazon-ecommerce
  Adicione arquivos a este diretório e execute 'synthlab topic-guide update --name amazon-ecommerce'
```

Isso cria:
- Diretório: `data/topic_guides/amazon-ecommerce/`
- Arquivo: `summary.md` com estrutura inicial

### 2. Adicionar Arquivos de Contexto

Copie seus materiais de pesquisa para o diretório do topic guide:

```bash
# Exemplo: screenshots da Amazon
cp screenshots/*.png data/topic_guides/amazon-ecommerce/

# Exemplo: documentos de pesquisa
cp documentos/*.pdf data/topic_guides/amazon-ecommerce/
cp notas/*.md data/topic_guides/amazon-ecommerce/
```

**Tipos de arquivo suportados**:
- Imagens: PNG, JPEG
- Documentos: PDF, Markdown (.md), Texto (.txt)

### 3. Gerar Descrições Automáticas

Execute o comando de atualização para processar todos os arquivos:

```bash
synthlab topic-guide update --name amazon-ecommerce
```

**Saída**:
```
Atualizando topic guide 'amazon-ecommerce'...

Processando arquivos:
  ✓ product-page.png - descrito com sucesso
  ✓ checkout-flow.pdf - descrito com sucesso
  ✓ payment-screen.png - descrito com sucesso
  ⊘ old-screenshot.png - inalterado (ignorado)
  ⚠ logo.svg - tipo de arquivo não suportado (ignorado)

Resumo:
  - 3 arquivos documentados
  - 1 arquivo inalterado
  - 1 arquivo ignorado (tipo não suportado)

Atualizado: /Users/user/synth-lab/data/topic_guides/amazon-ecommerce/summary.md
```

### 4. Visualizar o Topic Guide

Veja os detalhes e descrições geradas:

```bash
synthlab topic-guide show --name amazon-ecommerce
```

**Saída**:
```
Topic Guide: amazon-ecommerce
Caminho: data/topic_guides/amazon-ecommerce

Descrição do Contexto:
  Este guia contém materiais sobre a experiência de compra na Amazon.

Arquivos (4):
  ✓ product-page.png (documentado)
  ✓ checkout-flow.pdf (documentado)
  ✓ payment-screen.png (documentado)
  ⊘ notes.md (não documentado)

Descrições dos Arquivos:

product-page.png (hash: a3b5c7...):
  Screenshot da página de produto da Amazon mostrando detalhes do item,
  preço, avaliações de clientes e botão de adicionar ao carrinho.
  Interface desktop com navegação superior visível.

checkout-flow.pdf (hash: d4e6f8...):
  Documento descrevendo o fluxo de checkout da Amazon com diagramas de
  cada etapa do processo de finalização de compra.

payment-screen.png (hash: b1c3e5...):
  Tela de pagamento exibindo opções de cartão de crédito, endereço de
  cobrança e resumo do pedido com valor total.
```

### 5. Usar em Entrevistas (Futuro - P3)

Quando implementado, você poderá usar topic guides em entrevistas com synths:

```bash
synthlab research interview \
  --synth-id S001 \
  --topic "Experiência de compra na Amazon" \
  --topic-guide amazon-ecommerce
```

O synth terá acesso às descrições dos materiais e poderá referenciá-los em suas respostas.

## Comandos Principais

### Criar Topic Guide

```bash
synthlab topic-guide create --name <nome-do-guia>
```

**Quando usar**: Ao iniciar um novo projeto de pesquisa ou tópico de estudo.

### Atualizar Topic Guide

```bash
synthlab topic-guide update --name <nome-do-guia>
```

**Quando usar**:
- Após adicionar novos arquivos ao diretório
- Quando arquivos existentes foram modificados
- Para reprocessar todos os arquivos: `--force`

### Listar Topic Guides

```bash
# Lista simples
synthlab topic-guide list

# Lista detalhada
synthlab topic-guide list --verbose
```

**Quando usar**: Para ver todos os topic guides criados e obter visão geral do projeto.

### Exibir Topic Guide

```bash
synthlab topic-guide show --name <nome-do-guia>
```

**Quando usar**: Para visualizar descrições geradas e status de cada arquivo.

## Casos de Uso

### Caso 1: Pesquisa sobre E-commerce

**Objetivo**: Coletar feedback sobre a experiência de checkout da Amazon.

**Passos**:
1. Criar topic guide: `synthlab topic-guide create --name amazon-checkout`
2. Adicionar screenshots de cada etapa do checkout
3. Adicionar PDFs com especificações de funcionalidades
4. Gerar descrições: `synthlab topic-guide update --name amazon-checkout`
5. Conduzir entrevistas com synths usando o contexto

**Arquivos típicos**:
- `cart-view.png` - Visualização do carrinho
- `shipping-info.png` - Tela de informações de envio
- `payment-method.png` - Seleção de forma de pagamento
- `order-review.png` - Revisão final do pedido
- `confirmation.png` - Página de confirmação
- `checkout-specs.pdf` - Especificações técnicas do fluxo

### Caso 2: Teste de Usabilidade Mobile

**Objetivo**: Avaliar app mobile com synths de diferentes perfis.

**Passos**:
1. Criar topic guide: `synthlab topic-guide create --name mobile-app-v2`
2. Adicionar screenshots de diferentes telas do app
3. Adicionar notas de design (.md) e documentação (.pdf)
4. Atualizar: `synthlab topic-guide update --name mobile-app-v2`
5. Realizar testes com múltiplos synths

**Estrutura do diretório**:
```
data/topic_guides/mobile-app-v2/
├── onboarding/
│   ├── welcome.png
│   ├── signup.png
│   └── permissions.png
├── main-features/
│   ├── home.png
│   ├── search.png
│   └── profile.png
├── design-notes.md
└── feature-specs.pdf
```

### Caso 3: Comparação de Interfaces

**Objetivo**: Comparar diferentes versões de uma interface.

**Passos**:
1. Criar topic guides separados:
   - `synthlab topic-guide create --name interface-v1`
   - `synthlab topic-guide create --name interface-v2`
2. Adicionar screenshots correspondentes em cada
3. Atualizar ambos
4. Conduzir entrevistas A/B com synths

## Resolução de Problemas

### Problema: API key não encontrada

**Erro**:
```
✗ Error: OpenAI API key not found
```

**Solução**:
```bash
export OPENAI_API_KEY="sua-chave-aqui"
```

Ou adicione ao arquivo `.env`:
```
OPENAI_API_KEY=sua-chave-aqui
```

### Problema: Tipo de arquivo não suportado

**Erro**:
```
⚠ Warning: Unsupported files skipped:
  - video.mp4
  - logo.svg
```

**Solução**:
- Converta arquivos para formatos suportados (PNG, JPEG, PDF, MD, TXT)
- Ou ignore o aviso - arquivos não suportados são automaticamente ignorados

### Problema: Arquivo muito grande

**Erro**:
```
⚠ Warning: Image logo.png exceeds 20MB, skipping
```

**Solução**:
1. Comprima a imagem antes de adicionar ao topic guide
2. Para PDFs grandes, considere dividir em arquivos menores
3. Limite: 20MB por imagem (limitação da API OpenAI)

### Problema: Falha na API durante processamento

**Erro**:
```
⚠ corrupted.pdf - API failure (placeholder added)
```

**Solução**:
- O sistema adiciona um placeholder automático
- Você pode editar manualmente `summary.md` para adicionar uma descrição
- Ou executar novamente: `synthlab topic-guide update --name <nome> --force`

### Problema: Topic guide não encontrado

**Erro**:
```
✗ Error: Topic guide 'nonexistent' not found
```

**Solução**:
1. Verifique o nome: `synthlab topic-guide list`
2. Ou crie o topic guide: `synthlab topic-guide create --name nonexistent`

## Estrutura do summary.md

O arquivo `summary.md` é gerado automaticamente mas pode ser editado manualmente:

```markdown
# contexto para o guide: amazon-ecommerce

Este guia contém materiais sobre a experiência de compra na Amazon,
incluindo screenshots de diferentes etapas do processo e documentação
técnica do fluxo de checkout.

## FILE DESCRIPTION

- **product-page.png** (hash: a3b5c7d9e1f3a5b7c9d1e3f5a7b9c1d3)
  Screenshot da página de produto da Amazon mostrando detalhes do item,
  preço, avaliações e botão de compra.

- **checkout-flow.pdf** (hash: d4e6f8a0b2c4d6e8f0a2b4c6d8e0f2a4)
  Documento com diagramas do fluxo de checkout em cada etapa.
```

**Seções**:
1. **Título**: Nome do topic guide
2. **Contexto**: Descrição geral (editável)
3. **FILE DESCRIPTION**: Catálogo automático de arquivos (gerado pelo sistema)

## Dicas e Boas Práticas

### Organização de Arquivos

✅ **Bom**:
- Use nomes descritivos: `product-page-desktop.png`, `checkout-step-1.png`
- Agrupe por categoria em subdiretórios
- Mantenha tamanhos razoáveis (<10MB por arquivo)

❌ **Evite**:
- Nomes genéricos: `screen1.png`, `image.png`
- Misturar arquivos de diferentes projetos
- Arquivos muito grandes (>20MB)

### Atualização de Topic Guides

- Execute `update` apenas quando adicionar/modificar arquivos
- O sistema detecta mudanças automaticamente (via hash de conteúdo)
- Use `--force` apenas se precisar reprocessar tudo

### Edição Manual do summary.md

- Você pode editar a seção de contexto geral
- **Não edite** a seção `## FILE DESCRIPTION` manualmente
- Se editar descrições, elas serão sobrescritas no próximo `update`

### Performance e Custos

- Processamento: ~5 segundos por arquivo
- Custo: ~$0.000054 por arquivo (desprezível)
- Para 20 arquivos: ~2 minutos, ~$0.001

## Referência Rápida

| Tarefa | Comando |
|--------|---------|
| Criar novo guide | `synthlab topic-guide create --name <nome>` |
| Atualizar guide | `synthlab topic-guide update --name <nome>` |
| Listar guides | `synthlab topic-guide list` |
| Ver detalhes | `synthlab topic-guide show --name <nome>` |
| Reprocessar tudo | `synthlab topic-guide update --name <nome> --force` |
| Ver ajuda | `synthlab topic-guide --help` |

## Próximos Passos

1. **Criar seu primeiro topic guide** para um projeto real
2. **Adicionar materiais** relevantes (screenshots, docs)
3. **Gerar descrições** e revisar resultados
4. **Integrar com entrevistas** quando P3 for implementado

## Suporte

- **Documentação completa**: `docs/topic-guides/`
- **Exemplos**: `examples/topic-guides/`
- **Issues**: Reportar problemas no repositório

---

**Versão**: 1.0.0 | **Última atualização**: 2025-12-16
