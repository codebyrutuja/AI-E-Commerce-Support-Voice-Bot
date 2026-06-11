from services.llm_providers.providers.sarvam import get_llm_response as sarvam_response
from services.llm_providers.providers.gemini import get_llm_response as gemini_response
from services.llm_providers.providers.huggingface import get_llm_response as hf_response



def get_llm_response(user_query, chat_history=None, providers=None):
    #print("MANAGer CALLESd")
    if providers == "sarvam":
        #print("sarvam called")
        return sarvam_response(
            user_query,
            chat_history
        )
    elif providers == "huggingface":
        #print("hugging face called")
        return hf_response(
            user_query,
            chat_history
        )
    else:
        #print("gemini called")
        return gemini_response(
            user_query,
            chat_history
        )