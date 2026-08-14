# ThinkTank-ME Demo

ThinkTank-ME Demo is a two-part Polymarket forecasting workspace:

- a Streamlit frontend in [app/](app)
- a FastAPI backend in [server/](server)

The frontend lets you paste a Polymarket URL, browse previous chats, upload files, and view forecast output. The backend handles market inspection and forecast generation.

## Repository Layout

- [app/](app) - Streamlit UI, local chat storage, file uploads, and API client logic
- [server/](server) - FastAPI forecast service and embedding/index initialization
- [.gitignore](.gitignore) - ignores local data, media, and virtualenv folders

## How It Works

1. The Streamlit app sends a Polymarket URL to the FastAPI backend.
2. The backend inspects the market and returns normalized market data.
3. The frontend stores chat history locally in SQLite and renders the response.

## Quick Start

### 1. Start the backend

```bash
cd server
cp .env.example .env
python3 -m venv .polyvenv
source .polyvenv/bin/activate
pip install -r requirements.txt
make run
```

Backend defaults:
- API: `http://127.0.0.1:8000`
- Health check: `GET /health`
- Inspect endpoint: `POST /inspect`
- Forecast endpoint: `POST /forecast`

### 2. Start the Streamlit frontend

```bash
cd app
python3 -m venv .demovenv
source .demovenv/bin/activate
pip install -r requirements.txt
BACKEND_API_URL=http://127.0.0.1:8000 streamlit run app.py
```

Or use the app Makefile shortcut:

```bash
cd app
make bs
```

## Environment Variables

### Frontend

- `BACKEND_API_URL` - URL of the FastAPI backend
- `REQUEST_TIMEOUT_SECONDS` - request timeout for backend calls

### Backend

- `ANTHROPIC_API_KEY` - API key used by the forecast pipeline
- `CLAUDE_MODEL` - Claude model name
- `EMBEDDING_MODEL` - embedding model name
- `EMBEDDING_MODEL_PATH` - local embedding model path, if used
- `REQUEST_TIMEOUT_SECONDS` - backend request timeout
- `VECTOR_INDEX_STORAGE` - path to the vector index storage directory

## Local Data

- Chat history is stored in SQLite under `app/data/chat_history.db`
- Uploaded files are copied into `app/media/`
- The backend uses its configured vector storage directory for the skill index

## Notes

- Keep the frontend and backend in separate virtual environments.
- Do not commit local data, uploads, or virtualenv directories.
- If you change folders again, update the relative paths in the app and backend docs together.
