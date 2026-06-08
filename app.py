import uuid
import streamlit as st

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
        
initialize_session_state()

st.title("🎙️ AI E-Commerce Customer Support Voice Bot")
