import asyncio
import websockets

clients = set()

async def echo(websocket, path):
    clients.add(websocket)
    print(f"Client connected: {websocket.remote_address}")
    try:
        async for message in websocket:
            print(f"Message received: {message}")
            for client in clients:
                if client != websocket:
                    await client.send(message)
                    print(f"Message sent to {client.remote_address}")
    finally:
        clients.remove(websocket)
        print(f"Client disconnected: {websocket.remote_address}")

async def main():
    async with websockets.serve(echo, "0.0.0.0", 8765):
        await asyncio.Future()

asyncio.run(main())
