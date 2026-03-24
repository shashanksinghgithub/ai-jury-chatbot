import requests

API_KEY = "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"

url = "https://openrouter.ai/api/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

data = {
    "model": "openai/gpt-4o-mini",
    "messages": [
        {"role": "user", "content": "Say hello"}
    ]
}

response = requests.post(url, headers=headers, json=data)

print(response.json())