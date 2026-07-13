# ThinkTank-ME Demo

A lightweight Streamlit chat app that sends prompts to a configurable LLM server, uses SQLite for chat history, and supports PDF file prompting.

## Features

- Streamlit chat UI with persistent conversation history
- File prompting
- SQLite storage for chats and sidebar history
- Docker Compose setup for the app container

## Tech Stack

- Python 3.12
- Streamlit
- SQLite
- Docker / Docker Compose

## Project Files

- `app.py` - Streamlit UI, chat flow, file handling, and LLM requests
- `database.py` - SQLite setup and chat persistence
- `docker-compose.yml` - App service definition
- `Makefile` - Shortcuts for starting and stopping the app
- `requirements.txt` - Python dependencies

## Quick Start

### 1. Clone the repo

```bash
git clone https://github.com/MarcoEditia/ThinkTank-ME-Demo.git
cd ThinkTank-ME-Demo
```

### 2. First-time setup

Set the LLM endpoint before starting the app:

```bash
LLM_API_URL=http://your-llm-server:11434
LLM_MODEL=qwen3.5:0.8b
```

Then start the app:

```bash
make b
```

### 3. Open the app

- Streamlit UI: http://localhost:8501
- LLM API: set by `LLM_API_URL`

## Makefile Commands

### Streamlit App Shortcut
- `make b` - (build) - build and start the app container
- `make re` - (rebuild) - rebuild from scratch
- `make d` - (down) - stop the app containers

## Docker Notes

- The app container reads `LLM_API_URL` and `LLM_MODEL` from the environment
- SQLite data is persisted in `./sqlite_data`

## Local Development

If you want to run the Streamlit app directly on your machine, install the Python dependencies first:

```bash
pip install -r requirements.txt
streamlit run app.py
```

If you do this locally, make sure your LLM server is reachable at the value you set in `LLM_API_URL`.

## Troubleshooting

- If the app cannot reach the LLM server, check `LLM_API_URL` and the server logs.
