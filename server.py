import asyncio
import websockets
import pyaudio
import numpy as np
import wave
import os
from datetime import datetime

# ── Config ────────────────────────────────────────────────────────
SAMPLE_RATE = 16000
SAMPLES_PER_PACKET = 320
RENDER_URL = "wss://newaudiocluod.onrender.com"

async def play_voicemail():
    print(f"🔌 Connecting to Cloud Voicemail: {RENDER_URL}...")
    
    # Setup WAV file saving
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    wav_path = os.path.join(desktop, f"voicemail_{timestamp}.wav")
    
    wav_file = wave.open(wav_path, 'wb')
    wav_file.setnchannels(1)
    wav_file.setsampwidth(2)
    wav_file.setframerate(SAMPLE_RATE)
    
    pa = pyaudio.PyAudio()
    stream = pa.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=SAMPLE_RATE,
        output=True,
        frames_per_buffer=SAMPLES_PER_PACKET
    )
    
    try:
        # Increased max_size in case there's a large voicemail
        async with websockets.connect(RENDER_URL, max_size=10*1024*1024) as websocket:
            print("✅ Connected to Render!")
            
            # Act like the Receiver ESP32 button: Send the PLAY command
            print("▶️ Asking server for the stored audio...")
            await websocket.send("PLAY")
            
            print("🔊 Listening for playback...")
            while True:
                try:
                    # Wait for audio chunks. Timeout if the server stops sending.
                    packet = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                    
                    if isinstance(packet, bytes):
                        samples = np.frombuffer(packet, dtype=np.int16)
                        samples = samples.byteswap() # Keep the Endianness fix!
                        
                        # Play it AND save it
                        stream.write(samples.tobytes())
                        wav_file.writeframes(samples.tobytes())
                        
                except asyncio.TimeoutError:
                    print(f"\n✅ Playback finished. Saved to: {wav_path}")
                    break 
                    
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        stream.stop_stream()
        stream.close()
        pa.terminate()
        wav_file.close()

if __name__ == "__main__":
    asyncio.run(play_voicemail())
