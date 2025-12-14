# Modelo de Dados: Synth

**Feature**: 001-generate-synths
**Data**: 2025-12-14
**Fase**: Phase 1 - Design & Contracts

## Visão Geral

Este documento define a estrutura completa de um **Synth** (Synthetic Persona) - uma persona sintética representativa de um indivíduo brasileiro com atributos demográficos, psicográficos, comportamentais, físicos/cognitivos e de vieses comportamentais.

**Formato de Armazenamento**: JSON (um arquivo por Synth)
**Localização**: `data/synths/{id}.json`
**Validação**: JSON Schema em `data/schemas/synth-schema.json`

---

## Estrutura Completa do Synth

### 1. Identificação (7 campos)

Atributos únicos que identificam o Synth.

| Campo | Tipo | Obrigatório | Descrição | Exemplo | Validação |
|-------|------|-------------|-----------|---------|-----------|
| `id` | string | ✅ | Identificador único do Synth (6 caracteres alfanuméricos) | `"a1B2c3"` | String de 6 posições (letras e dígitos) |
| `nome` | string | ✅ | Nome completo brasileiro (primeiro nome + sobrenome) | `"Maria Silva Santos"` | 2-100 caracteres |
| `arquetipo` | string | ✅ | Resumo do perfil: "{Faixa Etária} {Região} {Perfil Psicográfico}" | `"Jovem Adulto Nordestina Criativa"` | Derivado automaticamente |
| `descricao` | string | ✅ | Descrição textual resumida do Synth | `"Mulher de 28 anos, designer gráfica, mora em Recife..."` | 50-500 caracteres |
| `link_photo` | string (URL) | ✅ | Link para foto de perfil (avatar gerado) | `"https://ui-avatars.com/api/?name=Maria+Silva&size=256"` | URL válida |
| `created_at` | string (ISO 8601) | ✅ | Timestamp de criação | `"2025-12-14T15:30:00Z"` | ISO 8601 com timezone |
| `version` | string | ✅ | Versão do schema usado | `"1.0.0"` | Semantic versioning |

---

### 2. Demografia (14 campos)

Atributos demográficos baseados em distribuições reais do IBGE.

| Campo | Tipo | Obrigatório | Descrição | Domínio/Enum | Fonte IBGE |
|-------|------|-------------|-----------|--------------|------------|
| `idade` | integer | ✅ | Idade em anos completos | 0-120 | Pirâmide etária IBGE 2023 |
| `genero_biologico` | string (enum) | ✅ | Gênero biológico | `["masculino", "feminino", "intersexo"]` | IBGE Censo |
| `identidade_genero` | string (enum) | ✅ | Identidade de gênero | `["homem cis", "mulher cis", "homem trans", "mulher trans", "não-binário", "outro"]` | - |
| `raca_etnia` | string (enum) | ✅ | Raça/etnia autodeclarada | `["branco", "pardo", "preto", "amarelo", "indígena"]` | PNAD 2022 |
| `localizacao.pais` | string | ✅ | País (sempre "Brasil" nesta versão) | `"Brasil"` | - |
| `localizacao.regiao` | string (enum) | ✅ | Região brasileira | `["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"]` | IBGE 2022 |
| `localizacao.estado` | string (enum) | ✅ | Estado (UF) | `["AC", "AL", ..., "TO"]` (27 UFs) | IBGE |
| `localizacao.cidade` | string | ✅ | Nome da cidade | `"São Paulo"`, `"Recife"` | Capitais + cidades grandes |
| `escolaridade` | string (enum) | ✅ | Nível de escolaridade | Ver tabela abaixo | PNAD Educação 2022 |
| `renda_mensal` | number | ✅ | Renda mensal individual em BRL | Valores positivos | PNAD Contínua 2023 |
| `ocupacao` | string | ✅ | Profissão/ocupação atual | CBO (200 comuns) | CBO 2022 |
| `estado_civil` | string (enum) | ✅ | Estado civil | `["solteiro", "casado", "união estável", "divorciado", "viúvo"]` | IBGE Registro Civil |
| `composicao_familiar.tipo` | string (enum) | ✅ | Tipo de família | `["unipessoal", "casal sem filhos", "casal com filhos", "monoparental", "multigeracional", "outros"]` | - |
| `composicao_familiar.numero_pessoas` | integer | ✅ | Número de pessoas no domicílio | 1-15 | - |

**Tabela de Escolaridade**:
```json
[
  "Sem instrução",
  "Fundamental incompleto",
  "Fundamental completo",
  "Médio incompleto",
  "Médio completo",
  "Superior incompleto",
  "Superior completo",
  "Pós-graduação"
]
```

---

### 3. Psicografia (8 campos + sub-campos)

Atributos de personalidade, valores e interesses.

**Nota**: Campos "atitudes" e "motivações" foram **removidos** conforme research.md (Seção 9) - sem fonte de dados confiável disponível.

| Campo | Tipo | Obrigatório | Descrição | Domínio | Distribuição |
|-------|------|-------------|-----------|---------|--------------|
| `personalidade_big_five.abertura` | integer | ✅ | Abertura a experiências | 0-100 | Normal (μ=50, σ=15) |
| `personalidade_big_five.conscienciosidade` | integer | ✅ | Conscienciosidade | 0-100 | Normal (μ=50, σ=15) |
| `personalidade_big_five.extroversao` | integer | ✅ | Extroversão | 0-100 | Normal (μ=50, σ=15) |
| `personalidade_big_five.amabilidade` | integer | ✅ | Amabilidade | 0-100 | Normal (μ=50, σ=15) |
| `personalidade_big_five.neuroticismo` | integer | ✅ | Neuroticismo | 0-100 | Normal (μ=50, σ=15) |
| `valores` | array[string] | ✅ | Valores pessoais (baseado em Schwartz Theory) | Ex: `["família", "trabalho", "liberdade"]` | Lista curada (~30-50 valores) |
| `interesses` | array[string] | ✅ | Áreas de interesse | Ex: `["tecnologia", "esportes", "música"]` | Lista curada (~100 interesses) |
| `hobbies` | array[string] | ✅ | Hobbies praticados (fonte: TIM + USP) | Ex: `["leitura", "videogames", "culinária"]` | Lista curada (~50-80 hobbies) |
| `estilo_vida` | string | ✅ | Descrição do estilo de vida | Ex: `"ativo e social"`, `"caseiro e tranquilo"` | Derivado de Big Five |
| `inclinacao_politica` | integer | ✅ | Espectro político | -100 (esquerda) a +100 (direita), 0=centro | DataSenado 2024: 29% direita, 15% esquerda, 11% centro, 40% neutro |
| `inclinacao_religiosa` | string (enum) | ✅ | Religião/crença | `["católico", "evangélico", "espírita", "umbanda/candomblé", "ateu/agnóstico", "outras"]` | IBGE Censo Religião 2022 |

**Fonte de Dados Psicográficos**:
- **Big Five**: Literatura psicométrica internacional (distribuição normal padrão)
- **Valores**: Schwartz Theory of Basic Values (lista curada de ~30-50 valores universais)
- **Hobbies**: Pesquisa TIM + USP sobre atividades de lazer dos brasileiros
- **Inclinação Política**: DataSenado/Nexus "Panorama Político 2024" (21.808 brasileiros)
- **Inclinação Religiosa**: IBGE Censo 2022 - Religião

---

### 4. Comportamento (9 campos + sub-campos)

Padrões comportamentais de consumo, tecnologia e mídia.

| Campo | Tipo | Obrigatório | Descrição | Exemplo | Fonte |
|-------|------|-------------|-----------|---------|-------|
| `habitos_consumo.frequencia_compras` | string (enum) | ✅ | Frequência de compras | `["diária", "semanal", "quinzenal", "mensal", "esporádica"]` | - |
| `habitos_consumo.preferencia_canal` | string (enum) | ✅ | Canal preferido | `["loja física", "e-commerce", "híbrido"]` | - |
| `habitos_consumo.categorias_preferidas` | array[string] | ✅ | Categorias de produtos | `["eletrônicos", "vestuário", "alimentos"]` | Lista curada |
| `uso_tecnologia.smartphone` | boolean | ✅ | Possui smartphone | `true/false` | - |
| `uso_tecnologia.computador` | boolean | ✅ | Possui computador | `true/false` | - |
| `uso_tecnologia.tablet` | boolean | ✅ | Possui tablet | `true/false` | - |
| `uso_tecnologia.smartwatch` | boolean | ✅ | Possui smartwatch | `true/false` | - |
| `padroes_midia.tv_aberta` | integer | ✅ | Horas/semana de TV aberta | 0-70 | - |
| `padroes_midia.streaming` | integer | ✅ | Horas/semana de streaming | 0-70 | - |
| `padroes_midia.redes_sociais` | integer | ✅ | Horas/semana em redes sociais | 0-70 | - |
| `fonte_noticias` | array[string] | ✅ | Fontes de notícias | `["TV", "jornais online", "redes sociais", "podcasts"]` | - |
| `comportamento_compra.impulsivo` | integer | ✅ | Tendência a compras impulsivas | 0-100 | Normal (μ=50, σ=20) |
| `comportamento_compra.pesquisa_antes_comprar` | integer | ✅ | Pesquisa antes de comprar | 0-100 | Normal (μ=60, σ=20) |
| `lealdade_marca` | integer | ✅ | Lealdade a marcas | 0-100 (0=troca fácil, 100=muito fiel) | Normal (μ=50, σ=20) |
| `engajamento_redes_sociais.plataformas` | array[string] | ✅ | Plataformas usadas | `["WhatsApp", "Instagram", "Facebook", "TikTok", "LinkedIn"]` | - |
| `engajamento_redes_sociais.frequencia_posts` | string (enum) | ✅ | Frequência de posts | `["nunca", "raro", "ocasional", "frequente", "muito frequente"]` | - |

---

### 5. Limitações Físicas e Cognitivas (5 campos)

Deficiências e limitações (distribuição realista da população).

| Campo | Tipo | Obrigatório | Descrição | Domínio | Prevalência IBGE PNS 2019 |
|-------|------|-------------|-----------|---------|------------------|
| `deficiencias.visual.tipo` | string (enum) \| null | ✅ | Tipo de deficiência visual | `["nenhuma", "leve", "moderada", "severa", "cegueira"]` | 3,4% da população |
| `deficiencias.auditiva.tipo` | string (enum) \| null | ✅ | Tipo de deficiência auditiva | `["nenhuma", "leve", "moderada", "severa", "surdez"]` | 1,1% da população |
| `deficiencias.motora.tipo` | string (enum) \| null | ✅ | Tipo de deficiência motora (membros inferiores) | `["nenhuma", "leve", "moderada", "severa"]` | 3,8% da população |
| `deficiencias.motora.usa_cadeira_rodas` | boolean | ✅ | Usa cadeira de rodas | `true/false` | Se motora severa |
| `deficiencias.cognitiva.tipo` | string (enum) \| null | ✅ | Tipo de limitação cognitiva/mental | `["nenhuma", "leve", "moderada", "severa"]` | 1,2% da população |

**Nota**: Total de 8,4% da população possui pelo menos uma deficiência (IBGE PNS 2019). 91,6% dos Synths terão "nenhuma" em todos os campos.

---

### 6. Capacidades Tecnológicas (10 campos)

Alfabetização digital e familiaridade com tecnologia.

**Fonte**: TIC Domicílios 2023 (CETIC.br) + NielsenIQ Ebit 2023

| Campo | Tipo | Obrigatório | Descrição | Domínio | Correlação |
|-------|------|-------------|-----------|---------|------------|
| `alfabetizacao_digital` | integer | ✅ | Nível de alfabetização digital | 0-100 | Correlaciona com idade (inverso) e escolaridade |
| `dispositivos.principal` | string (enum) | ✅ | Dispositivo principal | `["smartphone", "computador", "tablet", "nenhum"]` | - |
| `dispositivos.qualidade` | string (enum) | ✅ | Qualidade do dispositivo | `["novo", "intermediário", "antigo"]` | Correlaciona com renda |
| `preferencias_acessibilidade.zoom_fonte` | integer | ✅ | Nível de zoom/fonte (%) | 100-300 | Correlaciona com idade/deficiência visual |
| `preferencias_acessibilidade.alto_contraste` | boolean | ✅ | Usa alto contraste | `true/false` | Correlaciona com deficiência visual |
| `velocidade_digitacao` | integer | ✅ | Palavras por minuto | 10-120 | Correlaciona com idade e alfabetização digital |
| `frequencia_internet` | string (enum) | ✅ | Frequência de acesso | `["diária", "semanal", "mensal", "rara"]` | Correlaciona com renda/escolaridade |
| `familiaridade_plataformas.e_commerce` | integer | ✅ | Familiaridade com e-commerce | 0-100 | - |
| `familiaridade_plataformas.banco_digital` | integer | ✅ | Familiaridade com banco digital | 0-100 | - |
| `familiaridade_plataformas.redes_sociais` | integer | ✅ | Familiaridade com redes sociais | 0-100 | - |

---

### 7. Vieses Comportamentais (7 campos)

Intensidade de vieses de economia comportamental (Behavioral Economics).

**Fonte**: Literatura acadêmica de Behavioral Economics (Kahneman & Tversky, Thaler, Decision Lab)

| Campo | Tipo | Obrigatório | Descrição | Domínio | Implicação UX |
|-------|------|-------------|-----------|---------|---------------|
| `vieses.aversao_perda` | integer | ✅ | Aversão à perda | 0-100 | Alto: evita riscos, prefere status quo |
| `vieses.desconto_hiperbolico` | integer | ✅ | Desconto hiperbólico | 0-100 | Alto: prefere recompensas imediatas |
| `vieses.suscetibilidade_chamariz` | integer | ✅ | Efeito chamariz (decoy) | 0-100 | Alto: influenciado por opção intermediária |
| `vieses.ancoragem` | integer | ✅ | Ancoragem | 0-100 | Alto: primeiro preço visto influencia decisão |
| `vieses.vies_confirmacao` | integer | ✅ | Viés de confirmação | 0-100 | Alto: busca informações que confirmam crenças |
| `vieses.vies_status_quo` | integer | ✅ | Viés de status quo | 0-100 | Alto: prefere manter escolhas atuais |
| `vieses.sobrecarga_informacao` | integer | ✅ | Sobrecarga de informação | 0-100 | Alto: paralisa com muitas opções |

**Distribuição**: Todos os 7 vieses seguem distribuição Normal (μ=50, σ=20).
**Rationale**: Não há dados populacionais brasileiros específicos sobre prevalência de vieses. Literatura confirma que vieses existem em graus variados na população geral. Modelados como traços contínuos sem categorização binária, permitindo extremos mais frequentes que Big Five.

---

## Validação e Regras de Negócio

### Regras de Consistência

1. **Idade vs. Escolaridade**:
   - Idade <15: Máximo "Fundamental incompleto"
   - Idade 15-17: Máximo "Médio incompleto"
   - Idade 18+: Qualquer escolaridade possível

2. **Deficiências vs. Capacidades Tecnológicas**:
   - Deficiência visual severa/cegueira → `alto_contraste=true`, `zoom_fonte>=150`
   - Deficiência motora severa → `velocidade_digitacao` reduzida (10-40 wpm)

3. **Renda vs. Dispositivos**:
   - Renda <1 SM: Maioria `dispositivos.qualidade="antigo"`
   - Renda >10 SM: Maioria `dispositivos.qualidade="novo"`

4. **Região vs. Cidade**:
   - Estado deve pertencer à região especificada
   - Cidade deve existir no estado especificado

5. **Big Five vs. Estilo de Vida**:
   - Alta Extroversão + Baixo Neuroticismo → "Ativo e social"
   - Baixa Extroversão + Alto Neuroticismo → "Reservado e cauteloso"

### Campos Derivados Automaticamente

Os seguintes campos são **calculados automaticamente** (não gerados aleatoriamente):

- **`arquetipo`**: Baseado em idade + região + Big Five dominante
  - Exemplo: "Jovem Adulto Nordestina Criativa" (idade 28, região Nordeste, alta abertura)

- **`descricao`**: Template preenchido com atributos chave
  - Inclui: idade, ocupação, localização, traços de personalidade dominantes

- **`link_photo`**: Gerado a partir do nome usando serviço de avatar
  - Formato: `https://ui-avatars.com/api/?name={nome}&size=256&background=random`

- **`estilo_vida`**: Derivado dos traços Big Five
  - Alta Extroversão + Baixo Neuroticismo → "Ativo e social"
  - Baixa Extroversão + Alto Neuroticismo → "Reservado e cauteloso"
  - Alta Abertura + Alta Conscienciosidade → "Criativo e organizado"
  - Outras combinações geram estilos de vida descritivos apropriados

- **`created_at`**: Timestamp ISO 8601 no momento da geração

- **`version`**: Versão do schema (hardcoded, ex: "1.0.0")

**Nota Importante**: "Atitudes" e "Motivações" foram **removidos** do modelo (antes considerados para derivação) por falta de dados populacionais confiáveis (ver research.md Seção 9).

---

## Exemplo Completo de Synth

Ver arquivo: `specs/001-generate-synths/contracts/synth-example.json`

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

## Mapeamento para Functional Requirements

| Categoria | Functional Requirements Atendidos |
|-----------|----------------------------------|
| **Identificação** | FR-001, FR-002, FR-004, FR-005, FR-006, FR-017 |
| **Demografia** | FR-003, FR-007, FR-018 |
| **Psicografia** | FR-008 |
| **Comportamento** | FR-009 |
| **Limitações** | FR-010 |
| **Capacidades Tech** | FR-011 |
| **Vieses** | FR-012 |
| **Validação** | FR-013, FR-014 |
| **Armazenamento** | FR-019 |
| **Variação** | FR-020 |

---

## Changelog - Alinhamento com Research.md

**Data**: 2025-12-14

### Mudanças Realizadas

1. **Seção 3 - Psicografia**:
   - ✅ Corrigido campo `extroversao` (antes estava "extrover sao")
   - ✅ Removida menção a "motivações" na descrição da seção
   - ✅ Atualizada contagem de campos: 8 campos (antes 10)
   - ✅ Adicionada nota sobre remoção de "atitudes" e "motivações"
   - ✅ Atualizada descrição de `valores` para indicar fonte (Schwartz Theory)
   - ✅ Atualizada descrição de `hobbies` para indicar fonte (TIM + USP)
   - ✅ Atualizada distribuição de `inclinacao_politica` com dados DataSenado 2024
   - ✅ Adicionada seção "Fonte de Dados Psicográficos"

2. **Seção 5 - Limitações Físicas e Cognitivas**:
   - ✅ Corrigidas prevalências conforme IBGE PNS 2019:
     - Visual: 3,4% (mantido)
     - Auditiva: 1,1% (mantido)
     - Motora: 3,8% (antes 2,3%)
     - Cognitiva: 1,2% (antes 0,8%)
   - ✅ Adicionada nota sobre total de 8,4% com pelo menos uma deficiência

3. **Seção 6 - Capacidades Tecnológicas**:
   - ✅ Adicionada fonte de dados (TIC Domicílios 2023 + NielsenIQ Ebit 2023)

4. **Seção 7 - Vieses Comportamentais**:
   - ✅ Adicionada fonte de dados (Literatura acadêmica)
   - ✅ Expandida nota sobre distribuição Normal (μ=50, σ=20)
   - ✅ Adicionado rationale sobre modelagem como traços contínuos

5. **Campos Derivados Automaticamente**:
   - ✅ Expandida descrição de como `estilo_vida` é derivado
   - ✅ Adicionada nota sobre remoção de "Atitudes" e "Motivações"

### Conformidade com Research.md

- ✅ **Seção 9 do research.md** (Campos Removidos): Implementado
  - Atitudes: Removidas (sem fonte confiável)
  - Motivações: Removidas (sem fonte confiável)
  - Estilo de Vida: Mantido como campo derivado

- ✅ **Distribuições IBGE**: Todas atualizadas conforme Censo 2022 e PNAD 2023

- ✅ **Vieses Comportamentais**: Confirmado uso de distribuição Normal (μ=50, σ=20)

- ✅ **Big Five**: Confirmado uso de distribuição Normal (μ=50, σ=15)

---

## Próximos Passos

1. ✅ Data model definido e atualizado conforme research.md
2. ⏭️ Atualizar JSON Schema formal (`contracts/synth-schema.json`) para refletir mudanças
3. ⏭️ Validar quickstart.md está alinhado com data model atualizado
4. ⏭️ Implementar funções de geração (Phase 2 - Tasks)
