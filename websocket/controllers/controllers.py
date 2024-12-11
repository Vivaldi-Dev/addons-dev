import json
from curses import wrapper

from OpenSSL.rand import status

from odoo import http
from odoo.http import request
import threading
import websockets
import werkzeug
import asyncio

# Lista de clientes WebSocket ativos
active_websockets = []

class Websocket(http.Controller):
    @http.route('/websocket/send_message', auth='public', type="json", methods=['POST'])
    def index(self, **kw):
        data = request.jsonrequest
        name = data.get("name")
        state = data.get("state")
        message = data.get("message")
        description = data.get("description", "")

        if name and state and message:
            websocket_record = request.env['websocket.websocket'].sudo().create({
                'name': name,
                'state': state,
                'message': message,
                'description': description,
            })

            threading.Thread(target=self.send_to_relevant_websockets, args=(name, state, message, description)).start()

            return {
                'status': 'success',
                'data': {
                    'id': websocket_record.id,
                    'name': websocket_record.name,
                    'state': websocket_record.state,
                    'message': websocket_record.message,
                },
            }

        return {
            'status': 'error',
            'message': 'Campos obrigatórios faltando (name, state, message)',
        }


    def send_to_relevant_websockets(self, name, state, message, description):
        message_data = {
            'name': name,
            'state': state,
            'message': message,
            'description': description,
        }

        self.send_message_to_websockets(message_data)

    def send_message_to_websockets(self, message_data):
        uri = "ws://localhost:8765"
        try:
            asyncio.run(self.send_message(uri, message_data))
        except Exception as e:
            print(f"Erro ao enviar mensagem via WebSocket: {e}")

    async def send_message(self, uri, message_data):
        async with websockets.connect(uri) as websocket:
            await websocket.send(str(message_data))

    @http.route('/websocket/data', auth='none', type='http', csrf=False,methods=['GET'])
    def data(self, **kw):
        try:

            records = request.env['websocket.websocket'].sudo().search([])

            info = []
            for record in records:
                info.append({
                    'name': record.name,
                    'state': record.state,
                    'message': record.message,
                    'description': record.description,
                })

            return werkzeug.wrappers.Response(
                json.dumps(info),
                headers=[('Content-Type', 'application/json')],
                status=200

            )

        except Exception as e:

            error_message = {'error': f"An error occurred: {str(e)}"}
            return werkzeug.wrappers.Response(
                json.dumps(error_message),
                headers=[('Content-Type', 'application/json')],
                status=500

            )
