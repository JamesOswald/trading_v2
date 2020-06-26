import json
from autobahn.asyncio.websocket import WebSocketClientProtocol

class WebSocket(WebSocketClientProtocol):
    def onConnect(self, response):
        print('Server connected. {}'.format(response.peer))

    def onOpen(self):
        print('open')

    def onMessage(self, payload, isBinary):
        data = json.loads(payload.decode('utf8'))
        print('data')

    def onClose(self, wasClean, code, reason):
        print('Websocket connection closed: {}'.format(reason))