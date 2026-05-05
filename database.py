import sqlite3
import json
import os
import datetime

# --- DATABASE SETUP (SQLite) ---
# Ensure the data directory exists for our Docker volume mapping
os.makedirs("data", exist_ok=True)
DB_PATH = "data/chat_history.db"

def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS history
                 (session_id TEXT PRIMARY KEY, title TEXT, messages TEXT, last_updated TEXT)''')
    conn.commit()
    conn.close()


# get the necessary metadata for the sidebar(session_id, title etc)
def get_sidebar_chats():
    conn = get_connection()
    c = conn.cursor()

    # ONLY select the ID and Title. 
    c.execute("SELECT session_id, title FROM history ORDER BY last_updated DESC")
    rows = c.fetchall()
    conn.close()
    return rows

# Get the chat messages when the sidebar button is clicked
def get_chat_messages(session_id):
    conn = get_connection()
    c = conn.cursor()

    # Select the messages from specific ID
    c.execute("SELECT messages FROM history WHERE session_id = ?", (session_id,))
    row = c.fetchone()
    conn.close()
    
    if row:
        return json.loads(row[0]) # Convert the JSON string back to a Python list
    return []


def save_chat(session_id, title, messages_array):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "INSERT OR REPLACE INTO history (session_id, title, messages, last_updated) VALUES (?, ?, ?, ?)",
        (session_id, title, json.dumps(messages_array), datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )
    conn.commit()
    conn.close()
