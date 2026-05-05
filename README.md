# ThinkTank-ME Demo 🤖

A lightweight, containerized chat application featuring a persistent SQLite database for session history and lazy-loading sidebar navigation.

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

### 1. Install
```bash
git clone [https://github.com/marcoeditiahusin/ThinkTank-ME-Demo.git](https://github.com/marcoeditiahusin/ThinkTank-ME-Demo.git)
cd ThinkTank-ME-Demo
