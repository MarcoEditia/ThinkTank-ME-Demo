# FastAPI Backend

This folder contains the backend service for ThinkTank-ME Demo.

The backend exposes two public endpoints used by the Streamlit app:

- `POST /inspect` - normalize a Polymarket URL and load the selected market
- `POST /forecast` - run the full forecast pipeline and return the final response

There is also a small `GET /health` endpoint for liveness checks.

## What the Backend Does

The backend is responsible for:

- parsing Polymarket URLs
- loading market and event data
- building a forecast contract
- initializing the vector index used by the research/agent layer
- returning structured forecast output for the frontend

The backend does not store chat history. The Streamlit app keeps that locally in SQLite.

## Recommended runtime

- Python 3.11+
- FastAPI for the backend API
- Pydantic for typed inputs and outputs
- `httpx` for Polymarket Gamma API requests
- Claude Agent SDK for web research and independent expert runs
- Plain asynchronous Python orchestration for the first MVP

Avoid adding a complex workflow framework until this linear pipeline works.

## Key Files

- [src/main.py](src/main.py) - FastAPI app and routes
- [src/config.py](src/config.py) - environment-backed settings
- [src/pipeline.py](src/pipeline.py) - forecast orchestration
- [src/agents.py](src/agents.py) - agent execution helpers
- [src/aggregation.py](src/aggregation.py) - probability aggregation logic
- [src/skills.py](src/skills.py) - skill/index initialization
- [requirements.txt](requirements.txt) - backend dependencies

## Local Setup
```bash
cp .env.example .env
python3 -m venv .polyvenv
source .polyvenv/bin/activate
pip install -r requirements.txt
```

Set `ANTHROPIC_API_KEY` in `.env`, and make sure `VECTOR_INDEX_STORAGE` points to a writable directory.

Run the API:

```bash
uvicorn app.main:app --reload
```
Or run directly:
make run

Open the generated API docs at:

```text
http://127.0.0.1:8000/docs
```

## Environment Variables

- `ANTHROPIC_API_KEY` - required by the forecasting pipeline
- `CLAUDE_MODEL` - Claude model name, defaults to `sonnet`
- `EMBEDDING_MODEL` - embedding model name, defaults to `BAAI/bge-m3`
- `EMBEDDING_MODEL_PATH` - optional local embedding model path
- `REQUEST_TIMEOUT_SECONDS` - backend request timeout, defaults to `20`
- `VECTOR_INDEX_STORAGE` - storage directory for the vector index

## API Endpoints

### Health

```bash
curl http://127.0.0.1:8000/health
```

## Step-by-step interfaces

| Step | Component | Input | Output |
|---|---|---|---|
| 1 | `parse_polymarket_url` | Polymarket URL string | normalized URL and slug |
| 2 | `fetch_event_by_slug` | slug | raw Gamma Event JSON |
| 3 | `build_market_context` | Event JSON and `market_index` | `ForecastContract` and `MarketSnapshot` |
| 4 | `research_evidence` | `ForecastContract` without market price | `EvidencePacket` with URLs and claims |
| 5 | `run_all_experts` | contract and evidence | four independent `ExpertForecast` objects |
| 6 | `aggregate_forecasts` | expert probabilities | median probability, dispersion and agreement |
| 7 | `run_forecast` | URL and market index | complete `ForecastResponse` |

## First test: inspect Polymarket only

```bash
curl -X POST http://127.0.0.1:8000/inspect \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://polymarket.com/event/fed-decision-in-october",
    "market_index": 0
  }'
```

The result tells you whether URL parsing, slug extraction, Event loading, Market
selection, outcome prices, deadline, and resolution text are correct.

If `available_markets` contains multiple entries, select the desired
`market_index` in the next request.

## Full forecast

```bash
curl -X POST http://127.0.0.1:8000/forecast \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://polymarket.com/event/fed-decision-in-october",
    "market_index": 0
  }'
```

## Skills

Skills live under `.claude/skills/`. The MVP loads their `SKILL.md` text into
each agent's system prompt. This keeps procedural knowledge versioned and easy
to inspect.

## Suggested implementation order

1. Make `/inspect` reliable for ten Polymarket URLs.
2. Verify multi-market Event selection.
3. Run `research_evidence` alone and manually inspect source quality.
4. Run one Domain expert.
5. Add the other three experts in parallel.
6. Add aggregation and market comparison.
7. Save runs to SQLite and add a simple frontend.
8. Add price history and scheduled forecast updates.


## Localized, multi-market example: World Cup Winner

The URL below contains a locale prefix and many child markets:

```text
https://polymarket.com/zh/event/world-cup-winner
```

Inspect one team by name:

```bash
curl -X POST http://127.0.0.1:8000/inspect \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://polymarket.com/zh/event/world-cup-winner",
    "market_query": "France"
  }'
```

Run the full forecast:

```bash
curl -X POST http://127.0.0.1:8000/forecast \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://polymarket.com/zh/event/world-cup-winner",
    "market_query": "France"
  }'
```

For multi-market Events, prefer `market_query` over `market_index`, because
the ordering of child markets may change.

main.py -> pipeline.py -> agents.py/aggregation.py ->

## Notes

- Keep the backend virtualenv separate from the Streamlit virtualenv.
- The backend initializes its vector index on startup.
- The frontend should point `BACKEND_API_URL` at this service.
- Downloading the embedding model (BAAI/bge-m3) from hugging face is recommended 