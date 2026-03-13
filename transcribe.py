import os
import sys
import json
import tty
import termios
import asyncio
import threading
from datetime import datetime
from urllib.parse import urlencode

import pyaudio
import websockets
from deep_translator import GoogleTranslator
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("SMALLEST_API_KEY")
if not API_KEY:
    raise RuntimeError("Set SMALLEST_API_KEY in your .env file")

TARGET_LANGUAGE = os.getenv("TARGET_LANGUAGE", "english")

SAMPLE_RATE = 44100
CHANNELS = 1
FORMAT = pyaudio.paInt16
CHUNK_SIZE = 4096

WS_PARAMS = {
    "language": "multi",
    "encoding": "linear16",
    "sample_rate": str(SAMPLE_RATE),
    "word_timestamps": "false",
    "full_transcript": "true",
}
WS_URL = f"wss://api.smallest.ai/waves/v1/lightning/get_text?{urlencode(WS_PARAMS)}"

transcript_entries = []


def get_key():
    """Read a single keypress (Linux/Pi)."""
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        return sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def wait_for_r():
    """Block until user presses 'r' or 'R'."""
    while True:
        key = get_key()
        if key.lower() == "r":
            return


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


def list_audio_devices():
    audio = pyaudio.PyAudio()
    print("Available audio input devices:")
    for i in range(audio.get_device_count()):
        info = audio.get_device_info_by_index(i)
        if info["maxInputChannels"] > 0:
            print(f"  [{i}] {info['name']} (channels: {info['maxInputChannels']}, rate: {int(info['defaultSampleRate'])})")
    audio.terminate()
    print()


async def run():
    list_audio_devices()

    audio = pyaudio.PyAudio()
    try:
        mic = audio.open(
            input=True,
            frames_per_buffer=CHUNK_SIZE,
            channels=CHANNELS,
            format=FORMAT,
            rate=SAMPLE_RATE,
        )
    except Exception as e:
        print(f"Failed to open microphone: {e}")
        print("Make sure a USB microphone or audio device is connected.")
        audio.terminate()
        return

    output_path = get_output_path()
    headers = {"Authorization": f"Bearer {API_KEY}"}

    print(f"Connecting to smallest.ai ({WS_PARAMS['language']} mode)...")
    print(f"Sample rate: {SAMPLE_RATE} Hz")
    print("Press 'r' to start recording...")
    wait_for_r()
    print("\nRecording. Speak now. Press 'r' to stop.\n")

    try:
        async with websockets.connect(WS_URL, additional_headers=headers) as ws:
            print("Connected to smallest.ai STT WebSocket.\n")

            stop = asyncio.Event()

            async def wait_for_r_stop():
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, wait_for_r)
                stop.set()

            async def send_audio():
                loop = asyncio.get_event_loop()
                while not stop.is_set():
                    try:
                        data = await loop.run_in_executor(
                            None, lambda: mic.read(CHUNK_SIZE, exception_on_overflow=False)
                        )
                        await ws.send(data)
                    except Exception as e:
                        if not stop.is_set():
                            print(f"Audio read error: {e}")
                        break

                try:
                    await ws.send(json.dumps({"type": "finalize"}))
                except Exception:
                    pass

            async def receive_transcripts():
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
                            print("\nSession complete.")
                            stop.set()
                            break

                    except json.JSONDecodeError:
                        pass

            sender = asyncio.create_task(send_audio())
            receiver = asyncio.create_task(receive_transcripts())
            r_waiter = asyncio.create_task(wait_for_r_stop())

            await asyncio.gather(sender, receiver, r_waiter)

    except websockets.ConnectionClosed as e:
        print(f"\nConnection closed: {e.code} - {e.reason}")
    except KeyboardInterrupt:
        print("\n\nStopping...")
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        if mic.is_active():
            mic.stop_stream()
        mic.close()
        audio.terminate()

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
