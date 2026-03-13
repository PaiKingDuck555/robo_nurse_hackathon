import os
import sys
import json
import tty
import termios
import asyncio
import ctypes
from datetime import datetime
from urllib.parse import urlencode

import pyaudio
import websockets
from deep_translator import GoogleTranslator
from dotenv import load_dotenv

load_dotenv()

# Suppress ALSA/JACK error messages on Linux
try:
    asound = ctypes.cdll.LoadLibrary("libasound.so.2")
    c_error_handler = ctypes.CFUNCTYPE(None, ctypes.c_char_p, ctypes.c_int,
                                        ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p)
    asound.snd_lib_error_set_handler(c_error_handler(lambda *_: None))
except OSError:
    pass

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
_original_termios = None


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


def find_usb_input_device():
    """Find USB mic index, or first input device if not found."""
    audio = pyaudio.PyAudio()
    for i in range(audio.get_device_count()):
        info = audio.get_device_info_by_index(i)
        if info["maxInputChannels"] > 0 and "USB" in info["name"]:
            audio.terminate()
            return i
    for i in range(audio.get_device_count()):
        info = audio.get_device_info_by_index(i)
        if info["maxInputChannels"] > 0:
            audio.terminate()
            return i
    audio.terminate()
    return None


def enable_raw_stdin():
    """Switch stdin to raw mode so single keypresses are detected."""
    global _original_termios
    fd = sys.stdin.fileno()
    _original_termios = termios.tcgetattr(fd)
    tty.setcbreak(fd)


def restore_stdin():
    """Restore original terminal settings."""
    if _original_termios:
        termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, _original_termios)


def wait_for_key(target="r"):
    """Block until user presses target key. Does not echo."""
    while True:
        ch = sys.stdin.read(1)
        if ch.lower() == target:
            return


async def run():
    device_index = find_usb_input_device()
    if device_index is None:
        print("No audio input device found.")
        return

    audio = pyaudio.PyAudio()
    dev_name = audio.get_device_info_by_index(device_index)["name"]
    try:
        mic = audio.open(
            input=True,
            input_device_index=device_index,
            frames_per_buffer=CHUNK_SIZE,
            channels=CHANNELS,
            format=FORMAT,
            rate=SAMPLE_RATE,
        )
        print(f"Mic ready: [{device_index}] {dev_name}")
    except Exception as e:
        print(f"Failed to open microphone: {e}")
        audio.terminate()
        return

    output_path = get_output_path()
    headers = {"Authorization": f"Bearer {API_KEY}"}

    enable_raw_stdin()

    try:
        print(f"Sample rate: {SAMPLE_RATE} Hz | Language: auto-detect")
        print("Press 'r' to START recording...")
        wait_for_key("r")
        print("\n--- Recording started. Speak now. Press 'r' to STOP. ---\n")

        async with websockets.connect(WS_URL, additional_headers=headers) as ws:
            stop = asyncio.Event()

            async def wait_for_stop():
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, wait_for_key, "r")
                print("\n--- Recording stopped. ---")
                stop.set()

            async def send_audio():
                loop = asyncio.get_event_loop()
                while not stop.is_set():
                    try:
                        data = await loop.run_in_executor(
                            None, lambda: mic.read(CHUNK_SIZE, exception_on_overflow=False)
                        )
                        if stop.is_set():
                            break
                        await ws.send(data)
                    except Exception as e:
                        if not stop.is_set():
                            print(f"Audio read error: {e}")
                        break

                try:
                    await ws.send(json.dumps({"type": "finalize"}))
                    await asyncio.sleep(2)
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
                            stop.set()
                            break

                    except json.JSONDecodeError:
                        pass

            sender = asyncio.create_task(send_audio())
            receiver = asyncio.create_task(receive_transcripts())
            stopper = asyncio.create_task(wait_for_stop())

            done, pending = await asyncio.wait(
                [sender, receiver, stopper],
                return_when=asyncio.FIRST_EXCEPTION,
            )
            for task in pending:
                task.cancel()

    except websockets.ConnectionClosed as e:
        print(f"\nConnection closed: {e.code} - {e.reason}")
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        restore_stdin()
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
        restore_stdin()
        print("\nInterrupted.")
