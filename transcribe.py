import os
import sys
import json
import tty
import termios
import asyncio
import queue
import threading
from datetime import datetime
from urllib.parse import urlencode

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

transcript_entries = []


def get_output_path():
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return os.path.join(os.path.dirname(__file__), f"transcripts/transcript_{ts}.md")


def translate_text(text, source_lang="auto"):
    translator = GoogleTranslator(source=source_lang, target=TARGET_LANGUAGE)
    return translator.translate(text)


def save_transcript(path):
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


def find_usb_mic():
    devices = sd.query_devices()
    for i, d in enumerate(devices):
        if d["max_input_channels"] > 0 and "USB" in d["name"]:
            return i, d["name"]
    default_in = sd.default.device[0]
    if default_in is not None:
        return default_in, devices[default_in]["name"]
    return None, None


def get_mic_native_rate(mic_index):
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


def get_key():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch.lower()


def wait_for_key(target="r"):
    while True:
        ch = get_key()
        if ch == target:
            return
        if ch in ("\x03", "q"):
            raise KeyboardInterrupt


async def run():
    mic_index, mic_name = find_usb_mic()
    if mic_index is None:
        print("No audio input device found. Plug in a USB mic.")
        return

    mic_rate = get_mic_native_rate(mic_index)
    block_size = int(mic_rate * 0.05)  # 50ms chunks

    print(f"Mic: [{mic_index}] {mic_name}")
    print(f"Sample rate: {mic_rate} Hz")

    ws_params = {
        "language": "multi",
        "encoding": "linear16",
        "sample_rate": str(mic_rate),
        "word_timestamps": "false",
        "full_transcript": "true",
    }
    ws_url = f"wss://api.smallest.ai/waves/v1/lightning/get_text?{urlencode(ws_params)}"
    headers = {"Authorization": f"Bearer {API_KEY}"}
    output_path = get_output_path()

    print("\nPress [r] to start recording")
    print("Press [q] to quit\n")
    wait_for_key("r")

    print("Connecting to smallest.ai...")

    try:
        async with websockets.connect(ws_url, additional_headers=headers) as ws:
            print("Connected. Speak now! Press [r] to stop.\n")

            stop_event = threading.Event()
            audio_q = queue.Queue()  # thread-safe queue
            chunks_sent = 0

            def audio_callback(indata, frames, time_info, status):
                if not stop_event.is_set():
                    audio_q.put(indata.tobytes())

            stream = sd.InputStream(
                samplerate=mic_rate,
                channels=CHANNELS,
                blocksize=block_size,
                device=mic_index,
                dtype="int16",
                callback=audio_callback,
            )
            stream.start()

            def key_listener():
                wait_for_key("r")
                stop_event.set()

            key_thread = threading.Thread(target=key_listener, daemon=True)
            key_thread.start()

            async def send_audio():
                nonlocal chunks_sent
                loop = asyncio.get_event_loop()
                while not stop_event.is_set():
                    try:
                        data = await loop.run_in_executor(
                            None, lambda: audio_q.get(timeout=0.1)
                        )
                        await ws.send(data)
                        chunks_sent += 1
                    except queue.Empty:
                        continue
                    except Exception as e:
                        print(f"Send error: {e}")
                        break

                # Drain remaining audio
                while not audio_q.empty():
                    try:
                        data = audio_q.get_nowait()
                        await ws.send(data)
                        chunks_sent += 1
                    except Exception:
                        break

                print(f"\n--- Recording stopped. Sent {chunks_sent} chunks. Waiting for results... ---")
                await ws.send(json.dumps({"type": "finalize"}))

            async def receive_transcripts():
                async for message in ws:
                    try:
                        data = json.loads(message)

                        # Debug: print raw API response
                        msg_type = data.get("type", "")
                        transcript = data.get("transcript", "").strip()
                        is_final = data.get("is_final", False)
                        is_last = data.get("is_last", False)
                        lang = data.get("language", "unknown")

                        if not transcript:
                            if is_last:
                                print("[DEBUG] Got is_last=true, ending.")
                                break
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

            sender = asyncio.create_task(send_audio())
            receiver = asyncio.create_task(receive_transcripts())

            done, pending = await asyncio.wait(
                [sender, receiver],
                return_when=asyncio.ALL_COMPLETED,
            )
            for task in pending:
                task.cancel()

            stream.stop()
            stream.close()

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
