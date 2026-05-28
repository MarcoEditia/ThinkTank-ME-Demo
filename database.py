import sqlite3
import json
import datetime
from pathlib import Path

# --- DATABASE SETUP (SQLite) ---
# Ensure the data directory exists for our Docker volume mapping
Path("data").mkdir(exist_ok=True)
DB_PATH = "data/chat_history.db"

#Initalize the MEDIA directory to STORE FILES after uploading them in PROMPT
Path("media").mkdir(exist_ok=True)

def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    conn = get_connection()
    try:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS history
                     (session_id TEXT PRIMARY KEY, title TEXT, messages TEXT, last_updated TEXT)
                  ''')
        conn.commit()
    finally:
        conn.close()


# get the necessary metadata for the sidebar(session_id, title etc)
def get_sidebar_chats():
    conn = get_connection()
    try:
        c = conn.cursor()
        # ONLY select the ID and Title.
        c.execute("SELECT session_id, title FROM history ORDER BY last_updated DESC")
        rows = c.fetchall()
        return rows
    except Exception as e:
        print(f"get_sidebar_chats error: {e}")
        return []
    finally:
        conn.close()

# Get the chat messages when the sidebar button is clicked
def get_chat_messages(session_id):
    conn = get_connection()
    try:
        c = conn.cursor()

        # Select the messages from specific ID
        c.execute("SELECT messages FROM history WHERE session_id = ?", (session_id,))
        row = c.fetchone()
        if row:
            return json.loads(row[0]) # Convert the JSON string back to a Python list
        return []
    except Exception as e:
        print(f"get_chat_messages error {session_id}: {e}")
        return []
    finally:
        conn.close()


def save_chat(session_id, title, messages_array, files=None):
    conn = get_connection()
    try:
        c = conn.cursor()

        # copy the files into the media folder/directory
        if files:
            dir_path = Path("media") / session_id
            dir_path.mkdir(parents=True, exist_ok=True)
            for file in files:
                file_bytes = file.getvalue()
                safe_name = file.name.replace("/", "_").replace(" ", "_")
                file_id = file.file_id

                destination_file_path = dir_path / f"{file_id}-{safe_name}"
                destination_file_path.write_bytes(file_bytes)
        
        c.execute(
            "INSERT OR REPLACE INTO history (session_id, title, messages, last_updated) VALUES (?, ?, ?, ?)",
            (session_id, title, json.dumps(messages_array), datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"save_chat error for session {session_id}: {e}")
        return False
    finally:
        conn.close()
