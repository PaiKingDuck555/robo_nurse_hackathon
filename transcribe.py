import os
import sys
import json
import tty
import termios
import asyncio
import threading
from datetime import datetime
from urllib.parse import urlencode
from math import gcd

import numpy as np
import sounddevice as sd
import websockets
from deep_translator import GoogleTranslator
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("SMALLEST_API_KEY")
if not API_KEY:
    raise RuntimeError("Set SMALLEST_API_KEY in your .env file")

TARGET_LANGUAGE = os.getenv("TARGET_LANGUAGE", "english")

CHANNELS = 1
SEND_RATE = 16000  # smallest.ai expects 16kHz

transcript_entries = []


def get_output_path():
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return os.path.join(os.path.dirname(__file__), f"transcripts/transcript_{ts}.md")


def translate_text(text, source_lang="auto"):
    """Translate text to TARGET_LANGUAGE via Google Translate."""
    translator = GoogleTranslator(source=source_lang, target=TARGET_LANGUAGE)
    return translator.translate(text)


def save_transcript(path):
    """Write all collected transcript entries to a markdown file."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(f"# Transcript — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**Target language:** {TARGET_LANGUAGE}\n\n")
        f.write("---\n\n")

        for entry in transcript_entries:
            ts = entry["time"]
            orig = entry["original"]
            lang = entry.get("language", "unknown")
            translated = entry.get("translated", "")

            f.write(f"### [{ts}] (detected: {lang})\n\n")
            f.write(f"**Original:** {orig}\n\n")
            if translated and translated != orig:
                f.write(f"**{TARGET_LANGUAGE}:** {translated}\n\n")
            f.write("---\n\n")

    print(f"\nTranscript saved to {path}")


# ──────────────────────────────────────────────
# USB AUDIO HELPERS (from translator project)
# ──────────────────────────────────────────────
def find_usb_mic():
    """Find USB mic device index, or fall back to default input."""
    devices = sd.query_devices()
    for i, d in enumerate(devices):
        if d["max_input_channels"] > 0 and "USB" in d["name"]:
            return i, d["name"]
    default_in = sd.default.device[0]
    if default_in is not None:
        return default_in, devices[default_in]["name"]
    return None, None


def get_mic_native_rate(mic_index):
    """Probe the USB mic's native sample rate."""
    info = sd.query_devices(mic_index)
    default_rate = int(info["default_samplerate"])

    try:
        sd.check_input_settings(device=mic_index, samplerate=default_rate)
        return default_rate
    except Exception:
        pass

    for rate in [48000, 44100, 32000, 22050, 16000, 8000]:
        try:
            sd.check_input_settings(device=mic_index, samplerate=rate)
            return rate
        except Exception:
            continue

    return default_rate


def resample_audio(audio, from_rate, to_rate):
    """Resample audio using scipy-style polyphase resampling."""
    if from_rate == to_rate:
        return audio
    from scipy.signal import resample_poly
    divisor = gcd(from_rate, to_rate)
    up = to_rate // divisor
    down = from_rate // divisor
    return resample_poly(audio, up, down).astype(np.float32)


# ──────────────────────────────────────────────
# KEYBOARD INPUT (from translator project)
# ──────────────────────────────────────────────
def get_key():
    """Read a single keypress without echo."""
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch.lower()


def wait_for_key(target="r"):
    """Block until user presses target key."""
    while True:
        ch = get_key()
        if ch == target:
            return
        if ch in ("\x03", "q"):
            raise KeyboardInterrupt


# ──────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────
async def run():
    mic_index, mic_name = find_usb_mic()
    if mic_index is None:
        print("No audio input device found. Plug in a USB mic.")
        return

    mic_rate = get_mic_native_rate(mic_index)
    block_size = int(mic_rate * 0.1)  # ~100ms chunks

    print(f"Mic: [{mic_index}] {mic_name}")
    print(f"Native rate: {mic_rate} Hz", end="")
    if mic_rate != SEND_RATE:
        print(f" -> will resample to {SEND_RATE} Hz for API")
    else:
        print()

    ws_params = {
        "language": "multi",
        "encoding": "linear16",
        "sample_rate": str(SEND_RATE),
        "word_timestamps": "false",
        "full_transcript": "true",
    }
    ws_url = f"wss://api.smallest.ai/waves/v1/lightning/get_text?{urlencode(ws_params)}"
    headers = {"Authorization": f"Bearer {API_KEY}"}
    output_path = get_output_path()

    print("\nPress [r] to start recording")
    print("Press [q] to quit\n")

    wait_for_key("r")
    print("--- Recording started. Speak now. Press [r] to stop. ---\n")

    # Collect audio in callback
    audio_buffer = []
    is_recording = True

    def audio_callback(indata, frames, time_info, status):
        if is_recording:
            audio_buffer.append(indata.copy())

    stream = sd.InputStream(
        samplerate=mic_rate,
        channels=CHANNELS,
        blocksize=block_size,
        device=mic_index,
        dtype="float32",
        callback=audio_callback,
    )
    stream.start()

    # Wait for stop key in a thread
    stop_event = threading.Event()

    def key_listener():
        wait_for_key("r")
        stop_event.set()

    key_thread = threading.Thread(target=key_listener, daemon=True)
    key_thread.start()

    # Wait until user presses 'r' again
    while not stop_event.is_set():
        await asyncio.sleep(0.05)

    is_recording = False
    stream.stop()
    stream.close()

    chunk_count = len(audio_buffer)
    duration = chunk_count * block_size / mic_rate
    print(f"\n--- Recording stopped. Captured {duration:.1f}s of audio. ---\n")

    if chunk_count == 0:
        print("No audio captured.")
        return

    # Concatenate and resample to 16kHz for the API
    full_audio = np.concatenate(audio_buffer, axis=0).flatten()
    audio_buffer.clear()

    if mic_rate != SEND_RATE:
        print(f"Resampling {mic_rate} Hz -> {SEND_RATE} Hz...")
        full_audio = resample_audio(full_audio, mic_rate, SEND_RATE)

    # Convert float32 [-1,1] to int16 PCM bytes
    pcm_data = (full_audio * 32767).astype(np.int16).tobytes()

    # Stream to smallest.ai
    print("Sending audio to smallest.ai...\n")

    try:
        async with websockets.connect(ws_url, additional_headers=headers) as ws:
            # Send audio in 4096-byte chunks
            chunk_size = 4096
            for i in range(0, len(pcm_data), chunk_size):
                chunk = pcm_data[i : i + chunk_size]
                await ws.send(chunk)
                await asyncio.sleep(0.01)

            # Signal end of audio
            await ws.send(json.dumps({"type": "finalize"}))

            # Receive transcripts
            async for message in ws:
                try:
                    data = json.loads(message)
                    transcript = data.get("transcript", "").strip()
                    is_final = data.get("is_final", False)
                    is_last = data.get("is_last", False)
                    lang = data.get("language", "unknown")

                    if not transcript:
                        continue

                    if not is_final:
                        print(f"\r  [partial] {transcript}", end="", flush=True)
                        continue

                    print(f"\r{' ' * 100}\r", end="")

                    ts = datetime.now().strftime("%H:%M:%S")
                    print(f"[{ts}] ({lang}) {transcript}")

                    translated = ""
                    try:
                        translated = translate_text(transcript)
                        print(f"  [DEBUG] INPUT:  ({lang}) {transcript}")
                        print(f"  [DEBUG] OUTPUT: ({TARGET_LANGUAGE}) {translated}")
                    except Exception as e:
                        print(f"  [DEBUG] Translation failed: {e}")

                    transcript_entries.append({
                        "time": ts,
                        "original": transcript,
                        "language": lang,
                        "translated": translated,
                    })

                    if is_last:
                        break

                except json.JSONDecodeError:
                    pass

    except websockets.ConnectionClosed as e:
        print(f"\nConnection closed: {e.code} - {e.reason}")
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        if transcript_entries:
            save_transcript(output_path)
        else:
            print("No transcripts captured.")
        print("Done.")


if __name__ == "__main__":
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        print("\nInterrupted.")
