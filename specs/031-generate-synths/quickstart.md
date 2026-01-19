# Guia Rápido: Gerador de Synths

**Feature**: 001-generate-synths
**Data**: 2025-12-14
**Versão**: 1.0.0

## Instalação

### 1. Configurar Ambiente Python

```bash
# Criar virtual environment (se ainda não existe)
cd /Users/fulvio/Projects/synth-lab
python3.13 -m venv venv

# Ativar virtual environment
source venv/bin/activate  # macOS/Linux
# ou
venv\Scripts\activate  # Windows

# Instalar dependências
uv pip install -e .
```

### 2. Estrutura de Diretórios

O script criará automaticamente os diretórios necessários na primeira execução:

```text
synth-lab/
├── data/
│   ├── synths/          # Synths gerados (JSON files)
│   ├── config/          # Configurações IBGE, nomes, ocupações
│   └── schemas/         # JSON Schema para validação
└── scripts/
    └── gen_synth.py     # Script principal
```

---

## Uso Básico

### Gerar um Único Synth

```bash
# Executar com uv (recomendado)
uv run scripts/gen_synth.py --count 1

# Ou com Python diretamente (após ativar venv)
python scripts/gen_synth.py --count 1
```

**Saída esperada**:
```
[INFO] Carregando distribuições IBGE de data/config/ibge_distributions.json
[INFO] Carregando nomes brasileiros de data/config/brazilian_names.json
[INFO] Gerando 1 Synth(s)...
[INFO] Synth gerado: Maria Silva Santos (a1B2c3)
[INFO] Validando contra JSON Schema...
[SUCCESS] 1 Synth(s) gerado(s) com sucesso em data/synths/
[SUCCESS] Tempo total: 0.52s
```

**Resultado**:
- Arquivo criado: `data/synths/a1B2c3.json`
- Conteúdo: Synth completo com todos os atributos (ver [exemplo](#exemplo-de-synth-gerado))

---

### Gerar Múltiplos Synths (Batch)

```bash
# Gerar 10 Synths
uv run scripts/gen_synth.py --count 10

# Gerar 100 Synths
uv run scripts/gen_synth.py --count 100

# Gerar 1000 Synths
uv run scripts/gen_synth.py --count 1000
```

**Performance esperada**:
- **10 Synths**: ~5 segundos
- **100 Synths**: ~30 segundos ✅ <2min (SC-003)
- **1000 Synths**: ~5 minutos
- **10.000 Synths**: ~8-10 minutos ✅ (SC-010)

---

### Opções Avançadas

```bash
# Especificar diretório de saída
uv run scripts/gen_synth.py --count 50 --output data/synths_custom/

# Modo silencioso (sem output detalhado)
uv run scripts/gen_synth.py --count 100 --quiet

# Validar sem gerar (dry-run)
uv run scripts/gen_synth.py --validate-only

# Exibir ajuda completa
uv run scripts/gen_synth.py --help
```

---

## Validação de Synths Gerados

### Validar Synth Individual

```bash
# Validar um Synth específico
python scripts/gen_synth.py --validate data/synths/a1B2c3.json
```

**Saída esperada**:
```
[INFO] Carregando JSON Schema de data/schemas/synth-schema.json
[INFO] Validando data/synths/a1B2c3.json...
[SUCCESS] Synth válido! Nenhum erro encontrado.
```

### Validar Todos os Synths

```bash
# Validar todos os Synths no diretório
python scripts/gen_synth.py --validate-all
```

**Saída esperada**:
```
[INFO] Validando 100 Synth(s) em data/synths/...
[SUCCESS] 100/100 Synths válidos (100% taxa de sucesso)
[INFO] Tempo total de validação: 1.2s
```

---

## Análise de Distribuição Demográfica

### Verificar Distribuição Regional

```bash
# Analisar distribuição por região (100+ Synths recomendado)
python scripts/gen_synth.py --analyze-distribution --region
```

**Saída esperada**:
```
Distribuição Regional (1000 Synths analisados):

Região         | Count | %      | IBGE % | Delta
---------------|-------|--------|--------|-------
Sudeste        | 412   | 41.2%  | 40.7%  | +0.5%  ✅
Nordeste       | 258   | 25.8%  | 26.2%  | -0.4%  ✅
Sul            | 135   | 13.5%  | 13.8%  | -0.3%  ✅
Norte          | 89    | 8.9%   | 8.6%   | +0.3%  ✅
Centro-Oeste   | 76    | 7.6%   | 7.7%   | -0.1%  ✅

[SUCCESS] Erro médio: 0.32% (Margem aceitável: ≤10%) ✅ SC-004
```

### Verificar Distribuição Etária

```bash
python scripts/gen_synth.py --analyze-distribution --age
```

**Saída esperada**:
```
Distribuição Etária (1000 Synths analisados):

Faixa Etária  | Count | %      | IBGE % | Delta
--------------|-------|--------|--------|-------
0-14 anos     | 201   | 20.1%  | 19.8%  | +0.3%  ✅
15-29 anos    | 218   | 21.8%  | 22.1%  | -0.3%  ✅
30-44 anos    | 235   | 23.5%  | 22.8%  | +0.7%  ✅
45-59 anos    | 192   | 19.2%  | 19.6%  | -0.4%  ✅
60+ anos      | 154   | 15.4%  | 15.7%  | -0.3%  ✅

[SUCCESS] Erro médio: 0.40% (Margem aceitável: ≤10%) ✅ SC-004
```

---

## Exemplo de Synth Gerado

**Arquivo**: `data/synths/a1B2c3.json`

```json
{
  "id": "a1B2c3",
  "nome": "Maria Silva Santos",
  "arquetipo": "Jovem Adulto Nordestina Criativa",
  "descricao": "Mulher de 28 anos, designer gráfica, mora em Recife. Alta abertura a experiências e conscienciosidade moderada.",
  "link_photo": "https://ui-avatars.com/api/?name=Maria+Silva+Santos&size=256&background=random",
  "created_at": "2025-12-14T15:30:00Z",
  "version": "1.0.0",

  "demografia": {
    "idade": 28,
    "genero_biologico": "feminino",
    "identidade_genero": "mulher cis",
    "raca_etnia": "parda",
    "localizacao": {
      "pais": "Brasil",
      "regiao": "Nordeste",
      "estado": "PE",
      "cidade": "Recife"
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
    "estilo_vida": "Ativa e criativa",
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

---

## Casos de Uso

### 1. Testes de UX para Aplicativo de Finanças

```bash
# Gerar 50 Synths representativos da população brasileira
uv run scripts/gen_synth.py --count 50

# Analisar distribuição de alfabetização digital
python scripts/gen_synth.py --analyze-distribution --digital-literacy

# Filtrar Synths com baixa alfabetização digital (<40) para testes de usabilidade
python scripts/gen_synth.py --filter "alfabetizacao_digital<40" --output data/synths_low_digital/
```

**Resultado**: 50 Synths com perfis diversos para simular interações com o app.

---

### 2. Simulação Monte Carlo para Campanha de Marketing

```bash
# Gerar 1000 Synths para simulação robusta
uv run scripts/gen_synth.py --count 1000

# Analisar distribuição de renda
python scripts/gen_synth.py --analyze-distribution --income

# Analisar viés de ancoragem (importante para pricing)
python scripts/gen_synth.py --analyze-distribution --bias ancoragem
```

**Resultado**: Distribuição realista para testar mensagens de marketing em diferentes segmentos.

---

### 3. Validação de Acessibilidade

```bash
# Gerar 200 Synths
uv run scripts/gen_synth.py --count 200

# Filtrar Synths com deficiências
python scripts/gen_synth.py --filter "deficiencias.visual.tipo!=nenhuma OR deficiencias.motora.tipo!=nenhuma" --output data/synths_accessibility/

# Analisar distribuição de deficiências
python scripts/gen_synth.py --analyze-distribution --disabilities
```

**Resultado**: Subset de Synths com deficiências para testes de acessibilidade (WCAG, ARIA, etc.).

---

## Solução de Problemas

### Erro: "ModuleNotFoundError: No module named 'faker'"

**Solução**:
```bash
# Garantir que dependências estão instaladas
uv pip install -e .

# Ou instalar manualmente
pip install faker jsonschema
```

---

### Erro: "FileNotFoundError: data/config/ibge_distributions.json not found"

**Solução**:
```bash
# Criar arquivos de configuração (executar script de setup)
python scripts/gen_synth.py --setup

# Isso criará:
# - data/config/ibge_distributions.json
# - data/config/brazilian_names.json
# - data/config/occupations.json
# - data/config/interests_hobbies.json
```

---

### Erro: "ValidationError: ... does not match '^\\d+\\.\\d+\\.\\d+$'"

**Causa**: Synth gerado não passa na validação JSON Schema.

**Solução**:
```bash
# Executar validação diagnóstica
python scripts/gen_synth.py --diagnose

# Revalidar todos os Synths e reportar erros detalhados
python scripts/gen_synth.py --validate-all --verbose
```

---

## Performance Tips

### Otimizar Geração em Lote

```bash
# Usar modo paralelo para I/O (10 workers padrão)
uv run scripts/gen_synth.py --count 1000 --workers 20

# Desabilitar validação durante geração (validar depois)
uv run scripts/gen_synth.py --count 10000 --skip-validation
python scripts/gen_synth.py --validate-all  # Validar em batch
```

### Benchmark

```bash
# Medir tempo de geração
time uv run scripts/gen_synth.py --count 100

# Exemplo de saída:
# real  0m28.432s  ✅ <2min (SC-003)
# user  0m26.120s
# sys   0m1.850s
```

---

## Próximos Passos

1. ✅ Gerar Synths
2. ⏭️ Analisar Synths com Jupyter Notebook (`examples/analyze_synths.ipynb`)
3. ⏭️ Integrar Synths com testes de UX
4. ⏭️ Implementar hidratação de Synths (feature futura - OS-001)

---

## Referências

- **JSON Schema**: `data/schemas/synth-schema.json`
- **Data Model**: `specs/001-generate-synths/data-model.md`
- **Research**: `specs/001-generate-synths/research.md`
- **Specification**: `specs/001-generate-synths/spec.md`
- **Documentação IBGE**: https://www.ibge.gov.br/estatisticas/sociais/populacao.html
- **CBO**: https://www.gov.br/trabalho-e-emprego/pt-br/assuntos/cbo
