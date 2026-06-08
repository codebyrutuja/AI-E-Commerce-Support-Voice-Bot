
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

        
def clean_assistant_response(text):
    """Minimal cleaning - remove obvious thinking tags and prompt fragments."""
    if not text:
        return ""
    text = re.sub(r"<think>[\s\S]*?</think>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^[Ff]inal answer[:\s]*", "", text)
    return text.strip()



def _looks_like_valid_answer(text):
    if not text:
        return False
    stripped = text.strip()
    lower = stripped.lower()
    if not stripped:
        return False
    if lower.startswith(('1.', '2.', '*', '-', '•', '`')):
        return False
    if any(token in lower for token in [
        'analyze', 'analysis', 'reasoning', 'draft', 'critique', 'identify', 'steps', 'internal', 'planning',
        'persona', 'constraints', 'strategy', 'option', 'best option', 'formulate', 'review'
    ]):
        return False
    if 'do not' in lower and ('analysis' in lower or 'reasoning' in lower or 'steps' in lower):
        return False
    if len(stripped) > 250 and stripped.count('\n') > 1:
        return False
    return True