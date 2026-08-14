import streamlit as st
import datetime
from pathlib import Path
import re
from urllib.parse import urlparse

import database
from utils import file_utils
import llm_client

# --- PAGE CONFIG & SESSION STATE --- 
st.set_page_config(page_title="Polymarket Forecast Demo", page_icon="📈")

# Initialize the DB when the app starts
database.init_db()


# css
def load_css(file_path):  
    with open(file_path) as f:
        st.html(f"<style>{f.read()}</style>")


css_path = Path(".streamlit/styles.css")
load_css(css_path)

if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
if "session_url" not in st.session_state:
    st.session_state.session_url = ""
if "available_markets" not in st.session_state:
    st.session_state.available_markets = []
if "chat_title" not in st.session_state:
    st.session_state.chat_title = ""

# --- SIDEBAR  ---
# Only loads the IDs and Titles
sidebar_chats = database.get_sidebar_chats()

with st.sidebar:
    if st.button("New Chat", width="stretch"):
        st.session_state.messages = []
        st.session_state.session_id = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        st.session_state.session_url = ""
        st.session_state.available_markets = []
        st.session_state.chat_title = ""
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

                        messages, url, available_markets, chat_title = database.get_chat_messages(session_id)
                        st.session_state.messages = messages 
                        st.session_state.session_url = url
                        st.session_state.available_markets = available_markets
                        st.session_state.chat_title = chat_title

                        # FORCE UPDATE the widget key directly so the UI displays the loaded URL!
                        st.session_state["top_url_input"] = url or ""
                        st.rerun() 
            else:
                st.write("No history yet.")

# --- TOP INPUT PANEL ---
with st.container(border=True):
    # Split top row into two columns (2:1 ratio)
    col1, col2 = st.columns([2, 1])

    with col1:
        input_url = st.text_input(
            "Polymarket URL",
            value=st.session_state.session_url or "",
            placeholder="https://polymarket.com/event/...",
            key="top_url_input"
        )

    with col2:
        market_options = []
        if st.session_state.available_markets:
            market_options = [m.get("question", f"Market {i}") for i, m in enumerate(st.session_state.available_markets)]

        selected_market = st.selectbox(
            "Select Market",
            options=market_options,
            key="top_market_select"
        )

    # # Multi-select toggle pills
    # selected_modes = st.pills(
    #     label="Analysis Modes",
    #     options=[
    #         "🌐 Use Web Evidence",
    #         "📊 Use Market Signals",
    #         "👤 Use Domain Expert",
    #         "⚖️ Contrarian View"
    #     ],
    #     default=["🌐 Use Web Evidence", "📊 Use Market Signals", "👤 Use Domain Expert"],
    #     selection_mode="multi",
    #     label_visibility="collapsed"
    # )

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

# Process user inputs
URL_REGEX = r'(https?://[^\s;,\s]+)'
text = ""
files = []

prompt = st.chat_input(
    "Paste a Polymarket URL and optional market name...",
    accept_file="multiple",
    file_type=["pdf", "image", "audio", "video"]
)

if top_submit and input_url:
    # only take the url that the user paste 
    text =  input_url
    if selected_market:
        text = f"{input_url} {selected_market}"
    files = [] 
elif prompt:
    # takes both the url and other stuff that the user paste
    text = prompt.text or ""
    files = prompt.files or None

if text:
    found_urls = re.findall(URL_REGEX, text)
    primary_url = found_urls[0] if found_urls else ""
    
    # Verify and inspect via backend API
    if not st.session_state.session_url:
        if primary_url:
            inspect_result = llm_client.inspect_url(primary_url)
        
            if inspect_result["is_valid"]:
                st.session_state.session_url = primary_url
                st.session_state.available_markets = inspect_result["available_markets"]
                st.session_state.chat_title = inspect_result["contract"]["question"]
                
    else:
        if primary_url and primary_url.rstrip("/") != st.session_state.session_url.rstrip("/"):
            st.warning(
                "⚠️ **Market Locked to Current Session**\n\n"
                f"This chat is already analyzing: `{st.session_state.session_url}`\n\n"
                "To forecast a new market, please click **'New Chat'** in the sidebar."
            )
            st.stop()

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
            result = llm_client.query_model(messages_array=st.session_state.messages, session_url=st.session_state.session_url)
            response_text = result["content"]
            reasoning_text = result["reasoning"]

        if reasoning_text:
            with st.expander("💭 View Thinking Process"):
                st.markdown(reasoning_text)

        st.markdown(response_text)

    st.session_state.messages.append({"role": "assistant", "content": response_text})
    is_new_chat = len(st.session_state.messages) == 2

    # Generate Title if it's the first message, otherwise keep the existing one
    if len(st.session_state.messages) > 0:
        if (st.session_state.chat_title):
            chat_title = st.session_state.chat_title
        else:
            chat_title = "Invalid URL"
    else: 
        chat_title = "New Chat"

    # Save to database
    database.save_chat(
        session_id=st.session_state.session_id,
        title=chat_title,
        messages_array=st.session_state.messages,
        url=st.session_state.session_url,
        available_markets=st.session_state.available_markets,
        files=files
    )
    st.write("DEBUG: Saved messages:", st.session_state.messages)  # Shows what was saved
    
    if is_new_chat:
        st.rerun()