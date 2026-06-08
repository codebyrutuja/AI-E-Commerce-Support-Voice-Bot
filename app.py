import uuid
import streamlit as st

st.set_page_config(
    page_title="E-Commerce Voice Bot",
    page_icon="🎙️",
    layout="wide"
)


def initialize_session_state():
    if "turn_count" not in st.session_state:
        st.session_state.turn_count = 0
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())[:8]
    if "conversation_status" not in st.session_state:
        st.session_state.conversation_status = "Ready for audio input."
    
        
def reset_conversation():
    st.session_state.chat_history = []
    st.session_state.turn_count = 0
    st.session_state.session_id = str(uuid.uuid4())[:8]
    st.session_state.conversation_status = "New conversation started."
    st.session_state.current_transcript = ""
    st.session_state.current_response = ""
    st.session_state.last_audio_path = None

def build_message_history():
    return [
        {"role": item["role"], "content": item["content"]}
        for item in st.session_state.chat_history
    ]
    

def process_user_turn(user_text):
    st.session_state.current_transcript = user_text
    st.session_state.current_response = ""
    st.session_state.last_audio_path = None

    messages = build_message_history()
    response = get_llm_response(user_text, chat_history=messages)
    if not response:
        response = "Error: No response received from assistant."

    st.session_state.current_response = response
    append_turn("user", user_text)
    append_turn("assistant", response)
    st.session_state.turn_count += 1
    st.session_state.conversation_status = "Last turn completed successfully."

    audio_path = None
    if not response.startswith("Error:"):
        audio_path = text_to_speech(response)
        if audio_path and not audio_path.startswith("Error"):
            st.session_state.last_audio_path = audio_path
        else:
            audio_path = audio_path

    return response, audio_path


initialize_session_state()

st.title("🎙️ AI E-Commerce Customer Support Voice Bot")


status_col, control_col = st.columns([3, 1])
with status_col:
    st.markdown("---")
    st.markdown("### Conversation Status")
    st.info(st.session_state.conversation_status)
    st.write(f"**Session ID:** {st.session_state.session_id}")
    st.write(f"**Turns:** {st.session_state.turn_count}")
    
    
with control_col:
    if st.button("Start New Conversation", key="new_conversation"):
        reset_conversation()
        st.experimental_rerun()
        
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
        if st.form_submit_button("Ask Question") and custom_question.strip():
            process_user_turn(custom_question.strip())