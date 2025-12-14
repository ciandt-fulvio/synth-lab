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

- **Atributos Demográficos**: Idade, gênero, localização, escolaridade, renda, ocupação (IBGE Censo 2022, PNAD 2022/2023)
- **Atributos Psicográficos**: Personalidade Big Five, valores, interesses, hobbies, inclinação política/religiosa
- **Atributos Comportamentais**: Hábitos de consumo, uso de tecnologia, padrões de mídia social
- **Limitações Físicas/Cognitivas**: Deficiências visuais, auditivas, motoras, cognitivas (IBGE PNS 2019)
- **Capacidades Tecnológicas**: Alfabetização digital, dispositivos, familiaridade com plataformas (TIC Domicílios 2023)
- **Vieses Comportamentais**: 7 vieses de economia comportamental (literatura acadêmica)

## 🚀 Instalação

### Pré-requisitos

- Python 3.13 ou superior
- `uv` (gerenciador de pacotes recomendado)

### Setup

```bash
# Clone o repositório
git clone <repo-url>
cd synth-lab

# Criar virtual environment
python3.13 -m venv .venv
source .venv/bin/activate  # macOS/Linux
# ou
.venv\Scripts\activate  # Windows

# Instalar dependências com uv (recomendado)
uv pip install -e .

# Ou com pip
pip install -e .
```

## 📖 Uso

### Gerar Synths

```bash
# Gerar um Synth individual
uv run scripts/gen_synth.py --count 1

# Gerar batch de Synths
uv run scripts/gen_synth.py --count 100
uv run scripts/gen_synth.py --count 1000
```

### Estrutura de Saída

Os Synths são salvos como arquivos JSON em `data/synths/` com identificadores únicos. Cada Synth contém:

- **Identificação**: ID único, nome completo, CPF
- **Demografia**: Idade, gênero, região, estado, cidade, escolaridade, renda, ocupação
- **Psicografia**: Traços de personalidade (Big Five), valores, interesses, hobbies
- **Comportamento**: Hábitos de consumo, uso de tecnologia, redes sociais
- **Acessibilidade**: Deficiências físicas/cognitivas (se aplicável)
- **Tecnologia**: Alfabetização digital, dispositivos, familiaridade com apps
- **Vieses**: Vieses comportamentais (loss aversion, confirmation bias, etc.)
- **Metadata**: Timestamp de criação, versão do gerador

<details>
<summary>Exemplo de Synth gerado (clique para expandir)</summary>

```json
{
  "id": "SYNTH-ABC123",
  "name": "Maria da Silva Santos",
  "age": 34,
  "gender": "Feminino",
  "region": "Sudeste",
  "state": "SP",
  "city": "São Paulo",
  "education": "Superior completo",
  "income_bracket": "4-10 SM",
  "occupation": "Analista de Sistemas",
  "personality": {
    "openness": 0.72,
    "conscientiousness": 0.68,
    "extraversion": 0.45,
    "agreeableness": 0.81,
    "neuroticism": 0.34
  },
  "interests": ["Tecnologia", "Leitura", "Música"],
  "tech_literacy": "Alta",
  "devices": ["Smartphone", "Notebook"],
  "social_media": ["Instagram", "LinkedIn", "WhatsApp"],
  "behavioral_biases": ["loss_aversion", "confirmation_bias"],
  "created_at": "2024-12-14T19:30:00Z"
}
```
</details>

## 📁 Estrutura do Projeto

```
synth-lab/
├── scripts/
│   └── gen_synth.py              # Script principal de geração
├── data/
│   ├── synths/                   # Synths gerados (JSON)
│   ├── config/                   # Configurações demográficas
│   │   ├── ibge_distributions.json
│   │   ├── interests_hobbies.json
│   │   └── occupations_structured.json
│   └── schemas/                  # JSON Schema para validação
├── specs/
│   └── 001-generate-synths/      # Especificações técnicas
│       ├── spec.md               # Requisitos e escopo
│       ├── data-model.md         # Modelo de dados detalhado
│       ├── research.md           # Pesquisa e fontes
│       ├── plan.md               # Plano de implementação
│       ├── tasks.md              # Tarefas e progresso
│       └── quickstart.md         # Guia rápido
├── pyproject.toml                # Configuração do projeto
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
- **Distribuições Realistas**: Conformidade com dados do IBGE
- **Consistência Interna**: Validação de relações entre atributos (ex: ocupação vs. escolaridade)
- **Cobertura de Casos**: Inclusão de edge cases e perfis diversos

## 🛠️ Stack Tecnológica

- **Python 3.13+**: Linguagem base
- **Faker (pt_BR)**: Geração de dados sintéticos brasileiros
- **jsonschema**: Validação de estrutura de dados
- **uv**: Gerenciamento rápido de dependências

## 💡 Exemplos de Uso

### Análise Exploratória
Veja o notebook `first-lab.ipynb` para exemplos de análise exploratória dos Synths gerados.

### Casos de Uso

**1. Testes de UX/UI**
```python
# Selecionar Synths com baixa alfabetização digital
synths = [s for s in all_synths if s['tech_literacy'] == 'Baixa']
# Usar para testar simplicidade da interface
```

**2. Segmentação de Mercado**
```python
# Segmentar por renda e região
segment = [s for s in all_synths
           if s['income_bracket'] == '4-10 SM'
           and s['region'] == 'Sudeste']
```

**3. Validação de Acessibilidade**
```python
# Testar com Synths que possuem deficiências
accessible_test = [s for s in all_synths
                   if s.get('disabilities')]
```

## 🔮 Roadmap

### Em Desenvolvimento
- [ ] CLI com typer para interface mais amigável
- [ ] Validação automática de Synths gerados
- [ ] Análise de distribuições demográficas

### Futuro
- [ ] API REST para geração de Synths
- [ ] Dashboard de análise e visualização
- [ ] Exportação para múltiplos formatos (CSV, Parquet)
- [ ] Geração de famílias/grupos relacionados
- [ ] Testes unitários e integração
- [ ] Documentação expandida de atributos

## 🤝 Contribuindo

Contribuições são bem-vindas! Para contribuir:

1. Consulte as especificações em `specs/001-generate-synths/`
2. Verifique as issues abertas
3. Siga os padrões de código do projeto (Black, ruff)
4. Adicione testes para novas funcionalidades
5. Atualize a documentação conforme necessário

## 📝 Licença

MIT License - veja o arquivo LICENSE para detalhes.
