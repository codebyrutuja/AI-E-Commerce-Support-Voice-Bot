
import os
import re
from dotenv import load_dotenv
from sarvamai import SarvamAI


SYSTEM_PROMPT = (
    "You are a helpful e-commerce customer support assistant. "
    "Answer with a single direct customer-facing response. "
    "Do not include analysis, internal reasoning, planning, or debugging notes. "
    "Do not show steps, drafts, or any text intended for developers. "
    "Return only the final answer text in one or two short sentences unless the user explicitly asks for more detail."
)

MODEL_NAME = "sarvam-105b"

def get_sarvam_client():
    """Get fresh Sarvam client with reloaded API key."""
    load_dotenv(override=True)  # Force reload from disk
    api_key = os.getenv("SARVAM_API_KEY")
    if not api_key:
        raise ValueError("SARVAM_API_KEY not found in .env")
    return SarvamAI(api_subscription_key=api_key)



def get_llm_response(user_query, chat_history=None):
        client = get_sarvam_client()
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
        ]
        if chat_history:
            messages.extend(chat_history)
        messages.append({"role": "user", "content": user_query})

        response = client.chat.completions(
            messages=messages,
            model=MODEL_NAME,
            temperature=0.0,
            reasoning_effort="low",
            max_tokens=1200,
        )

        


