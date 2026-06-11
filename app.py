from urllib import response
import uuid
import streamlit as st

from services.llm_providers.manager import get_llm_response

from services.stt import transcribe_audio
from services.tts import text_to_speech

st.set_page_config(
    page_title="E-Commerce Voice Bot",
    page_icon="🎙️",
    layout="wide"
)


def initialize_session_state():
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "turn_count" not in st.session_state:
        st.session_state.turn_count = 0
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())[:8]
    if "conversation_status" not in st.session_state:
        st.session_state.conversation_status = "Ready for audio input."
    if "current_transcript" not in st.session_state:
        st.session_state.current_transcript = ""
    if "current_response" not in st.session_state:
        st.session_state.current_response = ""
    if "last_audio_path" not in st.session_state:
        st.session_state.last_audio_path = None
        
    if "current_cost" not in st.session_state:
        st.session_state.current_cost = 0.0
    if "current_tokens" not in st.session_state:
        st.session_state.current_tokens = 0
        
    if "selected_model" not in st.session_state:
        st.session_state.selected_model = "sarvam"
        
    if "chat_sessions" not in st.session_state:
        st.session_state.chat_sessions = {}
        
    if "current_chat_id" not in st.session_state:
        st.session_state.current_chat_id = str(uuid.uuid4())[:8]
        

    if "previous_model" not in st.session_state:
        st.session_state.previous_model = "sarvam"
   
        
        
        
def reset_conversation():
    st.session_state.chat_history = []
    st.session_state.turn_count = 0
    st.session_state.session_id = str(uuid.uuid4())[:8]
    st.session_state.conversation_status = "New conversation started."
    st.session_state.current_transcript = ""
    st.session_state.current_response = ""
    st.session_state.last_audio_path = None


def create_new_chat_session(model_name):

    st.session_state.chat_history = []

    st.session_state.turn_count = 0

    st.session_state.session_id = str(uuid.uuid4())[:8]

    st.session_state.current_transcript = ""

    st.session_state.current_response = ""
    
    st.session_state.last_audio_path = None

    st.session_state.selected_model = model_name

    st.session_state.conversation_status = (
        f"New chat session started with {model_name}"
    )
    
     
def build_message_history():  
    return [
        {"role": item["role"], "content": item["content"]}
        for item in st.session_state.chat_history
    ]
    
    
# user msg and assistant response stored in chat history
def append_turn(
    role,
    content,
    cost=None,
    tokens=None
    ):
    message = {
        "role": role,
        "content": content,
        "cost": cost,
        "tokens": tokens,
        "model": st.session_state.selected_model
    }
    
    # Current chat history (what you already have)
    st.session_state.chat_history.append(message)

    # Save to session-specific history
    current_chat_id = st.session_state.current_chat_id

    if current_chat_id not in st.session_state.chat_sessions:
        st.session_state.chat_sessions[current_chat_id] = []

    st.session_state.chat_sessions[current_chat_id].append(message)
    
    #print("History Length:", len(st.session_state.chat_history))
    
    


def process_user_turn(user_text):
    st.session_state.current_transcript = user_text
    st.session_state.current_response = ""
    st.session_state.last_audio_path = None
    
    
    messages = build_message_history()
    response = get_llm_response(user_text, chat_history=messages, providers=st.session_state.selected_model)
    if not response:
        response = {
        "message": "Error: No response received from assistant.",
        "cost": 0,
        "total_tokens": 0
    }
    if isinstance(response, str):
        response = {
            "message": response,
            "cost": 0,
            "total_tokens": 0
        }
    
     
    st.session_state.current_response = response["message"]
    
    st.session_state.current_cost = response["cost"]
    st.session_state.current_tokens = response["total_tokens"]
    #st.write("Current Model:", st.session_state.selected_model)
    
     # after LLM generated responsee
    
    append_turn(
    "user",
    user_text
    )

    append_turn(
    "assistant",
    response["message"],
    cost=response["cost"],
    tokens=response["total_tokens"]
    )# adds new message to chat history with role and content
    
    st.session_state.turn_count += 1
    st.session_state.conversation_status = "Last turn completed successfully."
    
    
    audio_path = None
    if not response["message"].startswith("Error:"):
        audio_path = text_to_speech(response["message"])
        if audio_path and not audio_path.startswith("Error"):
            st.session_state.last_audio_path = audio_path
    else:
        audio_path = audio_path

    return response['message'], audio_path


# it is used to create new chat after each session created

def create_chat_session(model):
    chat_id = str(uuid.uuid4())[:8]

    st.session_state.current_chat_id = chat_id

    st.session_state.chat_sessions[chat_id] = {
        "model": model,
        "messages": []
    }

    st.session_state.chat_history = []

    return chat_id


initialize_session_state()

st.title("🎙️ AI E-Commerce Customer Support Voice Bot")


status_col, control_col = st.columns([3, 1])
with status_col:
    st.markdown("---")
    st.markdown("### Conversation Status")
    st.info(st.session_state.conversation_status)
    st.write(f"**Session ID:** {st.session_state.session_id}")
    #st.write(f"**Turn Count:** {st.session_state.turn_count}")
    
    
with control_col:
    if st.button("Start New Conversation", key="new_conversation"):
        reset_conversation()
        
        st.session_state.previous_model = (
            st.session_state.selected_model
        )
        st.rerun()
        
st.markdown("---")

left_col, right_col = st.columns([3, 1])

with left_col:
    st.subheader("🛒 Ecommerce Voice Chat")
    st.write("Ask ecommerce questions, and the bot will reply with text and voice.")
    
    
    suggested_questions = [
        "What is your return policy?",
        "How long does shipping take?",
        "Can I cancel my order?",
        "Do you ship internationally?",
        "What payment methods do you accept?",
        "How do I track my package?"
    ]

    with st.expander("Suggested ecommerce questions", expanded=True):
        for index, question in enumerate(suggested_questions):
            if st.button(question, key=f"suggest_{index}"):
                process_user_turn(question)
                
    with st.form("question_form", clear_on_submit=True):
        custom_question = st.text_input(
            "Type a question",
            key="custom_question",
            placeholder="Ask about returns, shipping, orders, or payments"
        )
        selected_model = st.selectbox(
            "🤖 Select AI Model",
            [  "sarvam",
                "gemini",
                "huggingface"
            ]
        )
        if selected_model != st.session_state.previous_model:
            create_new_chat_session(selected_model)
            st.session_state.previous_model = selected_model
            st.rerun()
        
            
        st.session_state.selected_model = selected_model
        
        st.write("Current Model:", st.session_state.selected_model)
        if st.form_submit_button("Ask Question") and custom_question.strip():
            process_user_turn(custom_question.strip())
            
            
            
    st.markdown("---")
    st.subheader("🎤 Audio Input")
    uploaded_file = st.file_uploader(
        "Upload an audio file (WAV, MP3, M4A)",
        type=["wav", "mp3", "m4a"],
        key="audio_upload"
    )
    
    if uploaded_file:
        st.audio(uploaded_file)
        
        if st.button("Process Audio", key="process_audio"):
            with st.spinner("Transcribing and generating response..."):
                transcript = transcribe_audio(uploaded_file)
                if not transcript:
                    st.error("Error: No transcript received.")
                elif transcript.startswith("Error:"):
                    st.error(transcript)
                else:
                    process_user_turn(transcript)
                    
with right_col:
    st.subheader("Latest Turn")
    
    if st.session_state.current_transcript:
        st.markdown("**User:**")
        st.write(st.session_state.current_transcript)
    
    if st.session_state.current_response:
        st.markdown("**Bot:**")
        st.write(st.session_state.current_response)
        
    st.caption(
        f"Tokens: {st.session_state.current_tokens} | "
        f"Cost: ₹{st.session_state.current_cost:.6f}"
    )
    if st.session_state.last_audio_path:
        st.subheader("🔊 Latest Voice Response")
        st.audio(st.session_state.last_audio_path)
        

#conversaion history
#-----------------------------
    
    st.markdown("---")
    st.subheader("Conversation History")
    if st.session_state.chat_history:
        for index in range(0, len(st.session_state.chat_history), 2):
            user_item = st.session_state.chat_history[index]
            assistant_item = st.session_state.chat_history[index + 1] if index + 1 < len(st.session_state.chat_history) else None
            
            if user_item["role"] == "user":
                st.markdown(f"**{(index // 2) + 1}. 👤 User:** {user_item['content']}")
            else:
                st.markdown(f"**{(index // 2) + 1}. 👤 User:** {user_item['content']}")
# added here chat history for each model used
            if assistant_item and assistant_item["role"] == "assistant":
                model_used = assistant_item.get("model", "Unknown")

                st.caption(f"Model Used: {model_used}")

                st.markdown(f"- 🤖 Assistant: {assistant_item['content']}")

            if assistant_item and assistant_item.get("tokens") is not None:
                st.caption(
                    f"Tokens: {assistant_item['tokens']} | "
                    f"Cost: ₹{assistant_item['cost']:.6f}"
                )
    else:
        st.write("No conversation yet. Ask a question to start the chat.")