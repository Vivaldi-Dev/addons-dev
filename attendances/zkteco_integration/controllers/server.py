import asyncio
import websockets

clients = set()
messages_queue = {}

async def echo(websocket):
    clients.add(websocket)
    print(f"Client connected: {websocket.remote_address}")

    if websocket.remote_address in messages_queue:
        missed_messages = messages_queue[websocket.remote_address]
        print(f"Missed messages for {websocket.remote_address}: {missed_messages}")
        for message in missed_messages:
            try:
                await websocket.send(message)
                print(f"Missed message sent to {websocket.remote_address}: {message}")
            except Exception as e:
                print(f"Error sending missed message to {websocket.remote_address}: {e}")

        del messages_queue[websocket.remote_address]

    try:
        async for message in websocket:
            print(f"Message received from {websocket.remote_address}: {message}")

            for client in clients:
                if client != websocket:
                    try:
                        await client.send(message)
                        print(f"Message sent to {client.remote_address}: {message}")
                    except Exception as e:
                        print(f"Error sending message to {client.remote_address}: {e}")
    except websockets.exceptions.ConnectionClosed as e:
        print(f"Connection closed with {websocket.remote_address}: {e}")
    except Exception as e:
        print(f"Error: {e}")
    finally:

        clients.remove(websocket)
        print(f"Client disconnected: {websocket.remote_address}")

        if websocket.remote_address not in messages_queue:
            messages_queue[websocket.remote_address] = []

        for message in list(messages_queue.values()):
            messages_queue[websocket.remote_address].append(message)

        print(f"Updated message queue for {websocket.remote_address}: {messages_queue}")

async def main():
    async with websockets.serve(echo, "0.0.0.0", 8765):
        print("WebSocket server running...")
        await asyncio.Future()

asyncio.run(main())
