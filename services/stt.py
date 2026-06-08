import os
import tempfile

from dotenv import load_dotenv
from sarvamai import SarvamAI

def get_sarvam_client():
    """Get fresh Sarvam client with reloaded API key."""
    load_dotenv(override=True)  # Force reload from disk
    api_key = os.getenv("SARVAM_API_KEY")
    if not api_key:
        raise ValueError("SARVAM_API_KEY not found in .env")
    return SarvamAI(api_subscription_key=api_key)

def transcribe_audio(uploaded_file):
    temp_file_path = None
    try:
        client = get_sarvam_client()  # initialize the client

        file_name = getattr(uploaded_file, "name", None) or "upload.wav"
        file_ext = os.path.splitext(file_name)[1] or ".wav"

        # ensure uploaded_file pointer is at start
        try:
            uploaded_file.seek(0)
        except Exception:
            pass

        with temp_file.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
            temp_file.write(uploaded_file.read())
            temp_file_path = temp_file.name

        with open(temp_file_path, "rb") as audio_file:
            response = client.speech_to_text.transcribe(
                file=audio_file,
                model="saaras:v3",
                mode="transcribe"
            )

        # Support multiple possible response shapes
        transcript = None
        if hasattr(response, "transcript"):
            transcript = getattr(response, "transcript")
        elif isinstance(response, dict):
            transcript = response.get("transcript") or response.get("text") or response.get("content")
        elif hasattr(response, "choices") and response.choices:
            choice = response.choices[0]
            transcript = getattr(choice, "text", None) or getattr(choice, "content", None)

        if transcript:
            return transcript
        return "Error: Transcription returned empty result."

    except Exception as e:
        error_text = str(e)
        if "invalid_api_key_error" in error_text or "Invalid or missing authentication credentials" in error_text:
            return "Error: Invalid SARVAM_API_KEY. Please check your .env file and key permissions."
        return f"Error: {error_text}"
    finally:
        if temp_file_path:
            try:
                os.remove(temp_file_path)
            except Exception:
                pass