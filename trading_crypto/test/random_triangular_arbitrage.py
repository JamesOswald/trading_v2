from models.backtester.depth_feeder import DepthFeeder
from models.backtester.test import Test
from models.enums.test_type import TestTypeEnum
from data.base import Base
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy import (Column, DateTime, Float, ForeignKey, Integer, String,
                        Time, Boolean)
import random
import math
import numpy as np
import typing
from typing import List
from models.depth import Depth
from models.enums.depth_side import DepthSideEnum
from models.symbol import Symbol
from time import sleep
from multiprocessing import Process
import os 
from models.fee import Fee
import time
from models.stats.depth_stats import DepthStatistics

class DepthGenerator(DepthFeeder):
    def __init__(self, symbol:Symbol, volatility:float, bias:float, expected_return:float, number_of_updates:int, runtime:int, min_book_spacing:float=0.0001, max_book_spacing=0.01, min_book_quantity=0.001, max_book_quantity=1000, book_size:int=5, timestamps:List[int]=None):
        """
        Simulates a depth for a given Symbol. 
            volatility is a float percentage showing volatility of the asset
            bias is a float is how much the price is offset from 0
            expected_return is a float percentage that the stock is expected to earn, either negative or positive
            number_of_updates is the number of updates that will occur over the runtime of the simulation
            min_book_spacing is the minimum spacing between levels in the book, expressed as a percentage
            max_book_spacing is the maximum spacing between levels in the book, expressed as a percentage 
        """
        self.symbol = symbol
        self.timestamp_depth_map = {}
        self.volatility = volatility
        self.bias = bias
        self.current_mid_price = bias
        self.expected_return = expected_return
        self.runtime = runtime
        self.number_of_updates = number_of_updates
        self.min_book_spacing = min_book_spacing
        self.max_book_spacing = max_book_spacing
        self.min_book_quantity = min_book_quantity
        self.max_book_quantity = max_book_quantity
        self.book_size = book_size
        self.create_time = time.time()
        self.timestamps = timestamps if timestamps else self.get_timestamps()
        self.generate_books_for_timestamps()

    def generate_books_for_timestamps(self):
        for timestamp in self.timestamps:
            self.timestamp_depth_map[timestamp] = Depth(symbol=self.symbol, base=self.symbol.base, quote=self.symbol.quote,symbol_id=self.symbol.id, timestamp=timestamp)
            self.get_new_mid_price(timestamp)
            self.timestamp_depth_map[timestamp].bids = self.generate_side(self.book_size, DepthSideEnum.bids)
            self.timestamp_depth_map[timestamp].asks = self.generate_side(self.book_size, DepthSideEnum.asks)
    
    def get_new_mid_price(self, timestamp): 
        """
        Generates a new midprice for this timestamp by using the old price and some exponential factor based on the parameters of the test
        """
        timestamp = float(timestamp)
        epsilon = np.random.normal(0, 0.1, 1)[0]
        self.current_mid_price = self.current_mid_price * math.exp(self.expected_return * timestamp + self.volatility * math.sqrt(timestamp) * float(epsilon))
        return self.current_mid_price
    
    def get_timestamps(self):
        """
        Generates when the updates will be made to the book by distributing them randomly throughout the runtime. 
        """
        return sorted(np.random.uniform(0, self.runtime, self.number_of_updates))
    
    def generate_side(self, size, side, mid_price=None):
        """
        Generates either the bid or ask side of the book for a inputted mid price (or self.current_mid_price) of a given size
        """
        mid_price = mid_price if mid_price else self.current_mid_price
        levels = {}
        previous_price = mid_price
        level_quantity = 0
        for i in range(0, size): 
            delta = np.random.uniform(self.min_book_spacing * previous_price, self.max_book_spacing * previous_price)
            level_quantity += np.random.uniform(self.min_book_quantity, self.max_book_quantity)
            if side == DepthSideEnum.bids:
                if previous_price - delta > 0:
                    price = previous_price - delta
                else: pass
            else: 
                price = previous_price + delta
            levels[price] = level_quantity
            previous_price = price
        return levels

class RandomTriangularArbitrage(Test):
    
    __mapper_args__ = {
        'polymorphic_identity':TestTypeEnum.RandomTriangularArbitrage.value,
    }

    def read_configuration_from_file(self, config_file_location): 
        config_file = open(os.getcwd() + config_file_location, "r")
        symbol_parameters = {}
        for line in config_file:
            if line[0] != "#" and 'fee' not in line: #if this is not a comment
                variables = line.split(',')
                #split the line into kwargs used for the specific depth 
                #creates a map between the configuration for the depth and a symbol: int(variables[0])
                symbol_parameters[int(variables[0])] = {x.split('=')[0]: x.split('=')[1] for x in variables[1:]}
                #converts all the values into either floats or integers
                for name, value in symbol_parameters[int(variables[0])].items():
                    if "float" in value:
                        value = value.replace("float", "")
                        symbol_parameters[int(variables[0])][name] = float(value)
                    elif "int" in value: 
                        value = value.replace("int", "")
                        symbol_parameters[int(variables[0])][name] = int(value)
                    else: 
                        raise Exception("Invalid backtest value at: {} for symbol_id: {}".format(name, int(variables[0])))
            if 'fee' in line:
                print(self.exchange)
                self.fee = Fee(exchange=self.exchange, **{x.split('=')[0]: float(x.split('=')[1]) for x in line[4:].split(',')})
                self.fee.recording = True

        config_file.close()
        return symbol_parameters

    def __init__(self, session, exchange, symbols: List[Symbol], backtest_config):
        super().__init__(TestTypeEnum.RandomTriangularArbitrage.value)
        self.exchange = exchange
        self.symbols = symbols
        self.depth_feeders = {}
        self.fee = None
        symbol_parameters = self.read_configuration_from_file(backtest_config["BACKTEST_CONFIG_FILE_LOCATION"])
        for symbol in self.symbols: 
            self.depth_feeders[symbol.id] = DepthGenerator(symbol, **symbol_parameters[symbol.id])
            self.depths.extend(list(self.depth_feeders[symbol.id].timestamp_depth_map.values()))
        