import os
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

load_dotenv()

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
2. Keep responses under 4 sentences unless more detail is requested.
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
International shipping: Yes, we ship to select international destinations. International delivery typically takes 7-14 business days, and shipping charges may vary depending on the destination.

Always prioritize accuracy and customer satisfaction.
"""

MODEL_NAME = "meta-llama/Llama-3.1-8B-Instruct"

MODEL_PRICING = {
    "Llama-3.1-8B-Instruct": {
        "input_price": 0.02,   # USD per 1M input tokens
        "output_price": 0.05   # USD per 1M output tokens
    }
}

def get_llm_response(user_query, chat_history=None):
    try:
        client = InferenceClient(
            api_key=os.getenv("HF_TOKEN")
        )

        messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            }
        ]

        if chat_history:
            messages.extend(chat_history)

        messages.append({
            "role": "user",
            "content": user_query
        })

        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            max_tokens=500
        )
        
        usage = getattr(response, "usage", None)

        cost = 0
        total_tokens = 0

        if usage:
            prompt_tokens = usage.prompt_tokens
            completion_tokens = usage.completion_tokens
            total_tokens = usage.total_tokens

            cost = calculate_cost(
                prompt_tokens,
                completion_tokens
            )

            print("Prompt Tokens:", prompt_tokens)
            print("Completion Tokens:", completion_tokens)
            print("Total Tokens:", total_tokens)
            print("Cost:", cost)

        return {
            "message": response.choices[0].message.content,
            "cost": cost,
            "total_tokens": cost
        }

    except Exception as e:
        error_text = str(e)
        if "insufficient_quota_error" in error_text:
            return {
                "message": (
                    "Hugging Face credits exhausted. "
                    "Please switch to Other models"
                ),
                "cost": 0,
                "total_tokens": 0
                }

        return {
            "message": f"Sarvam Error: {error_text}",
            "cost": 0,
            "total_tokens": 0
        }
        
def calculate_cost(prompt_tokens, completion_tokens):

    input_cost = (
        prompt_tokens / 1_000_000
    ) * 0.02

    output_cost = (
        completion_tokens / 1_000_000
    ) * 0.05

    return round(input_cost + output_cost, 6)



if __name__ == "__main__":

    response = get_llm_response(
        "What is your return policy?"
    )

    print(response)