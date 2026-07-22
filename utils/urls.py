import streamlit as st
from urllib.parse import urlparse

def process_urls(urls):  
    parsed_urls = []
    for raw_url in urls or []:
        try:
            parsed = urlparse(raw_url)

            # Check if it has a valid domain (e.g., google.com, libconference.org)
            if parsed.netloc:
                st.success(f"Successfully isolated URL: `{raw_url}`")

                # Show the breakdown to the user
                st.write(f" **Domain (Netloc):** {parsed.netloc}")
                st.write(f" **Path to File:** {parsed.path}")
                parsed_urls.append(raw_url)
            else:
                st.error(f"{raw_url} is not a valid domain address.")

        except Exception:
            st.error("Failed to parse the link accurately.")

    return parsed_urls