# module/ExternalAI_API.py
import requests
import json

OPENROUTER_API = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_API_KEY = "Bearer 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"

def call_openrouter_chat(messages, model="deepseek/deepseek-r1-0528-qwen3-8b:free", stream=False):
    """
    Gọi OpenRouter API với messages.
    """
    payload = {
        "model": model,
        "messages": messages,
        "stream": stream
    }
    headers = {
        "Authorization": OPENROUTER_API_KEY,
        "Content-Type": "application/json"
    }
    resp = requests.post(OPENROUTER_API, headers=headers, data=json.dumps(payload))
    resp.raise_for_status()
    data = resp.json()
    # Lấy nội dung trả về từ message đầu tiên
    return data["choices"][0]["message"]["content"]

def ask_openrouter_with_guide(user_text, guide_content, model="google/gemma-3-12b-it:free"):
    """
    Gửi prompt tới OpenRouter dựa trên guide_content và user_text.
    """
    prompt = (
        "Based on the following information about the system and user guide:\n"
        f"{guide_content}\n"
        f"Please provide a concise and accurate answer to the user's question: \"{user_text}\""
    )
    messages = [
        {"role": "system", "content": "You are an assistant supporting users based on the system guide."},
        {"role": "user", "content": prompt}
    ]
    return call_openrouter_chat(messages, model=model)