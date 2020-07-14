#standard imports
import asyncio
import datetime
import json
import os
import pickle as p
import time
import typing
import threading


from autobahn.asyncio.websocket import WebSocketClientFactory, WebSocketClientProtocol
from bases.exchange_worker_base import ExchangeWorkerBase
from services.gdax_service import GdaxService
from multiprocessing import Manager, Pool, Process, Queue
from common.set_with_multiprocessing import set_with_multiprocessing
from common.generic_consumer import start_consumer_process
from time import sleep


try:
    import thread
except ImportError:
    import _thread as thread

#enum imports
from enums.channel import ChannelEnum
from enums.granularity import GranularityEnum

#model imports
from models.depth import Depth
from models.websocket import WebSocket

class GdaxWS(WebSocket):
    def __init__(self, socket_url):
        super(GdaxWS, self).__init__(socket_url)
        _, self.channel = self.mq_session.session()

    def on_message(self, message):
        data = json.loads(message)
        if data['type'] == 'snapshot' or data['type'] == 'l2update':
            ticker = data['product_id']
            queue = 'gdax_internal_depth_{}'.format(ticker)
            self.channel.basic_publish(exchange='', routing_key=queue, body=p.dumps(data))

        if data['type'] == 'ticker':
            ticker = data['product_id']
            queue = 'gdax_internal_bar_{}'.format(ticker)
            self.channel.basic_publish(exchange='', routing_key=queue, body=p.dumps(data))

        if data['type'] == 'match':
            ticker = data['product_id']
            queue = 'gdax_internal_trade_{}'.format(ticker)
            self.channel.basic_publish(exchange='', routing_key=queue, body=p.dumps(data))


class GdaxWorker(ExchangeWorkerBase):
    def __init__(self):
        exchange_id = int(os.getenv("GDAX_EXCHANGE_ID"))
        super(GdaxWorker, self).__init__(exchange_id)
        self.socket_url = os.getenv("GDAX_SOCKET_URL")
        self.gdax_service = GdaxService(self.exchange)
        self.incoming_depths = self.manager.dict()
        self.open_orders = self.manager.dict()
        self.exchange_websocket = GdaxWS(self.socket_url)
        self.message_subscription_map = {
            ChannelEnum.DEPTH: ["level2"],
            ChannelEnum.TRADES: ["matches"],
            ChannelEnum.BAR: ["ticker", "heartbeat"]
        }

    def listen_worker(self, channel_enum): 
        """
        Checks all three channels for new subscription events, creates websockets accordingly, route dictionary is either depth_symbols, trade_symbols or bar_symbols
        """ 
        
        channel_dictionary_map = {
            ChannelEnum.DEPTH : self.depth_symbols,
            ChannelEnum.BAR : self.bar_symbols, 
            ChannelEnum.TRADES: self.trade_symbols
        }
        print(self.depth_symbols)
        already_added_symbols = []
        channel_dictionary = channel_dictionary_map[channel_enum]
        try:
            new_symbols = [x for x in channel_dictionary if x not in already_added_symbols]
            if new_symbols:
                ticker_id_map = {s.ticker:s.id for s in self.symbols if s.id in new_symbols}
                print("Starting new {} worker".format(channel_enum))
                subscription_message = {
                    "type": "subscribe",
                    "product_ids": list(ticker_id_map.keys()),
                    #"product_ids": ["BTC-USD"],
                    "channels": self.message_subscription_map[channel_enum]
                }
                if channel_enum == ChannelEnum.DEPTH:
                    set_with_multiprocessing(obj=self.exchange_websocket.ticker_id_map_depth, value=ticker_id_map, key='dict_type')
                if channel_enum == ChannelEnum.BAR:
                    self.exchange_websocket.ticker_id_map_bar = ticker_id_map
                if channel_enum == ChannelEnum.TRADES:
                    self.exchange_websocket.ticker_id_map_trade = ticker_id_map
                payload = json.dumps(subscription_message, ensure_ascii=False).encode('utf8')
                print('sending message...')
                self.exchange_websocket.ws.send(data=payload)
                already_added_symbols.extend(new_symbols)
        except Exception as e:
            print("Error : listen_worker {}".format(e))
            
    def start_consumers(self):
        #start_consumer_process(queue='gdax_internal_depth_BTC-USD', callback=self.depth_consumer, mq_session=self.mq_session)
        for ticker in self.exchange_websocket.ticker_id_map_depth.keys():
            start_consumer_process(queue='gdax_internal_depth_{}'.format(ticker), callback=self.depth_consumer, mq_session=self.mq_session)
        for ticker in self.exchange_websocket.ticker_id_map_bar.keys():
            start_consumer_process(queue='gdax_internal_bar_{}'.format(ticker), callback=self.bar_consumer, mq_session=self.mq_session)
        for ticker in self.exchange_websocket.ticker_id_map_trade.keys():
            start_consumer_process(queue='gdax_internal_trade_{}'.format(ticker), callback=self.trade_consumer, mq_session=self.mq_session)
 
    def depth_consumer(self, route, method, properties, body): 
        data = p.loads(body)
        symbol_id = self.exchange_websocket.ticker_id_map_depth[data['product_id']]
        bid = False
        ask = False
        if data['type'] == 'snapshot':
            symbol = [s for s in self.symbols if s.id == symbol_id][0]
            depth = Depth(symbol=symbol, timestamp=time.time())
            depth.bids = {float(exchange_bid[0]): float(exchange_bid[1]) for exchange_bid in data['bids']}
            depth.asks = {float(exchange_ask[0]): float(exchange_ask[1]) for exchange_ask in data['asks']}
            set_with_multiprocessing(self.incoming_depths, depth, symbol_id)
        if data['type'] == 'l2update':
            depths = self.incoming_depths
            depth = depths[symbol_id]            
            for change in data['changes']:
                if change[0] == "buy":
                    if float(change[2]) == 0:
                        depth.set_remove_bid(float(change[1]), sort_book=False)
                    else:
                        depth.set_bid(change[1], change[2], sort_book=False)
                    bid = True
                else:
                    if float(change[2]) == 0:
                        depth.set_remove_ask(float(change[1]), sort_book=False)
                    else:
                        depth.set_ask(change[1], change[2], sort_book=False)
                    ask = True
            if bid: 
                depth.bids = depth.sort_book(depth.bids, desc=True)
            if ask: 
                depth.asks = depth.sort_book(depth.asks)
            depths[symbol_id] = depth
            self.incoming_depths = depths
            self.publish_depth_out(depth=depth, ticker=data['product_id'], symbol_id=symbol_id)

    def bar_consumer(self, route, method, properties, body): 
        # data = p.loads(body)
        # print('price: {}, servertime: {}, localtime: {}'.format(data['price'], datetime.strptime(data['time'], '%Y-%m-%dT%H:%M:%S.%f%z').timestamp(), time.time()))
        # symbol_id = self.exchange_websocket.ticker_id_map_bar[data['product_id']]
        # for queue in bar_queue_dict[symbol_id]: 
        #         queue.put(data)
        pass

    def trade_consumer(self, route, method, properties, body): 
        pass



    def start(self):
        super().start()
        self.exchange_websocket.connect_websocket()
        sleep(5)
        # for channel in ChannelEnum:
        #     print('running')
        #     p = Process(target=self.listen_worker, args=(channel,))
        #     p.start() 
        p = Process(target=self.listen_worker, args=(ChannelEnum.DEPTH,))
        p.start() 
        sleep(2)
        self.start_consumers()

        while True:
            sleep(1)