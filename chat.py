import json
from enum import Enum

from aiohttp import web
from aiohttp.web_request import Request


class MessageType(Enum):
    MESSAGE = 'MSG'
    DIRECT_MESSAGE = 'DM'
    USER_ENTER = 'USER_ENTER'
    USER_LEAVE = 'USER_LEAVE'


class WSChat:
    def __init__(self, host: str = '127.0.0.1', port: int = 8888):
        self.host = host
        self.port = port
        self.connections: dict[str, web.WebSocketResponse] = {}

    def run(self):
        app = web.Application()

        async def main_page(request):
            return web.FileResponse('./index.html')

        app.router.add_get('/', main_page)
        app.router.add_get('/chat', self.process_request)

        web.run_app(app, host=self.host, port=self.port)

    async def process_request(self, request: Request):
        web_socket = web.WebSocketResponse()
        await web_socket.prepare(request)

        json_data = None
        async for message in web_socket:
            data = message.data
            if data == 'ping':
                await web_socket.send_str('pong')
                continue

            json_data = json.loads(data)
            if json_data['mtype'] == 'INIT':
                self.connections[json_data['id']] = web_socket
                await self.update_page(MessageType.USER_ENTER,
                                       json_data['id'])
            else:
                if json_data['to'] is None:
                    await self.update_page(MessageType.MESSAGE,
                                           json_data['id'],
                                           json_data['text'])
                else:
                    await self.update_page(MessageType.DIRECT_MESSAGE,
                                           json_data['id'],
                                           json_data['text'],
                                           json_data['to'])

        await self.update_page(MessageType.USER_LEAVE, json_data['id'])
        del self.connections[json_data['id']]

    async def update_page(self, message_type: MessageType, from_id: str,
                          text: str = None, recipient: str = None):
        data = {
            'mtype': message_type.value,
            'id': from_id
        }
        if text is not None:
            data['text'] = text
        if recipient is not None:
            await self.connections[recipient].send_json(data)
            return
        for to_id, web_socket in self.connections.items():
            if to_id != from_id:
                await web_socket.send_json(data)


if __name__ == '__main__':
    WSChat().run()
