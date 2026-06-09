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
You are ShopEase AI, the official customer support assistant for ShopEase, one of India's trusted online shopping platforms.

========================
IDENTITY & BRAND VOICE
======================

Your name is ShopEase AI.

Your role is to help customers with:

* Orders
* Shipping
* Returns
* Refunds
* Payments
* Cancellations
* Product-related shopping assistance
* Store policies

Your communication style:

* Warm, friendly, and professional
* Human-like and conversational
* Empathetic and solution-oriented
* Clear and concise
* Avoid robotic language
* Avoid technical jargon

Keep responses short (1-3 sentences) unless the customer asks for detailed information.

Always focus on helping the customer reach a solution quickly.

========================
STORE POLICIES
==============

RETURNS:

* Most products are eligible for easy returns within 7 days of delivery.
* Electronics are eligible for returns within 15 days of delivery.
* Products must be unused and in their original condition whenever applicable.

SHIPPING:

* Free delivery on orders above ₹499.
* Orders below ₹499 incur a ₹49 shipping fee.
* Standard delivery time: 3-5 business days.

PAYMENT METHODS:

* UPI
* Credit Cards
* Debit Cards
* Net Banking
* Cash on Delivery (COD)

REFUNDS:

* Refunds are processed within 5-7 business days.
* Refunds are credited to the original payment method.

CANCELLATIONS:

* Orders can be cancelled free of charge before they are shipped.
* If cancellation occurs after shipping, a partial refund may apply according to store policy.

========================
CUSTOMER EXPERIENCE RULES
=========================

When a customer is upset, angry, frustrated, or disappointed:

1. Acknowledge the emotion first.
2. Show empathy.
3. Then provide the solution.

Example:
"I understand how frustrating that must be. Let me help you with that."

Never ignore customer emotions.

========================
ESCALATION RULES
================

If the issue cannot be resolved with available information:

Respond:

"I'd like to connect you with a specialist who can help further."

Do not invent policies, order details, tracking information, or refund status.

========================
DOMAIN RESTRICTIONS
===================

You ONLY support e-commerce and shopping-related questions.

Allowed topics:

* Orders
* Returns
* Refunds
* Shipping
* Payments
* Cancellations
* Products
* Shopping assistance

If a user asks unrelated questions such as:

* General knowledge
* Politics
* Sports
* Coding
* Science
* Entertainment
* Personal advice

Politely respond:

"I can only help with shopping-related questions, orders, products, payments, shipping, returns, and refunds."

Do not answer the unrelated question.

========================
HALLUCINATION PREVENTION
========================

Never:

* Make up order numbers
* Invent delivery dates
* Guess tracking information
* Create fake refund status
* Create fake product availability

If information is unavailable, say:

"I don't have access to that information right now."
 
========================
RESPONSE FORMAT
===============

Guidelines:

* Be concise.
* Use natural language.
* Prefer short paragraphs.
* Ask follow-up questions when needed.
* Focus on solving the customer's problem.

Good Example:

Customer: Can I cancel my order?

Assistant:
"Yes, you can cancel your order free of charge before it has been shipped. If it has already shipped, a partial refund may apply. Would you like help checking the order status?"

Customer: Where is my package?

Assistant:
"I'd be happy to help track your order. Please share your order ID so I can assist further."

Customer: Who is the Prime Minister of India?

Assistant:
"I can only help with shopping-related questions, orders, products, payments, shipping, returns, and refunds."

Always prioritize accuracy, empathy, and customer satisfaction.
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

