import os
from dotenv import load_dotenv
from google import genai
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
MODEL_PRICING = {
    "gemini-2.5-flash-lite": {
        "input_price": 8.30,   # ₹ per 1M input tokens
        "output_price": 33.20  # ₹ per 1M output tokens
    }
}

def get_llm_response(user_query, chat_history=None):
    try:
        load_dotenv()

        api_key = os.getenv("GEMINI_API_KEY")

        client = genai.Client(api_key=api_key)

        full_prompt = f"""
            {SYSTEM_PROMPT}

        Customer Question:
        {user_query}
        """
        

        response = client.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=full_prompt
        )



        usage = getattr(response, "usage_metadata", None)

        print("\n========== GEMINI USAGE ==========")
        print(usage)

        cost = 0
        total_tokens = 0

        if usage:
            prompt_tokens = usage.prompt_token_count
            completion_tokens = usage.candidates_token_count
            total_tokens = usage.total_token_count

            cost = calculate_cost(
                "gemini-2.5-flash-lite",
                prompt_tokens,
                completion_tokens
                )

        return {
            "message": response.text,
            "cost": cost,
            "total_tokens": cost
        }
        
    except Exception as e:
        error_text = str(e)

        if "insufficient_quota_error" in error_text:
            return {
                "message": (
                "GEMINI credits exhausted. "
                "Please switch to other model"
            ),
            "cost": 0,
            "total_tokens": 0
             }

        return {
            "message": f"Sarvam Error: {error_text}",
            "cost": 0,
            "total_tokens": 0
        }


        
        

def calculate_cost(model_name, prompt_tokens, completion_tokens):
    pricing = MODEL_PRICING[model_name]

    input_cost = (
        prompt_tokens / 1_000_000
    ) * pricing["input_price"]

    output_cost = (
        completion_tokens / 1_000_000
    ) * pricing["output_price"]

    total_cost = input_cost + output_cost

    return round(total_cost, 6)