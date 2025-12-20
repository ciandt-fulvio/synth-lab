# Guia de Teste Manual - synth-lab

## 🎯 Objetivo

Testar o sistema completo do synth-lab do zero:
1. Gerar synths com avatares
2. Carregar dados no banco de dados
3. Subir a API REST
4. Testar todos os endpoints disponíveis

---

## 📋 Pré-requisitos

```bash
# 1. Verificar instalação
uv --version
python3 --version

# 2. Configurar OPENAI_API_KEY (necessário para avatares)
export OPENAI_API_KEY="sk-your-api-key-here"

# 3. Verificar se está no branch correto
git branch --show-current
# Deve mostrar: 011-remove-cli-commands
```

---

## 🧹 Passo 1: Limpar Ambiente (Começar do Zero)

```bash
# Backup dos dados existentes (opcional)
mkdir -p ~/backup-synth-lab-$(date +%Y%m%d)
cp -r data ~/backup-synth-lab-$(date +%Y%m%d)/ 2>/dev/null || true
cp -r output ~/backup-synth-lab-$(date +%Y%m%d)/ 2>/dev/null || true

# Remover banco de dados SQLite
rm -f output/synthlab.db

# Remover synths JSON (se existir)
rm -f data/synths/synths.json

# Remover avatares
rm -rf data/synths/avatar/*

# Verificar limpeza
echo "✓ Banco de dados removido"
echo "✓ Synths JSON removido"
echo "✓ Avatares removidos"
```

**Resultado esperado**: Ambiente completamente limpo, sem dados anteriores.

---

## 🎨 Passo 2: Gerar 10 Synths com Avatares

### 2.1 Gerar os Synths

```bash
# Gerar 10 synths com avatares (será criado 2 blocos: 9 + 1)
uv run synthlab gensynth -n 10 --avatar --benchmark

# Verificar se foram criados
ls -lh data/synths/*.json | wc -l
# Deve mostrar: 10 (ou 11 se incluir synths.json agregado)

# Verificar avatares criados
ls -lh data/synths/avatar/*.png | wc -l
# Deve mostrar: 10
```

**Resultado esperado**:
```
✓ Synth gerado: abc123 - Nome Exemplo
  Arquétipo: Jovem Adulto Sudeste
  Idade: 28 anos

✓ Avatar gerado: data/synths/avatar/abc123.png
  Modelo: dall-e-3
  Tamanho: 341x341 pixels

... (mais 9 synths)

Benchmark:
  Total: 10 synths
  Tempo: ~2-3 minutos
  Custo avatares: ~$0.22 (2 blocos × $0.11)
```

### 2.2 Verificar Synths Criados

```bash
# Listar synths criados
ls -1 data/synths/*.json | grep -v synths.json

# Ver detalhes de um synth (exemplo)
cat data/synths/*.json | head -50

# Verificar estrutura do JSON agregado
cat data/synths/synths.json | python3 -m json.tool | head -20
```

**Resultado esperado**: 10 arquivos JSON individuais + 1 arquivo agregado `synths.json` com array de todos os synths.

---

## 💾 Passo 3: Preparar Banco de Dados

### 3.1 Executar Migração para SQLite

```bash
# Criar diretório de output se não existir
mkdir -p output

# Executar script de migração
uv run python scripts/migrate_to_sqlite.py

# Verificar se o banco foi criado
ls -lh output/synthlab.db
```

**Resultado esperado**:
```
✓ Banco de dados criado: output/synthlab.db
✓ Tamanho: ~50-100 KB (depende dos dados)
```

### 3.2 Verificar Dados no Banco

```bash
# Instalar DuckDB CLI (se não tiver)
# brew install duckdb  # macOS
# ou baixar de https://duckdb.org

# Conectar e verificar synths
sqlite3 output/synthlab.db "SELECT COUNT(*) as total_synths FROM synths;"
# Deve mostrar: 10

# Ver primeiros 3 synths
sqlite3 output/synthlab.db "SELECT id, nome, demografia_idade FROM synths LIMIT 3;"
```

**Resultado esperado**:
```
total_synths
10

id      nome                demografia_idade
abc123  João Silva          28
def456  Maria Santos        35
ghi789  Pedro Costa         42
```

---

## 🌐 Passo 4: Preparar Topic Guides (Opcional)

Se quiser testar os endpoints de topic guides, crie um exemplo:

```bash
# Criar topic guide de exemplo
mkdir -p data/topic_guides/compra-amazon

# Criar arquivo script.json (roteiro de perguntas)
cat > data/topic_guides/compra-amazon/script.json << 'EOF'
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
cat > data/topic_guides/compra-amazon/summary.md << 'EOF'
# Topic Guide: Compra Amazon

## Contexto
Este topic guide é para entrevistas sobre experiência de compra no e-commerce Amazon.

## Objetivos
- Entender comportamento de compra
- Identificar pain points
- Avaliar satisfação geral
EOF

# Verificar criação
ls -la data/topic_guides/compra-amazon/
```

**Resultado esperado**:
```
total 16
drwxr-xr-x  4 user  staff  128 Dec 20 10:00 .
drwxr-xr-x  3 user  staff   96 Dec 20 10:00 ..
-rw-r--r--  1 user  staff  234 Dec 20 10:00 script.json
-rw-r--r--  1 user  staff  187 Dec 20 10:00 summary.md
```

---

## 🚀 Passo 5: Subir a API REST

### 5.1 Iniciar Servidor

```bash
# Opção 1: Com logs detalhados
uv run python -m synth_lab.api.main

# Opção 2: Em background (para liberar o terminal)
uv run python -m synth_lab.api.main > /tmp/api.log 2>&1 &
echo $! > /tmp/api.pid
echo "API rodando em background, PID: $(cat /tmp/api.pid)"
echo "Logs em: /tmp/api.log"
```

**Resultado esperado**:
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

### 5.2 Verificar API Está Rodando

```bash
# Testar health check (se existir)
curl -s http://localhost:8000/ | python3 -m json.tool

# Ou testar documentação
curl -s http://localhost:8000/docs | head -20
```

---

## 🧪 Passo 6: Testar Todos os Endpoints

### 6.1 Documentação Interativa (Swagger UI)

```bash
# Abrir no navegador
open http://localhost:8000/docs

# Ou verificar OpenAPI spec
curl -s http://localhost:8000/openapi.json | python3 -m json.tool | head -50
```

**O que testar no Swagger**:
- ✅ Interface carrega corretamente
- ✅ Todos os endpoints estão listados
- ✅ Pode expandir e ver detalhes de cada endpoint

---

### 6.2 Endpoints de Synths

#### GET /synths/list - Listar todos os synths

```bash
# Teste básico
curl -s http://localhost:8000/synths/list | python3 -m json.tool

# Salvar resposta para análise
curl -s http://localhost:8000/synths/list > /tmp/synths_list.json

# Verificar estrutura
cat /tmp/synths_list.json | python3 -c "
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
      "demografia": {
        "idade": 28,
        "localizacao": {
          "cidade": "São Paulo",
          "estado": "SP"
        }
      },
      ...
    }
  ],
  "total": 10,
  "page": 1,
  "page_size": 50
}
```

**✅ Verificações**:
- [ ] Retorna HTTP 200
- [ ] Retorna JSON válido
- [ ] Campo "items" contém array com 10 synths
- [ ] Campo "total" é 10
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
curl -s "http://localhost:8000/synths/$SYNTH_ID" | python3 -m json.tool > /tmp/synth_detail.json

# Ver detalhes
cat /tmp/synth_detail.json | head -50
```

**Resultado esperado**:
```json
{
  "id": "abc123",
  "nome": "João Silva",
  "arquetipo": "Jovem Adulto Sudeste",
  "descricao": "...",
  "demografia": {
    "idade": 28,
    "genero_biologico": "masculino",
    "localizacao": {
      "cidade": "São Paulo",
      "estado": "SP",
      "regiao": "Sudeste"
    },
    ...
  },
  "psicografia": {
    "personalidade_big_five": {
      "abertura": 75,
      "conscienciosidade": 82,
      ...
    }
  },
  ...
}
```

**✅ Verificações**:
- [ ] Retorna HTTP 200
- [ ] Retorna dados completos do synth
- [ ] Inclui demografia, psicografia, comportamento
- [ ] JSON bem estruturado

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
    echo "✓ Avatar existe: $AVATAR_PATH"
    ls -lh "$AVATAR_PATH"
else
    echo "✗ Avatar não encontrado em: $AVATAR_PATH"
fi
```

**Resultado esperado**:
```json
{
  "synth_id": "abc123",
  "avatar_path": "data/synths/avatar/abc123.png",
  "exists": true
}
```

**✅ Verificações**:
- [ ] Retorna HTTP 200
- [ ] Campo "exists" é true
- [ ] Campo "avatar_path" aponta para arquivo PNG
- [ ] Arquivo realmente existe no disco

---

#### Teste de Erro - Synth Inexistente

```bash
# Testar com ID que não existe
curl -s http://localhost:8000/synths/XXXXX | python3 -m json.tool
```

**Resultado esperado**:
```json
{
  "detail": {
    "code": "SYNTH_NOT_FOUND",
    "message": "Synth not found: XXXXX"
  }
}
```

**✅ Verificações**:
- [ ] Retorna HTTP 404
- [ ] Mensagem de erro clara

---

### 6.3 Endpoints de Topics

#### GET /topics/list - Listar topic guides

```bash
# Listar todos os topic guides
curl -s http://localhost:8000/topics/list | python3 -m json.tool

# Verificar estrutura
curl -s http://localhost:8000/topics/list | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(f'Total topics: {len(data.get(\"topics\", []))}')
if data.get('topics'):
    for topic in data['topics']:
        print(f'  - {topic[\"name\"]}: {topic.get(\"file_count\", 0)} arquivos')
"
```

**Resultado esperado**:
```json
{
  "topics": [
    {
      "name": "compra-amazon",
      "display_name": "Compra Amazon",
      "file_count": 2,
      "has_script": true,
      "has_summary": true
    }
  ],
  "total": 1
}
```

**✅ Verificações**:
- [ ] Retorna HTTP 200
- [ ] Lista o topic guide "compra-amazon" criado
- [ ] Mostra file_count = 2 (script.json + summary.md)
- [ ] has_script e has_summary são true

---

#### GET /topics/{topic_name} - Obter detalhes de topic guide

```bash
# Obter detalhes do topic guide
curl -s http://localhost:8000/topics/compra-amazon | python3 -m json.tool > /tmp/topic_detail.json

# Ver conteúdo
cat /tmp/topic_detail.json

# Verificar perguntas do script
cat /tmp/topic_detail.json | python3 -c "
import json, sys
data = json.load(sys.stdin)
print('Perguntas:')
for q in data.get('script', []):
    print(f'  {q[\"id\"]}: {q[\"ask\"]}')
"
```

**Resultado esperado**:
```json
{
  "name": "compra-amazon",
  "display_name": "Compra Amazon",
  "script": [
    {
      "id": "q1",
      "ask": "Como você se sente ao fazer compras online?"
    },
    ...
  ],
  "summary": "# Topic Guide: Compra Amazon\n...",
  "files": [
    {
      "filename": "script.json",
      "size": 234
    },
    {
      "filename": "summary.md",
      "size": 187
    }
  ]
}
```

**✅ Verificações**:
- [ ] Retorna HTTP 200
- [ ] Mostra script com 3 perguntas
- [ ] Mostra summary markdown
- [ ] Lista arquivos do diretório

---

#### Teste de Erro - Topic Inexistente

```bash
curl -s http://localhost:8000/topics/nao-existe | python3 -m json.tool
```

**Resultado esperado**:
```json
{
  "detail": {
    "code": "TOPIC_NOT_FOUND",
    "message": "Topic guide not found: nao-existe"
  }
}
```

---

### 6.4 Endpoints de Research

**Nota**: Se não houver execuções de research, os endpoints retornarão listas vazias.

#### GET /research/list - Listar execuções de pesquisa

```bash
# Listar execuções
curl -s http://localhost:8000/research/list | python3 -m json.tool

# Se houver dados
curl -s http://localhost:8000/research/list | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(f'Total execuções: {data.get(\"total\", 0)}')
if data.get('items'):
    print('Execuções:')
    for item in data['items'][:3]:
        print(f'  - {item[\"execution_id\"]}: {item.get(\"topic_name\", \"N/A\")}')
"
```

**Resultado esperado (se houver dados)**:
```json
{
  "items": [
    {
      "execution_id": "batch_compra-amazon_20251219_110534",
      "topic_name": "compra-amazon",
      "synth_count": 5,
      "created_at": "2025-12-19T11:05:34"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 50
}
```

**Resultado esperado (sem dados)**:
```json
{
  "items": [],
  "total": 0,
  "page": 1,
  "page_size": 50
}
```

**✅ Verificações**:
- [ ] Retorna HTTP 200
- [ ] Retorna lista (vazia ou com dados)

---

#### GET /research/{execution_id} - Obter execução específica

```bash
# Se houver execução, pegar ID
EXEC_ID=$(curl -s http://localhost:8000/research/list | python3 -c "
import json, sys
data = json.load(sys.stdin)
if data.get('items'):
    print(data['items'][0]['execution_id'])
else:
    print('')
" 2>/dev/null)

if [ -n "$EXEC_ID" ]; then
    echo "Testando com execution ID: $EXEC_ID"
    curl -s "http://localhost:8000/research/$EXEC_ID" | python3 -m json.tool
else
    echo "⚠ Sem execuções de research para testar"
fi
```

---

#### GET /research/{execution_id}/summary - Obter resumo

```bash
if [ -n "$EXEC_ID" ]; then
    curl -s "http://localhost:8000/research/$EXEC_ID/summary" | python3 -m json.tool
fi
```

**Resultado esperado (se não houver summary)**:
```json
{
  "detail": {
    "code": "SUMMARY_NOT_FOUND",
    "message": "Summary file not found for execution: ..."
  }
}
```

---

### 6.5 Endpoints de PR-FAQ

#### GET /prfaq/list - Listar PR-FAQs

```bash
# Listar PR-FAQs
curl -s http://localhost:8000/prfaq/list | python3 -m json.tool

# Analisar resultado
curl -s http://localhost:8000/prfaq/list | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(f'Total PR-FAQs: {data.get(\"total\", 0)}')
"
```

---

#### GET /prfaq/{execution_id} - Obter PR-FAQ

```bash
# Se houver PR-FAQ, testar
PRFAQ_ID=$(curl -s http://localhost:8000/prfaq/list | python3 -c "
import json, sys
data = json.load(sys.stdin)
if data.get('items'):
    print(data['items'][0]['execution_id'])
else:
    print('')
" 2>/dev/null)

if [ -n "$PRFAQ_ID" ]; then
    curl -s "http://localhost:8000/prfaq/$PRFAQ_ID" | python3 -m json.tool
fi
```

---

#### GET /prfaq/{execution_id}/markdown - Obter markdown

```bash
if [ -n "$PRFAQ_ID" ]; then
    curl -s "http://localhost:8000/prfaq/$PRFAQ_ID/markdown" | python3 -m json.tool
fi
```

---

## 📊 Passo 7: Checklist Final de Verificação

### ✅ Checklist de Synths

- [ ] 10 synths criados com sucesso
- [ ] 10 avatares PNG gerados
- [ ] Arquivo `synths.json` agregado existe
- [ ] Synths carregados no banco SQLite

### ✅ Checklist de API

- [ ] API inicia sem erros
- [ ] Documentação Swagger acessível em /docs
- [ ] OpenAPI spec disponível em /openapi.json

### ✅ Checklist de Endpoints - Synths

- [ ] GET /synths/list retorna 10 synths
- [ ] GET /synths/{id} retorna dados completos
- [ ] GET /synths/{id}/avatar retorna caminho do avatar
- [ ] GET /synths/XXXXX retorna 404 corretamente

### ✅ Checklist de Endpoints - Topics

- [ ] GET /topics/list retorna topic guide criado
- [ ] GET /topics/compra-amazon retorna detalhes
- [ ] GET /topics/nao-existe retorna 404

### ✅ Checklist de Endpoints - Research

- [ ] GET /research/list retorna resposta (vazia ok)
- [ ] Endpoints não crasham sem dados

### ✅ Checklist de Endpoints - PR-FAQ

- [ ] GET /prfaq/list retorna resposta (vazia ok)
- [ ] Endpoints não crasham sem dados

---

## 🧹 Passo 8: Limpeza (Opcional)

```bash
# Parar API se rodando em background
if [ -f /tmp/api.pid ]; then
    kill $(cat /tmp/api.pid)
    rm /tmp/api.pid
    echo "✓ API parada"
fi

# Ver logs (se houver)
tail -50 /tmp/api.log

# Arquivos temporários criados
ls -lh /tmp/synths_list.json
ls -lh /tmp/synth_detail.json
ls -lh /tmp/topic_detail.json
```

---

## 📝 Relatório de Teste

Após completar todos os passos, documente:

```markdown
# Relatório de Teste Manual - synth-lab

**Data**: $(date +%Y-%m-%d)
**Branch**: 011-remove-cli-commands
**Testador**: [Seu Nome]

## Resultados

### Passo 1: Limpeza
- [x] Ambiente limpo com sucesso

### Passo 2: Geração de Synths
- [x] 10 synths gerados
- [x] 10 avatares criados
- [ ] Tempo total: ___ minutos
- [ ] Custo estimado: $___

### Passo 3: Banco de Dados
- [x] Migração executada com sucesso
- [x] 10 registros no banco

### Passo 4: Topic Guides
- [x] Topic guide de exemplo criado

### Passo 5: API
- [x] API iniciou sem erros
- [ ] Porta: 8000

### Passo 6: Endpoints Testados
- [x] Synths: 4/4 endpoints funcionando
- [x] Topics: 2/2 endpoints funcionando
- [x] Research: 3/3 endpoints funcionando
- [x] PR-FAQ: 3/3 endpoints funcionando

## Problemas Encontrados
- [ ] Nenhum problema
- [ ] Problema 1: ...
- [ ] Problema 2: ...

## Observações
- ...

## Conclusão
- [ ] ✅ Todos os testes passaram
- [ ] ⚠️ Alguns testes falharam (ver seção Problemas)
- [ ] ❌ Falhas críticas encontradas
```

---

## 🆘 Troubleshooting

### API não inicia

```bash
# Verificar se porta 8000 está em uso
lsof -i :8000

# Matar processo na porta 8000
kill -9 $(lsof -t -i:8000)

# Tentar novamente
uv run python -m synth_lab.api.main
```

### Banco de dados não criado

```bash
# Verificar se script existe
ls -la scripts/migrate_to_sqlite.py

# Executar com debug
uv run python -c "
from synth_lab.repositories.synth_repository import SynthRepository
repo = SynthRepository()
print('✓ Repositório criado')
"
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

## 📚 Referências

- [README.md](../README.md)
- [API Documentation](api.md)
- [CLI Documentation](cli.md)
- [CHANGELOG.md](../CHANGELOG.md)
