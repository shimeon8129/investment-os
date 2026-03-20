import requests
import os
import json

API_KEY = os.getenv("OPENAI_API_KEY")

def call_gpt(prompt):

    url = "https://api.openai.com/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    system_prompt = """
You must output ONLY valid JSON.

Format:
{
  "topic": "AI/TSMC/Memory/Server/Packaging/Other",
  "sentiment": "positive/neutral/negative",
  "strength": 0-100,
  "summary": "short summary"
}
"""

    data = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3
    }

    response = requests.post(url, headers=headers, json=data, timeout=10)
    print("RAW RESPONSE:", response.text)
    result = response.json()

    content = result["choices"][0]["message"]["content"]

    return json.loads(content)
