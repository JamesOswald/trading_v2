import json
from autobahn.twisted.websocket import WebSocketServerProtocol
from twisted.internet import reactor

class WebSocket(WebSocketServerProtocol):
    def onConnect(self, response):
        print('Server connected. {}'.format(response.peer))

    def onOpen(self):
        print('open')

    def onMessage(self, payload, isBinary):
        data = json.loads(payload.decode('utf8'))
        print('data')

    def onClose(self, wasClean, code, reason):
        print('Websocket connection closed: {}'.format(reason))