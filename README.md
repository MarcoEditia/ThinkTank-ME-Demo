# ThinkTank-ME Demo 🤖

A lightweight, containerized chat application featuring a persistent SQLite database for session history and lazy-loading sidebar navigation.
App demo: https://thinktank-me-demo.streamlit.app/

## Features
* **Interactive Chat UI:** Built with Streamlit for a seamless conversational experience.
* **Session Memory:** Chat histories are automatically saved and retrieved using SQLite.
* **Smart Sidebar:** Uses Streamlit fragments and lazy-loading to instantly pull previous conversations without slowing down the main app.
* **Dockerized:** Fully containerized for instant setup and environment consistency.

## Tech Stack
* Python 3 & Streamlit
* SQLite3
* Docker & Docker Compose

## File Structure
* `app.py`: Main frontend, UI logic, and state management.
* `database.py`: SQLite initialization, connection handling, and data retrieval.
* `sqlite_data/`: Volume-mapped directory to ensure the `.db` database file persists across container restarts.

---

## Quick Start

### 1. Installation
```bash
git clone [https://github.com/marcoeditiahusin/ThinkTank-ME-Demo.git](https://github.com/marcoeditiahusin/ThinkTank-ME-Demo.git)
cd ThinkTank-ME-Demo

```
### 2. Run the App
Option A: Using Make 
If you have make installed, use these shortcuts:

```bash
make b   # Build and start the app
make re  # Rebuild and restart the app (use after making code changes)
make d   # Stop and remove the container

```
Option B: Without Make
If you don't use make, run the underlying Docker commands directly:
```bash
docker-compose up -d --build  # Build and start the app
docker-compose down           # Stop and remove the container

```
### Local Python (If You don't have Docker installed)
To run it raw on your own machine without containers:

```bash
pip install -r requirements.txt
streamlit run app.py
```
Live App: http://localhost:8501
