import os, sys, signal
import _pickle as p
import json
import numpy as np
import uuid

from bases.exchange_worker_base import ExchangeWorkerBase
from sqlalchemy import inspect
from time import sleep
from multiprocessing import Process, Queue, Manager
from common.generic_consumer import start_consumer_process
from common.set_with_multiprocessing import set_with_multiprocessing
from common.two_way_dict import TwoWayDict
from test.random_triangular_arbitrage import RandomTriangularArbitrage, DepthGenerator
from test.statistical_arbitrage_backtest import StatisticalArbitrageTest, BarGenerator
from test.saved_test import SavedTestRunner


from models.route import Route
from models.backtester.test import Test
from models.enums.channel_enums import ChannelEnum
from models.enums.test_type import TestTypeEnum
from models.enums.orders.order_status_enum import OrderStatusEnum
from models.enums.orders.order_side_enum import OrderSideEnum
from models.enums.orders.order_type_enum import OrderTypeEnum

class BackTestWorker(ExchangeWorkerBase): 
    def __init__(self):
        super(BackTestWorker, self).__init__(10)
        self.test_enum_to_class_map = TwoWayDict()
        self.test_enum_to_class_map[TestTypeEnum.RandomTriangularArbitrage] = RandomTriangularArbitrage
        self.test_enum_to_class_map[TestTypeEnum.SavedTest] = SavedTestRunner
        self.test_enum_to_class_map[TestTypeEnum.StatisticalArbitrage] = StatisticalArbitrageTest
        self.running_tests = self.manager.dict()
        self.open_orders = self.manager.dict()
        self.exchange_orders = self.manager.dict()

        self.OrderSideMap = TwoWayDict()
        self.OrderSideMap['BUY'] = OrderSideEnum.BUY
        self.OrderSideMap['SELL'] = OrderSideEnum.SELL
    
    def depth_publisher(self, depth_feeder: DepthGenerator):
        previous_timestamp = 0
        for timestamp in sorted(depth_feeder.timestamp_depth_map.keys()):
            sleep(timestamp - previous_timestamp)
            self.publish_depth_out(depth_feeder.timestamp_depth_map[timestamp], depth_feeder.symbol.id)
            previous_timestamp = timestamp
        print("All timestamps completed for: {}".format(depth_feeder.symbol))
            
    def depth_worker(self):
        # for every symbol in self.depth_symbols create processes which send out test depths to the correct depth out routes at the correct time
        depth_feeders = self.test.get_depth_feeders()
        depth_publisher_processes = [Process(target=self.depth_publisher, args=(depth_feeder)) for depth_feeder in depth_feeders.values()]
        
        # start all depth publishing
        for depth_publisher_process in depth_publisher_processes: 
            depth_publisher_process.start()

        # wait for all proceses to execute 
        for depth_publisher_process in depth_publisher_processes:
            depth_publisher_process.join() 

        # remove all the depth symbols so that the strategy may be tested again.
        for key in self.depth_symbols.keys():
            self.depth_symbols.pop(key)
        
        self.test.cleanup(self.session)
        self.test = None
    
    def bar_publisher(self, bar_feeder: BarGenerator): 
        previous_timestamp = 0
        for timestamp in sorted(bar_feeder.timestamp_bar_map.keys()):
            sleep(0.25)
            self.publish_bar_out(bar_feeder.timestamp_bar_map[timestamp], bar_feeder.symbol.id)
            previous_timestamp = timestamp
        print("All timestamps completed for: {}".format(bar_feeder.symbol))
    
    def bar_worker(self): 
        # for every symbol in self.bar_symbols create processes which send out test depths to the correct depth out routes at the correct time
        bar_publisher_processes = [Process(target=self.bar_publisher, args=(self.test.bar_feeders[symbol_id],)) for symbol_id in self.bar_symbols.keys()]
        # print([self.test.bar_feeders[symbol_id].timestamp_bar_map for symbol_id in self.bar_symbols.keys()])
        
        # start all bar publishing
        for bar_publisher_process in bar_publisher_processes: 
            bar_publisher_process.start()

        # wait for all proceses to execute 
        for bar_publisher_process in bar_publisher_processes:
            bar_publisher_process.join() 

        # remove all the bar symbols so that the strategy may be tested again.
        for key in self.bar_symbols.keys():
            self.bar_symbols.pop(key)
        
        self.test.cleanup(self.session)
        self.test = None
        
    def session_subscribe_callback(self, route, method, properties, body):
        backtest_config, strategy_session = p.loads(body)
        symbols = [s for s in self.symbols if s.id in strategy_session.symbols]
        test_type_enum = int(backtest_config["BACKTEST_CLASS_ENUM"])
        self.test = self.test_enum_to_class_map[TestTypeEnum(test_type_enum)](self.session, self.exchange, symbols, backtest_config) #creating new test
        # add test to running test
        set_with_multiprocessing(self.running_tests, self.test, strategy_session.id)
        # add test to db
        self.session.add(self.test) 
        strategy_session.test = self.test # adds the test to this strategy session so that this test's dataset is linked to the strategy_session
        self.session.add(strategy_session)
        body = p.dumps(strategy_session)
        # finish hooking up routes
        super().session_subscribe_callback(route, method, properties, body)
        self.session.expire_on_commit = False 
        if self.test.fee.recording:
            strategy_session.test.fee.test = self.test
            self.session.add(self.test.fee)
        self.session.commit()
        print('Executing Test: {}'.format(self.test))
        #start the depth_worker which produces a test and feeds it to the strategy using ExchangeWorkerBase interface
        if ChannelEnum.DEPTH.value in strategy_session.channels:
            depth_worker_process = Process(target=self.depth_worker)
            depth_worker_process.start()

        if ChannelEnum.BAR.value in strategy_session.channels:
            bar_worker_process = Process(target=self.bar_worker)
            bar_worker_process.start()

    def orders_in_callback(self, route, method, properties, body):
        order = p.loads(body)
        symbol = [s for s in self.symbols if s.id == order.symbol_id][0]
        base = symbol.base
        quote = symbol.quote
        if order.order_type == OrderTypeEnum.MARKET:
            if order.side == OrderSideEnum.BUY:
                if self.test.balances[quote] < order.quote_quantity:
                    raise Exception('Invalid order: Balance less than order price.')
                else:
                    base_purchased, quote_remaining = self.calculate_order(order, order.side, order.order_type)
                    self.test.balances[quote] -= (order.quote_quantity - quote_remaining)
                    self.test.balances[base] += base_purchased * (1-self.test.fee.taker)
                    order.status = OrderStatusEnum.FILLED
                    order.exchange_order_id=uuid.uuid4()
            if order.side == OrderSideEnum.SELL:
                if self.test.balances[base] < order.quantity:
                    raise Exception('Invalid order: Balance less than order quantity')
                else:
                    quote_purchased, base_remaining = self.calculate_order(order, order.side, order.order_type)
                    self.test.balances[base] -= (order.quantity - base_remaining)
                    self.test.balances[quote] += quote_purchased * (1-self.test.fee.taker)
                    order.status = OrderStatusEnum.FILLED
                    order.exchange_order_id=uuid.uuid4()
            self.exchange_orders[order.exchange_order_id] = order
            self.open_orders[order.uuid] = order
            self.publish_order_out(order)
            print(self.test.balances)
        else:
            raise NotImplementedError

        
    def calculate_order(self, order, side, order_type):
        orderbook = self.test.get_current_orderbook(order.order_create_time, order.symbol_id)
        if side == OrderSideEnum.BUY and order_type == OrderTypeEnum.MARKET:
            avg_price, base_purchased, quote = orderbook.take_from_ask(order.quote_quantity)
            return base_purchased, quote
        if side == OrderSideEnum.SELL and order_type == OrderTypeEnum.MARKET:
            avg_price, quote_purchased, base = orderbook.take_from_bid(order.quantity)
            return quote_purchased, base
        if side == OrderSideEnum.BUY and order_type == OrderTypeEnum.LIMIT:
            raise NotImplementedError
        if side == OrderSideEnum.SELL and order_type == OrderTypeEnum.LIMIT:
            raise NotImplementedError

    def fee_grab_callback(self, route, method, properties, body):
        fee_out_route = p.loads(body)
        self.publish_fee_out(self.running_tests[fee_out_route.strategy_session_id].fee, fee_out_route)

    def start(self): 
        """
        backtester requires special start function
        """
        super().start()
        # corrs = []
        # symbols = [self.symbol_service.get_symbol_by_id('1431'), self.symbol_service.get_symbol_by_id('1433')]
        # for i in range(0, 25):
        #     corrs.append(StatisticalArbitrageTest(self.session, self.exchange,symbols,{'BACKTEST_CONFIG_FILE_LOCATION': '/test/config/stat_arb_test_config.txt'}).corr)
        # print("avg: {}".format(np.mean(corrs)))

        while True:
            sleep(1) 



        
