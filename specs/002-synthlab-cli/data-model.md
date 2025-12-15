# Data Model: SynthLab CLI

**Branch**: `002-synthlab-cli` | **Date**: 2025-12-15

## Core Entities

### Synth (Persona Sintética)

A entidade principal do sistema - representa uma persona sintética brasileira completa.

```python
@dataclass
class Synth:
    """Persona sintética brasileira."""

    # Identificação
    id: str                          # ID alfanumérico único (6 chars)
    nome: str                        # Nome completo brasileiro
    arquetipo: str                   # "{Faixa Etária} {Região} {Perfil}"
    descricao: str                   # Descrição textual (min 50 chars)
    link_photo: str                  # URL para avatar (ui-avatars.com)
    created_at: str                  # ISO 8601 timestamp
    version: str                     # Versão do schema (semver)

    # Componentes
    demografia: Demografia
    psicografia: Psicografia
    comportamento: Comportamento
    deficiencias: Deficiencias
    capacidades_tecnologicas: CapacidadesTecnologicas
    vieses: ViesesComportamentais
```

### Demografia

Atributos demográficos baseados em distribuições IBGE.

```python
@dataclass
class Localizacao:
    pais: str = "Brasil"
    regiao: str              # Norte, Nordeste, Sudeste, Sul, Centro-Oeste
    estado: str              # UF (SP, RJ, etc.)
    cidade: str              # Cidade principal do estado

@dataclass
class ComposicaoFamiliar:
    tipo: str                # unipessoal, casal sem filhos, casal com filhos,
                            # monoparental, multigeracional, outros
    numero_pessoas: int      # 1-7

@dataclass
class Demografia:
    idade: int               # 18-100
    genero_biologico: str    # masculino, feminino, intersexo
    identidade_genero: str   # homem cis, mulher cis, homem trans,
                            # mulher trans, não-binário, outro
    raca_etnia: str          # branca, parda, preta, amarela, indígena
    localizacao: Localizacao
    escolaridade: str        # Sem instrução até Pós-graduação
    renda_mensal: float      # Em reais
    ocupacao: str            # Nome da ocupação
    estado_civil: str        # solteiro, casado, união estável,
                            # divorciado, viúvo
    composicao_familiar: ComposicaoFamiliar
```

### Psicografia

Atributos psicográficos incluindo personalidade Big Five.

```python
@dataclass
class PersonalidadeBigFive:
    abertura: int            # 0-100 (openness)
    conscienciosidade: int   # 0-100 (conscientiousness)
    extroversao: int         # 0-100 (extraversion)
    amabilidade: int         # 0-100 (agreeableness)
    neuroticismo: int        # 0-100 (neuroticism)

@dataclass
class Psicografia:
    personalidade_big_five: PersonalidadeBigFive
    valores: list[str]       # 3-5 valores pessoais
    interesses: list[str]    # 3-10 interesses
    hobbies: list[str]       # 3-7 hobbies
    estilo_vida: str         # Derivado do Big Five
    inclinacao_politica: int # -100 (esquerda) a +100 (direita)
    inclinacao_religiosa: str # Religião ou "sem religião"
```

### Comportamento

Padrões de comportamento de consumo e mídia.

```python
@dataclass
class HabitosConsumo:
    frequencia_compras: str      # diária, semanal, quinzenal, mensal, esporádica
    preferencia_canal: str       # loja física, e-commerce, híbrido
    categorias_preferidas: list[str]

@dataclass
class UsoTecnologia:
    smartphone: bool
    computador: bool
    tablet: bool
    smartwatch: bool

@dataclass
class PadroesMidia:
    tv_aberta: int           # horas/semana (0-35)
    streaming: int           # horas/semana (0-50)
    redes_sociais: int       # horas/semana (5-70)

@dataclass
class ComportamentoCompra:
    impulsivo: int           # 0-100
    pesquisa_antes_comprar: int  # 0-100

@dataclass
class EngajamentoRedesSociais:
    plataformas: list[str]   # 2-6 plataformas
    frequencia_posts: str    # nunca, raro, ocasional, frequente, muito frequente

@dataclass
class Comportamento:
    habitos_consumo: HabitosConsumo
    uso_tecnologia: UsoTecnologia
    padroes_midia: PadroesMidia
    fonte_noticias: list[str]
    comportamento_compra: ComportamentoCompra
    lealdade_marca: int      # 0-100
    engajamento_redes_sociais: EngajamentoRedesSociais
```

### Deficiências

Atributos de deficiência baseados em PNS 2019.

```python
@dataclass
class DeficienciaVisual:
    tipo: str                # nenhuma, leve, moderada, severa, cegueira

@dataclass
class DeficienciaAuditiva:
    tipo: str                # nenhuma, leve, moderada, severa, surdez

@dataclass
class DeficienciaMotora:
    tipo: str                # nenhuma, leve, moderada, severa
    usa_cadeira_rodas: bool

@dataclass
class DeficienciaCognitiva:
    tipo: str                # nenhuma, leve, moderada, severa

@dataclass
class Deficiencias:
    visual: DeficienciaVisual
    auditiva: DeficienciaAuditiva
    motora: DeficienciaMotora
    cognitiva: DeficienciaCognitiva
```

### Capacidades Tecnológicas

```python
@dataclass
class Dispositivos:
    principal: str           # smartphone, computador, tablet
    qualidade: str           # novo, intermediário, antigo

@dataclass
class PreferenciasAcessibilidade:
    zoom_fonte: int          # 100-200 (%)
    alto_contraste: bool

@dataclass
class FamiliaridadePlataformas:
    e_commerce: int          # 0-100
    banco_digital: int       # 0-100
    redes_sociais: int       # 0-100

@dataclass
class CapacidadesTecnologicas:
    alfabetizacao_digital: int  # 10-100
    dispositivos: Dispositivos
    preferencias_acessibilidade: PreferenciasAcessibilidade
    velocidade_digitacao: int   # 10-120 WPM
    frequencia_internet: str    # diária, semanal, mensal, rara
    familiaridade_plataformas: FamiliaridadePlataformas
```

### Vieses Comportamentais

```python
@dataclass
class ViesesComportamentais:
    aversao_perda: int               # 0-100
    desconto_hiperbolico: int        # 0-100
    suscetibilidade_chamariz: int    # 0-100
    ancoragem: int                   # 0-100
    vies_confirmacao: int            # 0-100
    vies_status_quo: int             # 0-100
    sobrecarga_informacao: int       # 0-100
```

---

## Configuration Entities

### Config (Runtime Configuration)

```python
@dataclass
class Config:
    """Configurações carregadas dos arquivos JSON."""
    ibge: dict              # Distribuições IBGE
    occupations: dict       # Lista de ocupações
    interests_hobbies: dict # Listas de interesses e hobbies
```

### Paths (Static Configuration)

```python
# Definidos em config.py
DATA_DIR = Path(__file__).parent.parent.parent.parent / "data"
CONFIG_DIR = DATA_DIR / "config"
SCHEMAS_DIR = DATA_DIR / "schemas"
SYNTHS_DIR = DATA_DIR / "synths"
SCHEMA_PATH = SCHEMAS_DIR / "synth-schema.json"
```

---

## Validation Entities

```python
@dataclass
class ValidationResult:
    """Resultado de validação de um synth."""
    is_valid: bool
    errors: list[str]

@dataclass
class BatchValidationStats:
    """Estatísticas de validação em lote."""
    total: int
    valid: int
    invalid: int
    errors: list[dict]  # {"file": str, "errors": list[str]}
```

---

## Analysis Entities

```python
@dataclass
class DistributionDataPoint:
    """Ponto de dados de distribuição."""
    ibge: float          # Porcentagem esperada (IBGE)
    actual: float        # Porcentagem real
    count: int           # Contagem absoluta
    error: float         # Erro absoluto

@dataclass
class RegionalAnalysis:
    """Análise de distribuição regional."""
    total: int
    regions: dict[str, DistributionDataPoint]

@dataclass
class AgeAnalysis:
    """Análise de distribuição etária."""
    total: int
    age_groups: dict[str, DistributionDataPoint]
```

---

## State Transitions

### Synth Lifecycle

```
[Config Loaded] -> [Demographics Generated] -> [Name Generated]
                                            -> [Big Five Generated]
                                            -> [Psychographics Generated]
                                            -> [Behavior Generated]
                                            -> [Disabilities Generated]
                                            -> [Tech Caps Generated]
                                            -> [Biases Generated]
                -> [Synth Assembled] -> [Derived Fields Computed]
                                    -> [Saved to File]
                                    -> [Validated against Schema]
```

### Validation States

```
[File Loaded] -> [Schema Validated] -> [Valid] or [Invalid with Errors]
```

---

## Relationships

```
Config (1) ----< generates >---- (*) Synth
Synth (1) ----< contains >---- (1) Demografia
Synth (1) ----< contains >---- (1) Psicografia
Synth (1) ----< contains >---- (1) Comportamento
Synth (1) ----< contains >---- (1) Deficiencias
Synth (1) ----< contains >---- (1) CapacidadesTecnologicas
Synth (1) ----< contains >---- (1) ViesesComportamentais

Demographics ----< uses >---- Config.occupations
Demographics ----< uses >---- Config.ibge
Psychographics ----< uses >---- Config.interests_hobbies
Psychographics ----< uses >---- Config.ibge
Behavior ----< uses >---- Config.interests_hobbies
```

---

## Coherence Rules

1. **Gênero**: `identidade_genero == "mulher cis"` implies `genero_biologico == "feminino"`
2. **Família/Civil**: `estado_civil == "solteiro"` implies `composicao_familiar.tipo != "casal*"`
3. **Família/Pessoas**: `composicao_familiar.tipo == "unipessoal"` implies `numero_pessoas == 1`
4. **Idade/Escolaridade**: `idade < 22` implies `escolaridade != "Pós-graduação"`
5. **Ocupação/Escolaridade**: `escolaridade_index(escolaridade) >= escolaridade_index(ocupacao.escolaridade_minima)`
6. **Renda/Ocupação**: `ocupacao.faixa_salarial.min <= renda <= ocupacao.faixa_salarial.max`
