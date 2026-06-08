import os
from dotenv import load_dotenv
from sarvamai import SarvamAI

import base64
import tempfile

def get_sarvam_client():
    """Get fresh Sarvam client with reloaded API key."""
    load_dotenv(override=True)  # Force reload from disk
    api_key = os.getenv("SARVAM_API_KEY")
    if not api_key:
        raise ValueError("SARVAM_API_KEY not found in .env")
    return SarvamAI(api_subscription_key=api_key)




def text_to_speech(text):
    try:
        client = get_sarvam_client()
        response = client.text_to_speech.convert(
            text=text,
            target_language_code="en-IN",
            speaker="anushka",
            model="bulbul:v2",
            output_audio_codec="mp3"
        )

        # Sarvam returns audio as list of base64 strings in 'audios'
        if not response.audios or len(response.audios) == 0:
            return "Error: No audio response from Sarvam TTS."
            
        audio_data = base64.b64decode(response.audios[0])

        # Save temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
            f.write(audio_data)
            audio_path = f.name

        return audio_path

    except Exception as e:
        error_text = str(e)
        if "invalid_api_key_error" in error_text or "Invalid or missing authentication credentials" in error_text:
            return "Error: Invalid SARVAM_API_KEY. Please check your .env file and key permissions."
        return f"Error: {error_text}"
