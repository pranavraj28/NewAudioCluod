import asyncio
import os
import websockets
import http

stored_audio = bytearray()
connected_clients = set()

async def audio_broker(websocket):
    global stored_audio
    connected_clients.add(websocket)
    print(f"🟢 Device connected! Total: {len(connected_clients)}", flush=True)

    try:
        async for message in websocket:
            
            # 1. Store RAW BYTES
            if isinstance(message, bytes):
                stored_audio.extend(message)
                print(f"📥 Stored {len(message)} bytes. Total size: {len(stored_audio)}", flush=True)
            
            # 2. Command routing
            elif isinstance(message, str):
                if message == "PLAY":
                    if len(stored_audio) > 0:
                        print(f"📤 Streaming {len(stored_audio)} bytes to Receiver!", flush=True)
                        await websocket.send(stored_audio)
                        print("✅ Playback sent. Keeping memory intact for alarm looping.")
                    else:
                        print("⚠️ Receiver requested PLAY, but no audio is stored.", flush=True)
                
                elif message == "ACK":
                    print("✅ Receiver acknowledged alarm. Wiping memory clean.", flush=True)
                    stored_audio.clear()
                        
    except websockets.exceptions.ConnectionClosedOK:
        pass
    except Exception as e:
        print(f"💥 Error: {e}", flush=True)
    finally:
        connected_clients.discard(websocket)

def health_check(connection, request):
    # Intercept Render's GET health check and return 200 OK safely
    if request.path == "/healthz":
        return http.HTTPStatus.OK, [], b"OK\n"
    return None 

async def main():
    port = int(os.environ.get("PORT", 8765))
    print(f"🚀 Voicemail Server starting on port {port}", flush=True)
    
    async with websockets.serve(audio_broker, "0.0.0.0", port, ping_interval=20, ping_timeout=10, max_size=15*1024*1024, process_request=health_check):
        await asyncio.Future() 

if __name__ == "__main__":
    asyncio.run(main())
