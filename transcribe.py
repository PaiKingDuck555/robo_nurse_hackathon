import os
import sys
import json
import tty
import termios
import struct
import threading
from urllib.parse import urlencode

import sounddevice as sd
import websockets
import asyncio
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("SMALLEST_API_KEY")
SAMPLE_RATE = 44100


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


async def main():
    # Step 1: Wait for R to start
    print("Press [r] to start recording...")
    wait_for_r()

    # Step 2: Record audio until R is pressed again
    print("\nRecording... speak now. Press [r] to stop.\n")
    audio_chunks = []
    stop = threading.Event()

    def callback(indata, frames, time_info, status):
        if not stop.is_set():
            audio_chunks.append(indata.tobytes())

    stream = sd.InputStream(samplerate=SAMPLE_RATE, channels=1,
                            blocksize=2205, dtype="int16", callback=callback)
    stream.start()

    def key_listener():
        wait_for_r()
        stop.set()

    t = threading.Thread(target=key_listener, daemon=True)
    t.start()

    while not stop.is_set():
        await asyncio.sleep(0.05)

    stream.stop()
    stream.close()

    pcm_data = b"".join(audio_chunks)
    duration = len(pcm_data) / (SAMPLE_RATE * 2)
    print(f"Recorded {duration:.1f}s of audio.\n")

    if not pcm_data:
        print("No audio captured.")
        return

    # Step 3: Send to smallest.ai and get transcription
    print("Transcribing...")
    print(f"  API key: {API_KEY[:8]}...{API_KEY[-4:]}" if API_KEY else "  API key: MISSING!")

    ws_url = f"wss://api.smallest.ai/waves/v1/pulse/get_text?{urlencode({
        'language': 'en',
        'encoding': 'linear16',
        'sample_rate': str(SAMPLE_RATE),
    })}"
    print(f"  URL: {ws_url}")
    print(f"  Audio: {len(pcm_data)} bytes")

    transcript = ""

    print("  Connecting to WebSocket...")
    async with websockets.connect(ws_url, additional_headers={"Authorization": f"Bearer {API_KEY}"}) as ws:
        print("  Connected!")

        chunks = 0
        for i in range(0, len(pcm_data), 4096):
            await ws.send(pcm_data[i:i+4096])
            chunks += 1
        print(f"  Sent {chunks} audio chunks.")

        await ws.send(json.dumps({"type": "finalize"}))
        print("  Sent finalize. Waiting for response...")

        try:
            while True:
                msg = await asyncio.wait_for(ws.recv(), timeout=10)
                print(f"  [API] {msg[:200]}")
                data = json.loads(msg)
                text = data.get("transcript", "").strip()
                if data.get("is_final") and text:
                    transcript = data.get("full_transcript", text)
                if data.get("is_last"):
                    break
        except asyncio.TimeoutError:
            print("  Timed out waiting for response (10s).")
        except websockets.exceptions.ConnectionClosed as e:
            print(f"  Connection closed: {e}")

    # Step 4: Print result
    if transcript:
        print(f"\n=== TRANSCRIPTION ===")
        print(transcript)
        print(f"=====================\n")
    else:
        print("No speech detected.\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nDone.")
