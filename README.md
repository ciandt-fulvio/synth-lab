# SynthLab - Gerador de Personas Sintéticas Brasileiras

Gerador de personas sintéticas (Synths) com atributos demográficos, psicográficos, comportamentais e cognitivos realistas, baseados em dados do IBGE e pesquisas verificadas.

## 🎯 Objetivo

Criar Synths representativos da população brasileira para:
- Testes de UX
- Simulações Monte Carlo
- Validação de acessibilidade
- Pesquisas de mercado
- Desenvolvimento de produtos

## ✨ Características

- **Atributos Demográficos**: Idade, gênero, localização, escolaridade, renda, ocupação (IBGE Censo 2022)
- **Atributos Psicográficos**: Personalidade Big Five, valores, interesses, hobbies, inclinação política/religiosa
- **Atributos Comportamentais**: Hábitos de consumo, uso de tecnologia, padrões de mídia
- **Limitações Físicas/Cognitivas**: Deficiências visuais, auditivas, motoras, cognitivas (IBGE PNS 2019)
- **Capacidades Tecnológicas**: Alfabetização digital, dispositivos, familiaridade com plataformas (TIC Domicílios 2023)
- **Vieses Comportamentais**: 7 vieses de economia comportamental (literatura acadêmica)

## 🚀 Instalação

### Pré-requisitos

- Python 3.13 ou superior
- \`uv\` (gerenciador de pacotes recomendado) ou \`pip\`

### Setup

\`\`\`bash
# Clone o repositório
git clone <repo-url>
cd synth-lab

# Criar virtual environment
python3.13 -m venv venv
source venv/bin/activate  # macOS/Linux
# ou
venv\Scripts\activate  # Windows

# Instalar dependências com uv (recomendado)
uv pip install -e .

# Ou com pip
pip install -e .
\`\`\`

## 📖 Uso

### Gerar um Synth individual

\`\`\`bash
uv run scripts/gen_synth.py --count 1
\`\`\`

### Gerar batch de Synths

\`\`\`bash
# 100 Synths
uv run scripts/gen_synth.py --count 100

# 1000 Synths
uv run scripts/gen_synth.py --count 1000
\`\`\`

### Validar Synths gerados

\`\`\`bash
# Validar um Synth específico
python scripts/gen_synth.py --validate data/synths/<id>.json

# Validar todos os Synths
python scripts/gen_synth.py --validate-all
\`\`\`

### Analisar distribuições demográficas

\`\`\`bash
# Distribuição por região
python scripts/gen_synth.py --analyze-distribution --region

# Distribuição por idade
python scripts/gen_synth.py --analyze-distribution --age
\`\`\`

## 📁 Estrutura do Projeto

\`\`\`
synth-lab/
├── scripts/
│   └── gen_synth.py          # Script principal de geração
├── data/
│   ├── synths/               # Synths gerados (JSON files)
│   ├── config/               # Configurações IBGE, nomes, ocupações
│   └── schemas/              # JSON Schema para validação
├── docs/
│   └── synth_attributes.md   # Documentação de atributos
├── examples/
│   └── analyze_synths.ipynb  # Notebook de análise (futuro)
└── specs/
    └── 001-generate-synths/  # Especificações da feature
\`\`\`

## 🎓 Documentação

- **Especificação**: \`specs/001-generate-synths/spec.md\`
- **Modelo de Dados**: \`specs/001-generate-synths/data-model.md\`
- **Pesquisa Técnica**: \`specs/001-generate-synths/research.md\`
- **Guia Rápido**: \`specs/001-generate-synths/quickstart.md\`
- **Atributos**: \`docs/synth_attributes.md\` (em desenvolvimento)

## 📊 Fontes de Dados

- **IBGE Censo 2022**: População, religião, raça/etnia
- **IBGE PNAD 2022/2023**: Demografia, renda, escolaridade
- **IBGE PNS 2019**: Deficiências físicas e cognitivas
- **TIC Domicílios 2023 (CETIC.br)**: Capacidades tecnológicas
- **DataSenado 2024**: Inclinação política
- **Pesquisa TIM + USP**: Hobbies e interesses

## 🧪 Validação

Todos os Synths gerados são validados contra JSON Schema (Draft 2020-12) para garantir:
- 100% dos campos obrigatórios preenchidos
- Valores dentro de domínios válidos
- Distribuições realistas conforme IBGE

## 📝 Licença

[Adicionar licença]

## 🤝 Contribuindo

Contribuições são bem-vindas! Por favor, consulte as especificações em \`specs/\` antes de submeter PRs.
