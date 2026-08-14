import streamlit as st

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