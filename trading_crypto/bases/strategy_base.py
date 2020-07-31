#not refactored yet
import _pickle as p
import atexit
import json
import os
import signal
import sys
import time
from functools import wraps
from multiprocessing import Manager, Process, Queue
from threading import Thread
from time import sleep
import psutil

from common import routes
from common.mq_session import MQSession
from common.two_way_dict import TwoWayDict
from common.set_with_multiprocessing import set_with_multiprocessing
from bases.data.sql import SQL
from bases.data.base import Session
from dotenv import load_dotenv
from models.depth import Depth
from enums.channel import ChannelEnum
from enums.route_type import RouteTypeEnum
from enums.order.order_status_enum import OrderStatusEnum
from enums.order.order_type_enum import OrderTypeEnum
# from enums.state_enum import StateEnum
from models.order import Order
from models.strategy_session import StrategySession
from models.symbol import Symbol
from models.token import Token
from services.utility.symbol_service import SymbolService
from services.utility.token_service import TokenService
from common.generic_consumer import start_consumer_process, generic_consumer
# from services.utility.twilio_service import TwilioService
from services.utility.worker_service import WorkerService
from bases.worker_base import WorkerBase
import typing
from typing import List
from models.worker import Worker
from models.route import Route
from models.strategy import Strategy
from models.manager import Manager
from models.backtester.test import Test
from models.strategy_config import StrategyConfig, Channel

class StrategyBase(WorkerBase):
    def __init__(self, config_path, start_later=False):
        signal.signal(signal.SIGINT, self.handler)
        self.config = StrategyConfig.from_json(session=Session(), config_path=config_path)
        super().__init__(worker_id=self.config.strategy_id)
        self.symbol_service = SymbolService()
        self.token_service = TokenService()
        self.worker_service = WorkerService()
        # self.twilio_service = TwilioService()
        self.session = self.sql.get_session()
        self.session.expire_on_commit = False
        

        self.exchanges = self.manager.list()
        self.symbols = self.manager.list()
        self.channels = self.manager.list()

        self.exchanges.extend(self.get_exchanges())
        self.symbols.extend(self.get_symbols())
        self.channels.extend(self.get_channels())
        

        self.fees = self.manager.dict()
        # self.state = StateEnum.Stop
        self.orders=self.manager.dict()
        self.routes = self.manager.dict()

        self.channel_route_type_map = TwoWayDict()
        self.channel_route_type_map[ChannelEnum.DEPTH] = (RouteTypeEnum.STRATEGY_RECIEVE_DEPTH, self.depth_callback)
        self.channel_route_type_map[ChannelEnum.BAR] = (RouteTypeEnum.STRATEGY_RECIEVE_BAR, self.bar_callback)
        self.channel_route_type_map[ChannelEnum.TRADES] = (RouteTypeEnum.STRATEGY_REVIEVE_TRADE, self.trades_callback)
        
        

        if not start_later: 
            self.start_session()

    def exit(self):
        print('Exiting Strategy')

    def end_session(self):
        return 0

    def session_unsubscribe(self):
        _, channel = self.mq_session.session()
        for exchange in self.exchanges:
             channel.basic_publish(exchange='', routing_key="{}_session_unsubscribe".format(exchange.name), body=p.dumps(self.strategy_session))
        _.close()

    
    def handler(self, signum, frame):
        #self.session_unsubscribe() 
        sys.exit(0)

    def depth_callback(self, route, method, properties, body):
        raise NotImplementedError
    
    def bar_callback(self, route, method, properties, body):
        raise NotImplementedError

    def trades_callback(self, route, method, properties, body):
        raise NotImplementedError
    
    def order_callback(self, route, method, properties, body):
        raise NotImplementedError

    def balance_callback(self, route, method, properties, body):
        raise NotImplementedError
    
    #can be overriden if other functionality other than just saving the fees for p&l calculations
    # fees may be accessed by the fee manager dict
    def fee_callback(self, route, method, properties, body):
        fee = p.loads(body)
        set_with_multiprocessing(self.fees, fee,fee.exchange)

    def fetch_fee(self, exchange):
        _, channel = self.mq_session.session()
        channel.basic_publish(exchange='', routing_key="{}_grab_fee".format(exchange.name), body=p.dumps(self.strategy_session.fee_in_route))
        _.close()

    def get_exchanges(self) -> List[int]:
        """
        Override to change how the strategy grabs the exchange ids it needs to trade, by deafult this uses an enviorment variable called EXCHANGES
        """
        symbol_ids = []
        for c in self.config.channels:
            for s in c.symbols:
                if s.id not in symbol_ids:
                    symbol_ids.append(s.id)
        symbols = self.symbol_service.get_symbols_from_array(symbol_ids)
        exchange_ids = []
        for symbol in symbols:
            if symbol.exchange_id not in exchange_ids:
                exchange_ids.append(symbol.exchange_id)
        return self.worker_service.get_workers_from_id_array(exchange_ids)
    
    def get_symbols(self) -> List[Symbol]:
        """
        Override to change how the strategy grabs the symbols it needs to trade, by deafult this uses an enviorment variable called SYMBOLS
        """
        symbol_ids = []
        for c in self.config.channels:
            for s in c.symbols:
                if s.id not in symbol_ids:
                    symbol_ids.append(s.id)
        return self.symbol_service.get_symbols_from_array(symbol_ids)
    
    def get_channels(self) -> List[int]: 
        """
        Override to change how the strategy grabs the channels that it needs to trade, by default this uses an enviorment variable called CHANNELS
        """
        return [v for v in self.config.channels]
    
    def get_tokens(self) -> List[Token]:
        """
        Override to change how the strategy grabs the tokens that it needs to trade, by default this gets all tokens linked to the tradeable symbols
        """
        base_ids = [t.base_id for t in self.symbols]
        quote_ids = [t.quote_id for t in self.symbols]
        return self.token_service.get_tokens_by_token_ids(base_ids + quote_ids)

    def send_order(self, order):
        _, channel = self.mq_session.session()
        #save the order to the current session
        self.orders[(order.exchange_id, order.symbol_id, order.create_timestamp)] = order
        #get the correct route for the symbol/order
        oms_route = [route for route in self.strategy_session.oms_routes if route.route_type == RouteTypeEnum.STRATEGY_SUBMIT_ORDER and route.symbol_id == order.symbol_id][0]
        print(oms_route.route_string)
        channel.basic_publish(exchange='', routing_key=oms_route.route_string, body=p.dumps(order))
        _.close()

    def handle_exception(self, e):
        print('handling exception')
        print(e)
    
    def get_custom_identifier(self, channel, symbol): 
        return None

    def start_session(self):
        connection, channel = self.mq_session.session()
        
        channels = self.get_channels()

        depth_symbols = []
        bar_symbols = []
        trade_symbols = []
        
        for c in self.config.channels:
            if c.channel_type == ChannelEnum.DEPTH:
                depth_symbols = c.symbols
            if c.channel_type == ChannelEnum.BAR.value:
                bar_symbols = c.symbols
            if c.channel_type == ChannelEnum.TRADES.value:
                trade_symbols = c.symbols
        channel_dict_map = {}
        channel_dict_map[ChannelEnum.DEPTH] = (depth_symbols, "depth")
        channel_dict_map[ChannelEnum.BAR] = (bar_symbols, "bar")
        channel_dict_map[ChannelEnum.TRADES] = (trade_symbols, "trade")

        print(depth_symbols)
        #create new strategy session
        self.strategy_session = StrategySession(strategy_id=self.worker.id, symbols=[s.id for s in self.symbols], depth_symbols=[s.id for s in depth_symbols], bar_symbols=[s.id for s in bar_symbols], trade_symbols=[s.id for s in trade_symbols], channels=[c.channel_type.value for c in channels], exchanges=[e.id for e in self.exchanges])
        self.session.add(self.strategy_session)
        self.session.commit()

        print(self.strategy_session.depth_symbols)
        # setup fee in route for this strategy
        fee_in_route = Route(RouteTypeEnum.OTHER, consumer_worker=self.worker, strategy_session_id=self.strategy_session.id, channel=channel, route_string="{}_fee_in".format(self.worker.id))
        self.strategy_session.fee_in_route = fee_in_route

        #get all tie used in trading
        self.tokens = self.get_tokens()
        
        start_consumer_process(fee_in_route.route_string, self.fee_callback, self.mq_session)

        self.oms_worker = self.session.query(Worker).filter(Worker.name == 'OMS').one()
        
        #generate all dynamic routes
        sleep(2)
        for exchange in self.strategy_session.exchanges:
            exchange = self.session.query(Worker).filter(Worker.id == exchange).one()
            route_session = MQSession()
            for c in self.strategy_session.channels:
                route_type, callback = self.channel_route_type_map[ChannelEnum(c)]
                route = Route(route_type=route_type, publisher_worker=exchange, consumer_worker=self.worker, channel=channel, strategy_session_id=self.strategy_session.id, route_string='{}_{}'.format(exchange, c))
                self.strategy_session.routes.append(route)
                arguments={'x-match' : 'any'}
                for symbol in channel_dict_map[ChannelEnum(c)][0]:
                    if symbol.exchange_id == exchange.id:
                        arguments[symbol.ticker] = symbol.id
                channel.queue_declare(queue=route.route_string)
                channel.queue_bind(exchange='{}_{}'.format(exchange.name, channel_dict_map[ChannelEnum(c)][1]), queue=route.route_string, routing_key='', arguments=arguments)
                start_consumer_process(queue=route.route_string, callback=callback, mq_session=route_session)
            for symbol in self.symbols: 
                if symbol.exchange_id == exchange.id:
                    if not self.config.meta:
                        # hook up and create order in and out routes
                        route = Route(RouteTypeEnum.STRATEGY_RECIEVE_ORDER, self.oms_worker, self.worker, channel, symbol=symbol, strategy_session_id=self.strategy_session.id)
                        #time.sleep(0.2)
                        start_consumer_process(route.route_string, self.order_callback, route_session)
                        self.strategy_session.oms_routes.append(route)
                        self.strategy_session.oms_routes.append(Route(RouteTypeEnum.STRATEGY_SUBMIT_ORDER, self.worker, self.oms_worker, channel, symbol=symbol, strategy_session_id=self.strategy_session.id))
                        self.strategy_session.oms_routes.append(Route(RouteTypeEnum.OMS_RECIEVE_ORDER, exchange, self.oms_worker, channel, symbol=symbol, strategy_session_id=self.strategy_session.id))
                        self.strategy_session.oms_routes.append(Route(RouteTypeEnum.OMS_SUBMIT_ORDER, self.oms_worker, exchange, channel, symbol=symbol, strategy_session_id=self.strategy_session.id)) 
            if not self.config.meta:
                #start balance subscriber for exchange
                route = Route(RouteTypeEnum.STRATEGY_RECIEVE_BALANCE, self.oms_worker, self.worker, channel, strategy_session_id=self.strategy_session.id, custom_identifier=str(exchange.id))
                self.strategy_session.oms_routes.append(route)
                start_consumer_process(route.route_string, self.balance_callback, route_session)
                self.strategy_session.oms_routes.append(Route(RouteTypeEnum.OMS_RECIEVE_BALANCE, exchange, self.oms_worker, channel, strategy_session_id=self.strategy_session.id))
                    
            # notify exchange of subscription event
            if not self.config.is_backtest:
                channel.basic_publish(exchange='', routing_key="{}_session_subscribe".format(exchange.name.lower()), body=p.dumps(self.strategy_session))
            else: 
                #all enviroment variables needed for running the backtest begin with the prefix BACKTEST and are passed to the backtester these can be modified in the respective strategy backtest env file
                backtest_config = {k:v for k,v in os.environ.items() if 'BACKTEST_' in k}
                channel.basic_publish(exchange='', routing_key=routes.backtester_session_subscribe, body=p.dumps((backtest_config, self.strategy_session)))

        #notify oms and logger of subscription event if not meta
        if not self.config.meta:
            channel.basic_publish(exchange='', routing_key="oms_session_subscribe", body=p.dumps(self.strategy_session))
            channel.basic_publish(exchange='', routing_key="logger_session_subscribe", body=p.dumps(self.strategy_session))

        #add all routes to the database
        for route in self.strategy_session.routes:
            self.session.add(route)
        for oms_route in self.strategy_session.oms_routes: 
            self.session.add(oms_route)


        self.session.commit()
        os.environ["SESSION_ID"] = str(self.strategy_session.id)
       
        connection.close()
        self.session.close()
        # self.state = StateEnum.Start
        sleep(2)