import streamlit as st
import datetime
from pathlib import Path
import re
from urllib.parse import urlparse

import database
from utils import file_utils, url_utils
import llm_client

# Initialize the DB when the app starts
database.init_db()
# css
def load_css(file_path):  
    with open(file_path) as f:
        st.html(f"<style>{f.read()}</style>")

css_path = Path(".streamlit/styles.css")
load_css(css_path)

# --- PAGE CONFIG & SESSION STATE --- 
st.set_page_config(page_title="Polymarket Forecast Demo", page_icon="📈")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

# --- SIDEBAR  ---
# Only loads the IDs and Titles
sidebar_chats = database.get_sidebar_chats()

with st.sidebar:
    if st.button("New Chat", width="stretch"):
        st.session_state.messages = []
        st.session_state.session_id = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        st.rerun()
    with st.container():

        # display chat history
        with st.expander("Recents"):

            if sidebar_chats:
                for chat in sidebar_chats:
                    session_id = chat[0]
                    title = chat[1]
                    
                    # Create the button
                    if st.button(title, key=session_id, width="stretch"):
                        st.session_state.session_id = session_id
                        st.session_state.messages = database.get_chat_messages(session_id)
                        st.rerun() 
            else:
                st.write("No history yet.")

# --- TOP CONTROL PANEL ---
with st.container(border=True):
    # Split top row into two columns (2:1 ratio)
    col1, col2 = st.columns([2, 1])

    with col1:
        input_url_or_question = st.text_input(
            "Polymarket URL or Question",
            placeholder="https://polymarket.com/event/...",
            key="top_url_input"
        )

    with col2:
        selected_market = st.selectbox(
            "Select Market",
            options=[
                "Will the Fed cut rates in June 2024?",
                "US Election 2024",
                "Custom..."
            ],
            key="top_market_select"
        )

    # Multi-select toggle pills
    selected_modes = st.pills(
        label="Analysis Modes",
        options=[
            "🌐 Use Web Evidence",
            "📊 Use Market Signals",
            "👤 Use Domain Expert",
            "⚖️ Contrarian View"
        ],
        default=["🌐 Use Web Evidence", "📊 Use Market Signals", "👤 Use Domain Expert"],
        selection_mode="multi",
        label_visibility="collapsed"
    )

    # Optional: Direct button to trigger processing from the top panel
    top_submit = st.button("Submit Query", type="primary", use_container_width=True)

# --- MAIN UI AND LOGIC ---
# Render the existing chat/chat history from the database
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("files"):
            dir_path = Path("media")/st.session_state.session_id
            st.write("directory path:", dir_path)
            file_utils.render_files(message["files"], dir_path)

URL_REGEX = r'(https?://[^\s;,\s]+)'
if prompt := st.chat_input("Paste a Polymarket URL and optional market name..." ,accept_file="multiple", file_type=["pdf", "image", "audio", "video"]):
    text = prompt.text or ""
    files = prompt.files or None
    valid_urls = re.findall(URL_REGEX, prompt.text)
    
    urls = url_utils.process_urls(valid_urls)

    with st.chat_message("user"):
        st.markdown(text)
        # render the file into the chat from streamlit cache
        if files:
            file_utils.render_files(files)

    file_data = file_utils.process_files(files)
    user_message = {"role": "user", "content": text, "files": file_data}
    st.session_state.messages.append(user_message)

    with st.chat_message("assistant"):
        with st.spinner("Processing..."):
            result = llm_client.query_model(st.session_state.messages)
            response_text = result["content"]
            reasoning_text = result["reasoning"]

        if reasoning_text:
            with st.expander("💭 View Thinking Process"):
                st.markdown(reasoning_text)

        st.markdown(response_text)

    st.session_state.messages.append({"role": "assistant", "content": response_text})
    is_new_chat = len(st.session_state.messages) == 2

    # Generate Title if it's the first message, otherwise keep the existing one
    chat_title = st.session_state.messages[0]["content"][:30] + "..." if len(st.session_state.messages) > 0 else "New Chat"

    # Save to database
    database.save_chat(st.session_state.session_id, chat_title, st.session_state.messages, files)
    st.write("DEBUG: Saved messages:", st.session_state.messages)  # Shows what was saved
    if is_new_chat:
        st.rerun()