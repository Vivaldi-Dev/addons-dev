import pika
import json
import asyncio
import websockets

async def send_to_websocket(message):
    uri = "ws://localhost:8765"
    try:
        async with websockets.connect(uri) as websocket:
            await websocket.send(message)
            print(f"Mensagem enviada ao WebSocket: {message}")
    except Exception as e:
        print(f"Erro ao enviar mensagem via WebSocket: {e}")

def consume_messages():
    def callback(ch, method, properties, body):
        message = json.loads(body)
        print("Mensagem recebida do RabbitMQ:", message)

        # Enviar a mensagem para o WebSocket
        asyncio.run(send_to_websocket(json.dumps(message)))

    try:

        connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        channel = connection.channel()

        channel.queue_declare(queue='attendance_queue')

        channel.basic_consume(
            queue='attendance_queue',
            on_message_callback=callback,
            auto_ack=True
        )
        print("Aguardando mensagens...")
        channel.start_consuming()
    except Exception as e:
        print(f"Erro no consumidor: {e}")

if __name__ == "__main__":
    consume_messages()
