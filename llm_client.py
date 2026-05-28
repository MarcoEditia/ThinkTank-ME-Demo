import os
import requests

LLM_API_URL = os.getenv("LLM_API_URL", "http://localhost:8000")
LLM_MODEL = os.getenv("LLM_MODEL", "qwen3.5-9b")

def payload(messages_array):
    # only text for now
    text_history = []
    for msg in messages_array:
        text_history.append({
            "role": msg["role"],
            "content": msg["content"] 
        })
    return text_history

def query_model(messages_array):
    url = f"{LLM_API_URL}/v1/chat/completions"
    
    # Run the history through the text filter
    messages_payload = payload(messages_array)
    
    api_payload = {
        "model": LLM_MODEL,
        "messages": messages_payload,
        "temperature": 0.7, 
        "stream": False,
    }
    
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(url, json=api_payload, headers=headers)
        response.raise_for_status()
        raw_content = response.json()['choices'][0]['message']['content']
        
        # If the model uses a thinking, split it
        if "</think>" in raw_content:
            parts = raw_content.split("</think>", 1)
            # Clean up any tags
            reasoning = parts[0].replace("<think>", "").replace("Thinking Process:\n\n", "").strip()
            clean_content = parts[1].strip()
        else:
            reasoning = ""
            clean_content = raw_content
            
        return {"content": clean_content, "reasoning": reasoning}
        
    except Exception as e:
        return {"content": f"Inference API Error: {str(e)}", "reasoning": ""}