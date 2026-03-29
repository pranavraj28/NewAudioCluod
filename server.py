import asyncio
import os
import websockets
import http

# This memory buffer will store your voice on the cloud!
stored_audio = bytearray()
connected_clients = set()

async def audio_broker(websocket):
    global stored_audio
    connected_clients.add(websocket)
    print(f"🟢 Device connected! Total: {len(connected_clients)}", flush=True)

    try:
        async for message in websocket:
            
            # 1. If we receive RAW BYTES (from Sender), store them in memory
            if isinstance(message, bytes):
                stored_audio.extend(message)
                print(f"📥 Stored {len(message)} bytes. Total size: {len(stored_audio)}", flush=True)
            
            # 2. If we receive TEXT (from Receiver), check for the PLAY command
            elif isinstance(message, str):
                if message == "PLAY":
                    if len(stored_audio) > 0:
                        print(f"📤 Streaming {len(stored_audio)} bytes to Receiver!", flush=True)
                        
                        # Send in 4KB chunks so we don't crash the ESP32's RAM
                        chunk_size = 4096
                        for i in range(0, len(stored_audio), chunk_size):
                            chunk = stored_audio[i:i+chunk_size]
                            await websocket.send(chunk)
                            await asyncio.sleep(0.05) # Pacing to prevent overflow
                            
                        print("✅ Playback finished.")
                        # stored_audio.clear() # Optional: delete audio after playing
                    else:
                        print("⚠️ Receiver requested PLAY, but no audio is stored.", flush=True)
                        
    except websockets.exceptions.ConnectionClosedOK:
        pass
    except Exception as e:
        print(f"💥 Error: {e}", flush=True)
    finally:
        connected_clients.discard(websocket)

def health_check(connection, request):
    if getattr(request, "method", "") == "HEAD":
        return http.HTTPStatus.OK, [], b"OK\n"
    return None 

async def main():
    port = int(os.environ.get("PORT", 8765))
    print(f"🚀 Voicemail Server starting on port {port}", flush=True)
    async with websockets.serve(audio_broker, "0.0.0.0", port, ping_interval=20, ping_timeout=10, max_size=5*1024*1024, process_request=health_check):
        await asyncio.Future() 

if __name__ == "__main__":
    asyncio.run(main())
