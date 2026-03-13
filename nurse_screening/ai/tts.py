"""
ai/tts.py

Text-to-speech via smallest.ai Lightning V2 (primary).
Fallback: gTTS.
"""

import io
import wave

import requests

from config import SMALLEST_API_KEY

_TTS_URL  = "https://waves-api.smallest.ai/api/v1/lightning-v2/get_speech"

# Voice IDs from smallest.ai lightning-v2
VOICE_MAP = {
    "en": "emily",
    "es": "isabel",
    "hi": "arjun",
    "fr": "claire",
    "ar": "omar",
    "de": "hans",
    "pt": "lucia",
}


def speak(text: str, language: str = "en") -> bytes:
    """
    Converts text to speech using smallest.ai Lightning V2.
    Returns WAV audio bytes, or empty bytes on failure.
    """
    if not text.strip():
        return b""

    voice_id = VOICE_MAP.get(language, "emily")

    try:
        response = requests.post(
            _TTS_URL,
            headers={
                "Authorization": f"Bearer {SMALLEST_API_KEY}",
                "Content-Type":  "application/json",
            },
            json={
                "text":          text,
                "voice_id":      voice_id,
                "language":      language,
                "sample_rate":   24000,
                "output_format": "wav",
            },
            timeout=20,
        )
        response.raise_for_status()
        print(f"[TTS] smallest.ai ({language}, voice={voice_id}): {text[:60]}...")
        return response.content

    except requests.RequestException as e:
        print(f"[TTS] smallest.ai error: {e}. Falling back to gTTS...")
        return _speak_gtts(text, language)


def _speak_gtts(text: str, language: str) -> bytes:
    """gTTS fallback (pip install gtts pydub)."""
    try:
        from gtts import gTTS
        from pydub import AudioSegment

        tts = gTTS(text=text, lang=language)
        mp3_buf = io.BytesIO()
        tts.write_to_fp(mp3_buf)
        mp3_buf.seek(0)
        audio = AudioSegment.from_mp3(mp3_buf)
        wav_buf = io.BytesIO()
        audio.export(wav_buf, format="wav")
        print(f"[TTS/gTTS] ({language}): {text[:60]}...")
        return wav_buf.getvalue()

    except ImportError:
        print("[TTS] gTTS/pydub not installed: pip install gtts pydub")
        return b""
    except Exception as e:
        print(f"[TTS] gTTS error: {e}")
        return b""
