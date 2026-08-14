# Streamlit Frontend

This folder contains the Streamlit UI for ThinkTank-ME Demo.

The app lets you:

- paste a Polymarket URL
- select a market when the event has multiple markets
- upload files with the prompt
- review previous chats from local SQLite storage

The frontend talks to the backend over HTTP. It does not run the forecasting pipeline itself.

## Key Files

- [app.py](app.py) - Streamlit UI, chat flow, and backend calls
- [database.py](database.py) - local SQLite persistence for chat history
- [llm_client.py](llm_client.py) - HTTP client for the backend forecast service
- [Makefile](Makefile) - local run shortcuts
- [requirements.txt](requirements.txt) - Streamlit-side Python dependencies

## Local Setup

```bash
python3 -m venv .demovenv
source .demovenv/bin/activate
pip install -r requirements.txt
```

Set the backend URL if it is not already running at the default address:

```bash
export BACKEND_API_URL=http://127.0.0.1:8000
```

Then run the app:

```bash
streamlit run app.py
```

Or use the Makefile shortcut:

```bash
make bs
```

## Environment Variables

- `BACKEND_API_URL` - backend base URL, defaults to `http://127.0.0.1:8000`
- `REQUEST_TIMEOUT_SECONDS` - timeout for backend requests, defaults to `20`

## Data Storage

- Chat history is stored in `data/chat_history.db`
- Uploaded files are copied into `media/<session_id>/`

## Notes

- Run this app from the `app/` directory so the `.streamlit/styles.css` path resolves correctly.
- Keep the frontend virtualenv separate from the backend virtualenv.

