# CLI - Interface de Linha de Comando synth-lab

## Visão Geral

O synth-lab oferece uma CLI (Command Line Interface) simplificada construída com **argparse** e **Rich** para formatação de saída.

### Características

- **Framework**: argparse (stdlib) para CLI principal
- **Output**: Rich tables, progress bars, colorização
- **Comando principal**: `gensynth` para geração de personas sintéticas
- **Validação**: Type hints e Pydantic para validação automática
- **Help**: Documentação inline com `--help`

> 📝 **Nota**: Outras funcionalidades (consultas, pesquisas UX, topic guides, PR-FAQ) estão disponíveis via **REST API**. Veja [API REST](api.md).

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

# Configurar DATABASE_URL
export DATABASE_URL="postgresql://synthlab:synthlab_dev@localhost:5432/synthlab"

# Rodar migrações do banco
alembic upgrade head

# Testar CLI
uv run synthlab --help
```

---

## Comandos Disponíveis

### 1. Comando de Geração (gensynth)

O único comando CLI disponível é `gensynth`, usado para gerar personas sintéticas.

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

### 2. Comandos Globais

#### 2.1 Help

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
```

---

#### 2.2 Version

```bash
synthlab --version
```

**Output**:

```
synthlab version 2.0.0
```

---

## Outras Funcionalidades (via REST API)

As seguintes funcionalidades foram migradas para a **REST API**:

### Consultas (anteriormente `listsynth`)

Use a REST API ou DuckDB CLI diretamente:

```bash
# Listar synths via API
curl http://localhost:8000/synths/list

# Consultas SQL via DuckDB CLI
duckdb synths.duckdb "SELECT * FROM synths WHERE demografia.idade > 30"
```

Veja [API REST](api.md) para mais detalhes.

---

### Topic Guides (anteriormente `topic-guide`)

Gerencie topic guides manualmente e acesse via REST API:

```bash
# Criar diretório manualmente
mkdir -p data/topic_guides/mobile-banking
cp screens/*.png data/topic_guides/mobile-banking/

# Listar via API
curl http://localhost:8000/topics/list

# Obter detalhes
curl http://localhost:8000/topics/mobile-banking
```

Veja [API REST](api.md) para mais detalhes.

---

### Entrevistas de Pesquisa (anteriormente `research`)

Acesse execuções de pesquisa via REST API:

```bash
# Listar execuções
curl http://localhost:8000/research/list

# Obter detalhes
curl http://localhost:8000/research/{execution_id}

# Obter resumo
curl http://localhost:8000/research/{execution_id}/summary
```

Veja [API REST](api.md) para mais detalhes.

---

### PR-FAQ (anteriormente `research-prfaq`)

Acesse PR-FAQs via REST API:

```bash
# Listar PR-FAQs
curl http://localhost:8000/prfaq/list

# Obter PR-FAQ
curl http://localhost:8000/prfaq/{execution_id}

# Obter markdown
curl http://localhost:8000/prfaq/{execution_id}/markdown
```

Veja [API REST](api.md) para mais detalhes.

---

## Formatação de Output

### Rich Tables

Tabelas formatadas com Rich para listagens:

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

Chave da API OpenAI (requerida para avatares):

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
Error: could not connect to server: Connection refused
```

**Solução**:

```bash
# Verificar se PostgreSQL está rodando
docker compose up -d postgres

# Rodar migrações
alembic upgrade head
```

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

---

## Integração com Scripts

### Python

```python
import subprocess

# Executar comando
result = subprocess.run(
    ["uv", "run", "synthlab", "gensynth", "-n", "10"],
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

---

## Conclusão

A CLI do synth-lab oferece uma interface simplificada focada em:

- **Gerar synths** com distribuições realistas
- **Gerar avatares** para personas sintéticas
- **Validar qualidade** dos synths gerados
- **Analisar distribuições** demográficas

Para outras funcionalidades (consultas, topic guides, entrevistas, PR-FAQ), use a **REST API**.

Para mais informações:
- [Arquitetura](arquitetura.md)
- [API REST](api.md)
- [Camada de Serviços](services.md)
