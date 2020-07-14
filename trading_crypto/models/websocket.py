import json
import websocket
import threading

from multiprocessing import Queue, Manager
from common.mq_session import MQSession
from common.generic_consumer import start_consumer_process
#from autobahn.asyncio.websocket import WebSocketClientProtocol
try:
    import thread
except ImportError:
    import _thread as thread

#AUTOBAHN
# class WebSocket(WebSocketClientProtocol):
#     def onConnect(self, response):
#         print('Server connected. {}'.format(response.peer))

#     def onOpen(self):
#         print('open')

#     def onMessage(self, payload, isBinary):
#         data = json.loads(payload.decode('utf8'))
#         print('data')

#     def onClose(self, wasClean, code, reason):
#         print('Websocket connection closed: {}'.format(reason))

#WEBSOCKET
class WebSocket():
    def __init__(self, socket_url):
        self.socket_url = socket_url
        self.manager = Manager()
        self.mq_session = MQSession()
        self.ws = None
        self.ticker_id_map_depth = self.manager.dict()
        self.ticker_id_map_bar = self.manager.dict()
        self.ticker_id_map_trade = self.manager.dict()
        self.incoming_depths = self.manager.dict()

    def connect_websocket(self):
        self.ws = websocket.WebSocketApp(self.socket_url, 
                                        on_open = self.on_open, 
                                        on_message = self.on_message,
                                        on_close = self.on_close)
        wst = threading.Thread(target=self.thread_runner)
        wst.daemon = True
        wst.start()

    def thread_runner(self):
        self.ws.run_forever(ping_interval=500)

    def on_open(self):
        print('websocket connected to {}'.format(self.socket_url))

    def on_message(self, message):
        raise NotImplementedError

    def depth_consumer(self):
        raise NotImplementedError

    def bar_consumer(self):
        raise NotImplementedError

    def trade_consumer(self):
        raise NotImplementedError

    def on_error(self, error):
        print(error)

    def on_close(self):
        print('### closed ###')

