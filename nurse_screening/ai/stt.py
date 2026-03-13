"""
ai/stt.py

Speech-to-text via smallest.ai Pulse (primary).
Fallback: on-device Whisper.

Key API details:
  - Body: raw audio bytes as application/octet-stream (NOT multipart)
  - Params: passed as query parameters
  - language=multi → auto-detects English, Spanish, and 30+ other languages
  - Response field: "transcription" (not "text")
"""

import requests

from config import SMALLEST_API_KEY

_SMALLEST_STT_URL = "https://waves-api.smallest.ai/api/v1/pulse/get_text"


def transcribe(audio_bytes: bytes, language: str = "multi") -> str:
    """
    Transcribes audio using smallest.ai Pulse STT.

    Args:
        audio_bytes: Raw WAV bytes.
        language:    ISO 639-1 code (e.g. "es", "en") or "multi" for
                     automatic language detection across 30+ languages.
                     Defaults to "multi" so it handles both Spanish and English.

    Returns:
        Transcribed text string, or empty string on failure.
    """
    try:
        response = requests.post(
            _SMALLEST_STT_URL,
            headers={
                "Authorization": f"Bearer {SMALLEST_API_KEY}",
                "Content-Type":  "application/octet-stream",
            },
            params={
                "model":    "pulse",
                "language": language,
            },
            data=audio_bytes,
            timeout=20,
        )
        response.raise_for_status()
        data = response.json()
        text = data.get("transcription", "").strip()
        print(f"[STT] smallest.ai ({language}): {text}")
        return text

    except requests.RequestException as e:
        print(f"[STT] smallest.ai error: {e}. Falling back to Whisper...")
        return _transcribe_whisper(audio_bytes)


def _transcribe_whisper(audio_bytes: bytes) -> str:
    """On-device Whisper fallback (pip install openai-whisper)."""
    try:
        import tempfile
        import whisper

        model = whisper.load_model("base")
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(audio_bytes)
            tmp_path = f.name
        result = model.transcribe(tmp_path)
        text = result.get("text", "").strip()
        print(f"[STT/Whisper]: {text}")
        return text
    except ImportError:
        print("[STT] Whisper not installed: pip install openai-whisper")
        return ""
    except Exception as e:
        print(f"[STT] Whisper error: {e}")
        return ""
