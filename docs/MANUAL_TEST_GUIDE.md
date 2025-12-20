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

```bash
# Listar execuções
curl -s http://localhost:8000/research/list | python3 -m json.tool
```

**Nota**: Se não houver execuções de research, retorna lista vazia.

---

### 6.5 Endpoints de PR-FAQ

```bash
# Listar PR-FAQs
curl -s http://localhost:8000/prfaq/list | python3 -m json.tool
```

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

### Endpoints - Research/PR-FAQ
- [ ] Endpoints não crasham sem dados

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
