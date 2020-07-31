import pika
import signal
import json
import time
import pickle as p

from bases.worker_base import WorkerBase
from common import routes
from common.generic_consumer import start_consumer_process
from time import sleep
from multiprocessing import Pool, Process, Manager
from services.utility.symbol_service import SymbolService
from services.utility.worker_service import WorkerService
from services.utility.token_service import TokenService

#enum imports
from enums.route_type import RouteTypeEnum
from enums.worker_type import WorkerTypeEnum

#model imports
from models.order import Order
from models.symbol import Symbol
from models.strategy_session import StrategySession
from models.manager import Manager


class OMS(WorkerBase):
    def __init__(self):
        super(OMS, self).__init__()
        self.running=False
        self.running_strategy_sessions = {}

        #declare order managers
        self.strategy_recieve_order_routes = self.manager.dict()
        self.exchange_recieve_order_routes = self.manager.dict()
        self.open_orders = self.manager.dict()
        self.orphan_orders = self.manager.dict()

        self.strategy_recieve_balance_routes = self.manager.dict()
        self.balances = self.manager.dict()

        self.symbol_service = SymbolService(self.session)
        self.worker_service = WorkerService(self.session)
        self.token_service = TokenService(self.session)


     #saves an order to the db 
    def save_order(self, order):
        self.session.add(order)
        self.session.commit()
    
    #Callback for orphan orders
    def orphan_order_callback(self,route, method, properties, body):
        o = p.loads(body)
        print('Orphaned order received')
        print(o)

    #Catches orders from worker that aren't assigned to a strategy
    def orphan_order_in_subscription(self):
        _, channel = self.mq_session.session()
        channel.basic_consume(queue=routes.oms_orphaned_orders, auto_ack=True, on_message_callback=self.orphan_order_callback)
        channel.start_consuming()

    #callback when exchange publishes an order to strategy
    def exchange_worker_order_out_callback(self, route, method, properties, body):
        order = p.loads(body)
        # update_order_process = Process(target=self.update_order, args=(order,))
        # update_order_process.start()
        connection, channel = self.mq_session.session()
        out_route = self.strategy_recieve_order_routes[(order.session_id, order.symbol_id, order.exchange_id)]
        channel.basic_publish(exchange='', routing_key=out_route.route_string, body=p.dumps(order))
        connection.close()
   
    #callback when strategy publishes an order to oms
    def strategy_order_out_callback(self, route, method, properties, body):
        order = p.loads(body)
        #save order
        print('Order Received')
        #save_order_process = Process(target=self.save_order, args=(order,))
        #save_order_process.start()

        connection, channel = self.mq_session.session()
        #get exchange route to publish to
        route = self.exchange_recieve_order_routes[order.symbol_id]
        print(route.route_string)
        channel.basic_publish(exchange='', routing_key=route.route_string, body=p.dumps(order))
        connection.close()

    def  exchange_worker_order_out_subscriber(self, order_out_route):
         _, channel = self.mq_session.session()
         print("oms: subscribing to {}".format(order_out_route))
         channel.basic_consume(queue=order_out_route, auto_ack=True, on_message_callback=self.exchange_worker_order_out_callback)
         channel.start_consuming()
         _.close()
            
    
    # the callback for starting a strategy_session, this generates subscribers for all the order_in routes from strategy_session
    # and then publishes to the respective exchanges the strategy_session.id, so they can initalize their routes
    def oms_session_subscriber_callback(self, route, method, properties, body):
        strategy_session = p.loads(body)
        self.running_strategy_sessions[strategy_session.id] = strategy_session
        
        # setup routes recieved from new subscribing strategy
        for oms_route in strategy_session.oms_routes:
            if oms_route.route_type == RouteTypeEnum.STRATEGY_SUBMIT_ORDER: # recieve order from strategy
                start_consumer_process(oms_route.route_string, self.strategy_order_out_callback, self.mq_session)
            elif oms_route.route_type == RouteTypeEnum.STRATEGY_RECIEVE_ORDER: # publish order to strategy
                self.strategy_recieve_order_routes[(oms_route.strategy_session_id, oms_route.symbol_id, oms_route.symbol.exchange_id)] = oms_route
            elif oms_route.route_type == RouteTypeEnum.STRATEGY_RECIEVE_BALANCE: # publish balance to strategy 
                self.strategy_recieve_balance_routes[(strategy_session.id, oms_route.custom_identifier)] = oms_route
            elif oms_route.route_type == RouteTypeEnum.OMS_RECIEVE_BALANCE: # recieve balance from exchange
                start_consumer_process(oms_route.route_string, self.balance_callback, self.mq_session)
            elif oms_route.route_type == RouteTypeEnum.OMS_RECIEVE_ORDER: 
                start_consumer_process(oms_route.route_string, self.exchange_worker_order_out_callback, self.mq_session) #recive order from excahgne
            elif oms_route.route_type == RouteTypeEnum.OMS_SUBMIT_ORDER: 
                self.exchange_recieve_order_routes[oms_route.symbol_id] = oms_route #submit order to exchange

            
   
    def balance_callback(self, route, method, properties, body):
        balances = p.loads(body)
        _,channel = self.mq_session.session()
        #to do implement strategy_session specific balances, 
        # when that becomes a thing, add to the key of self.strategy_balance_routes s.t. key=(startegy_session.id, exchange_id)
        # in oms_session_subscriber_callback, for now, just using exchange_id as the key
        print('balance received')
        
        if isinstance(balances, (list,)):
            for balance in balances:
                self.balances[balances.exchange_id][balances.base.ticker] = balances.base
                self.balances[balances.exchange_id][balances.quote.ticker] = balances.quote
                channel.basic_publish(exchange='', routing_key=self.strategy_recieve_balance_routes[balance.exchange_id], body=p.dumps(balance))
       
        if isinstance(balances, (Symbol, )):
            self.balances[balances.exchange_id][balances.base.ticker] = balances.base
            self.balances[balances.exchange_id][balances.quote.ticker] = balances.quote
            channel.basic_publish(exchange='', routing_key=self.strategy_recieve_balance_routes[balances.exchange_id], body=p.dumps(balances))
        
    def start(self):
        #declare static queues 
        print("Declaring Queues")
        _, channel = self.mq_session.session()
        channel.queue_declare(queue=routes.oms_session_subscribe)
        channel.queue_declare(queue=routes.oms_balance_update)
        channel.queue_declare(queue=routes.oms_orphaned_orders)
        channel.queue_purge(queue=routes.oms_session_subscribe)
        channel.queue_purge(queue=routes.oms_balance_update)
        print("Starting Balance Consumers")

        self.exchanges = self.worker_service.get_workers_by_type(WorkerTypeEnum.EXCHANGE)

        for exchange in self.exchanges:
            self.balances[exchange.id] = self.manager.dict()

        print("Starting Session Subscriber")
        #subscribe to new static queue to get dynamically generate oms routes
        start_consumer_process(routes.oms_session_subscribe, self.oms_session_subscriber_callback, self.mq_session)
        #Orphan order watcher
        start_consumer_process(routes.oms_orphaned_orders, self.orphan_order_callback, self.mq_session)

        print("Starting Exchange Worker")
        #subscribe to the exchange worker order route
        #this special queue posts all the order_out routes generated by every exchange worker, 
        _.close()
        
        self.running=True
        while True: 
            sleep(1)