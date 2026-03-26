import asyncio
import os
import websockets
import http

connected_clients = set()

async def audio_broker(websocket, path):
    connected_clients.add(websocket)
    print(f"🟢 Device connected! Total devices: {len(connected_clients)}", flush=True)

    try:
        async for message in websocket:
            if connected_clients:
                others = [c for c in connected_clients if c != websocket]
                if others:
                    await asyncio.gather(
                        *[client.send(message) for client in others],
                        return_exceptions=True 
                    )
    except websockets.exceptions.ConnectionClosedOK:
        print("🔴 Device disconnected cleanly.", flush=True)
    except Exception as e:
        print(f"💥 Unexpected error: {e}", flush=True)
    finally:
        connected_clients.discard(websocket)
        print(f"👥 Remaining devices: {len(connected_clients)}", flush=True)

# --- THIS IS THE FIX ---
# This function intercepts Render's health checks before they crash the WebSocket
async def health_check(path, request_headers):
    if path == "/healthz" or "HEAD" in str(request_headers):
        return http.HTTPStatus.OK, [], b"OK\n"
    # Return None to let the WebSocket handshake continue normally
    return None 

async def main():
    port = int(os.environ.get("PORT", 8765))
    print(f"🚀 Cloud Audio Server starting on port {port}", flush=True)

    async with websockets.serve(
        audio_broker,
        "0.0.0.0",
        port,
        ping_interval=20,
        ping_timeout=10,
        max_size=2 * 1024 * 1024,
        process_request=health_check # Attach the health check interceptor here!
    ):
        print(f"✅ Server listening on port {port}", flush=True)
        await asyncio.Future() 

if __name__ == "__main__":
    asyncio.run(main())
