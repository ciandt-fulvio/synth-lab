# Requisitos do Projeto synth-lab

## Visão Geral

O **synth-lab** é uma plataforma completa para geração e gerenciamento de personas sintéticas brasileiras (Synths), com capacidade de realizar pesquisas de UX qualitativas simuladas através de entrevistas com IA.

## Requisitos Funcionais

### RF1 - Geração de Personas Sintéticas

#### RF1.1 - Geração Individual
- O sistema deve permitir a geração de personas sintéticas individuais
- Cada synth deve ter atributos demográficos, psicográficos, comportamentais e cognitivos
- Os dados devem ser baseados em distribuições estatísticas reais (IBGE, PNAD, TIC Domicílios)
- Cada synth deve ter um ID único de 6 caracteres

#### RF1.2 - Geração em Lote
- O sistema deve permitir a geração de múltiplos synths em uma única operação
- O sistema deve suportar geração de até 1000 synths por lote
- A geração em lote deve ser eficiente (>1000 synths/segundo)

#### RF1.3 - Geração de Avatares
- O sistema deve gerar avatares visuais realistas usando OpenAI DALL-E
- Avatares devem ter 341x341 pixels em formato PNG
- Cada avatar deve refletir as características demográficas do synth (idade, gênero, etnia)
- O sistema deve suportar geração em blocos de 9 avatares
- O sistema deve armazenar avatares no diretório `output/synths/avatar/`

### RF2 - Topic Guides (Materiais de Contexto)

#### RF2.1 - Criação de Topic Guides
- O sistema deve permitir a criação de topic guides com nome único
- Cada topic guide deve ter um diretório próprio em `data/topic_guides/`
- O sistema deve criar automaticamente um arquivo `summary.md` inicial

#### RF2.2 - Gerenciamento de Arquivos
- O sistema deve suportar imagens (PNG, JPEG), PDFs, markdown e texto
- O sistema deve gerar descrições automáticas de imagens usando OpenAI Vision API
- O sistema deve extrair e processar conteúdo de PDFs e documentos de texto
- O sistema deve usar hash de conteúdo para detectar mudanças

#### RF2.3 - Estrutura de Script
- Cada topic guide deve ter um arquivo `script.json` com perguntas estruturadas
- Perguntas devem ter ID único e texto (`ask`)
- O sistema deve validar a estrutura do script ao carregar

### RF3 - Entrevistas de Pesquisa UX

#### RF3.1 - Entrevista Individual
- O sistema deve permitir entrevistas entre um interviewer (IA) e um synth (IA)
- O interviewer deve usar o topic guide como roteiro
- O synth deve responder baseado em sua personalidade Big Five
- O sistema deve suportar configuração de número máximo de turnos
- O sistema deve salvar transcrições em formato JSON

#### RF3.2 - Pesquisa em Batch
- O sistema deve permitir entrevistas paralelas com múltiplos synths
- O sistema deve suportar paralelização com controle de concorrência
- O sistema deve gerar um resumo agregado (summary) ao final
- O sistema deve tratar rate limits da OpenAI com retry automático
- O sistema deve mostrar progresso em tempo real

#### RF3.3 - Streaming de Progresso
- A API REST deve transmitir eventos de progresso via Server-Sent Events (SSE)
- Eventos devem incluir: início, turnos de conversação, conclusão, erros
- O sistema deve permitir que clientes web acompanhem execuções em tempo real

### RF4 - Relatórios

#### RF4.1 - Summary de Pesquisa
- O sistema deve gerar resumos executivos de research executions
- Resumos devem incluir insights agregados de múltiplas entrevistas
- Resumos devem ser salvos em formato Markdown

#### RF4.2 - PR-FAQ
- O sistema deve gerar documentos Press Release + FAQ a partir de research
- PR-FAQ deve incluir headline, one-liner e perguntas frequentes
- O sistema deve calcular score de confiança da geração
- O sistema deve validar a qualidade do PR-FAQ gerado

### RF5 - API REST

#### RF5.1 - Endpoints de Synths
- `GET /synths/list` - Listar synths com paginação
- `GET /synths/{synth_id}` - Obter detalhes de um synth
- `POST /synths/search` - Busca avançada com SQL WHERE clause
- `GET /synths/{synth_id}/avatar` - Download de avatar (PNG)
- `GET /synths/fields` - Listar campos disponíveis para filtros

#### RF5.2 - Endpoints de Topics
- `GET /topics/list` - Listar topic guides com paginação
- `GET /topics/{topic_name}` - Obter detalhes de um topic
- `GET /topics/{topic_name}/research` - Listar research executions de um topic

#### RF5.3 - Endpoints de Research
- `POST /research/execute` - Executar pesquisa com streaming SSE
- `GET /research/list` - Listar research executions
- `GET /research/{exec_id}` - Obter detalhes de uma execution
- `GET /research/{exec_id}/transcripts` - Listar transcrições
- `GET /research/{exec_id}/transcripts/{synth_id}` - Obter transcrição específica
- `GET /research/{exec_id}/summary` - Download do summary (Markdown)

#### RF5.4 - Endpoints de PR-FAQ
- `GET /prfaq/list` - Listar PR-FAQs gerados
- `GET /prfaq/{exec_id}` - Obter metadata de um PR-FAQ
- `GET /prfaq/{exec_id}/markdown` - Download do PR-FAQ (Markdown)

#### RF5.5 - Endpoints de Jobs
- `GET /jobs/{job_id}` - Consultar status de job assíncrono

### RF6 - Interface CLI

#### RF6.1 - Comandos de Geração
- `synthlab gensynth` - Gerar synths com opções de quantidade, avatares, benchmark
- `synthlab gensynth --validate-all` - Validar todos os synths
- `synthlab gensynth --analyze <type>` - Analisar distribuições

#### RF6.2 - Comandos de Consulta
- `synthlab listsynth` - Listar synths com filtros SQL
- `synthlab listsynth --where <clause>` - Filtrar com WHERE clause
- `synthlab listsynth --full-query <sql>` - Query SQL personalizada

#### RF6.3 - Comandos de Topic Guides
- `synthlab topic-guide create` - Criar novo topic guide
- `synthlab topic-guide update` - Atualizar descrições de arquivos
- `synthlab topic-guide list` - Listar topic guides
- `synthlab topic-guide show` - Visualizar conteúdo de um guide

#### RF6.4 - Comandos de Research
- `synthlab research interview` - Entrevista individual
- `synthlab research batch` - Entrevistas em lote

### RF7 - Persistência de Dados

#### RF7.1 - Banco de Dados SQLite
- O sistema deve usar SQLite com extensão JSON1
- O banco deve estar localizado em `output/synthlab.db`
- O banco deve usar modo WAL para leituras concorrentes
- O banco deve enforçar foreign keys e constraints

#### RF7.2 - Modelos de Dados
- Synths devem ter campos JSON para dados aninhados (demografia, psicografia)
- Research executions devem ter status (pending, running, completed, failed)
- Transcripts devem ter mensagens em formato JSON
- Topic guides devem cachear metadata (contagem de arquivos, hashes)

## Requisitos Não-Funcionais

### RNF1 - Performance

#### RNF1.1 - Geração de Synths
- Geração individual: < 0.01s por synth
- Geração em lote: > 1000 synths/segundo
- Batch de 100 synths: < 2 minutos (incluindo avatares)

#### RNF1.2 - API REST
- Tempo de resposta de listagem: < 100ms para 50 itens
- Paginação: suportar até 200 itens por página
- Streaming SSE: latência < 500ms por evento

#### RNF1.3 - Banco de Dados
- Queries de leitura: < 50ms para queries simples
- Suporte a leituras concorrentes (modo WAL)
- Índices em campos frequentemente consultados

### RNF2 - Escalabilidade

#### RNF2.1 - Armazenamento
- Suportar até 10.000 synths no banco
- Suportar até 1.000 research executions
- Avatares compactados em PNG (< 100KB por avatar)

#### RNF2.2 - Concorrência
- Suportar até 10 entrevistas paralelas em research batch
- API deve suportar múltiplas conexões simultâneas
- Controle de rate limit da OpenAI com retry automático

### RNF3 - Confiabilidade

#### RNF3.1 - Validação de Dados
- 100% dos synths devem passar validação JSON Schema
- Distribuições demográficas: < 10% erro vs. IBGE
- Consistência interna: relações entre atributos validadas

#### RNF3.2 - Tratamento de Erros
- Retry automático para erros transitórios (rate limits)
- Rollback de transações em caso de falha
- Logging estruturado de erros com contexto

#### RNF3.3 - Disponibilidade
- API REST deve ter endpoint `/health` para health checks
- Banco de dados deve ter backup automático (WAL mode)
- Tolerância a falhas em jobs assíncronos

### RNF4 - Usabilidade

#### RNF4.1 - Interface CLI
- Mensagens de erro claras e actionáveis
- Output colorido e formatado com Rich
- Progress bars para operações longas
- Documentação inline com `--help`

#### RNF4.2 - API REST
- Documentação interativa em `/docs` (Swagger UI)
- Mensagens de erro padronizadas com códigos
- Respostas JSON bem formatadas
- CORS configurado para desenvolvimento web

#### RNF4.3 - Developer Experience
- Type hints completas em todo o código
- Modelos Pydantic para validação automática
- Dependency injection para testabilidade
- Logging estruturado com níveis configuráveis

### RNF5 - Manutenibilidade

#### RNF5.1 - Arquitetura
- Arquitetura em 3 camadas (Interface → Service → Database)
- Separação clara de responsabilidades
- Service layer compartilhada entre CLI e API
- Repositórios isolam acesso ao banco de dados

#### RNF5.2 - Código
- Máximo 500 linhas por arquivo
- Funções com < 30 linhas
- Cobertura de testes > 80%
- Linting com Ruff (PEP 8)

#### RNF5.3 - Documentação
- Docstrings Google-style em todas as funções públicas
- README completo com exemplos
- Documentação de arquitetura atualizada
- Changelog de versões

### RNF6 - Segurança

#### RNF6.1 - API REST
- Validação de entrada com Pydantic
- Sanitização de queries SQL (whitelist de keywords)
- CORS configurável por ambiente
- Rate limiting (futuro)

#### RNF6.2 - Dados Sensíveis
- OpenAI API Key em variável de ambiente
- Não logar credenciais ou tokens
- Hash de conteúdo de arquivos (MD5) para cache

#### RNF6.3 - Banco de Dados
- Foreign keys habilitadas
- Constraints de validação (JSON_VALID)
- Transações com rollback automático
- Backup regular do arquivo `.db`

### RNF7 - Compatibilidade

#### RNF7.1 - Python
- Python 3.13+
- Type hints modernos (list[T], dict[K,V])
- Async/await para operações I/O

#### RNF7.2 - Dependências
- FastAPI >= 0.109.0
- Pydantic >= 2.5.0
- SQLite 3.38+ (JSON1 built-in)
- OpenAI SDK >= 2.8.0

#### RNF7.3 - Plataformas
- Linux, macOS, Windows
- Docker (futuro)
- Cloud deployment ready (futuro)

## Priorização de Requisitos

### P0 - Críticos (MVP)
- RF1.1, RF1.2 - Geração de synths
- RF5.1 - Endpoints de synths (list, get)
- RF7.1, RF7.2 - Banco de dados SQLite
- RNF1.1 - Performance de geração
- RNF3.1 - Validação de dados

### P1 - Importantes
- RF1.3 - Geração de avatares
- RF2 - Topic guides completo
- RF3.1, RF3.2 - Entrevistas (individual e batch)
- RF5.2, RF5.3 - Endpoints de topics e research
- RNF2.2 - Concorrência
- RNF4 - Usabilidade

### P2 - Desejáveis
- RF3.3 - Streaming SSE
- RF4 - Relatórios (summary, PR-FAQ)
- RF5.4, RF5.5 - Endpoints de PR-FAQ e jobs
- RNF6 - Segurança avançada

### P3 - Futuros
- Autenticação e autorização na API
- Rate limiting na API
- Webhooks para eventos
- Dashboard web para visualização
- Export de dados em múltiplos formatos
- Integração com ferramentas de analytics

## Critérios de Aceitação

### Geração de Synths
- ✅ Synths gerados passam 100% validação JSON Schema
- ✅ Distribuições demográficas < 10% erro vs. IBGE
- ✅ IDs únicos sem colisões
- ✅ Avatares salvos corretamente em PNG

### API REST
- ✅ Todos os 17 endpoints retornam status codes corretos
- ✅ Paginação funciona em todos os endpoints de listagem
- ✅ Erros retornam JSON padronizado com código
- ✅ Documentação Swagger UI acessível em `/docs`

### Research Executions
- ✅ Entrevistas salvam transcrições completas
- ✅ Batch research executa em paralelo respeitando rate limits
- ✅ Streaming SSE transmite eventos em tempo real
- ✅ Jobs assíncronos completam sem travar

### Qualidade de Código
- ✅ 100% type hints em funções públicas
- ✅ Cobertura de testes > 80%
- ✅ Ruff linting sem erros
- ✅ Documentação completa (README + docs/)

## Restrições

### Técnicas
- SQLite não suporta múltiplos writers simultâneos (WAL mode mitiga)
- OpenAI API tem rate limits (retry com backoff mitiga)
- Avatares ocupam espaço em disco (compressão PNG mitiga)

### Negócio
- Custos de API OpenAI por geração de avatares (~$0.02/bloco)
- Dados sintéticos não substituem 100% pesquisas reais
- Distribuições baseadas em dados de 2019-2023 (atualizações futuras)

### Regulatórias
- LGPD: dados sintéticos não contêm informações pessoais reais
- Uso responsável de IA: disclaimers sobre natureza sintética dos dados
