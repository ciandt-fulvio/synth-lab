# Quickstart: Migration from CLI to REST API

**Feature**: Remove CLI Commands & Fix Architecture
**Date**: 2025-12-20
**Audience**: Users of removed CLI commands, developers integrating with synth-lab

## Overview

This guide helps you migrate from the removed CLI commands to the REST API. All functionality previously available via CLI is now accessible through modern REST endpoints.

**Removed Commands**:
- `uv run synthlab listsynth` → Use GET `/synths/list`
- `uv run synthlab research` → Use POST `/research/execute`
- `uv run synthlab research-batch` → Use POST `/research/execute`
- `uv run synthlab topic-guide` → Use `/topics/*` endpoints
- `uv run synthlab research-prfaq` → Use `/prfaq/*` endpoints

**Kept Commands**:
- `uv run synthlab gensynth` → Still available (generates synths and avatars)

---

## Quick Migration Guide

### 1. List Synths

**Before (CLI)**:
```bash
uv run synthlab listsynth --format table
```

**After (REST API)**:
```bash
# Using curl
curl http://localhost:8000/synths/list

# Using HTTPie
http GET :8000/synths/list

# Using Python
import requests
response = requests.get("http://localhost:8000/synths/list")
synths = response.json()
```

**Response**:
```json
{
  "data": [
    {
      "synth_id": "synth_001",
      "name": "Maria Silva",
      "age": 34,
      "occupation": "Product Manager",
      "created_at": "2025-12-01T10:00:00Z"
    }
  ],
  "pagination": {
    "offset": 0,
    "limit": 50,
    "total": 127
  }
}
```

---

### 2. Execute Research Interview

**Before (CLI)**:
```bash
uv run synthlab research \
    --synth-id synth_001 \
    --topic "compra-amazon" \
    --model gpt-4o
```

**After (REST API with SSE)**:
```bash
# Using curl (Server-Sent Events)
curl -N http://localhost:8000/research/execute \
  -H "Content-Type: application/json" \
  -d '{
    "synth_id": "synth_001",
    "topic": "compra-amazon",
    "model": "gpt-4o"
  }'
```

**Python Example**:
```python
import requests
import json

url = "http://localhost:8000/research/execute"
payload = {
    "synth_id": "synth_001",
    "topic": "compra-amazon",
    "model": "gpt-4o"
}

# SSE streaming
response = requests.post(url, json=payload, stream=True)
for line in response.iter_lines():
    if line:
        event_data = line.decode('utf-8')
        if event_data.startswith('data: '):
            data = json.loads(event_data[6:])
            print(f"Event: {data.get('event')}")
            print(f"Message: {data.get('message')}")
```

**Response (SSE Stream)**:
```
data: {"event": "started", "exec_id": "exec_001", "message": "Interview started"}

data: {"event": "progress", "message": "Asking question 1/10"}

data: {"event": "progress", "message": "Processing response..."}

data: {"event": "completed", "exec_id": "exec_001", "message": "Interview completed"}
```

---

### 3. Generate Topic Guide

**Before (CLI)**:
```bash
uv run synthlab topic-guide create \
    --topic compra-amazon \
    --files data/transcripts/*.txt
```

**After (REST API)**:
```bash
# Step 1: Create topic
curl -X POST http://localhost:8000/topics \
  -H "Content-Type: application/json" \
  -d '{
    "topic_name": "compra-amazon",
    "description": "Amazon shopping experience research"
  }'

# Step 2: Upload files (if file upload endpoint exists)
# Or process files server-side using existing transcript directory
```

**Python Example**:
```python
import requests

# Create topic
url = "http://localhost:8000/topics"
payload = {
    "topic_name": "compra-amazon",
    "description": "Amazon shopping experience research"
}
response = requests.post(url, json=payload)
topic = response.json()
print(f"Created topic: {topic['topic_id']}")
```

---

### 4. Generate PR-FAQ

**Before (CLI)**:
```bash
uv run synthlab research-prfaq generate \
    --batch-id batch_compra-amazon_20251218_164204
```

**After (REST API)**:
```bash
curl -X POST http://localhost:8000/prfaq/generate \
  -H "Content-Type: application/json" \
  -d '{
    "exec_id": "batch_compra-amazon_20251218_164204",
    "model": "gpt-4o"
  }'
```

**Python Example**:
```python
import requests

url = "http://localhost:8000/prfaq/generate"
payload = {
    "exec_id": "batch_compra-amazon_20251218_164204",
    "model": "gpt-4o"
}
response = requests.post(url, json=payload)
prfaq = response.json()
print(f"Generated PR-FAQ: {prfaq['exec_id']}")

# Get markdown content
markdown_url = f"http://localhost:8000/prfaq/{prfaq['exec_id']}/markdown"
markdown_response = requests.get(markdown_url)
print(markdown_response.text)
```

---

## Complete API Reference

### Synths

| Endpoint | Method | Description | CLI Equivalent |
|----------|--------|-------------|----------------|
| `/synths/list` | GET | List all synths | `listsynth` |
| `/synths/{synth_id}` | GET | Get synth details | `listsynth --id` |
| `/synths/{synth_id}/avatar` | GET | Get synth avatar | N/A |

### Research

| Endpoint | Method | Description | CLI Equivalent |
|----------|--------|-------------|----------------|
| `/research/execute` | POST | Execute research interview (SSE) | `research` |
| `/research/executions` | GET | List executions | N/A |
| `/research/executions/{exec_id}` | GET | Get execution details | N/A |
| `/research/executions/{exec_id}/summary` | GET | Get summary | N/A |

### Topics

| Endpoint | Method | Description | CLI Equivalent |
|----------|--------|-------------|----------------|
| `/topics` | POST | Create topic | `topic-guide create` |
| `/topics` | GET | List topics | `topic-guide list` |
| `/topics/{topic_id}` | GET | Get topic details | N/A |

### PR-FAQ

| Endpoint | Method | Description | CLI Equivalent |
|----------|--------|-------------|----------------|
| `/prfaq/generate` | POST | Generate PR-FAQ | `research-prfaq generate` |
| `/prfaq` | GET | List PR-FAQs | `research-prfaq list` |
| `/prfaq/{exec_id}` | GET | Get PR-FAQ metadata | N/A |
| `/prfaq/{exec_id}/markdown` | GET | Get PR-FAQ markdown | N/A |

---

## Starting the API Server

### Development Mode

```bash
# Start API server
uvicorn synth_lab.api.main:app --reload

# API will be available at:
# - Swagger UI: http://localhost:8000/docs
# - ReDoc: http://localhost:8000/redoc
# - OpenAPI spec: http://localhost:8000/openapi.json
```

### Production Mode

```bash
# Using uvicorn directly
uvicorn synth_lab.api.main:app --host 0.0.0.0 --port 8000 --workers 4

# Using gunicorn with uvicorn workers
gunicorn synth_lab.api.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

---

## Interactive API Documentation

The REST API provides interactive documentation via Swagger UI:

1. Start the API server: `uvicorn synth_lab.api.main:app --reload`
2. Open browser: http://localhost:8000/docs
3. Try out endpoints directly in the browser
4. View request/response schemas
5. Download OpenAPI spec for client generation

**Features**:
- **Try it out**: Execute requests directly from the browser
- **Schemas**: See full request/response models
- **Authentication**: Configure auth tokens if needed
- **Examples**: Pre-filled example requests

---

## Python SDK Usage

For Python applications, use the `requests` library or `httpx` for async:

### Synchronous (requests)

```python
import requests

BASE_URL = "http://localhost:8000"

# List synths
response = requests.get(f"{BASE_URL}/synths/list")
synths = response.json()

# Execute research
payload = {
    "synth_id": "synth_001",
    "topic": "compra-amazon",
    "model": "gpt-4o"
}
response = requests.post(
    f"{BASE_URL}/research/execute",
    json=payload,
    stream=True  # For SSE
)
for line in response.iter_lines():
    if line:
        print(line.decode('utf-8'))
```

### Asynchronous (httpx)

```python
import httpx
import asyncio

async def main():
    async with httpx.AsyncClient() as client:
        # List synths
        response = await client.get("http://localhost:8000/synths/list")
        synths = response.json()

        # Execute research (async SSE)
        payload = {
            "synth_id": "synth_001",
            "topic": "compra-amazon",
            "model": "gpt-4o"
        }
        async with client.stream(
            "POST",
            "http://localhost:8000/research/execute",
            json=payload
        ) as response:
            async for line in response.aiter_lines():
                print(line)

asyncio.run(main())
```

---

## Shell Scripts Migration

If you have shell scripts using CLI commands, update them to use `curl`:

**Before**:
```bash
#!/bin/bash
# old_script.sh

for synth in synth_001 synth_002 synth_003; do
    uv run synthlab research \
        --synth-id "$synth" \
        --topic compra-amazon \
        --model gpt-4o
done
```

**After**:
```bash
#!/bin/bash
# new_script.sh

API_URL="http://localhost:8000"

for synth in synth_001 synth_002 synth_003; do
    curl -X POST "$API_URL/research/execute" \
        -H "Content-Type: application/json" \
        -d "{
            \"synth_id\": \"$synth\",
            \"topic\": \"compra-amazon\",
            \"model\": \"gpt-4o\"
        }"
done
```

---

## Troubleshooting

### API Server Not Starting

**Problem**: `ModuleNotFoundError` or import errors

**Solution**:
```bash
# Ensure dependencies are installed
uv sync

# Verify installation
python -c "from synth_lab.api.main import app; print('OK')"
```

### Connection Refused

**Problem**: `curl: (7) Failed to connect to localhost port 8000`

**Solution**:
```bash
# Ensure API server is running
ps aux | grep uvicorn

# Start if not running
uvicorn synth_lab.api.main:app --reload
```

### 404 Not Found

**Problem**: Endpoint returns 404

**Solution**:
```bash
# Check available endpoints
curl http://localhost:8000/openapi.json | jq '.paths | keys'

# Verify correct endpoint path (e.g., /synths/list not /synths)
```

### SSE Not Streaming

**Problem**: SSE events not appearing in real-time

**Solution**:
```bash
# Use -N flag with curl to disable buffering
curl -N http://localhost:8000/research/execute ...

# Or use --no-buffer
curl --no-buffer http://localhost:8000/research/execute ...
```

---

## Migration Checklist

- [ ] Review removed CLI commands in your scripts/automation
- [ ] Update scripts to use REST API endpoints
- [ ] Test API endpoints with curl or Swagger UI
- [ ] Update documentation/runbooks to reference API
- [ ] Configure API server deployment (if needed)
- [ ] Set up monitoring for API endpoints (optional)
- [ ] Update team training materials

---

## Additional Resources

- **API Documentation**: http://localhost:8000/docs (when server running)
- **OpenAPI Specification**: http://localhost:8000/openapi.json
- **Full API Spec**: `docs/api.md` (repository documentation)
- **Architecture Documentation**: `docs/arquitetura.md`
- **Database Models**: `docs/database_model.md`

---

## Support

If you encounter issues during migration:

1. Check API server logs for errors
2. Verify request payload matches schema in `/docs`
3. Consult `docs/api.md` for detailed endpoint documentation
4. Review this quickstart for correct endpoint usage

**CLI Still Available**:
- `uv run synthlab gensynth` - Synth and avatar generation

All other functionality is now API-only.
