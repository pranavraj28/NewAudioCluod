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
            
            # 1. If we receive RAW BYTES (from Sender), store them in memory
            if isinstance(message, bytes):
                stored_audio.extend(message)
                print(f"📥 Stored {len(message)} bytes. Total size: {len(stored_audio)}", flush=True)
            
            # 2. If we receive TEXT, check for commands
            elif isinstance(message, str):
                if message == "PLAY":
                    if len(stored_audio) > 0:
                        print(f"📤 Streaming {len(stored_audio)} bytes to Receiver!", flush=True)
                        
                        # Send the entire voicemail in one clean shot
                        await websocket.send(stored_audio)
                        
                        print("✅ Playback finished. Wiping memory clean.")
                        # 🚨 THE FIX: Completely delete the old audio so it never plays again
                        stored_audio.clear() 
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
    
    # max_size increased to handle large one-shot downloads
    async with websockets.serve(audio_broker, "0.0.0.0", port, ping_interval=20, ping_timeout=10, max_size=15*1024*1024, process_request=health_check):
        await asyncio.Future() 

if __name__ == "__main__":
    asyncio.run(main())
