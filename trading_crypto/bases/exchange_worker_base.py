#standard imports 
import os
import _pickle as p
import psutil
import pika
import signal
import sys

from bases.data.sql import SQL
from bases.worker_base import WorkerBase
from common.generic_consumer import start_consumer_process
from common.set_with_multiprocessing import set_with_multiprocessing
from common.two_way_dict import TwoWayDict
from multiprocessing import Process, Queue, Manager
from services.utility.symbol_service import SymbolService
from services.utility.token_service import TokenService
from time import sleep
from manager.oms import OMS

#enum imports
from enums.channel import ChannelEnum
from enums.route_type import RouteTypeEnum

#model imports
from models.symbol import Symbol
from models.exchange import Exchange
from models.worker import Worker
#from models.fee import Fee
#from models.route import Route
#from models.strategy_session import StrategySession

from common import routes

class ExchangeWorkerBase(WorkerBase):
    
    def __init__(self, worker_id): 
        super(ExchangeWorkerBase, self).__init__(worker_id=worker_id)
        signal.signal(signal.SIGINT, self.handler)
        self.worker = self.worker
        self.exchange = self.session.query(Exchange).filter(Exchange.id == self.worker.id).one()
        self.manager = Manager()
        self.strategy_sessions = self.manager.dict()
        self.save_depth_queue = Queue()
        self.save_fee_queue = Queue() 
        self.depth_subscriber_queue = Queue()
        self.bar_subscriber_queue = Queue()
        self.trade_subscriber_queue = Queue()
        self.order_routes = self.manager.dict()
        self.exchange_session_subscribe = ""
        self.exchange_depth_request = ""
        self.exchange_service_request = ""
        self.symbols = self.manager.list()
        self.tokens = self.manager.list()
        self.depth_symbols = self.manager.list()
        self.bar_symbols = self.manager.list()
        self.trade_symbols = self.manager.list()
        self.balance_routes = self.manager.dict()
        self.route_manager_map = TwoWayDict()
        self.symbol_service = SymbolService()
        self.token_service = TokenService()
        
        self.route_manager_map[RouteTypeEnum.STRATEGY_RECIEVE_DEPTH] = self.depth_symbols
        self.route_manager_map[RouteTypeEnum.STRATEGY_REVIEVE_TRADE] = self.trade_symbols
        self.route_manager_map[RouteTypeEnum.STRATEGY_RECIEVE_BAR] = self.bar_symbols


    def handler(self, signum, frame):
        sys.exit(0)

    def orders_in_callback(self, route, method, properties, body):
        #override this method and implement send to exchange flow
        raise NotImplementedError

    def fee_grab_callback(self, route, method, properties, body):
        """
          override this method and implement fee request flow, the body of this callback 
          function is a route object to send the fee back to
        """
      
        raise NotImplementedError

    def publish_order_out(self, order): 
        connection, channel = self.mq_session.session()
        #If Orphan send to orphan endpoint
        if order.strategy_id == -1 or order.session_id == -1:
            channel.basic_publish(exchange='', routing_key=routes.oms_orphaned_orders, body=p.dumps(order))
        else:
            out_route = self.order_routes[order.session_id, order.symbol_id]
            channel.basic_publish(exchange='', routing_key=out_route.route_string, body=p.dumps(order))
        connection.close()

    def publish_balances_out(self, balances):
        """
        Publish multiple balances to strategy and oms
        """
        _, channel = self.mq_session.session()
        for balance in balances:
            channel.basic_publish(exchange="", routing_key=routes.oms_balance_update, body=p.dumps(balance))
        _.close()

    def publish_depth_out(self, depth, ticker, symbol_id):
        _, channel = self.mq_session.session()
        channel.basic_publish(exchange='{}_depth'.format(self.worker.name), routing_key='', body=p.dumps(depth), properties=pika.BasicProperties(headers={ticker : symbol_id}))

    def publish_trade_out(self, trade): 
        _, channel = self.mq_session.session()
        channel.basic_publish(exchange='{}_trade'.format(self.worker.name), routing_key='', body=p.dumps(trade), properties=pika.BasicProperties(headers={ticker : symbol_id}))
    
    def publish_bar_out(self, bar, symbol_id): 
        _, channel = self.mq_session.session()
        channel.basic_publish(exchange='{}_bar'.format(self.worker.name), routing_key='', body=p.dumps(bar), properties=pika.BasicProperties(headers={ticker : symbol_id}))
    
    # def publish_fee_out(self, fee: Fee, out_route: Route): 
    #     _, channel = self.mq_session.session()
    #     channel.basic_publish(exchange="", routing_key=out_route.route_string, body=p.dumps(fee))
    #     _.close()
    
    def session_unsubscribe_callback(self, route, method, properties, body):
        strategy_session = p.loads(body)
        del self.strategy_sessions[strategy_session.id]

    # this is a special queue subscription, 
    # which generates all (exchange)_(symbol)_orders_in and (exchange)_(symbol)_orders_out
    # routes for a specific strategy session, it appends the strategy_session to the list of running strategies 
    # and tells oms to subscribe to these orders_out_routes
    def session_subscribe_callback(self, route, method, properties, body):
        strategy_session = p.loads(body)
        self.strategy_sessions[strategy_session.id] = strategy_session
        print('New Strategy: {} subscribing'.format(strategy_session.id))
        
        # deal with order and balance routes
        for oms_route in strategy_session.oms_routes:
            if oms_route.route_type == RouteTypeEnum.OMS_RECIEVE_ORDER and oms_route.symbol.exchange_id == self.exchange.id: 
                self.order_routes[oms_route.strategy_session_id, oms_route.symbol_id] = oms_route
            elif oms_route.route_type == RouteTypeEnum.OMS_SUBMIT_ORDER and oms_route.symbol.exchange_id == self.exchange.id:
                start_consumer_process(oms_route.route_string, self.orders_in_callback, self.mq_session)
            elif oms_route.route_type == RouteTypeEnum.OMS_RECIEVE_BALANCE: 
                if oms_route.symbol_id in self.balance_routes.keys(): 
                    self.balance_routes[oms_route.symbol_id].append(oms_route)
                else: 
                    self.balance_routes[oms_route.symbol_id] = [oms_route]

        # deal with market data channels 
        set_with_multiprocessing(obj=self.depth_symbols, value=strategy_session.depth_symbols)
        set_with_multiprocessing(obj=self.bar_symbols, value=strategy_session.bar_symbols)
        set_with_multiprocessing(obj=self.trade_symbols, value=strategy_session.trade_symbols)


    def get_symbols(self):
        """
        Override to change what symbols the exchange has avaialable to trade with
        """
        return self.symbol_service.get_symbols_by_exchange(self.exchange.id)

    def get_tokens(self):
        """
        Override to change what tokens the exchange has available to trade with
        """
        return self.token_service.get_tokens_by_exchange(self.exchange.id)
    
    # def save_depth_queue_listener(self):
    #     while True:
    #         if self.save_depth_queue.get():
    #             depth = self.save_depth_queue.get()
    #             if depth.recording: 
    #                 self.session.add(depth)
    #                 self.session.commit()
    #         else:
    #             sleep(0.25)

    def start(self):
        self.symbols.extend(self.get_symbols())
        self.tokens.extend(self.get_tokens())
        # get fixed routes for the exchange
        self.exchange_session_subscribe = getattr(routes, "{}_session_subscribe".format(self.exchange.name.lower()))
        self.exchange_session_unsubscribe = "{}_session_unsubscribe".format(self.exchange.name)
        self.grab_fee_route = "{}_grab_fee".format(self.exchange.name)
        #declare fixed routes for the exchange
        _, channel = self.mq_session.session() 
        channel.exchange_declare(exchange='{}_depth'.format(self.worker.name), exchange_type='headers')
        channel.exchange_declare(exchange='{}_bar'.format(self.worker.name), exchange_type='headers')
        channel.exchange_declare(exchange='{}_trade'.format(self.worker.name), exchange_type='headers')
        channel.queue_declare(queue=self.exchange_session_subscribe)
        channel.queue_declare(queue=self.grab_fee_route)
        channel.queue_declare(queue=self.exchange_session_unsubscribe)
        
        #purge queues
        channel.queue_purge(self.exchange_session_subscribe)
        channel.queue_purge(queue=self.grab_fee_route)
        channel.queue_purge(self.exchange_session_unsubscribe)
        
        # start_consumer_process(self.grab_fee_route, self.fee_grab_callback, self.mq_session)
        # #subscribe to subscribe_session
        start_consumer_process(self.exchange_session_subscribe, self.session_subscribe_callback, self.mq_session)
        start_consumer_process(self.exchange_session_unsubscribe, self.session_unsubscribe_callback, self.mq_session)


       