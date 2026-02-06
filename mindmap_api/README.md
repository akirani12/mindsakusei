# Mindmap Generator API

Serial LLM workflow (KW → RKW → SCN → ALT → MAP) exposed as a FastAPI service.

## Setup

```bash
cd mindmap_api
pip install -e ".[dev]"
```

## Environment

Copy and edit the example:

```bash
cp .env.example .env
# Edit .env with your keys
```

Required variables:
- `APP_API_KEY` – API key clients must send via `X-API-Key` header
- `OPENAI_API_KEY` – OpenAI API key

## Run

```bash
cd mindmap_api
uvicorn mindmap_api.app:app --host 0.0.0.0 --port 8000
```

Or with auto-reload for development:

```bash
uvicorn mindmap_api.app:app --reload --host 0.0.0.0 --port 8000
```

## API

### POST /v1/mindmap/generate

**Headers:**
- `X-API-Key: <your APP_API_KEY>`

**Request body:**
```json
{
  "reqcons": "AIを活用したノート取りアプリの要件",
  "qchar": "大学生",
  "ppc": null
}
```

- `reqcons` (required, max 1000 chars): requirement description
- `qchar` (optional): character/persona
- `ppc` (optional): reserved for future use

**Response:**
```json
{
  "mindmap_markdown": "# ノート取りアプリ\n## ..."
}
```

**curl example:**
```bash
curl -X POST http://localhost:8000/v1/mindmap/generate \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key-here" \
  -d '{"reqcons": "ECサイトの商品検索機能", "qchar": "一般消費者"}'
```

## Tests

```bash
cd mindmap_api
python -m pytest tests/ -v
```

## Per-node configuration

Each workflow node (kw, rkw, scn, alt, map) can override model and temperature via env vars:

```
NODE_KW__MODEL=gpt-4o
NODE_KW__TEMPERATURE=0.3
NODE_MAP__TEMPERATURE=0.4
```

## Azure OpenAI

Set `LLM_PROVIDER=azure` and configure the `AZURE_OPENAI_*` variables in `.env`.

## Prompts

Prompt templates are in `prompts/` as `.txt` files. They use `{variable}` placeholders filled at runtime.
