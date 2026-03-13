import os
import sys
import json
import queue
import threading
from urllib.parse import urlencode

import sounddevice as sd
import websockets
import asyncio
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("SMALLEST_API_KEY")
SAMPLE_RATE = 44100
BLOCK_SIZE = 2205  # 50ms at 44100Hz


async def main():
    ws_url = f"wss://api.smallest.ai/waves/v1/lightning/get_text?{urlencode({
        'language': 'multi',
        'encoding': 'linear16',
        'sample_rate': str(SAMPLE_RATE),
    })}"

    audio_q = queue.Queue()
    stop = threading.Event()

    def callback(indata, frames, time_info, status):
        audio_q.put(indata.tobytes())

    print("Recording... speak now. Ctrl+C to stop.\n")

    stream = sd.InputStream(samplerate=SAMPLE_RATE, channels=1, blocksize=BLOCK_SIZE,
                            dtype="int16", callback=callback)
    stream.start()

    async with websockets.connect(ws_url, additional_headers={"Authorization": f"Bearer {API_KEY}"}) as ws:

        async def send():
            loop = asyncio.get_event_loop()
            while not stop.is_set():
                try:
                    data = await loop.run_in_executor(None, lambda: audio_q.get(timeout=0.1))
                    await ws.send(data)
                except queue.Empty:
                    continue
            await ws.send(json.dumps({"type": "finalize"}))

        async def recv():
            async for msg in ws:
                data = json.loads(msg)
                text = data.get("transcript", "").strip()
                if not text:
                    if data.get("is_last"):
                        break
                    continue
                if data.get("is_final"):
                    print(f">> {text}")
                else:
                    print(f"   ...{text}", end="\r")

        try:
            await asyncio.gather(send(), recv())
        except KeyboardInterrupt:
            stop.set()
            stream.stop()
            stream.close()
            print("\nDone.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nDone.")
