# ThinkTank-ME Demo

A lightweight Streamlit chat app that uses Ollama for local LLM responses, SQLite for chat history, and PDF file prompting.

## Features

- Streamlit chat UI with persistent conversation history
- Ollama-backed local model inference
- File prompting support for uploaded PDFs
- SQLite storage for chats and sidebar history
- Docker Compose setup for the app and Ollama service

## Tech Stack

- Python 3.12
- Streamlit
- Ollama
- SQLite
- Docker / Docker Compose
- PyMuPDF4LLM for PDF text extraction

## Project Files

- `app.py` - Streamlit UI, chat flow, file handling, and Ollama requests
- `database.py` - SQLite setup and chat persistence
- `docker-compose.yml` - App + Ollama services
- `Makefile` - Shortcuts for starting, pulling, and verifying Ollama
- `requirements.txt` - Python dependencies

## Quick Start

### 1. Clone the repo

```bash
git clone https://github.com/MarcoEditia/ThinkTank-ME-Demo.git
cd ThinkTank-ME-Demo
```

### 2. First-time setup

If this is your first time running the app, pull the model first:

```bash
make po
```

Then start the app:

```bash
make ra
```

If you already pulled the model before, you can go straight to:

```bash
make ra
```

### 3. Verify the model/API

```bash
make vo
```

### 4. Open the app

- Streamlit UI: http://localhost:8501
- Ollama API: http://localhost:11434

## Makefile Commands

### Run App and Ollama Shortcut
- `make ra` - (run app) - start Ollama and the app

### Ollama Shortcut
- `make po` - (pull ollama) - start Ollama and pull `MODEL` (default: `tinyllama`)
- `make vo` - (verify ollama) - verify the model and Ollama API
- `make ro` - (run ollama) - run the selected model interactively in the container
- `make remove-model` - delete the selected model from the Ollama volume

### Streamlit App Shortcut
- `make b` - (build) - build and start the app container
- `make re` - (rebuild) - rebuild from scratch
- `make d` - (down) - stop the app containers

You can override the model name:

```bash
make po MODEL=llama3.1
make ro MODEL=llama3.1
make remove-model MODEL=llama3.1
```

## File Prompting

The app accepts uploaded PDF files from `st.chat_input(..., accept_file="multiple")`.

Current file handling flow:

- PDFs are extracted with `pymupdf4llm`
- The extracted text is added to the conversation context before sending it to Ollama

If you upload a PDF, the app writes it to a temporary file, converts it to markdown, and appends that text to the prompt context.

## Docker Notes

- The app container uses `OLLAMA_URL=http://ollama:11434`
- Ollama stores models in a named Docker volume, so models persist across restarts
- SQLite data is persisted in `./sqlite_data`

## Local Development

If you want to run the Streamlit app directly on your machine, install the Python dependencies first:

```bash
pip install -r requirements.txt
streamlit run app.py
```

If you do this locally, make sure Ollama is also running and reachable at `http://localhost:11434`.

## Troubleshooting

- If `make po` fails, confirm Docker Desktop is running.
- If the app cannot reach Ollama, check `docker compose ps` and `make vo`.
- If PDFs are not parsing correctly, confirm `pymupdf4llm` is installed and the uploaded file is a valid PDF.
