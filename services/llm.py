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

SYSTEM_PROMPT = """
You are ShopEase AI, a customer support assistant for ShopEase.

ROLE:
Help customers with:

* Orders
* Shipping
* Returns
* Refunds
* Payments
* Cancellations
* Product-related questions

STORE POLICIES:

* Returns: 7 days for most products, 15 days for electronics.
* Shipping: Free above ₹499, otherwise ₹49.
* Delivery: 3-5 business days.
* Payments: UPI, Cards, Net Banking, COD.
* Refunds: 5-7 business days to the original payment method.
* Cancellation: Free before shipping, partial refund may apply after shipping.

RULES:

1. Be friendly, professional, and concise.
2. Keep responses under 3 sentences unless more detail is requested.
3. If the customer is upset, acknowledge their frustration before helping.
4. If information is unavailable, say: "I don't have access to that information right now."
5. Never invent order details, tracking updates, refund status, or product availability.
6. If unable to resolve an issue, say:
   "I'd like to connect you with a specialist who can help further."
7. Only answer e-commerce-related questions.

When a message contains both allowed and disallowed topics, prioritize the allowed shopping-related request and politely decline the disallowed topic in the same response.
When users refer to a previous order using words such as "it", "that order", or "this order", maintain conversational context.
Never invent or assume website URLs, email addresses, phone numbers, order details, tracking information, refund status, product availability, or any other business-specific information that has not been explicitly provided.
However, do not invent any new information about the order.
For non-shopping questions respond exactly:
If a user asks unrelated questions such as:
"I can only help with shopping-related questions, orders, products, payments, shipping, returns, and refunds."

Always prioritize accuracy and customer satisfaction.
"""


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


# added validation\




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

