import asyncio
import websockets

clients = set()


async def echo(websocket):
    clients.add(websocket)

    try:
        async for message in websocket:

            recipients = [client for client in clients if client != websocket]

            for client in recipients:
                try:
                    await client.send(message)

                except Exception as e:
                    clients.remove(client)

    except Exception as e:
        print(f"Servidor: ERRO na conexão com {websocket.remote_address}: {str(e)}")
    finally:
        clients.remove(websocket)



async def main():

    async with websockets.serve(echo, "0.0.0.0", 8765):
        await asyncio.Future()


if __name__ == "__main__":
    print("Iniciando aplicação WebSocket...")
    asyncio.run(main())