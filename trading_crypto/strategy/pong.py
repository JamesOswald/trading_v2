import sys, os
from models.order import Order
from bases.strategy_base import StrategyBase
from dotenv import load_dotenv
from multiprocessing import Manager, Process
from enums.channel import ChannelEnum
from models.depth import Depth
from time import sleep
import json
import numpy as np
import _pickle as p 
import time
from enums.order.order_side_enum import OrderSideEnum
from enums.order.order_type_enum import OrderTypeEnum
from enums.order.order_status_enum import OrderStatusEnum
from enums.order.order_tif_enum import OrderTifEnum
from enums.granularity import GranularityEnum
import uuid


class Pong(StrategyBase):
    def __init__(self, config_path):
        self.config_path = config_path
        self.manager = Manager()
        self.market_data_queues = self.manager.dict()
        self.market_data_queues[ChannelEnum.DEPTH.name] = self.manager.dict()
        self.market_data_queues[ChannelEnum.TRADES.name] = self.manager.dict()
        self.interval=1
        self.open_orders = self.manager.dict()
        self.balances = self.manager.dict()
        super(Pong, self).__init__(self.config_path) 

    def depth_callback(self, route, method, properties, body):
        # try:
        #print('depth callback')
        depth = p.loads(body)
        print(depth)

    def trades_callback(self, route, method, properties, body):
        trade = p.loads(body)
        print(trade)

    def order_callback(self, route, method, properties, body):
        order = p.loads(body)
        self.open_orders[order.uuid] = order
        print(order)
    
    def balance_callback(self, route, method, properties, body):
        balance = p.loads(body)
        self.balances[balance.asset_id] = balance
        print(balance)
    
    def fee_callback(self, route, method, properties, body):
        fee = p.loads(body)
        print(fee)
    
    def bar_callback(self, route, method, properties, body):
        bar = p.loads(body)
        #print(bar)
    
    def get_custom_identifier(self, channel, symbol):
        if channel == ChannelEnum.BAR.value:
            return GranularityEnum.MINUTE_1.name
        return None

    
    def start(self):
        sleep(5)
        # uuid_value = uuid.uuid4()
        # order = Order(uuid_value,
        # self.symbols[0].id, 
        # order_side=OrderSideEnum.SELL, 
        # session_id=self.strategy_session.id, 
        # exchange_id=3, 
        # order_type=OrderTypeEnum.MARKET,
        # time_in_force=OrderTifEnum.GTC,
        # quote_quantity=0, 
        # base_quantity=20,
        # )
        # self.send_order(order)
        # print('order sent')
        
 
        while True:
            #print("I AM PONG")
            # if order.uuid in self.open_orders.keys() and first ==True:
            #     order = self.open_orders[order.uuid]
            #     print(order.exchange_order_id)
            #     order.side = OrderSideEnum.CANCEL
            #     self.send_order(order)
            #     first = False

            sleep(1)
        
