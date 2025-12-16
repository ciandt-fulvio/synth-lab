# API Contract: OpenAI Image Generation

**Feature**: Synth Avatar Generation
**API**: OpenAI Images API
**Version**: v1 (gpt-image-1-mini 2/3)
**Date**: 2025-12-16

## Overview

This document defines the contract for integrating with OpenAI's Image Generation API to create avatar images for synthetic personas.

## Authentication

**Method**: Bearer Token (API Key)

**Header**:
```
Authorization: Bearer {OPENAI_API_KEY}
```

**Environment Variable**:
```bash
export OPENAI_API_KEY="sk-..."
```

**Python SDK Configuration**:
```python
from openai import OpenAI
import os

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
```

## Endpoint

**Base URL**: `https://api.openai.com/v1`

**Image Generation Endpoint**:
```
POST /images/generations
```

## Request Format

### Using Python SDK (Recommended)

```python
response = client.images.generate(
    model="gpt-image-1-mini-2",          # Required: "gpt-image-1-mini-2" or "gpt-image-1-mini-3"
    prompt="...",              # Required: Text description (max 4000 chars)
    n=1,                       # Optional: Number of images (1 for gpt-image-1-mini 3)
    size="1024x1024",          # Optional: "256x256" | "512x512" | "1024x1024"
    quality="standard",        # Optional: "standard" | "hd" (gpt-image-1-mini 3 only)
    response_format="url"      # Optional: "url" | "b64_json"
)
```

### Raw HTTP Request

```http
POST https://api.openai.com/v1/images/generations
Content-Type: application/json
Authorization: Bearer {OPENAI_API_KEY}

{
  "model": "gpt-image-1-mini-2",
  "prompt": "[detailed prompt here]",
  "n": 1,
  "size": "1024x1024",
  "response_format": "url"
}
```

### Request Parameters

| Parameter | Type | Required | Values | Default | Description |
|-----------|------|----------|--------|---------|-------------|
| `model` | string | Yes | "gpt-image-1-mini-2", "gpt-image-1-mini-3" | - | Model to use for generation |
| `prompt` | string | Yes | Any text, max 4000 chars | - | Text description of image |
| `n` | integer | No | 1-10 (gpt-image-1-mini 2), 1 (gpt-image-1-mini 3) | 1 | Number of images to generate |
| `size` | string | No | "256x256", "512x512", "1024x1024" | "1024x1024" | Size of generated images |
| `quality` | string | No | "standard", "hd" | "standard" | Image quality (gpt-image-1-mini 3 only) |
| `response_format` | string | No | "url", "b64_json" | "url" | Format of returned image |

### For This Feature

**Fixed Values**:
- `model`: "gpt-image-1-mini-2" (cost-effective choice)
- `n`: 1 (one grid image per block)
- `size`: "1024x1024" (required for 3x3 grid)
- `response_format`: "url" (simpler handling)

**Variable Values**:
- `prompt`: Generated from 9 synth descriptions

## Response Format

### Success Response (HTTP 200)

**Using Python SDK**:
```python
response.data[0].url  # Image URL
response.data[0].revised_prompt  # gpt-image-1-mini 3 may revise prompts (optional)
response.created  # Timestamp
```

**Raw JSON**:
```json
{
  "created": 1702835421,
  "data": [
    {
      "url": "https://oaidalleapiprodscus.blob.core.windows.net/private/..."
    }
  ]
}
```

**Response Fields**:
| Field | Type | Description |
|-------|------|-------------|
| `created` | integer | Unix timestamp |
| `data` | array | List of generated images (length = n) |
| `data[].url` | string | Temporary URL to download image (expires in ~1 hour) |
| `data[].b64_json` | string | Base64-encoded image data (if response_format="b64_json") |
| `data[].revised_prompt` | string | gpt-image-1-mini 3 revised prompt (optional) |

### Error Responses

#### 400 Bad Request
```json
{
  "error": {
    "message": "Invalid prompt: prompt is too long",
    "type": "invalid_request_error",
    "param": "prompt",
    "code": null
  }
}
```

**Causes**:
- Prompt exceeds 4000 characters
- Invalid size parameter
- Invalid model name
- n > 1 for gpt-image-1-mini 3

#### 401 Unauthorized
```json
{
  "error": {
    "message": "Incorrect API key provided",
    "type": "invalid_request_error",
    "param": null,
    "code": "invalid_api_key"
  }
}
```

**Cause**: Invalid or missing API key

#### 429 Rate Limit Exceeded
```json
{
  "error": {
    "message": "Rate limit exceeded. Please try again in 20 seconds.",
    "type": "rate_limit_error",
    "param": null,
    "code": "rate_limit_exceeded"
  }
}
```

**Cause**: Too many requests in time window

#### 500 Internal Server Error
```json
{
  "error": {
    "message": "The server had an error while processing your request",
    "type": "server_error",
    "param": null,
    "code": null
  }
}
```

**Cause**: OpenAI service issue

### Python SDK Exception Mapping

```python
from openai import (
    APIError,           # Generic API error (500)
    APIConnectionError, # Network/connection issues
    RateLimitError,     # 429 rate limit
    AuthenticationError # 401 invalid API key
)

try:
    response = client.images.generate(...)
except AuthenticationError as e:
    # Handle invalid API key
    pass
except RateLimitError as e:
    # Handle rate limiting (retry with backoff)
    pass
except APIConnectionError as e:
    # Handle network errors
    pass
except APIError as e:
    # Handle other API errors
    pass
```

## Example Prompt for Avatar Block

### Template
```python
PROMPT_TEMPLATE = """Create a single image divided into a precise 3x3 grid (3 rows, 3 columns) containing 9 distinct portrait photographs of Brazilian individuals. Each portrait should be centered in its grid cell with clear separation.

GRID LAYOUT:
Row 1: [1] Top-Left | [2] Top-Center | [3] Top-Right
Row 2: [4] Mid-Left | [5] Mid-Center | [6] Mid-Right
Row 3: [7] Bot-Left | [8] Bot-Center | [9] Bot-Right

PORTRAITS:
{portrait_descriptions}

VISUAL STYLE:
- Apply diverse filters randomly across portraits: no filter, black & white, sepia, warm tone, cool tone, or 3D movie character style
- Backgrounds should relate to each person's profession with bokeh/defocused effect
- Vary clothing colors, patterns, and accessories (glasses, earrings, hair items)
- Occasionally include profession-related items or attire
- Ensure accurate representation of Brazilian demographics (age, ethnicity, gender)
- Professional headshot quality for each portrait
"""
```

### Example with Real Data
```
Create a single image divided into a precise 3x3 grid (3 rows, 3 columns) containing 9 distinct portrait photographs of Brazilian individuals. Each portrait should be centered in its grid cell with clear separation.

GRID LAYOUT:
Row 1: [1] Top-Left | [2] Top-Center | [3] Top-Right
Row 2: [4] Mid-Left | [5] Mid-Center | [6] Mid-Right
Row 3: [7] Bot-Left | [8] Bot-Center | [9] Bot-Right

PORTRAITS:
[1] Man, 35 years old, white ethnicity, mechanic. Apply warm tone filter.
[2] Woman, 42 years old, pardo ethnicity, teacher. Use black & white filter.
[3] Man, 28 years old, black ethnicity, software engineer. No filter.
[4] Woman, 56 years old, white ethnicity, nurse. Apply sepia filter.
[5] Man, 47 years old, indigenous ethnicity, construction worker. Use 3D movie character style.
[6] Woman, 33 years old, pardo ethnicity, salesperson. Apply cool tone filter.
[7] Man, 61 years old, asian ethnicity, chef. No filter.
[8] Woman, 25 years old, black ethnicity, graphic designer. Apply warm tone filter.
[9] Man, 52 years old, white ethnicity, lawyer. Use black & white filter.

VISUAL STYLE:
- Apply diverse filters randomly across portraits: no filter, black & white, sepia, warm tone, cool tone, or 3D movie character style
- Backgrounds should relate to each person's profession with bokeh/defocused effect
- Vary clothing colors, patterns, and accessories (glasses, earrings, hair items)
- Occasionally include profession-related items or attire
- Ensure accurate representation of Brazilian demographics (age, ethnicity, gender)
- Professional headshot quality for each portrait
```

## Rate Limits and Quotas

### Rate Limits (Tier-dependent)

| Tier | Requests/Min | Requests/Day |
|------|--------------|--------------|
| Free | 5 | 50 |
| Tier 1 | 50 | 500 |
| Tier 2 | 50 | 500 |
| Tier 3+ | 100 | 1000+ |

**Recommendation**: Add 1-2 second delay between requests to stay under limits

### Costs

| Model | Size | Quality | Cost per Image |
|-------|------|---------|----------------|
| gpt-image-1-mini 2 | 1024x1024 | Standard | $0.020 |
| gpt-image-1-mini 2 | 512x512 | Standard | $0.018 |
| gpt-image-1-mini 2 | 256x256 | Standard | $0.016 |
| gpt-image-1-mini 3 | 1024x1024 | Standard | $0.040 |
| gpt-image-1-mini 3 | 1024x1024 | HD | $0.080 |

**For This Feature**: Using gpt-image-1-mini 2, 1024x1024 = **$0.020 per block** (9 avatars)

## Retry Strategy

### Recommended Backoff

```python
import time
from openai import RateLimitError, APIConnectionError

MAX_RETRIES = 3
BACKOFF_FACTOR = 2  # Exponential backoff

for attempt in range(MAX_RETRIES):
    try:
        response = client.images.generate(...)
        break  # Success
    except RateLimitError as e:
        if attempt < MAX_RETRIES - 1:
            wait_time = BACKOFF_FACTOR ** attempt  # 1s, 2s, 4s
            logger.warning(f"Rate limit hit, retrying in {wait_time}s...")
            time.sleep(wait_time)
        else:
            logger.error("Max retries exceeded")
            raise
    except APIConnectionError as e:
        if attempt < MAX_RETRIES - 1:
            wait_time = BACKOFF_FACTOR ** attempt
            logger.warning(f"Connection error, retrying in {wait_time}s...")
            time.sleep(wait_time)
        else:
            raise
```

### Retry Conditions

| Error Type | Retry? | Strategy |
|------------|--------|----------|
| RateLimitError (429) | Yes | Exponential backoff |
| APIConnectionError | Yes | Exponential backoff |
| AuthenticationError (401) | No | Fix API key, don't retry |
| APIError (400) | No | Fix request, don't retry |
| APIError (500) | Yes | Linear backoff (server issue) |

## Image Download

### URL Expiration
- Image URLs expire after **~1 hour**
- MUST download immediately after receiving response
- DO NOT store URLs for later use

### Download Pattern
```python
import requests
from pathlib import Path

def download_image(url: str, output_path: str) -> None:
    """Download image from OpenAI URL to local file."""
    response = requests.get(url, stream=True, timeout=30)
    response.raise_for_status()

    with open(output_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
```

## Testing

### Mock Response for Tests
```python
from unittest.mock import Mock

# Mock successful response
mock_response = Mock()
mock_response.data = [Mock(url="https://example.com/test.png")]
mock_response.created = 1702835421

# Mock client
mock_client = Mock()
mock_client.images.generate.return_value = mock_response
```

### Test Mode
- Use `@pytest.mark.slow` for real API tests
- Mock API calls in fast test battery
- Store test images in `tests/fixtures/avatars/`

## Compliance and Safety

### Content Policy
- OpenAI prohibits generation of:
  - Explicit or violent content
  - Public figures' likenesses
  - Deceptive content

**For This Feature**: Generic Brazilian personas are compliant (no public figures, appropriate content)

### Privacy
- Do not include real names in prompts
- Use only synthetic demographic data
- Avatars are fictional representations, not real people

## References

- Official API Docs: https://platform.openai.com/docs/api-reference/images
- Python SDK: https://github.com/openai/openai-python
- gpt-image-1-mini Guide: https://platform.openai.com/docs/guides/images
