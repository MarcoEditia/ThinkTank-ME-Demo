import streamlit as st
import database
import llm_client
import datetime
from pathlib import Path

# Initialize the DB when the app starts
database.init_db()

# --- PAGE CONFIG & SESSION STATE ---
st.set_page_config(page_title="LLM Demo", page_icon="🤖")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

def process_files(files):
    if not files:
        return []
    file_list = []
    for file in files:
        st.write(file)
        file_name = file.name
        file_id = file.file_id

        # file.type returns something like "image/png", "application/pdf"
        # mime_type: "image" and file_type: "png"
        mime_type, file_type = file.type.split('/')
        
        file_data = {
            "name": file_name, 
            "id": file_id, 
            "mime": mime_type, 
            "type": file_type
        }

        file_list.append(file_data)

    #list of dictionary
    return file_list

def render_files(file_data, path=None):
    for file in file_data or []:
        # path = True means render from database
        if(path):
            name = file["name"]
            safe_name = name.replace("/", "_").replace(" ", "_")
            fid = file["id"]
            mime_type = file["mime"]
            file_type = file["type"]
            input = path / f"{fid}-{safe_name}"
        # else render straight from the streamlit chat_input
        else:
            name = file.name
            mime_type, file_type = file.type.split('/')
            input = file

        st.write(f"Attached: {name}")

        if mime_type == "image":
            try:
                st.image(input, caption=name)
            except Exception:
                st.error(f"(couldn't render image at {input})")
        elif mime_type == "video":
            try:
                st.video(input, format=f"{mime_type}/{file_type}")
            except Exception:
                st.error(f"(couldn't render video at {input})")
        elif mime_type == "audio":
            try:
                st.video(input, format=f"{mime_type}/{file_type}")
            except Exception:
                st.error(f"(couldn't render audio at {input})")
        elif mime_type == "application":
            try:
                st.pdf(input)
            except Exception:
                st.error(f"(couldn't render application at {input})")
        else:
            st.error(f"File not supported")

# --- SIDEBAR  ---
# Only loads the IDs and Titles
sidebar_chats = database.get_sidebar_chats()

with st.sidebar:
    st.markdown("ThinkTank-ME")
    
    if st.button("New Chat", width="stretch"):
        st.session_state.messages = []
        st.session_state.session_id = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        st.rerun()
    with st.container():

        # display chat history
        st.markdown("Recents")

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

# --- MAIN UI AND LOGIC ---
# Render the existing chat/chat history from the database
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("files"):
            dir_path = Path("media")/st.session_state.session_id
            st.write("directory path:", dir_path)
            render_files(message["files"], dir_path)

if prompt := st.chat_input("Ask a question..." ,accept_file="multiple", file_type=["pdf", "image", "audio", "video"]):
    text = prompt.text or ""
    files = prompt.files or None

    with st.chat_message("user"):
        st.markdown(text)
        # render the file into the chat from streamlit cache
        if files:
            render_files(files)

    file_data = process_files(files)
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
