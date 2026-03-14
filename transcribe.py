import os
import sys
import json
import tty
import termios
import threading
from datetime import datetime, timezone
from urllib.parse import urlencode

import sounddevice as sd
import numpy as np
import websockets
import asyncio
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("SMALLEST_API_KEY")
SAMPLE_RATE = 44100
TRANSCRIPT_FILE = os.path.join(os.path.dirname(__file__), "transcripts.json")

LANGUAGE = "en"


def find_input_device():
    devices = sd.query_devices()
    default_in, _ = sd.default.device

    inputs = []
    for i, d in enumerate(devices):
        if d['max_input_channels'] > 0:
            inputs.append(i)

    if not inputs:
        return None, SAMPLE_RATE

    for i in inputs:
        if 'usb' in sd.query_devices(i)['name'].lower():
            info = sd.query_devices(i)
            return i, int(info['default_samplerate'])

    chosen = default_in if default_in is not None else inputs[0]
    info = sd.query_devices(chosen)
    return chosen, int(info['default_samplerate'])


def get_key():
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        return sys.stdin.read(1).lower()
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def wait_for_r():
    while True:
        ch = get_key()
        if ch == "r":
            return
        if ch in ("\x03", "q"):
            sys.exit(0)


async def transcribe(pcm_data, language):
    params = {
        'language': language,
        'encoding': 'linear16',
        'sample_rate': str(SAMPLE_RATE),
    }
    ws_url = f"wss://api.smallest.ai/waves/v1/pulse/get_text?{urlencode(params)}"
    print(f"[API] URL: {ws_url}")

    transcript = ""
    detected_lang = language
    try:
        async with websockets.connect(
            ws_url,
            additional_headers={"Authorization": f"Bearer {API_KEY}"},
        ) as ws:
            print(f"[API] Connected")

            n_chunks = (len(pcm_data) + 4095) // 4096
            for idx, i in enumerate(range(0, len(pcm_data), 4096)):
                await ws.send(pcm_data[i:i+4096])
                await asyncio.sleep(0.05)
            print(f"[API] Sent {n_chunks} chunks")

            await ws.send(json.dumps({"type": "finalize"}))
            print(f"[API] Sent finalize, waiting for response...")

            msg_count = 0
            try:
                while True:
                    msg = await asyncio.wait_for(ws.recv(), timeout=15)
                    msg_count += 1
                    data = json.loads(msg)
                    text = data.get("transcript", "").strip()
                    is_final = data.get("is_final", False)
                    is_last = data.get("is_last", False)
                    lang = data.get("language", "")
                    print(f"[API] msg#{msg_count}: is_final={is_final} is_last={is_last} lang={lang} text={repr(text[:80])}")
                    if lang:
                        detected_lang = lang
                    if text:
                        transcript = data.get("full_transcript", text)
                    if is_last:
                        break
            except asyncio.TimeoutError:
                print(f"[API] TIMEOUT after {msg_count} messages (using best transcript so far)")
            except websockets.exceptions.ConnectionClosed as e:
                print(f"[API] CONNECTION CLOSED: {e}")

    except Exception as e:
        print(f"[API] ERROR: {type(e).__name__}: {e}")

    print(f"[API] Done. transcript={repr(transcript[:100]) if transcript else 'EMPTY'}")
    return transcript, detected_lang


def save_transcript(text, language, duration):
    entries = []
    if os.path.exists(TRANSCRIPT_FILE):
        with open(TRANSCRIPT_FILE, "r") as f:
            try:
                entries = json.load(f)
            except json.JSONDecodeError:
                entries = []

    entries.append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "language": language,
        "duration_s": round(duration, 2),
        "text": text,
    })

    with open(TRANSCRIPT_FILE, "w") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)

    return len(entries)


async def record_once(mic_idx, language):
    print("\nPress [r] to start recording...")
    wait_for_r()

    print("\nRecording... speak now. Press [r] to stop.\n")
    audio_chunks = []
    stop = threading.Event()

    def callback(indata, frames, time_info, status):
        if not stop.is_set():
            audio_chunks.append(indata.tobytes())

    stream = sd.InputStream(samplerate=SAMPLE_RATE, channels=1,
                            blocksize=2205, dtype="int16",
                            device=mic_idx, callback=callback)
    stream.start()

    t = threading.Thread(target=lambda: (wait_for_r(), stop.set()), daemon=True)
    t.start()

    while not stop.is_set():
        await asyncio.sleep(0.05)

    stream.stop()
    stream.close()

    pcm_data = b"".join(audio_chunks)
    duration = len(pcm_data) / (SAMPLE_RATE * 2)
    print(f"[MIC] Recorded {duration:.1f}s of audio ({len(pcm_data)} bytes, {len(audio_chunks)} chunks)")

    if not pcm_data:
        print("[MIC] No audio captured.")
        return

    samples = np.frombuffer(pcm_data, dtype=np.int16)
    peak = int(np.max(np.abs(samples)))
    rms = int(np.sqrt(np.mean(samples.astype(np.float64) ** 2)))
    print(f"[MIC] peak={peak}/32767  rms={rms}  samples={len(samples)}")
    if peak < 100:
        print("[MIC] WARNING: Audio is nearly silent — mic may not be working.")
        return
    print(f"[MIC] Audio OK")

    print(f"[API] Connecting to smallest.ai...")
    transcript, detected_lang = await transcribe(pcm_data, language)

    if transcript:
        count = save_transcript(transcript, detected_lang, duration)
        print(f"\n>>> [{detected_lang}] {transcript}")
        print(f"    (saved — {count} entries total)\n")
    else:
        print("\nNo speech detected.\n")


async def main():
    mic_idx, mic_rate = find_input_device()
    if mic_idx is None:
        print("No microphone found. Plug in a USB mic and try again.")
        return

    global SAMPLE_RATE
    SAMPLE_RATE = mic_rate

    mic_name = sd.query_devices(mic_idx)['name']
    print(f"Mic: {mic_name} @ {SAMPLE_RATE}Hz")

    while True:
        await record_once(mic_idx, LANGUAGE)
        print("--- Press [r] to record again, [q] to quit ---")
        while True:
            ch = get_key()
            if ch == "r":
                break
            if ch in ("\x03", "q"):
                print("\nDone.")
                return


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nDone.")
