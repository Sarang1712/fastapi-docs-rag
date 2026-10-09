import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
_client = None

def generate_answer(system, user):
    global _client
    if _client is None:
        _client = Groq(api_key=os.environ["GROQ_API_KEY"])
    resp = _client.chat.completions.create(
        model=os.environ["GROQ_MODEL"],
        messages=[{"role": "system", "content": system},
                  {"role": "user", "content": user}],
        temperature=0,
        max_tokens=2000,
    )
    return resp.choices[0].message.content.strip()