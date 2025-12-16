# SynthLab - Gerador de Personas Sintéticas Brasileiras

> Gerador de personas sintéticas (Synths) com atributos demográficos, psicográficos, comportamentais e cognitivos realistas, baseados em dados do IBGE e pesquisas verificadas.

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🎯 Objetivo

Criar Synths representativos da população brasileira para:
- Testes de UX e design de interfaces
- Simulações Monte Carlo e modelagem estatística
- Validação de acessibilidade e inclusão
- Pesquisas de mercado e segmentação
- Desenvolvimento e validação de produtos

## ✨ Características

### Interface CLI Moderna
- 🎨 **Saída colorida e formatada** com biblioteca Rich
- ⚡ **Comandos intuitivos**: `synthlab gensynth -n 100`, `synthlab listsynth`
- 📊 **Benchmark integrado** para análise de performance
- 🔇 **Modo silencioso** para integração em pipelines
- ✅ **Validação e análise** de distribuições demográficas
- 🔍 **Consultas SQL** com DuckDB para análise de dados

### Dados Realistas (Schema v2.0.0)
- **Atributos Demográficos**: Idade, gênero, localização, escolaridade, renda, ocupação (IBGE Censo 2022, PNAD 2022/2023)
- **Atributos Psicográficos**: Personalidade Big Five, interesses, inclinação política/religiosa
- **Atributos Comportamentais**: Hábitos de consumo, padrões de mídia social
- **Limitações Físicas/Cognitivas**: Deficiências visuais, auditivas, motoras, cognitivas (IBGE PNS 2019)
- **Capacidades Tecnológicas**: Alfabetização digital, dispositivos, familiaridade com plataformas (TIC Domicílios 2023)
- **Vieses Comportamentais**: 7 vieses cognitivos alinhados com traços de personalidade (literatura acadêmica)

## 🚀 Instalação

### Pré-requisitos

- Python 3.13 ou superior
- `uv` (gerenciador de pacotes)

### Setup

```bash
# Clone o repositório
git clone <repo-url>
cd synth-lab

# Instalar dependências (uv cria automaticamente o .venv)
uv sync

# Pronto! Use uv run para executar comandos
uv run synthlab --help
```

> **Nota**: Não é necessário ativar o ambiente virtual ou instalar o pacote. O `uv run` gerencia tudo automaticamente, executando comandos diretamente no ambiente isolado.

## 📖 Uso

### Interface de Linha de Comando

O SynthLab oferece uma CLI intuitiva com saída colorida para melhor experiência do usuário.

**Todos os comandos usam `uv run` para execução automática no ambiente virtual**:

```bash
# Ver ajuda geral
uv run synthlab --help

# Ver versão
uv run synthlab --version

# Ver ajuda de um comando específico
uv run synthlab gensynth --help
uv run synthlab listsynth --help
```

### Comandos Disponíveis

#### Gerar Synths

```bash
# Gerar um Synth individual
uv run synthlab gensynth -n 1

# Gerar batch de Synths
uv run synthlab gensynth -n 100
uv run synthlab gensynth -n 1000

# Com benchmark de performance
uv run synthlab gensynth -n 100 --benchmark

# Modo silencioso (minimal output)
uv run synthlab gensynth -n 100 --quiet

# Output em diretório customizado
uv run synthlab gensynth -n 10 --output ./meus-synths/
```

#### Validar Synths

```bash
# Validar todos os Synths no diretório
uv run synthlab gensynth --validate-all

# Validar um arquivo específico
uv run synthlab gensynth --validate-file data/synths/abc123.json

# Executar testes de validação internos
uv run synthlab gensynth --validar
```

#### Analisar Distribuições

```bash
# Analisar distribuição regional vs IBGE
uv run synthlab gensynth --analyze region

# Analisar distribuição etária vs IBGE
uv run synthlab gensynth --analyze age

# Analisar ambas as distribuições
uv run synthlab gensynth --analyze all
```

#### Consultar Synths (Query)

```bash
# Listar todos os Synths gerados
uv run synthlab listsynth

# Filtrar com condição WHERE (use notação de ponto para campos aninhados)
uv run synthlab listsynth --where "demografia.idade > 30"
uv run synthlab listsynth --where "demografia.localizacao.cidade = 'São Paulo'"

# Query SQL personalizada
uv run synthlab listsynth --full-query "SELECT id, nome, demografia.idade FROM synths LIMIT 10"
uv run synthlab listsynth --full-query "SELECT demografia.localizacao.cidade as cidade, COUNT(*) FROM synths GROUP BY cidade"
uv run synthlab listsynth --full-query "SELECT nome, demografia.renda_mensal FROM synths WHERE demografia.renda_mensal > 5000"
```

> **Nota**: Use a notação de ponto (`.`) para acessar campos aninhados. Por exemplo: `demografia.idade`, `demografia.localizacao.regiao`, `capacidades_tecnologicas.alfabetizacao_digital`.

### Estrutura de Saída

Os Synths são salvos como arquivos JSON em `data/synths/` com identificadores únicos. Cada Synth contém:

- **Identificação**: ID único (6 chars), nome completo, arquétipo, descrição, link para foto
- **Demografia**: Idade, gênero biológico/identidade, raça/etnia, localização, escolaridade, renda, ocupação, estado civil, composição familiar
- **Psicografia**: Big Five (abertura, conscienciosidade, extroversão, amabilidade, neuroticismo), interesses, inclinação política/religiosa
- **Comportamento**: Hábitos de consumo, padrões de mídia, fonte de notícias, lealdade a marca, engajamento em redes sociais
- **Deficiências**: Limitações visuais, auditivas, motoras (cadeira de rodas), cognitivas (se aplicável)
- **Capacidades Tecnológicas**: Alfabetização digital, dispositivos (principal, qualidade), preferências de acessibilidade (zoom, contraste), velocidade de digitação, frequência de internet, familiaridade com plataformas
- **Vieses Comportamentais**: Aversão à perda, desconto hiperbólico, suscetibilidade a chamariz, ancoragem, viés de confirmação, viés de status quo, sobrecarga de informação (alinhados com traços de personalidade)
- **Metadata**: Timestamp de criação (ISO 8601), versão do schema (2.0.0)

<details>
<summary>Exemplo de Synth gerado (clique para expandir)</summary>

```json
{
  "id": "abc123",
  "nome": "Maria Silva Santos",
  "arquetipo": "Jovem Adulto Sudeste Criativo",
  "descricao": "Mulher de 28 anos, designer gráfica, mora em São Paulo, SP. Possui traços marcantes de Abertura, Amabilidade.",
  "link_photo": "https://ui-avatars.com/api/?name=Maria+Silva+Santos&size=256&background=random",
  "created_at": "2025-12-14T15:30:00Z",
  "version": "2.0.0",
  "demografia": {
    "idade": 28,
    "genero_biologico": "feminino",
    "identidade_genero": "mulher cis",
    "raca_etnia": "parda",
    "localizacao": {
      "pais": "Brasil",
      "regiao": "Sudeste",
      "estado": "SP",
      "cidade": "São Paulo"
    },
    "escolaridade": "Superior completo",
    "renda_mensal": 4500.00,
    "ocupacao": "Designer gráfico",
    "estado_civil": "solteiro",
    "composicao_familiar": {
      "tipo": "unipessoal",
      "numero_pessoas": 1
    }
  },
  "psicografia": {
    "personalidade_big_five": {
      "abertura": 78,
      "conscienciosidade": 62,
      "extroversao": 55,
      "amabilidade": 71,
      "neuroticismo": 42
    },
    "valores": ["criatividade", "autonomia", "justiça social"],
    "interesses": ["design", "arte", "tecnologia", "música"],
    "hobbies": ["desenho", "fotografia", "videogames", "yoga"],
    "estilo_vida": "Criativo e explorador",
    "inclinacao_politica": -25,
    "inclinacao_religiosa": "católico"
  },
  "comportamento": {
    "habitos_consumo": {
      "frequencia_compras": "semanal",
      "preferencia_canal": "híbrido",
      "categorias_preferidas": ["tecnologia", "livros", "vestuário", "decoração"]
    },
    "uso_tecnologia": {
      "smartphone": true,
      "computador": true,
      "tablet": true,
      "smartwatch": false
    },
    "padroes_midia": {
      "tv_aberta": 2,
      "streaming": 15,
      "redes_sociais": 12
    },
    "fonte_noticias": ["jornais online", "redes sociais", "podcasts"],
    "comportamento_compra": {
      "impulsivo": 45,
      "pesquisa_antes_comprar": 75
    },
    "lealdade_marca": 55,
    "engajamento_redes_sociais": {
      "plataformas": ["Instagram", "LinkedIn", "Pinterest", "WhatsApp"],
      "frequencia_posts": "ocasional"
    }
  },
  "deficiencias": {
    "visual": {"tipo": "nenhuma"},
    "auditiva": {"tipo": "nenhuma"},
    "motora": {"tipo": "nenhuma", "usa_cadeira_rodas": false},
    "cognitiva": {"tipo": "nenhuma"}
  },
  "capacidades_tecnologicas": {
    "alfabetizacao_digital": 85,
    "dispositivos": {
      "principal": "computador",
      "qualidade": "novo"
    },
    "preferencias_acessibilidade": {
      "zoom_fonte": 100,
      "alto_contraste": false
    },
    "velocidade_digitacao": 70,
    "frequencia_internet": "diária",
    "familiaridade_plataformas": {
      "e_commerce": 90,
      "banco_digital": 85,
      "redes_sociais": 95
    }
  },
  "vieses": {
    "aversao_perda": 48,
    "desconto_hiperbolico": 55,
    "suscetibilidade_chamariz": 42,
    "ancoragem": 51,
    "vies_confirmacao": 60,
    "vies_status_quo": 38,
    "sobrecarga_informacao": 45
  }
}
```
</details>

## 📁 Estrutura do Projeto

```
synth-lab/
├── src/
│   └── synth_lab/                # Pacote principal
│       ├── __init__.py
│       ├── __main__.py           # Entry point CLI
│       ├── gen_synth/            # Módulo de geração
│       │   ├── __init__.py
│       │   ├── gen_synth.py      # Orquestrador principal
│       │   ├── config.py         # Configurações e paths
│       │   └── utils.py          # Funções utilitárias
│       └── query/                # Módulo de consulta
│           ├── __init__.py       # Enums e exceções
│           ├── validator.py      # Validação de queries
│           ├── database.py       # Operações DuckDB
│           ├── formatter.py      # Formatação Rich tables
│           └── cli.py            # Comando listsynth
├── tests/
│   ├── unit/
│   │   └── synth_lab/
│   │       ├── gen_synth/        # Testes unitários de geração
│   │       └── query/            # Testes unitários de query
│   ├── integration/
│   │   └── synth_lab/
│   │       └── query/            # Testes de integração
│   └── fixtures/
│       └── query/                # Fixtures para testes
├── data/
│   ├── synths/                   # Synths gerados (JSON)
│   ├── config/                   # Configurações demográficas
│   │   ├── ibge_distributions.json
│   │   ├── interests_hobbies.json
│   │   └── occupations_structured.json
│   └── schemas/                  # JSON Schema para validação
│       └── synth-schema.json
├── specs/
│   ├── 001-generate-synths/      # Feature 1: Geração de Synths
│   ├── 002-synthlab-cli/         # Feature 2: CLI SynthLab
│   └── 003-synth-query/          # Feature 3: Query de Synths
│       ├── spec.md               # Especificação da feature
│       ├── plan.md               # Plano de implementação
│       └── tasks.md              # Tarefas e progresso
├── pyproject.toml                # Configuração do projeto
├── pytest.ini                    # Configuração pytest
└── README.md                     # Este arquivo
```

## 🎓 Documentação

### Especificações Técnicas

- **[spec.md](specs/001-generate-synths/spec.md)**: Requisitos completos, escopo e critérios de aceitação
- **[data-model.md](specs/001-generate-synths/data-model.md)**: Modelo de dados detalhado com todos os atributos
- **[research.md](specs/001-generate-synths/research.md)**: Fontes de dados, metodologia e referências
- **[quickstart.md](specs/001-generate-synths/quickstart.md)**: Guia rápido para começar
- **[plan.md](specs/001-generate-synths/plan.md)**: Plano de implementação e arquitetura
- **[tasks.md](specs/001-generate-synths/tasks.md)**: Tarefas e progresso do desenvolvimento

## 📊 Fontes de Dados

Todas as distribuições estatísticas são baseadas em fontes oficiais e pesquisas verificadas:

| Fonte | Dados | Ano |
|-------|-------|-----|
| **IBGE Censo** | População por região, religião, raça/etnia | 2022 |
| **IBGE PNAD** | Demografia, renda, escolaridade, ocupação | 2022/2023 |
| **IBGE PNS** | Deficiências físicas e cognitivas | 2019 |
| **TIC Domicílios (CETIC.br)** | Alfabetização digital, uso de tecnologia | 2023 |
| **DataSenado** | Inclinação política da população | 2024 |
| **Pesquisa TIM + USP** | Hobbies e interesses dos brasileiros | Recente |

## 🧪 Validação e Qualidade

- **JSON Schema**: Validação automática de todos os campos (Draft 2020-12)
- **Distribuições Realistas**: Conformidade com dados do IBGE (<10% erro)
- **Consistência Interna**: Validação de relações entre atributos (ex: ocupação vs. escolaridade)
- **Cobertura de Casos**: Inclusão de edge cases e perfis diversos
- **ID Únicos**: Garantia de IDs únicos com sistema de retry
- **Validação Automática**: 10 testes internos de coerência

### Métricas de Performance

```
✅ Geração individual: ~0.001s por synth
✅ Geração em lote: ~1800 synths/segundo
✅ Batch de 100: ~0.06s (bem abaixo do limite de 2 minutos)
✅ Distribuição regional: <7% erro vs IBGE
✅ Distribuição etária: <4% erro vs IBGE
✅ Validação schema: 100% dos synths gerados passam
```

## 🛠️ Stack Tecnológica

- **Python 3.13+**: Linguagem base
- **Faker (pt_BR)**: Geração de dados sintéticos brasileiros
- **jsonschema**: Validação de estrutura de dados
- **rich**: Interface CLI com saída colorida e formatada
- **DuckDB**: Motor SQL para consultas rápidas em JSON
- **Typer**: Framework CLI moderno com type hints
- **Loguru**: Sistema de logging estruturado
- **pytest**: Framework de testes unitários e integração
- **uv**: Gerenciamento rápido de dependências

## 💡 Exemplos de Uso

### Análise Exploratória
Veja o notebook `first-lab.ipynb` para exemplos de análise exploratória dos Synths gerados.

### Casos de Uso

**1. Análise Demográfica com SQL**
```bash
# Distribuição por região
uv run synthlab listsynth --full-query "SELECT demografia.localizacao.regiao as regiao, COUNT(*) as total FROM synths GROUP BY regiao ORDER BY total DESC"

# Média de renda por escolaridade
uv run synthlab listsynth --full-query "SELECT demografia.escolaridade, AVG(demografia.renda_mensal) as media_renda FROM synths GROUP BY demografia.escolaridade"

# Perfis de alto poder aquisitivo
uv run synthlab listsynth --where "demografia.renda_mensal > 10000 AND demografia.escolaridade = 'Superior completo'"
```

**2. Testes de UX/UI**
```bash
# Selecionar Synths com baixa alfabetização digital
uv run synthlab listsynth --where "capacidades_tecnologicas.alfabetizacao_digital < 40"

# Usuários com deficiências visuais
uv run synthlab listsynth --full-query "SELECT nome, demografia.idade, demografia.localizacao.cidade FROM synths WHERE deficiencias.visual.tipo != 'nenhuma'"
```

**3. Segmentação de Mercado**
```bash
# Jovens da região Sudeste
uv run synthlab listsynth --where "demografia.idade BETWEEN 18 AND 35 AND demografia.localizacao.regiao = 'Sudeste'"

# Perfil tecnológico e renda média-alta
uv run synthlab listsynth --where "capacidades_tecnologicas.alfabetizacao_digital > 70 AND demografia.renda_mensal > 5000"
```

**4. Análise Comportamental**
```python
# Usar Python para análise mais complexa
import json
synths = json.load(open('data/synths/synths.json'))
high_openness = [s for s in synths if s['psicografia']['personalidade_big_five']['abertura'] > 70]
```

## 📝 Licença

MIT License - veja o arquivo LICENSE para detalhes.
