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
