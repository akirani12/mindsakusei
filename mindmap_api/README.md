# Mindmap Generator API

Serial LLM workflow (KW → RKW → SCN → ALT → MAP) exposed as a FastAPI service.
Dify DSL の直列パイプラインを Python/FastAPI で再実装。

## Directory structure

```
mindmap_api/
  pyproject.toml
  README.md
  .env.example
  src/mindmap_api/
    __init__.py
    main.py                # FastAPI app
    auth.py                # API Key auth dependency
    schemas.py             # Pydantic models
    config.py              # env/config loading
    logging_setup.py       # Structured JSON logging
    prompts.py             # Template loader
    llm/
      __init__.py
      base.py              # LLMClient interface + LLMResponse
      openai_client.py     # OpenAI / Azure OpenAI implementation
    workflow/
      __init__.py
      runner.py            # Orchestration (KW→RKW→SCN→ALT→MAP)
      steps.py             # Individual step functions
      validators.py        # Light validation (log-only)
    prompts/
      kw_system.txt / kw_user.txt
      rkw_system.txt / rkw_user.txt
      scn_system.txt / scn_user.txt
      alt_system.txt / alt_user.txt
      map_system.txt / map_user.txt
  tests/
    test_api.py
    test_workflow_smoke.py
```

## Setup

```bash
cd mindmap_api
pip install -e ".[dev]"
```

## Environment

```bash
cp .env.example .env
# Edit .env with your keys
```

Required:
- `APP_API_KEY` – API key clients must send via `X-API-Key` header
- `OPENAI_API_KEY` – OpenAI API key

## Run

```bash
uvicorn mindmap_api.main:app --host 0.0.0.0 --port 8000
```

Development (auto-reload):

```bash
uvicorn mindmap_api.main:app --reload --host 0.0.0.0 --port 8000
```

## API

### POST /v1/mindmap/generate

**Headers:** `X-API-Key: <your APP_API_KEY>`

**Request:**
```json
{
  "reqcons": "ECサイトの商品検索機能（必須, max 1000文字）",
  "qchar": "一般消費者（任意）",
  "ppc": "3（任意, 予約フィールド）"
}
```

**Response:**
```json
{
  "mindmap_markdown": "---\n...\n---\n# ..."
}
```

**curl:**
```bash
curl -X POST http://localhost:8000/v1/mindmap/generate \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key-here" \
  -d '{"reqcons": "ECサイトの商品検索機能", "qchar": "一般消費者"}'
```

**Error codes:** 401 (API Key不正) / 422 (バリデーション) / 500 (LLM失敗/タイムアウト)

## Tests

```bash
python -m pytest tests/ -v
```

## Per-node configuration

DSL温度デフォルト: KW=0.7, RKW=0.7, SCN=0.7, ALT=0.4, MAP=0.3

Env で上書き可能:
```
NODE_KW__MODEL=gpt-5-chat-latest
NODE_ALT__TEMPERATURE=0.4
NODE_MAP__TEMPERATURE=0.3
```

## Azure OpenAI

`LLM_PROVIDER=azure` に設定し `AZURE_OPENAI_*` 変数を `.env` で構成。

## Prompts

テンプレートは `src/mindmap_api/prompts/` 配下の `.txt` ファイル。`{variable}` プレースホルダを実行時に展開。
