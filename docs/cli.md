# CLI - Interface de Linha de Comando synth-lab

## Visão Geral

O synth-lab oferece uma CLI (Command Line Interface) moderna e intuitiva construída com **Typer** e **Rich** para formatação de saída.

### Características

- **Framework**: Typer 0.9+
- **Output**: Rich tables, progress bars, colorização
- **Comandos**: Organizados por módulo (synth, topic-guide, research)
- **Validação**: Type hints e Pydantic para validação automática
- **Help**: Documentação inline com `--help`

### Entry Point

```bash
uv run synthlab <command> [options]
```

---

## Instalação

```bash
# Clonar repositório
git clone <repo-url>
cd synth-lab

# Instalar dependências
uv sync

# Configurar API Key
export OPENAI_API_KEY="sk-your-api-key-here"

# Inicializar banco de dados
uv run python scripts/migrate_to_sqlite.py

# Testar CLI
uv run synthlab --help
```

---

## Comandos Disponíveis

### 1. Comandos de Geração (gensynth)

#### 1.1 Gerar Synths

```bash
synthlab gensynth [OPTIONS]
```

**Opções**:

| Opção | Tipo | Padrão | Descrição |
|-------|------|--------|-----------|
| `-n, --count` | int | 1 | Número de synths a gerar |
| `--avatar` | flag | False | Gerar avatares visuais |
| `-b, --avatar-blocks` | int | auto | Número de blocos de avatares (9 por bloco) |
| `--synth-ids` | str | None | IDs específicos para gerar avatares (separados por vírgula) |
| `--benchmark` | flag | False | Mostrar métricas de performance |
| `--quiet` | flag | False | Modo silencioso (minimal output) |
| `--output` | str | data/synths | Diretório de saída customizado |
| `--arquetipo` | str | None | Arquétipo específico para geração |

**Exemplos**:

```bash
# Gerar um synth
uv run synthlab gensynth -n 1

# Gerar 100 synths
uv run synthlab gensynth -n 100

# Gerar 9 synths com avatares (1 bloco)
uv run synthlab gensynth -n 9 --avatar

# Gerar 27 synths com avatares (3 blocos automáticos)
uv run synthlab gensynth -n 27 --avatar

# Gerar 5 blocos de avatares (45 synths)
uv run synthlab gensynth --avatar -b 5

# Gerar avatares para synths específicos
uv run synthlab gensynth --avatar --synth-ids ynnasw,abc123,def456

# Gerar avatares para todos os synths sem avatar
uv run synthlab gensynth --avatar

# Com benchmark
uv run synthlab gensynth -n 100 --benchmark

# Modo silencioso
uv run synthlab gensynth -n 50 --quiet

# Output customizado
uv run synthlab gensynth -n 10 --output ./meus-synths/

# Arquétipo específico
uv run synthlab gensynth -n 5 --arquetipo "Jovem Adulto Sudeste"
```

**Output Exemplo**:

```
✓ Synth gerado: ynnasw - Ravy Lopes
  Arquétipo: Jovem Adulto Sudeste
  Idade: 32 anos
  Ocupação: Desenvolvedor de software
  Localização: São Paulo, SP

✓ Avatar gerado: output/synths/avatar/ynnasw.png
  Modelo: dall-e-3
  Tamanho: 341x341 pixels
```

---

#### 1.2 Validar Synths

```bash
synthlab gensynth --validate-all
```

Valida todos os synths no diretório padrão.

**Opções**:

| Opção | Tipo | Descrição |
|-------|------|-----------|
| `--validate-all` | flag | Validar todos os synths |
| `--validate-file` | str | Validar arquivo específico |

**Exemplos**:

```bash
# Validar todos
uv run synthlab gensynth --validate-all

# Validar arquivo específico
uv run synthlab gensynth --validate-file data/synths/ynnasw.json
```

**Output Exemplo**:

```
✓ Validando synth ynnasw... OK
✓ Validando synth abc123... OK
✗ Validando synth def456... FALHOU
  Erro: Campo 'demografia.idade' fora do range (150)

Total: 3 synths
Válidos: 2 (66.7%)
Inválidos: 1 (33.3%)
```

---

#### 1.3 Analisar Distribuições

```bash
synthlab gensynth --analyze <type>
```

Analisa distribuições demográficas vs. IBGE.

**Tipos de Análise**:

| Tipo | Descrição |
|------|-----------|
| `region` | Distribuição por região |
| `age` | Distribuição etária |
| `all` | Ambas as distribuições |

**Exemplos**:

```bash
# Analisar distribuição regional
uv run synthlab gensynth --analyze region

# Analisar distribuição etária
uv run synthlab gensynth --analyze age

# Analisar todas
uv run synthlab gensynth --analyze all
```

**Output Exemplo**:

```
┌─────────────┬───────────┬───────────┬─────────┐
│ Região      │ Synths    │ IBGE      │ Erro    │
├─────────────┼───────────┼───────────┼─────────┤
│ Sudeste     │ 42.3%     │ 42.0%     │ +0.7%   │
│ Nordeste    │ 27.1%     │ 27.2%     │ -0.4%   │
│ Sul         │ 14.8%     │ 14.3%     │ +3.5%   │
│ Norte       │ 8.9%      │ 8.6%      │ +3.5%   │
│ Centro-Oeste│ 6.9%      │ 7.9%      │ -12.7%  │
└─────────────┴───────────┴───────────┴─────────┘

✓ Erro médio: 4.16% (dentro do limite de 10%)
```

---

### 2. Comandos de Consulta (listsynth)

#### 2.1 Listar Todos os Synths

```bash
synthlab listsynth [OPTIONS]
```

**Opções**:

| Opção | Tipo | Descrição |
|-------|------|-----------|
| `--limit` | int | Número máximo de resultados (padrão: 50) |
| `--where` | str | Cláusula WHERE SQL |
| `--full-query` | str | Query SQL completa |
| `--fields` | str | Campos a exibir (separados por vírgula) |

**Exemplos**:

```bash
# Listar todos (padrão 50)
uv run synthlab listsynth

# Limitar a 10 resultados
uv run synthlab listsynth --limit 10

# Filtrar por idade
uv run synthlab listsynth --where "demografia.idade > 30"

# Filtrar por cidade
uv run synthlab listsynth --where "demografia.localizacao.cidade = 'São Paulo'"

# Filtrar por alfabetização digital
uv run synthlab listsynth --where "capacidades_tecnologicas.alfabetizacao_digital < 40"

# Filtrar por múltiplas condições
uv run synthlab listsynth --where "demografia.idade BETWEEN 25 AND 35 AND demografia.renda_mensal > 5000"

# Query SQL completa
uv run synthlab listsynth --full-query "SELECT id, nome, demografia.idade FROM synths LIMIT 10"

# Agrupar por cidade
uv run synthlab listsynth --full-query "SELECT demografia.localizacao.cidade as cidade, COUNT(*) as total FROM synths GROUP BY cidade"

# Campos específicos
uv run synthlab listsynth --fields id,nome,demografia.idade,demografia.localizacao.cidade
```

**Output Exemplo**:

```
┌────────┬─────────────────┬──────┬─────────────┬──────────────────────┐
│ ID     │ Nome            │ Idade│ Arquétipo   │ Cidade               │
├────────┼─────────────────┼──────┼─────────────┼──────────────────────┤
│ ynnasw │ Ravy Lopes      │ 32   │ Jovem       │ São Paulo            │
│ abc123 │ Maria Silva     │ 28   │ Jovem       │ Rio de Janeiro       │
│ def456 │ João Santos     │ 45   │ Meia-Idade  │ Belo Horizonte       │
└────────┴─────────────────┴──────┴─────────────┴──────────────────────┘

Total: 3 synths
```

---

### 3. Comandos de Topic Guides (topic-guide)

#### 3.1 Criar Topic Guide

```bash
synthlab topic-guide create --name <name>
```

**Opções**:

| Opção | Tipo | Requerido | Descrição |
|-------|------|-----------|-----------|
| `--name` | str | Sim | Nome do topic guide (slug) |
| `--display-name` | str | Não | Nome formatado |
| `--description` | str | Não | Descrição do topic |

**Exemplos**:

```bash
# Criar topic guide básico
uv run synthlab topic-guide create --name amazon-ecommerce

# Com display name e descrição
uv run synthlab topic-guide create \
  --name mobile-banking \
  --display-name "Mobile Banking UX" \
  --description "Entrevista sobre experiência com apps de banco digital"
```

**Output Exemplo**:

```
✓ Topic guide criado: amazon-ecommerce
  Path: data/topic_guides/amazon-ecommerce/
  Arquivos:
    - script.json (criado)
    - summary.md (criado)

Próximos passos:
1. Copie imagens/PDFs para o diretório criado
2. Execute: synthlab topic-guide update --name amazon-ecommerce
```

---

#### 3.2 Atualizar Topic Guide

```bash
synthlab topic-guide update --name <name> [--force]
```

Escaneia arquivos no diretório do topic guide e gera descrições automáticas com IA.

**Opções**:

| Opção | Tipo | Descrição |
|-------|------|-----------|
| `--name` | str | Nome do topic guide |
| `--force` | flag | Re-processar todos os arquivos (ignora cache) |

**Exemplos**:

```bash
# Atualizar descrições (apenas arquivos novos/modificados)
uv run synthlab topic-guide update --name amazon-ecommerce

# Forçar re-processamento de todos os arquivos
uv run synthlab topic-guide update --name amazon-ecommerce --force
```

**Output Exemplo**:

```
✓ Escaneando arquivos em data/topic_guides/amazon-ecommerce/...
  Encontrados: 8 arquivos

✓ Processando imagens com Vision API...
  [1/5] home-page.png... OK (descrição gerada)
  [2/5] product-detail.png... OK (descrição gerada)
  [3/5] checkout.png... CACHE (não modificado)
  [4/5] cart.png... OK (descrição gerada)
  [5/5] payment.png... OK (descrição gerada)

✓ Processando documentos...
  [1/3] user-guide.pdf... OK (conteúdo extraído)
  [2/3] research-findings.md... OK (carregado)
  [3/3] notes.txt... OK (carregado)

✓ Atualizando summary.md...

Total processado: 8 arquivos
Novos/modificados: 5
Do cache: 3
Custo estimado: $0.000270
```

---

#### 3.3 Listar Topic Guides

```bash
synthlab topic-guide list [--verbose]
```

**Opções**:

| Opção | Tipo | Descrição |
|-------|------|-----------|
| `--verbose` | flag | Mostrar detalhes (arquivos, paths) |

**Exemplos**:

```bash
# Listagem básica
uv run synthlab topic-guide list

# Listagem detalhada
uv run synthlab topic-guide list --verbose
```

**Output Exemplo**:

```
┌────────────────────┬───────────────────┬────────────┬─────────────┐
│ Nome               │ Display Name      │ Perguntas  │ Arquivos    │
├────────────────────┼───────────────────┼────────────┼─────────────┤
│ amazon-ecommerce   │ Amazon E-Commerce │ 12         │ 8           │
│ mobile-banking     │ Mobile Banking UX │ 10         │ 6           │
│ food-delivery      │ Food Delivery App │ 8          │ 4           │
└────────────────────┴───────────────────┴────────────┴─────────────┘

Total: 3 topic guides
```

**Output Verbose**:

```
Topic Guide: amazon-ecommerce
  Display Name: Amazon E-Commerce
  Description: Entrevista sobre experiência de compra no e-commerce Amazon
  Path: data/topic_guides/amazon-ecommerce/
  Perguntas: 12
  Arquivos: 8
    - home-page.png (PNG, 245KB)
    - product-detail.png (PNG, 312KB)
    - checkout.png (PNG, 189KB)
    - user-guide.pdf (PDF, 1.2MB)
  Criado em: 2025-12-15 10:00:00
  Atualizado em: 2025-12-19 14:30:00
```

---

#### 3.4 Visualizar Topic Guide

```bash
synthlab topic-guide show --name <name>
```

Exibe conteúdo completo de um topic guide.

**Opções**:

| Opção | Tipo | Descrição |
|-------|------|-----------|
| `--name` | str | Nome do topic guide |

**Exemplos**:

```bash
uv run synthlab topic-guide show --name amazon-ecommerce
```

**Output Exemplo**:

```
═══════════════════════════════════════════════════════
Topic Guide: Amazon E-Commerce
═══════════════════════════════════════════════════════

Descrição: Entrevista sobre experiência de compra no e-commerce Amazon

─────────────────────────────────────────────────────
Script (12 perguntas)
─────────────────────────────────────────────────────

Q1: Como você se sente ao fazer compras online?
    Contexto: Explore sentimentos, medos, preferências

Q2: O que você mais valoriza em um e-commerce?
    Contexto: Facilidade, preço, confiabilidade

...

─────────────────────────────────────────────────────
Arquivos (8 total)
─────────────────────────────────────────────────────

[IMG] home-page.png
  Página inicial da Amazon mostrando categorias de produtos, ofertas
  em destaque e barra de busca proeminente no topo.

[IMG] product-detail.png
  Página de detalhes de produto com galeria de imagens, descrição,
  preço, avaliações e botão de adicionar ao carrinho.

[PDF] user-guide.pdf
  Guia do usuário com instruções passo-a-passo para compra, dicas
  de segurança e FAQ sobre entregas.

...

─────────────────────────────────────────────────────
Summary
─────────────────────────────────────────────────────

Este topic guide contém materiais para entrevistas sobre a experiência
de compra no e-commerce Amazon. Inclui screenshots das principais
telas do fluxo de compra, documentação de usuário e notas de pesquisas
anteriores.

O entrevistador deve usar as imagens como referência ao fazer perguntas
sobre usabilidade, layout e clareza das informações.
```

---

### 4. Comandos de Research (research)

#### 4.1 Entrevista Individual

```bash
synthlab research interview <synth_id> <topic_name> [OPTIONS]
```

**Argumentos Posicionais**:

| Argumento | Tipo | Descrição |
|-----------|------|-----------|
| `synth_id` | str | ID do synth a entrevistar |
| `topic_name` | str | Nome do topic guide |

**Opções**:

| Opção | Tipo | Padrão | Descrição |
|-------|------|--------|-----------|
| `--max-rounds` | int | 6 | Número máximo de turnos |
| `--model` | str | gpt-5-mini | Modelo LLM a usar |
| `--output` | str | data/transcripts | Diretório de saída |

**Exemplos**:

```bash
# Entrevista básica
uv run synthlab research interview ynnasw compra-amazon

# Com mais turnos
uv run synthlab research interview ynnasw compra-amazon --max-rounds 15

# Com modelo diferente
uv run synthlab research interview ynnasw compra-amazon --model gpt-4o

# Output customizado
uv run synthlab research interview ynnasw compra-amazon --output ./minhas-entrevistas
```

**Output Exemplo**:

```
═══════════════════════════════════════════════════════
Entrevista: Ravy Lopes (ynnasw)
Topic: Amazon E-Commerce
═══════════════════════════════════════════════════════

[Turno 1/6]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Interviewer:
Como você se sente ao fazer compras online?

Interviewee:
Eu me sinto bem confortável comprando online. Uso bastante e-commerce,
principalmente a Amazon. Acho prático poder comparar preços e ver
avaliações de outros compradores antes de decidir.

[Turno 2/6]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Interviewer:
O que você mais valoriza em um e-commerce?

Interviewee:
Pra mim, o mais importante é a confiabilidade. Quero ter certeza que
vou receber o produto, que é original e que se tiver problema vou
conseguir resolver facilmente.

...

✓ Entrevista concluída!
  Turnos: 6
  Duração: 2min 34s
  Salvo em: data/transcripts/ynnasw_20251219_143052.json
```

---

#### 4.2 Entrevistas em Batch

```bash
synthlab research batch <topic_name> [OPTIONS]
```

Executa entrevistas com múltiplos synths em paralelo.

**Argumentos Posicionais**:

| Argumento | Tipo | Descrição |
|-----------|------|-----------|
| `topic_name` | str | Nome do topic guide |

**Opções**:

| Opção | Tipo | Padrão | Descrição |
|-------|------|--------|-----------|
| `--synth-ids` | str | None | IDs específicos (separados por vírgula) |
| `--limit` | int | None | Número de synths aleatórios |
| `--max-rounds` | int | 6 | Número máximo de turnos por entrevista |
| `--model` | str | gpt-5-mini | Modelo LLM a usar |
| `--max-concurrent` | int | 5 | Entrevistas paralelas simultâneas |
| `--output` | str | data/transcripts | Diretório de saída |
| `--summary` | flag | False | Gerar summary ao final |

**Exemplos**:

```bash
# Batch com synths específicos
uv run synthlab research batch compra-amazon --synth-ids ynnasw,abc123,def456

# Batch com 10 synths aleatórios
uv run synthlab research batch compra-amazon --limit 10

# Com summary automático
uv run synthlab research batch compra-amazon --limit 20 --summary

# Com configurações customizadas
uv run synthlab research batch mobile-banking \
  --limit 15 \
  --max-rounds 12 \
  --model gpt-4o \
  --max-concurrent 3 \
  --summary
```

**Output Exemplo**:

```
═══════════════════════════════════════════════════════
Research Batch: Amazon E-Commerce
═══════════════════════════════════════════════════════

Synths selecionados: 10
Modelo: gpt-5-mini
Max turnos: 6
Concorrência: 5

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Progresso
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[1/10] ynnasw (Ravy Lopes)... ✓ Completado (2min 34s)
[2/10] abc123 (Maria Silva)... ✓ Completado (2min 12s)
[3/10] def456 (João Santos)... ✓ Completado (3min 05s)
[4/10] ghi789 (Ana Costa)... ✓ Completado (2min 45s)
[5/10] jkl012 (Pedro Alves)... ✗ Falhou (LLM timeout)
[6/10] mno345 (Carla Lima)... ✓ Completado (2min 28s)
[7/10] pqr678 (Lucas Rocha)... ✓ Completado (2min 51s)
[8/10] stu901 (Julia Martins)... ✓ Completado (2min 19s)
[9/10] vwx234 (Bruno Souza)... ✓ Completado (3min 12s)
[10/10] yz567 (Beatriz Dias)... ✓ Completado (2min 34s)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ Research concluída!
  Total: 10 entrevistas
  Bem-sucedidas: 9 (90%)
  Falhadas: 1 (10%)
  Duração total: 15min 42s
  Output: data/transcripts/batch_compra-amazon_20251219_110534/

✓ Gerando summary...
  Summary salvo em: data/transcripts/batch_compra-amazon_20251219_110534/batch_summary.json
```

---

### 5. Comandos Globais

#### 5.1 Help

```bash
synthlab --help
synthlab <command> --help
```

**Exemplos**:

```bash
# Help geral
uv run synthlab --help

# Help de comando específico
uv run synthlab gensynth --help
uv run synthlab listsynth --help
uv run synthlab topic-guide --help
uv run synthlab research --help
```

---

#### 5.2 Version

```bash
synthlab --version
```

**Output**:

```
synth-lab CLI version 2.0.0
```

---

## Formatação de Output

### Rich Tables

Tabelas formatadas com Rich para listagens:

```bash
uv run synthlab listsynth --limit 5
```

```
┌────────┬─────────────────┬──────┬─────────────────┬──────────────┐
│ ID     │ Nome            │ Idade│ Arquétipo       │ Cidade       │
├────────┼─────────────────┼──────┼─────────────────┼──────────────┤
│ ynnasw │ Ravy Lopes      │ 32   │ Jovem Adulto    │ São Paulo    │
│ abc123 │ Maria Silva     │ 28   │ Jovem Adulto    │ Rio          │
└────────┴─────────────────┴──────┴─────────────────┴──────────────┘
```

### Progress Bars

Barras de progresso para operações longas:

```bash
uv run synthlab gensynth -n 100
```

```
Gerando synths: ████████████████████ 100/100 [00:05<00:00, 19.8 synths/s]
```

### Colorização

- ✓ **Verde**: Sucesso
- ✗ **Vermelho**: Erro
- **Amarelo**: Avisos
- **Azul**: Informações

---

## Variáveis de Ambiente

### OPENAI_API_KEY

Chave da API OpenAI (requerida para avatares e entrevistas):

```bash
export OPENAI_API_KEY="sk-your-api-key-here"
```

### SYNTHLAB_DB_PATH

Path customizado para banco de dados:

```bash
export SYNTHLAB_DB_PATH="/custom/path/synthlab.db"
```

### SYNTHLAB_LOG_LEVEL

Nível de logging:

```bash
export SYNTHLAB_LOG_LEVEL="DEBUG"  # DEBUG, INFO, WARNING, ERROR
```

### SYNTHLAB_DEFAULT_MODEL

Modelo LLM padrão:

```bash
export SYNTHLAB_DEFAULT_MODEL="gpt-4o"
```

---

## Troubleshooting

### Comando não encontrado

```bash
# Verificar instalação
uv run python -c "import synth_lab; print(synth_lab.__version__)"

# Reinstalar
uv sync --force
```

### OpenAI API Key não configurada

```
Error: OpenAI API key não encontrada. Configure: export OPENAI_API_KEY="sk-..."
```

**Solução**:

```bash
export OPENAI_API_KEY="sk-your-api-key-here"
```

### Banco de dados não encontrado

```
Error: Database file not found: output/synthlab.db
```

**Solução**:

```bash
uv run python scripts/migrate_to_sqlite.py
```

### Rate limit da OpenAI

```
Error: Rate limit exceeded. Aguarde 20 segundos...
```

**Solução**: Aguardar ou reduzir `--max-concurrent` em batch operations.

---

## Scripts Úteis

### Gerar Dataset Completo

```bash
#!/bin/bash
# scripts/generate_dataset.sh

# Gerar 1000 synths com avatares
uv run synthlab gensynth -n 1000 --avatar --benchmark

# Validar todos
uv run synthlab gensynth --validate-all

# Analisar distribuições
uv run synthlab gensynth --analyze all
```

### Executar Research Completa

```bash
#!/bin/bash
# scripts/full_research.sh

TOPIC="compra-amazon"

# Criar topic guide
uv run synthlab topic-guide create --name $TOPIC

# Copiar arquivos
cp research-materials/*.png data/topic_guides/$TOPIC/

# Gerar descrições
uv run synthlab topic-guide update --name $TOPIC

# Executar entrevistas
uv run synthlab research batch $TOPIC --limit 50 --summary
```

---

## Integração com Scripts

### Python

```python
import subprocess
import json

# Executar comando
result = subprocess.run(
    ["uv", "run", "synthlab", "listsynth", "--limit", "10"],
    capture_output=True,
    text=True
)

print(result.stdout)
```

### Bash

```bash
#!/bin/bash

# Gerar synths em loop
for i in {1..10}; do
    uv run synthlab gensynth -n 100 --quiet
    echo "Batch $i completado"
done

# Listar todos os synths
uv run synthlab listsynth --full-query "SELECT COUNT(*) as total FROM synths"
```

---

## Boas Práticas

### 1. Use uv run

Sempre prefira `uv run` ao invés de ativar o venv:

```bash
# Correto
uv run synthlab gensynth -n 10

# Evite
source .venv/bin/activate
synthlab gensynth -n 10
```

### 2. Valide Synths Regularmente

```bash
# Após gerar muitos synths
uv run synthlab gensynth --validate-all
```

### 3. Backup do Banco de Dados

```bash
# Antes de operações grandes
cp output/synthlab.db output/synthlab_backup_$(date +%Y%m%d).db
```

### 4. Use --quiet em Scripts

```bash
# Para scripts automatizados
uv run synthlab gensynth -n 100 --quiet 2>&1 | tee generation.log
```

### 5. Monitore Rate Limits

```bash
# Reduza concorrência se hit rate limits
uv run synthlab research batch compra-amazon --limit 50 --max-concurrent 2
```

---

## Conclusão

A CLI do synth-lab oferece uma interface poderosa e intuitiva para:

- **Gerar synths** com distribuições realistas
- **Gerenciar topic guides** com descrições IA
- **Executar entrevistas** individuais ou em batch
- **Consultar dados** com SQL flexível
- **Validar qualidade** dos synths gerados

Para mais informações:
- [Arquitetura](arquitetura.md)
- [API REST](api.md)
- [Camada de Serviços](services.md)
