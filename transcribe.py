import os
import sys
import json
import tty
import termios
import struct
import time
import logging
import threading
from urllib.parse import urlencode

import sounddevice as sd
import websockets
import asyncio
from dotenv import load_dotenv

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

load_dotenv()

API_KEY = os.getenv("SMALLEST_API_KEY")
SAMPLE_RATE = 44100


def find_input_device():
    """List all audio devices, find USB mic, return (index, native_rate)."""
    devices = sd.query_devices()
    default_in, _ = sd.default.device

    print("\nAudio devices:")
    inputs = []
    for i, d in enumerate(devices):
        if d['max_input_channels'] > 0:
            tag = " <-- DEFAULT" if i == default_in else ""
            print(f"  [{i}] {d['name']} ({d['max_input_channels']}ch, {int(d['default_samplerate'])}Hz){tag}")
            inputs.append(i)

    if not inputs:
        print("  NO INPUT DEVICES FOUND! Plug in a USB mic.")
        return None, SAMPLE_RATE

    usb_idx = None
    for i in inputs:
        name = devices[i]['name'].lower()
        if 'usb' in name:
            usb_idx = i
            break

    chosen = usb_idx if usb_idx is not None else default_in
    if chosen is None:
        chosen = inputs[0]

    info = sd.query_devices(chosen)
    rate = int(info['default_samplerate'])
    print(f"\n  Using: [{chosen}] {info['name']} @ {rate}Hz")
    return chosen, rate


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
    # Step 0: Detect mic
    mic_idx, mic_rate = find_input_device()
    if mic_idx is None:
        print("No microphone found. Exiting.")
        return

    global SAMPLE_RATE
    SAMPLE_RATE = mic_rate

    # Step 1: Wait for R to start
    print("\nPress [r] to start recording...")
    wait_for_r()

    # Step 2: Record audio until R is pressed again
    print("\nRecording... speak now. Press [r] to stop.\n")
    audio_chunks = []
    stop = threading.Event()

    def callback(indata, frames, time_info, status):
        if status:
            print(f"  [audio status] {status}")
        if not stop.is_set():
            audio_chunks.append(indata.tobytes())

    stream = sd.InputStream(samplerate=SAMPLE_RATE, channels=1,
                            blocksize=2205, dtype="int16",
                            device=mic_idx, callback=callback)
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

    import numpy as np
    samples = np.frombuffer(pcm_data, dtype=np.int16)
    peak = int(np.max(np.abs(samples)))
    rms = int(np.sqrt(np.mean(samples.astype(np.float64) ** 2)))
    print(f"  Audio check: {len(samples)} samples, peak={peak}, rms={rms}")
    if peak < 100:
        print("  WARNING: Audio is nearly silent! Mic may not be working.")
    else:
        print(f"  Audio looks good (peak {peak}/32767).")

    # Step 3: Send to smallest.ai and get transcription
    print("=" * 60)
    print("TRANSCRIPTION PIPELINE")
    print("=" * 60)
    print(f"  API key      : {API_KEY[:8]}...{API_KEY[-4:]}" if API_KEY else "  API key: MISSING!")
    print(f"  Sample rate  : {SAMPLE_RATE}")
    print(f"  Audio bytes  : {len(pcm_data)}")
    print(f"  Duration     : {duration:.2f}s")
    print(f"  First 20 bytes (hex): {pcm_data[:20].hex()}")

    ws_url = f"wss://api.smallest.ai/waves/v1/pulse/get_text?{urlencode({
        'language': 'en',
        'encoding': 'linear16',
        'sample_rate': str(SAMPLE_RATE),
    })}"
    print(f"  URL          : {ws_url}")

    transcript = ""

    try:
        t0 = time.time()
        print(f"\n[{time.time()-t0:.3f}s] Connecting to WebSocket...")
        async with websockets.connect(
            ws_url,
            additional_headers={"Authorization": f"Bearer {API_KEY}"},
            ping_interval=20,
            ping_timeout=20,
            close_timeout=10,
        ) as ws:
            print(f"[{time.time()-t0:.3f}s] Connected! ws.open={ws.open}")

            total_chunks = (len(pcm_data) + 4095) // 4096
            print(f"[{time.time()-t0:.3f}s] Sending {total_chunks} chunks of 4096 bytes with 50ms pacing...")
            for idx, i in enumerate(range(0, len(pcm_data), 4096)):
                chunk = pcm_data[i:i+4096]
                await ws.send(chunk)
                if idx % 10 == 0:
                    print(f"  chunk {idx+1}/{total_chunks} ({len(chunk)} bytes)")
                await asyncio.sleep(0.05)
            print(f"[{time.time()-t0:.3f}s] All {total_chunks} chunks sent.")

            finalize_msg = json.dumps({"type": "finalize"})
            print(f"[{time.time()-t0:.3f}s] Sending finalize: {finalize_msg}")
            await ws.send(finalize_msg)
            print(f"[{time.time()-t0:.3f}s] Finalize sent. Listening for responses...")

            msg_count = 0
            try:
                while True:
                    msg = await asyncio.wait_for(ws.recv(), timeout=15)
                    msg_count += 1
                    elapsed = time.time() - t0
                    print(f"[{elapsed:.3f}s] MSG #{msg_count}: {msg[:500]}")
                    try:
                        data = json.loads(msg)
                        print(f"  Keys: {list(data.keys())}")
                        print(f"  transcript  : {repr(data.get('transcript', ''))}")
                        print(f"  is_final    : {data.get('is_final')}")
                        print(f"  is_last     : {data.get('is_last')}")
                        print(f"  session_id  : {data.get('session_id')}")
                        if 'error' in data:
                            print(f"  ERROR       : {data['error']}")
                        text = data.get("transcript", "").strip()
                        if data.get("is_final") and text:
                            transcript = data.get("full_transcript", text)
                        if data.get("is_last"):
                            print(f"[{elapsed:.3f}s] Got is_last, breaking.")
                            break
                    except json.JSONDecodeError:
                        print(f"  (not JSON)")
            except asyncio.TimeoutError:
                print(f"[{time.time()-t0:.3f}s] TIMEOUT: No message received for 15s. Got {msg_count} messages total.")
            except websockets.exceptions.ConnectionClosed as e:
                print(f"[{time.time()-t0:.3f}s] CONNECTION CLOSED: code={e.code} reason={e.reason}")
            except Exception as e:
                print(f"[{time.time()-t0:.3f}s] UNEXPECTED ERROR: {type(e).__name__}: {e}")

    except websockets.exceptions.InvalidStatusCode as e:
        print(f"WS connection rejected: HTTP {e.status_code}")
    except Exception as e:
        print(f"FATAL ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

    print("=" * 60)
    if transcript:
        print(f"TRANSCRIPTION: {transcript}")
    else:
        print("No speech detected.")
    print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nDone.")
