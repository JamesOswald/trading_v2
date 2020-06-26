#standard imports
import asyncio
import json
import os
import pickle as p
import time
import typing

from autobahn.asyncio.websocket import WebSocketClientFactory, WebSocketClientProtocol
from bases.exchange_worker_base import ExchangeWorkerBase
from services.gdax_service import GdaxService
from multiprocessing import Manager, Pool, Process, Queue
from time import sleep


try:
    import thread
except ImportError:
    import _thread as thread

#enum imports
from enums.channel import ChannelEnum

#model imports
from models.websocket import WebSocket

class GdaxWS(WebSocket):
    def onOpen(self):
        print('open')

    def onMessage(self, payload, isBinary):
        data = json.loads(payload.decode('utf8'))
        print(data)

class GdaxWorker(ExchangeWorkerBase):
    def __init__(self):
        exchange_id = int(os.getenv("GDAX_EXCHANGE_ID"))
        super(GdaxWorker, self).__init__(exchange_id)
        self.socket_url = os.getenv("GDAX_SOCKET_URL")
        self.gdax_service = GdaxService(self.exchange)
        self.incoming_depths = self.manager.dict()
        self.open_orders = self.manager.dict()

        #start websocket client
        self.ws = WebSocketClientFactory()
        self.ws.protocol = GdaxWS
        loop = asyncio.get_event_loop()
        coro = loop.create_connection(self.ws, self.socket_url, ssl=True)
        loop.run_until_complete(coro)
        loop.run_forever()
        loop.close()
        
        self.message_subscription_map = {
            ChannelEnum.DEPTH: "level2",
            ChannelEnum.TRADES: "matches",
            ChannelEnum.BAR: ["ticker", "heartbeat"]}
        # self.socket_subscriptions = []

    def listen_worker(self, channel_enum): 
        """
        Checks all three channels for new subscription events, creates websockets accordingly, route dictionary is either depth_symbols, trade_symbols or bar_symbols
        """ 
        channel_dictionary_map = {
            ChannelEnum.DEPTH : self.depth_symbols,
            ChannelEnum.BAR : self.bar_symbols, 
            ChannelEnum.TRADES: self.trade_symbols
        }
        already_added_symbols = []
        dictionary = channel_dictionary_map[channel_enum]
        while True:
            try:
                new_symbols = [x for x in dictionary.keys() if x not in already_added_symbols]
                if new_symbols:
                    ticker_id_map = {s.ticker:s.id for s in self.symbols if s.id in new_symbols}
                    print("Starting new {} worker".format(channel_enum))
                    
                    # if channel_enum == ChannelEnum.BAR:  
                    #     for symbol_id in new_symbols:
                    #         symbol = [s for s in self.symbols if s.id == symbol_id][0]
                    #         queue = Queue()
                    #         self.bar_tracker(symbol, self.bar_symbols[symbol_id])
                    subscription_message = {
                        "type": "subscribe",
                        "product_ids": list(ticker_id_map.keys()),
                        "channels": self.message_subscription_map[channel_enum]
                    }
                    payload = json.dumps(subscription_message, ensure_ascii=False).encode('utf8')
                    self.ws.protocol.sendMessage(payload)
                    already_added_symbols.extend(new_symbols)
   
            except Exception as e: 
                print("Error : listen_worker {}".format(e))
            sleep(1)
        print("Listen worker shut down")

    def start(self):
        super().start()

        for channel in ChannelEnum:
            p = Process(target=self.listen_worker, args=(channel,))
            p.start() 

        while True:
            sleep(1)