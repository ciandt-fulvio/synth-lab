# Feature Specification: Gerar Synths Realistas

**Feature Branch**: `001-generate-synths`
**Created**: 2025-12-14
**Status**: Draft
**Input**: User description: "estamos fazendo o seguinte projeto: PRD - Project SynthLab (Nome Provisório) - a primeira feature deve ser 001-generate-synths: Gerar Synths Realistas. Os synths devem ser gerados através de um script que crie um JSON com atributos básicos, demográficos, psicográficos, comportamentais realistas, limitações físicas e cognitivas, capacidades tecnológicas e lentes comportamentais, baseados em dados reais do IBGE e pesquisas de mercado para garantir representação da realidade Brasileira. Devemos começar criando um JSON schema, com informações sobre tipo de dados e domínio."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Gerar Synth Individual com Atributos Completos (Priority: P1)

Um pesquisador de UX precisa criar uma persona sintética representativa de um brasileiro real para validar um novo aplicativo de finanças pessoais. O pesquisador executa um script que gera um único Synth completo com todos os atributos demográficos, psicográficos, comportamentais e cognitivos salvos em formato JSON.

**Why this priority**: Esta é a funcionalidade central e mínima viável - sem a capacidade de gerar ao menos um Synth válido e completo, nenhuma outra funcionalidade da plataforma SynthLab pode existir. É o alicerce de todo o sistema.

**Independent Test**: Pode ser totalmente testado executando o script de geração e validando que o JSON produzido contém todos os campos obrigatórios com valores realistas e dentro dos domínios esperados (ex: idade entre 0-120, renda mensal positiva, etc.).

**Acceptance Scenarios**:

1. **Given** o script de geração está disponível, **When** o pesquisador executa o comando de geração de um Synth, **Then** o sistema cria um arquivo JSON contendo um Synth com todos os atributos básicos (id, nome, arquétipo, descrição, link photo, data de criação)
2. **Given** o JSON de um Synth foi gerado, **When** o pesquisador abre o arquivo, **Then** o Synth contém atributos demográficos completos e realistas (idade, gênero biológico, identidade de gênero, localização Brasil completa, escolaridade, renda mensal, ocupação, estado civil, composição familiar)
3. **Given** o JSON de um Synth foi gerado, **When** o pesquisador valida os atributos psicográficos, **Then** o Synth possui personalidade Big Five, valores, interesses, hobbies, estilo de vida, atitudes, motivações, inclinação política e religiosa
4. **Given** o JSON de um Synth foi gerado, **When** o pesquisador valida os atributos comportamentais, **Then** o Synth possui hábitos de consumo, uso de tecnologia, padrões de mídia, fonte de notícias, comportamento de compra, lealdade à marca e engajamento em redes sociais
5. **Given** o JSON de um Synth foi gerado, **When** o pesquisador valida limitações físicas e cognitivas, **Then** o Synth pode ter nenhuma, uma ou múltiplas deficiências (visuais, auditivas, motoras, cognitivas) conforme distribuição realista
6. **Given** o JSON de um Synth foi gerado, **When** o pesquisador valida capacidades tecnológicas, **Then** o Synth possui nível de alfabetização digital, dispositivos utilizados, configurações de acessibilidade, velocidade de digitação, frequência de uso da internet e familiaridade com plataformas
7. **Given** o JSON de um Synth foi gerado, **When** o pesquisador valida lentes comportamentais, **Then** o Synth possui intensidades realistas de vieses cognitivos de economia comportamental (aversão à perda, desconto hiperbólico, efeito chamariz, ancoragem, viés de confirmação, status quo, sobrecarga de informação)

---

### User Story 2 - Validar Schema JSON dos Synths (Priority: P2)

Um desenvolvedor técnico precisa garantir que os Synths gerados seguem um schema consistente e bem documentado para integração com outras ferramentas. O desenvolvedor acessa um arquivo JSON Schema que define todos os campos, tipos de dados e domínios válidos para cada atributo de um Synth.

**Why this priority**: Sem um schema formal, seria impossível validar automaticamente os Synths gerados, integrar com ferramentas de terceiros ou garantir consistência. Esta é a base para qualidade e escalabilidade, mas depende primeiro de ter Synths sendo gerados (P1).

**Independent Test**: Pode ser testado carregando o JSON Schema em um validador (como AJV) e validando que Synths gerados passam na validação sem erros, além de verificar que o schema documenta todos os domínios e tipos esperados.

**Acceptance Scenarios**:

1. **Given** o JSON Schema está disponível, **When** um desenvolvedor valida um Synth gerado contra o schema, **Then** o Synth passa na validação sem erros
2. **Given** o JSON Schema está disponível, **When** um desenvolvedor inspeciona o schema, **Then** todos os campos obrigatórios estão marcados como `required` e possuem `description` clara em português
3. **Given** o JSON Schema está disponível, **When** um desenvolvedor verifica os domínios de valores, **Then** campos numéricos possuem `minimum` e `maximum`, campos de texto possuem `enum` quando aplicável (ex: estados do Brasil, níveis de escolaridade)
4. **Given** o JSON Schema está disponível, **When** um desenvolvedor tenta validar um Synth com valores inválidos (ex: idade negativa), **Then** a validação falha com mensagem de erro clara

---

### User Story 3 - Gerar Batch de Synths Representativos (Priority: P3)

Um pesquisador de mercado precisa criar 100 Synths que representem a diversidade demográfica brasileira para testar uma campanha de marketing. O pesquisador executa o script com um parâmetro de quantidade, e o sistema gera 100 Synths distribuídos realisticamente por região, idade, renda, etnia e outros fatores demográficos conforme dados do IBGE.

**Why this priority**: Escalabilidade é importante para casos de uso reais (simulações Monte Carlo), mas primeiro precisamos garantir que conseguimos gerar um Synth de qualidade (P1) com schema validado (P2).

**Independent Test**: Pode ser testado executando o script com parâmetro de quantidade (ex: `--count 100`) e validando que: (a) 100 arquivos JSON válidos são criados, (b) a distribuição demográfica agregada se aproxima das proporções reais do IBGE (ex: proporção de pessoas no Sudeste vs Norte, distribuição de faixas etárias).

**Acceptance Scenarios**:

1. **Given** o script de geração aceita parâmetro de quantidade, **When** o pesquisador executa com `--count 100`, **Then** o sistema gera exatamente 100 arquivos JSON de Synths válidos
2. **Given** 100 Synths foram gerados, **When** o pesquisador analisa a distribuição por região, **Then** a proporção de Synths por região (Norte, Nordeste, Centro-Oeste, Sudeste, Sul) aproxima-se da distribuição populacional do IBGE com margem de erro de 10%
3. **Given** 100 Synths foram gerados, **When** o pesquisador analisa a distribuição por faixa etária, **Then** a proporção de Synths por faixa etária aproxima-se da pirâmide etária brasileira
4. **Given** 100 Synths foram gerados, **When** o pesquisador analisa a distribuição por renda, **Then** a proporção reflete a desigualdade de renda real (concentração de baixa renda, cauda longa de alta renda)
5. **Given** 100 Synths foram gerados, **When** o pesquisador valida a diversidade étnica, **Then** as proporções de raça/etnia aproximam-se dos dados do IBGE (pardos, brancos, pretos, amarelos, indígenas)

---

### User Story 4 - Consultar Documentação dos Atributos (Priority: P4)

Um novo usuário do SynthLab precisa entender o que cada atributo do Synth representa e quais valores são válidos. O usuário acessa uma documentação clara que explica cada campo, seu propósito, tipo de dado, domínio válido e exemplos.

**Why this priority**: Essencial para adoção e uso correto da plataforma, mas pode ser desenvolvido em paralelo ou após as funcionalidades de geração estarem funcionando.

**Independent Test**: Pode ser testado fornecendo a documentação a um usuário novo e medindo se ele consegue interpretar corretamente o significado de cada atributo em um Synth gerado, sem precisar de suporte adicional.

**Acceptance Scenarios**:

1. **Given** a documentação está disponível, **When** um usuário busca o significado de "Big Five", **Then** a documentação explica que são os cinco grandes traços de personalidade (Abertura, Conscienciosidade, Extroversão, Amabilidade, Neuroticismo) com escala de valores e exemplos
2. **Given** a documentação está disponível, **When** um usuário busca o significado de "Desconto Hiperbólico", **Then** a documentação explica o viés comportamental com exemplo prático aplicado ao contexto de testes de UX
3. **Given** a documentação está disponível, **When** um usuário quer saber os valores válidos para "Escolaridade", **Then** a documentação lista as categorias do IBGE (Sem instrução, Fundamental incompleto, Fundamental completo, Médio incompleto, etc.)

---

### Edge Cases

- O que acontece quando o script tenta gerar um Synth mas não consegue acessar dados de distribuição (arquivo de configuração do IBGE faltando)?
- Como o sistema lida com valores extremos mas válidos (ex: pessoa de 110 anos, renda mensal de R$ 1.000.000)?
- O que acontece se o usuário solicita 0 Synths ou um número negativo?
- Como garantir que Synths gerados para mesma faixa demográfica ainda têm variação psicográfica e comportamental suficiente (evitar clones)?
- Como o sistema trata combinações estatisticamente raras mas possíveis (ex: pessoa de 90 anos com alta alfabetização digital)?
- O que acontece se dois Synths são gerados simultaneamente e recebem o mesmo ID?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Sistema DEVE gerar um Synth individual completo com todos os atributos obrigatórios em formato JSON válido
- **FR-002**: Sistema DEVE atribuir a cada Synth um ID único de 6 caracteres alfanuméricos
- **FR-003**: Sistema DEVE gerar nome brasileiro realista considerando a localização geográfica do Synth
- **FR-004**: Sistema DEVE associar cada Synth a um arquétipo que resume sua personalidade e perfil
- **FR-005**: Sistema DEVE gerar descrição textual do Synth que resume suas características principais
- **FR-006**: Sistema DEVE incluir timestamp de criação em formato ISO 8601
- **FR-007**: Sistema DEVE gerar atributos demográficos baseados em distribuições reais do IBGE (idade, gênero, localização com País/Estado/Cidade brasileiros, escolaridade, renda mensal, ocupação, estado civil, composição familiar)
- **FR-008**: Sistema DEVE gerar atributos psicográficos incluindo personalidade Big Five (escala 0-100 para cada traço), valores pessoais, interesses, hobbies, estilo de vida, atitudes, motivações, inclinação política (espectro) e religiosa
- **FR-009**: Sistema DEVE gerar atributos comportamentais realistas incluindo hábitos de consumo, uso de tecnologia, padrões de consumo de mídia, fontes de notícias preferidas, comportamento de compra, lealdade à marca, engajamento em redes sociais
- **FR-010**: Sistema DEVE gerar limitações físicas e cognitivas com distribuição realista da população brasileira (incluindo possibilidade de ausência de limitações)
- **FR-011**: Sistema DEVE gerar capacidades tecnológicas incluindo nível de alfabetização digital, tipo de dispositivos utilizados (categorizado como novo/intermediário/antigo), preferências de zoom/fonte, velocidade de digitação, frequência de uso da internet, familiaridade com plataformas online
- **FR-012**: Sistema DEVE atribuir intensidades de vieses comportamentais (economia comportamental) para cada Synth: aversão à perda, desconto hiperbólico, suscetibilidade ao efeito chamariz, ancoragem, viés de confirmação, viés de status quo, sobrecarga de informação
- **FR-013**: Sistema DEVE fornecer um JSON Schema formal documentando todos os campos, tipos, domínios e constraints
- **FR-014**: Sistema DEVE validar que todos os Synths gerados aderem ao JSON Schema antes de salvá-los
- **FR-015**: Sistema DEVE permitir geração de múltiplos Synths em batch através de parâmetro de quantidade
- **FR-016**: Sistema DEVE garantir que a distribuição agregada de um batch de Synths aproxima-se das distribuições demográficas reais do IBGE (regiões, idade, renda, etnia) com margem de erro máxima de 10%
- **FR-017**: Sistema DEVE gerar link para foto de perfil do Synth (placeholder ou gerada via serviço externo)
- **FR-018**: Sistema DEVE garantir que nomes gerados são culturalmente apropriados para a região/etnia do Synth
- **FR-019**: Sistema DEVE salvar cada Synth em arquivo JSON individual nomeado pelo padrão `{id}.json`
- **FR-020**: Sistema DEVE garantir variação suficiente entre Synths da mesma categoria demográfica para evitar duplicação psicográfica

### Key Entities

- **Synth**: Representa uma persona sintética completa. Atributos principais incluem:
  - **Identificação**: id (string de 6 caracteres alfanuméricos), nome (string), arquétipo (string), descrição (string), link_photo (URL), created_at (ISO 8601 timestamp)
  - **Demografia**: idade (0-120 anos), genero_biologico (enum), identidade_genero (enum), localizacao (objeto com país/estado/cidade), escolaridade (enum), renda_mensal (número positivo em BRL), ocupacao (string), estado_civil (enum), composicao_familiar (objeto descrevendo estrutura familiar)
  - **Psicografia**: personalidade_big_five (objeto com 5 traits de 0-100), valores (array de strings), interesses (array de strings), hobbies (array de strings), estilo_vida (string), atitudes (objeto), motivacoes (array de strings), inclinacao_politica (escala -100 a +100), inclinacao_religiosa (string/enum)
  - **Comportamento**: habitos_consumo (objeto), uso_tecnologia (objeto), padroes_midia (objeto), fonte_noticias (array de strings), comportamento_compra (objeto), lealdade_marca (escala), engajamento_redes_sociais (objeto)
  - **Limitações**: deficiencias (objeto com booleanos/escalas para visual, auditiva, motora, cognitiva)
  - **Capacidade Tecnológica**: alfabetizacao_digital (escala 0-100), dispositivos (array de objetos), preferencias_acessibilidade (objeto), velocidade_digitacao (palavras/minuto), frequencia_internet (enum), familiaridade_plataformas (objeto)
  - **Vieses Comportamentais**: aversao_perda (escala 0-100), desconto_hiperbolico (escala 0-100), suscetibilidade_chamariz (escala 0-100), ancoragem (escala 0-100), vies_confirmacao (escala 0-100), vies_status_quo (escala 0-100), sobrecarga_informacao (escala 0-100)

- **JSON Schema**: Define a estrutura formal, tipos de dados e validações para o Synth. Relacionamento: todo Synth gerado DEVE ser validado contra este schema.

- **Dados de Referência IBGE**: Distribuições estatísticas da população brasileira (região, idade, renda, etnia, escolaridade). Relacionamento: usado como base probabilística para gerar atributos demográficos realistas dos Synths.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Sistema gera um Synth individual completo em menos de 5 segundos
- **SC-002**: 100% dos Synths gerados passam na validação do JSON Schema sem erros
- **SC-003**: Sistema gera batch de 100 Synths em menos de 2 minutos
- **SC-004**: Distribuição demográfica agregada de 1000 Synths gerados aproxima-se da distribuição real do IBGE com erro máximo de 10% para cada categoria demográfica principal (região, faixa etária, faixa de renda)
- **SC-005**: Nenhum Synth gerado possui ID duplicado em uma sessão de 10.000 gerações
- **SC-006**: 95% dos usuários novos conseguem interpretar o significado dos atributos de um Synth consultando apenas a documentação, sem necessidade de suporte adicional
- **SC-007**: Variação psicográfica entre Synths da mesma faixa demográfica é superior a 60% (medida por distância euclidiana nos atributos psicográficos e comportamentais)
- **SC-008**: Todos os nomes gerados são reconhecidos como nomes brasileiros válidos por validadores de antroponímia
- **SC-009**: 100% dos Synths gerados possuem todos os campos obrigatórios preenchidos (nenhum campo null/undefined)
- **SC-010**: Sistema suporta geração de até 10.000 Synths em uma única execução sem falha de memória ou corrupção de dados

## Assumptions

- **A-001**: Dados do IBGE estão disponíveis em formato estruturado (JSON/CSV) ou podem ser incorporados em arquivo de configuração estático no projeto
- **A-002**: Distribuições de vieses comportamentais seguem distribuição normal na população brasileira (não há dados IBGE específicos para isso)
- **A-003**: Fotos de perfil podem ser links placeholder inicialmente (ex: https://placeholder.com/) ou integração futura com serviço de geração de avatares
- **A-004**: Escala Big Five usa valores de 0-100 onde 50 é a média populacional e valores extremos (0-20, 80-100) são raros
- **A-005**: Nomenclatura de ocupações segue classificação brasileira de ocupações (CBO) quando possível
- **A-006**: Para atributos sem dados estatísticos disponíveis (ex: lealdade a marcas), assume-se distribuição uniforme ou normal com parametrização razoável
- **A-007**: Sistema será executado em ambiente com Python 3.13+ e biblioteca padrão disponível
- **A-008**: Arquivos JSON gerados serão armazenados localmente no filesystem (não em banco de dados nesta fase)

## Dependencies

- **D-001**: Dados demográficos do IBGE (pode ser arquivo estático incorporado ao projeto ou API pública do IBGE)
- **D-002**: Biblioteca de validação de JSON Schema para Python (ex: jsonschema)
- **D-003**: Gerador de nomes brasileiros (pode ser lista estática ou biblioteca como `python-faker` com locale pt-BR)
- **D-004**: Gerador de IDs alfanuméricos (disponível na biblioteca padrão Python com `random` e `string`)

## Out of Scope

- **OS-001**: Hidratação de Synths com contexto momentâneo (notícias, clima, economia) - isso faz parte de feature futura
- **OS-002**: Interface gráfica para visualização ou edição manual de Synths
- **OS-003**: Armazenamento de Synths em banco de dados
- **OS-004**: API REST para acesso aos Synths gerados
- **OS-005**: Geração de fotos de perfil realistas via IA (nesta fase usamos placeholders ou links externos)
- **OS-006**: Suporte a outros países além do Brasil
- **OS-007**: Personalização de distribuições demográficas pelo usuário (ex: "gere apenas Synths da região Sul")
- **OS-008**: Versionamento ou histórico de alterações em Synths
- **OS-009**: Execução do sistema "hot" (agentes rodando 24/7) - Synths são arquivos estáticos "frios"
