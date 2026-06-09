import os
import re
from dotenv import load_dotenv
from sarvamai import SarvamAI

def get_sarvam_client():
    """Get fresh Sarvam client with reloaded API key."""
    load_dotenv(override=True)  # Force reload from disk
    api_key = os.getenv("SARVAM_API_KEY")
    if not api_key:
        raise ValueError("SARVAM_API_KEY not found in .env")
    return SarvamAI(api_subscription_key=api_key)

SYSTEM_PROMPT = ( 
                "You are a helpful e-commerce customer support assistant. "
                "Answer with a single direct customer-facing response. " 
                "Do not include analysis, internal reasoning, planning, or debugging notes. " 
                "Do not show steps, drafts, or any text intended for developers. " 
                "Return only the final answer text sentences." "You are an AI E-commerce Assistant." 
                "Your job is ONLY to answer questions related to: Products, Orders, Shipping , Returns, Refunds, Payments, Inventory, Customer support" "If a user asks anything outside e-commerce, reply exactly:" "I'm sorry, I can only assist with e-commerce related questions such as products, orders, shipping, returns, and payments." "Do not answer general knowledge questions, politics, history, sports, science, or any topic unrelated to e-commerce." )

MODEL_NAME = "sarvam-105b"

#to remove thinking of response
def clean_assistant_response(text):
    """Minimal cleaning - remove obvious thinking tags and prompt fragments."""
    if not text:
        return ""
    text = re.sub(r"<think>[\s\S]*?</think>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^[Ff]inal answer[:\s]*", "", text) 
    return text.strip()

#validation function that checks whether the AI response is a meaningful answer



def _looks_like_valid_answer(text):
    if not text:
        return False
    stripped = text.strip()
    
    lower = stripped.lower()
    
    if not stripped:
        return False
    if lower.startswith(('1.', '2.', '*', '-', '•', '`')):
        return False
    if any(token in lower for token in [ #atleast 1 condition true
        'analyze', 'analysis', 'reasoning', 'draft', 'critique', 'identify', 'steps', 'internal', 'planning',
        'persona', 'constraints', 'strategy', 'option', 'best option', 'formulate', 'review'
    ]):
        return False
    if 'do not' in lower and ('analysis' in lower or 'reasoning' in lower or 'steps' in lower):
        return False
    if len(stripped) > 250 and stripped.count('\n') > 1:
        return False
    return True


def _extract_final_answer_from_reasoning(text):
    if not text:
        return None

    final_answer_match = re.search(r"(?:final answer|answer|response)[:\-]\s*(.+)$", text, flags=re.IGNORECASE | re.DOTALL)
    if final_answer_match:
        candidate = final_answer_match.group(1).strip()
        if candidate and _looks_like_valid_answer(candidate):
            return candidate

    paragraphs = [p.strip() for p in re.split(r"\n\n+", text) if p.strip()]
    for paragraph in reversed(paragraphs[-3:]):
        if _looks_like_valid_answer(paragraph):
            return paragraph
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for line in reversed(lines[-5:]):
        if _looks_like_valid_answer(line):
            return line
    return None


def _extract_choice_text(choice):
    if choice is None:
        return None

    message = getattr(choice, "message", None)
    if message is not None:
        content = getattr(message, "content", None)
        if content and isinstance(content, str) and content.strip() and _looks_like_valid_answer(content):
            return content.strip()

        # Only consider reasoning_content if it looks like a direct final answer,
        # not an internal analysis trace.
        reasoning = getattr(message, "reasoning_content", None)
        if reasoning and isinstance(reasoning, str) and reasoning.strip():
            answer = _extract_final_answer_from_reasoning(reasoning)
            if answer:
                return answer

        refusal = getattr(message, "refusal", None)
        if refusal:
            if hasattr(refusal, "content"):
                refusal_content = getattr(refusal, "content", None)
                if refusal_content and isinstance(refusal_content, str) and refusal_content.strip():
                    return refusal_content.strip()
            if isinstance(refusal, str) and refusal.strip():
                return refusal.strip()

    if hasattr(choice, "content"):
        content = getattr(choice, "content")
        if content and isinstance(content, str) and content.strip() and _looks_like_valid_answer(content):
            return content.strip()

    if hasattr(choice, "text"):
        text = getattr(choice, "text")
        if text and isinstance(text, str) and text.strip() and _looks_like_valid_answer(text):
            return text.strip()

    return None


def get_llm_response(user_query, chat_history=None):
    
    try:
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

        if hasattr(response, "choices") and response.choices:
            content = _extract_choice_text(response.choices[0])
            if content:
                return clean_assistant_response(content)
            return "Error: LLM returned empty response. Please try again."

        return "Error: No assistant response returned from Sarvam."
    except Exception as e:
        error_text = str(e)
        if "invalid_api_key_error" in error_text or "Invalid or missing authentication credentials" in error_text:
            return "Error: Invalid SARVAM_API_KEY. Please check your .env file and key permissions."
        return f"Error: {error_text}"

