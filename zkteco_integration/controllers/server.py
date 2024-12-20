import asyncio
import websockets

clients = set()

async def echo(websocket):

    clients.add(websocket)
    print(f"Client connected: {websocket.remote_address}")

    try:
        async for message in websocket:
            print(f"Message received: {message}")

            for client in clients:
                if client != websocket:
                    try:
                        await client.send(message)
                        print(f"Message sent to {client.remote_address}")
                    except Exception as e:
                        print(f"Error sending message to {client.remote_address}: {e}")
    except websockets.exceptions.ConnectionClosed as e:
        print(f"Connection closed with {websocket.remote_address}: {e}")
    except Exception as e:
        print(f"Error: {e}")
    finally:

        clients.remove(websocket)
        print(f"Client disconnected: {websocket.remote_address}")

async def main():

    async with websockets.serve(echo, "0.0.0.0", 8765):
        print("WebSocket server running...")
        await asyncio.Future()


asyncio.run(main())