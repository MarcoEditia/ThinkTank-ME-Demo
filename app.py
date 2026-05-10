import streamlit as st
import database
import datetime
import requests
import os
import pymupdf4llm
import tempfile

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
# Initialize the DB when the app starts
database.init_db()

# --- PAGE CONFIG & SESSION STATE ---
st.set_page_config(page_title="LLM Demo", page_icon="🤖")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = datetime.datetime.now().strftime("%Y%m%d%H%M%S")


# Function to send a prompt to the local Ollama server and return its response
def query_ollama(prompt, model):
    url = f"{OLLAMA_URL}/api/generate"  # Ollama's local API endpoint
    payload = {
        "model": model,      # Model name (e.g., llama3)
        "prompt": prompt,    # User's input
        "stream": False      # Set to False for full (non-streamed) response
    }
    # Send POST request and return the response text
    response = requests.post(url, json=payload)
    return response.json().get("response", "No response")


def process_files(files):
    """Convert uploaded files into readable text for the LLM prompt."""
    if not files:
        return ""

    extracted_parts = []

    for file in files:
        filename = file.name
        suffix = os.path.splitext(filename)[1] or ".pdf"

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file.write(file.getvalue())
            temp_path = temp_file.name

        try:
            markdown_text = pymupdf4llm.to_markdown(temp_path)
            extracted_parts.append(f"\n\n[FILE: {filename}]\n{markdown_text}")
        finally:
            try:
                os.remove(temp_path)
            except OSError:
                pass

    return "\n".join(extracted_parts).strip()

def build_conversation_prompt(messages, system_msg="You are a helpful assistant"):
    prompt =  "<|begin_of_text|><|start_header_id|>system<|end_header_id|>" + system_msg + ".<|eot_id|>"
    for msg in messages[-10:]:
        st.write(msg)
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if isinstance(content, dict):
            content = content.get("text", "")
        prompt += f"<|start_header_id|>{role}<|end_header_id|>\n\n {content}<|eot_id|>"
    prompt += "<|start_header_id|>assistant<|end_header_id|>"  # Let the model complete
    st.write(prompt)
    return prompt

# --- SIDEBAR  ---
# Only loads the IDs and Titles
sidebar_chats = database.get_sidebar_chats()

with st.sidebar:
    with st.container():
        st.markdown("ThinkTank-ME")
        
        if st.button("New Chat", width="stretch"):
            st.session_state.messages = []
            st.session_state.session_id = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            st.rerun()

        # display chat history
        st.markdown("Chat")

        if sidebar_chats:
            for chat in sidebar_chats:
                session_id = chat[0]
                title = chat[1]
                
                # Create the button
                if st.button(title, key=session_id, width="stretch"):
                    # ON CLICK: get the chat history
                    st.session_state.session_id = session_id
                    st.session_state.messages = database.get_chat_messages(session_id)
                    st.rerun() # Refresh the screen
        else:
            st.write("No history yet.")

# --- MAIN UI AND LOGIC ---
# Render the current chat
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask a question..." ,accept_file="multiple", file_type=["pdf"]):
    #prompt.text = the text and prompt.files = is where the files at  ,accept_file="multiple", file_type=["jpg", "jpeg", "png", "pdf"]
    # Render and save user prompt
    text = prompt.text or ""
    files = prompt.files
    prompt = prompt.text + process_files(files)
    with st.chat_message("user"):
        st.markdown(text)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Build conversation context and query Ollama
    conversation_text = build_conversation_prompt(st.session_state.messages)
    response = query_ollama(conversation_text, "tinyllama")
    with st.chat_message("assistant"):
        st.markdown(response)
    st.session_state.messages.append({"role": "assistant", "content": response})
    is_new_chat = len(st.session_state.messages) == 2

    # Generate Title if it's the first message, otherwise keep the existing one
    chat_title = st.session_state.messages[0]["content"][:30] + "..." if len(st.session_state.messages) > 0 else "New Chat"

    # Save to database
    database.save_chat(st.session_state.session_id, chat_title, st.session_state.messages)
    if is_new_chat:
        st.rerun()
