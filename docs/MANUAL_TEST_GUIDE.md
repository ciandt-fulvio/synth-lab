# Guia de Teste Manual - synthlab

## Objetivo

Testar o sistema completo do synth-lab do zero:
1. Gerar synths com avatares (salvos diretamente no SQLite)
2. Subir a API REST
3. Testar todos os endpoints disponíveis

---

## Pré-requisitos

```bash
# 1. Verificar instalação
uv --version
python3 --version

# 2. Instalar dependências
make install

# 3. Configurar OPENAI_API_KEY (necessário para avatares)
export OPENAI_API_KEY="sk-your-api-key-here"

# 4. Ver comandos disponíveis
make help
```

---

## Passo 1: Limpar Ambiente (Começar do Zero)

```bash
# Remover o output antigo (caso exista)
rm -f output/synthlab.db
rm -rf output/synths/
```

**Resultado esperado**: Ambiente completamente limpo, sem dados anteriores.

---

## Passo 2: Inicializar o Banco de Dados

```bash
# Criar banco SQLite com schema
make init-db

# Verificar se existe
ls -la output/synthlab.db
```

**Resultado esperado**: Arquivo `output/synthlab.db` criado com tabelas vazias.

---

## Passo 3: Gerar 9 Synths com Avatares

### 3.1 Gerar os Synths

Os synths são salvos **diretamente no banco de dados SQLite** durante a geração.

```bash
# Gerar 9 synths com avatares
uv run synthlab gensynth -n 9 --avatar

# Verificar synths no banco
sqlite3 output/synthlab.db "SELECT COUNT(*) as total FROM synths;"
# Deve mostrar: 9

# Ver primeiros 3 synths
sqlite3 output/synthlab.db "SELECT id, nome, arquetipo FROM synths LIMIT 3;"

# Verificar avatares criados
ls -lh output/synths/avatar/*.png | wc -l
# Deve mostrar: 9
```

**Resultado esperado**:
```
=== Gerando 9 Synth(s) ===
  [1/9] João Silva (abc123)
  [2/9] Maria Santos (def456)
  ...

9 synth(s) gerado(s) com sucesso!

Benchmark:
  Total: 9 synths
  Tempo: ~2-3 minutos
  Custo avatares: ~$0.22 (2 blocos x $0.11)
```

### 3.2 Verificar Synths no Banco

```bash
# Listar todos os synths
sqlite3 output/synthlab.db "SELECT id, nome, arquetipo FROM synths;"

# Ver detalhes de um synth (com campos JSON)
sqlite3 output/synthlab.db "SELECT id, nome, json_extract(demografia, '$.idade') as idade FROM synths LIMIT 3;"
```

**Resultado esperado**:
```
abc123|João Silva|Jovem Adulto Sudeste
def456|Maria Santos|Adulto Nordeste
ghi789|Pedro Costa|Idoso Sul
```

---

## Passo 4: Preparar Topic Guides (Opcional)

Topic guides são armazenados em `output/topic_guides/`. Se quiser testar os endpoints de topic guides, crie um exemplo:

```bash
# Criar topic guide de exemplo
mkdir -p output/topic_guides/compra-amazon

# Criar arquivo script.json (roteiro de perguntas)
cat > output/topic_guides/compra-amazon/script.json << 'EOF'
[
  {
    "id": "q1",
    "ask": "Como você se sente ao fazer compras online?"
  },
  {
    "id": "q2",
    "ask": "O que você mais valoriza em um e-commerce?"
  },
  {
    "id": "q3",
    "ask": "Já teve alguma experiência negativa com compras online?"
  }
]
EOF

# Criar arquivo summary.md (contexto)
cat > output/topic_guides/compra-amazon/summary.md << 'EOF'
# Topic Guide: Compra Amazon

## Contexto
Este topic guide é para entrevistas sobre experiência de compra no e-commerce Amazon.

## Objetivos
- Entender comportamento de compra
- Identificar pain points
- Avaliar satisfação geral
EOF

# Verificar criação
ls -la output/topic_guides/compra-amazon/
```

---

## Passo 5: Subir a API REST

### 5.1 Iniciar Servidor

```bash
# Usando Makefile (recomendado)
make serve

# Ou diretamente
uv run uvicorn synth_lab.api.main:app --host 127.0.0.1 --port 8000 --reload
```

**Resultado esperado**:
```
Starting synth-lab API on http://127.0.0.1:8000
OpenAPI docs: http://127.0.0.1:8000/docs

INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
```

### 5.2 Verificar API Está Rodando

```bash
# Testar endpoint de synths
curl -s http://localhost:8000/synths/list | python3 -m json.tool | head -20

# Verificar documentação Swagger
open http://localhost:8000/docs
```

---

## Passo 6: Testar Todos os Endpoints

### 6.1 Documentação Interativa (Swagger UI)

```bash
# Abrir no navegador
open http://localhost:8000/docs

# Ou verificar OpenAPI spec
curl -s http://localhost:8000/openapi.json | python3 -m json.tool | head -50
```

**O que testar no Swagger**:
- Interface carrega corretamente
- Todos os endpoints estão listados
- Pode expandir e ver detalhes de cada endpoint

---

### 6.2 Endpoints de Synths

#### GET /synths/list - Listar todos os synths

```bash
# Teste básico
curl -s http://localhost:8000/synths/list | python3 -m json.tool

# Verificar estrutura
curl -s http://localhost:8000/synths/list | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(f'Total synths: {len(data.get(\"items\", []))}')
print(f'Keys: {list(data.keys())}')
if data.get('items'):
    print(f'Primeiro synth: {data[\"items\"][0].get(\"id\")} - {data[\"items\"][0].get(\"nome\")}')
"
```

**Resultado esperado**:
```json
{
  "items": [
    {
      "id": "abc123",
      "nome": "João Silva",
      "arquetipo": "Jovem Adulto Sudeste",
      ...
    }
  ],
  "total": 9,
  "page": 1,
  "page_size": 50
}
```

**Verificações**:
- [ ] Retorna HTTP 200
- [ ] Retorna JSON válido
- [ ] Campo "items" contém array com 9 synths
- [ ] Campo "total" é 9
- [ ] Cada synth tem id, nome, arquetipo

---

#### GET /synths/{synth_id} - Obter synth específico

```bash
# Pegar ID do primeiro synth
SYNTH_ID=$(curl -s http://localhost:8000/synths/list | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(data['items'][0]['id'])
")

echo "Testando com synth ID: $SYNTH_ID"

# Buscar detalhes do synth
curl -s "http://localhost:8000/synths/$SYNTH_ID" | python3 -m json.tool | head -50
```

**Verificações**:
- [ ] Retorna HTTP 200
- [ ] Retorna dados completos do synth
- [ ] Inclui demografia, psicografia, capacidades_tecnologicas

---

#### GET /synths/{synth_id}/avatar - Obter caminho do avatar

```bash
# Testar avatar do mesmo synth
curl -s "http://localhost:8000/synths/$SYNTH_ID/avatar" | python3 -m json.tool

# Verificar se arquivo existe
AVATAR_PATH=$(curl -s "http://localhost:8000/synths/$SYNTH_ID/avatar" | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(data.get('avatar_path', ''))
")

if [ -f "$AVATAR_PATH" ]; then
    echo "Avatar existe: $AVATAR_PATH"
    ls -lh "$AVATAR_PATH"
else
    echo "Avatar não encontrado em: $AVATAR_PATH"
fi
```

**Verificações**:
- [ ] Retorna HTTP 200
- [ ] Campo "exists" é true
- [ ] Arquivo realmente existe no disco

---

#### Teste de Erro - Synth Inexistente

```bash
# Testar com ID que não existe
curl -s http://localhost:8000/synths/XXXXX | python3 -m json.tool
```

**Resultado esperado**: HTTP 404 com mensagem de erro clara.

---

### 6.3 Endpoints de Topics

#### GET /topics/list - Listar topic guides

```bash
# Listar todos os topic guides
curl -s http://localhost:8000/topics/list | python3 -m json.tool
```

---

#### GET /topics/{topic_name} - Obter detalhes de topic guide

```bash
# Obter detalhes do topic guide
curl -s http://localhost:8000/topics/compra-amazon | python3 -m json.tool
```

---

### 6.4 Endpoints de Research

#### POST /research/execute - Executar research

Primeiro precisamos executar uma pesquisa com synths usando um topic guide:

```bash
# Executar research com 3 synths usando o topic guide compra-amazon
curl -X POST "http://localhost:8000/research/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "topic_name": "compra-amazon",
    "synth_count": 3
  }' | python3 -m json.tool

# Salvar o exec_id retornado
EXEC_ID=$(curl -s -X POST "http://localhost:8000/research/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "topic_name": "compra-amazon",
    "synth_count": 3
  }' | python3 -c "import json, sys; print(json.load(sys.stdin)['exec_id'])")

echo "Execution ID: $EXEC_ID"
```

**Resultado esperado**:
```json
{
  "exec_id": "batch_compra-amazon_20231215_143022",
  "status": "running",
  "topic_name": "compra-amazon",
  "synth_count": 3,
  "started_at": "2023-12-15T14:30:22"
}
```

**Verificações**:
- [ ] Retorna HTTP 200
- [ ] Campo "status" é "running" (execução assíncrona)
- [ ] Campo "exec_id" começa com "batch_"
- [ ] Campo "synth_count" é 3

---

#### GET /research - Listar execuções

```bash
# Listar todas as execuções de research
curl -s http://localhost:8000/research | python3 -m json.tool
```

**Resultado esperado**:
```json
{
  "data": [
    {
      "exec_id": "batch_compra-amazon_20231215_143022",
      "topic_name": "compra-amazon",
      "synth_count": 3,
      "status": "completed",
      "started_at": "2023-12-15T14:30:22"
    }
  ],
  "pagination": {
    "total": 1,
    "limit": 20,
    "offset": 0
  }
}
```

**Verificações**:
- [ ] Retorna HTTP 200
- [ ] Lista contém a execução recém-criada
- [ ] Campo "pagination.total" é pelo menos 1

---

#### GET /research/{exec_id} - Obter detalhes de execução

```bash
# Obter detalhes da execução
curl -s "http://localhost:8000/research/$EXEC_ID" | python3 -m json.tool

# Ver transcripts gerados
curl -s "http://localhost:8000/research/$EXEC_ID" | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(f'Exec ID: {data[\"exec_id\"]}')
print(f'Topic: {data[\"topic_name\"]}')
print(f'Synths: {data[\"synth_count\"]}')
print(f'Status: {data[\"status\"]}')
"
```

**Verificações**:
- [ ] Retorna HTTP 200
- [ ] Contém detalhes completos da execução
- [ ] Lista de transcripts gerados

---

### 6.5 SSE - Streaming de Entrevistas em Tempo Real

O endpoint SSE permite visualizar as mensagens das entrevistas em tempo real enquanto a execução está acontecendo.

#### GET /research/{exec_id}/stream - Stream de mensagens via SSE

**Conceito**: Server-Sent Events (SSE) é uma tecnologia que permite ao servidor enviar dados ao cliente em tempo real através de uma conexão HTTP persistente.

##### Teste com curl (Terminal)

```bash
# 1. Primeiro, inicie uma execução de research (em outro terminal)
EXEC_ID=$(curl -s -X POST "http://localhost:8000/research/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "topic_name": "compra-amazon",
    "synth_count": 3,
    "max_turns": 4,
    "max_concurrent": 2,
    "generate_summary": false
  }' | python3 -c "import json, sys; print(json.load(sys.stdin)['exec_id'])")

echo "Execution ID: $EXEC_ID"

# 2. Conectar ao stream SSE (use -N para desabilitar buffering)
curl -N "http://localhost:8000/research/$EXEC_ID/stream"
```

**Resultado esperado** (eventos em tempo real):
```
event: message
data: {"event_type":"message","exec_id":"batch_compra-amazon_20251220_150000","synth_id":"abc123","turn_number":1,"speaker":"Interviewer","text":"Olá! Gostaria de conversar sobre sua experiência...","timestamp":"2025-12-20T15:00:05","is_replay":false}

event: message
data: {"event_type":"message","exec_id":"batch_compra-amazon_20251220_150000","synth_id":"abc123","turn_number":2,"speaker":"Interviewee","text":"Claro! Eu costumo fazer compras online...","timestamp":"2025-12-20T15:00:10","is_replay":false}

...

event: execution_completed
data: {}
```

##### Teste com JavaScript (Browser Console)

Abra o console do navegador (F12) e execute:

```javascript
// Substitua pelo exec_id real
const execId = 'batch_compra-amazon_20251220_150000';

const events = new EventSource(`http://localhost:8000/research/${execId}/stream`);

// Contador de mensagens
let messageCount = 0;

events.addEventListener('message', (e) => {
    const data = JSON.parse(e.data);
    messageCount++;
    const prefix = data.is_replay ? '🔄 [replay]' : '🔴 [live]';
    const speaker = data.speaker === 'Interviewer' ? '🎤' : '👤';
    console.log(`${prefix} ${speaker} ${data.speaker} (${data.synth_id?.slice(0,6)}): ${data.text?.slice(0,80)}...`);
});

events.addEventListener('execution_completed', () => {
    console.log(`✅ Execução concluída! Total de mensagens: ${messageCount}`);
    events.close();
});

events.onerror = (e) => {
    console.error('Erro no SSE:', e);
};

// Para encerrar manualmente: events.close();
```

##### Teste com Script Python

```bash
# Salvar como test_sse.py e executar com: uv run python test_sse.py <exec_id>
cat > /tmp/test_sse.py << 'EOF'
import sys
import httpx

exec_id = sys.argv[1] if len(sys.argv) > 1 else "batch_compra-amazon_20251220_150000"
url = f"http://localhost:8000/research/{exec_id}/stream"

print(f"Conectando ao stream: {url}")
print("-" * 60)

with httpx.Client(timeout=None) as client:
    with client.stream("GET", url) as response:
        buffer = ""
        for chunk in response.iter_text():
            buffer += chunk
            while "\n\n" in buffer:
                event_str, buffer = buffer.split("\n\n", 1)

                event_type = "message"
                event_data = "{}"

                for line in event_str.split("\n"):
                    if line.startswith("event:"):
                        event_type = line[6:].strip()
                    elif line.startswith("data:"):
                        event_data = line[5:].strip()

                if event_type == "execution_completed":
                    print("\n✅ Execução concluída!")
                    sys.exit(0)

                if event_type == "message":
                    import json
                    data = json.loads(event_data)
                    prefix = "[replay]" if data.get("is_replay") else "[live]"
                    speaker = data.get("speaker", "?")
                    text = (data.get("text") or "")[:60]
                    synth = (data.get("synth_id") or "?")[:6]
                    print(f"{prefix} [{speaker}] ({synth}): {text}...")
EOF

# Executar:
uv run python /tmp/test_sse.py $EXEC_ID
```

##### Comportamento do SSE

| Cenário | Comportamento |
|---------|---------------|
| Cliente conecta durante execução | Recebe replay das mensagens já salvas + mensagens live |
| Cliente conecta após execução | Recebe replay completo + evento `execution_completed` |
| Cliente conecta antes da execução | Aguarda até haver mensagens, então recebe live |
| Execução falha | Recebe evento `execution_completed` (mesmo em falha) |

##### Campos do Evento `message`

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `event_type` | string | Sempre "message" para mensagens de entrevista |
| `exec_id` | string | ID da execução |
| `synth_id` | string | ID do synth sendo entrevistado |
| `turn_number` | int | Número do turno na conversa (1, 2, 3...) |
| `speaker` | string | "Interviewer" ou "Interviewee" |
| `text` | string | Conteúdo da mensagem |
| `timestamp` | datetime | Momento da mensagem |
| `is_replay` | boolean | `true` se veio do histórico, `false` se é tempo real |

**Verificações**:
- [ ] Conexão SSE estabelecida (curl não fecha imediatamente)
- [ ] Mensagens chegam em tempo real durante execução
- [ ] Campo `is_replay` diferencia histórico de live
- [ ] Evento `execution_completed` chega ao final
- [ ] Múltiplos clientes podem conectar simultaneamente

---

### 6.6 Endpoints de PR-FAQ

#### POST /prfaq/generate - Gerar PR-FAQ

Primeiro precisamos gerar um PR-FAQ a partir de um research:

```bash
# Usar o EXEC_ID da execução de research anterior
# Gerar PR-FAQ
curl -X POST "http://localhost:8000/prfaq/generate" \
  -H "Content-Type: application/json" \
  -d "{
    \"exec_id\": \"$EXEC_ID\"
  }" | python3 -m json.tool

# Salvar o prfaq_id retornado
PRFAQ_ID=$(curl -s -X POST "http://localhost:8000/prfaq/generate" \
  -H "Content-Type: application/json" \
  -d "{
    \"exec_id\": \"$EXEC_ID\"
  }" | python3 -c "import json, sys; print(json.load(sys.stdin)['prfaq_id'])")

echo "PR-FAQ ID: $PRFAQ_ID"
```

**Resultado esperado**:
```json
{
  "prfaq_id": "prfaq_20231215_144530",
  "status": "running",
  "exec_id": "batch_compra-amazon_20231215_143022"
}
```

**Verificações**:
- [ ] Retorna HTTP 200
- [ ] Campo "status" é "completed"
- [ ] Arquivo PR-FAQ gerado em `output/prfaq/`
- [ ] Arquivo markdown contém seções: Press Release, FAQs

---

#### GET /prfaq/list - Listar PR-FAQs

```bash
# Listar todos os PR-FAQs gerados
curl -s http://localhost:8000/prfaq/list | python3 -m json.tool
```

**Resultado esperado**:
```json
{
  "items": [
    {
      "prfaq_id": "prfaq_20231215_144530",
      "product_name": "Amazon Shopping App",
      "created_at": "2023-12-15T14:45:30"
    }
  ],
  "total": 1
}
```

**Verificações**:
- [ ] Retorna HTTP 200
- [ ] Lista contém o PR-FAQ recém-gerado
- [ ] Campo "total" é pelo menos 1

---

#### GET /prfaq/{prfaq_id} - Obter PR-FAQ específico

```bash
# Obter detalhes do PR-FAQ
curl -s "http://localhost:8000/prfaq/$PRFAQ_ID" | python3 -m json.tool

# Ver conteúdo do arquivo gerado
PRFAQ_PATH=$(curl -s "http://localhost:8000/prfaq/$PRFAQ_ID" | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(data['file_path'])
")

if [ -f "$PRFAQ_PATH" ]; then
    echo "PR-FAQ gerado em: $PRFAQ_PATH"
    head -30 "$PRFAQ_PATH"
else
    echo "Arquivo não encontrado: $PRFAQ_PATH"
fi
```

**Verificações**:
- [ ] Retorna HTTP 200
- [ ] Contém detalhes completos do PR-FAQ
- [ ] Arquivo existe e contém conteúdo válido

---

## Checklist Final de Verificação

### Synths
- [ ] 9 synths criados no banco SQLite
- [ ] 9 avatares PNG gerados em output/synths/avatar/

### API
- [ ] API inicia sem erros (`make serve`)
- [ ] Documentação Swagger acessível em /docs
- [ ] OpenAPI spec disponível em /openapi.json

### Endpoints - Synths
- [ ] GET /synths/list retorna 9 synths
- [ ] GET /synths/{id} retorna dados completos
- [ ] GET /synths/{id}/avatar retorna caminho do avatar
- [ ] GET /synths/XXXXX retorna 404 corretamente

### Endpoints - Topics
- [ ] GET /topics/list retorna topic guides
- [ ] GET /topics/{name} retorna detalhes

### Endpoints - Research
- [ ] POST /research/execute cria execução com 3 synths
- [ ] GET /research retorna execuções criadas
- [ ] GET /research/{exec_id} retorna detalhes completos
- [ ] GET /research/{exec_id}/stream retorna eventos SSE

### Endpoints - PR-FAQ
- [ ] POST /prfaq/generate cria PR-FAQ a partir de research
- [ ] GET /prfaq/list retorna PR-FAQs gerados
- [ ] GET /prfaq/{prfaq_id} retorna detalhes do PR-FAQ
- [ ] Arquivo markdown gerado em output/prfaq/

---

## Troubleshooting

### API não inicia

```bash
# Verificar se porta 8000 está em uso
lsof -i :8000

# Matar processo na porta 8000
kill -9 $(lsof -t -i:8000)

# Tentar novamente
make serve
```

### Banco de dados não criado

```bash
# Inicializar banco manualmente
make init-db

# Verificar se existe
ls -la output/synthlab.db
```

### Avatares não gerando

```bash
# Verificar OPENAI_API_KEY
echo $OPENAI_API_KEY

# Testar API key
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY" | head -20
```

---

## Comandos Úteis (Makefile)

| Comando | Descrição |
|---------|-----------|
| `make install` | Instalar dependências com uv |
| `make init-db` | Inicializar banco de dados SQLite |
| `make serve` | Iniciar API REST (porta 8000) |
| `make test` | Rodar suite de testes pytest |
| `make lint-format` | Rodar linter e formatter (ruff) |
| `make validate-ui` | Validar arquivos UI do trace visualizer |
| `make clean` | Remover arquivos de cache |

---

## CLI - Comando gensynth

O CLI do synth-lab possui apenas o comando `gensynth`:

```bash
# Ver ajuda do comando
uv run synthlab gensynth --help

# Exemplos de uso:
uv run synthlab gensynth -n 5            # Gerar 5 synths
uv run synthlab gensynth -n 9 --avatar   # Gerar 9 synths com avatares
uv run synthlab gensynth --validate-all  # Validar todos os synths existentes
uv run synthlab gensynth --analyze all   # Analisar distribuição demográfica
```

---

## Referências

- [README.md](../README.md)
- [API Documentation](api.md)
- [CLI Documentation](cli.md)
- [CHANGELOG.md](../CHANGELOG.md)
