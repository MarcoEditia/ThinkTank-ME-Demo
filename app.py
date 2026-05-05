import streamlit as st
import database
import datetime

# Initialize the DB when the app starts
database.init_db()

# --- PAGE CONFIG & SESSION STATE ---
st.set_page_config(page_title="LLM Demo", page_icon="🤖")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

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

if prompt := st.chat_input("Ask a question..."):
    # Render and save user prompt
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Mock LLM Response
    response = f"ThinkTank-ME: {prompt}"
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
