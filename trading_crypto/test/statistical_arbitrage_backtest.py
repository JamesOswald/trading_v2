from models.backtester.bar_feeder import BarFeeder
from models.backtester.depth_feeder import DepthFeeder
from models.backtester.test import Test
from models.enums.test_type import TestTypeEnum
from models.enums.depth_side import DepthSideEnum
from typing import List
import random
import math
import numpy as np
from matplotlib import pyplot as plt
from matplotlib import dates, ticker
import mplfinance
from scipy import array, linalg, dot
import typing
from models.symbol import Symbol
from models.depth import Depth
from models.fee import Fee
from models.bar import Bar
import os
import pandas as pd
from models.stats.bar_stats import BarStatistics

class BarGenerator(BarFeeder):
    def __init__(self, symbol:Symbol, volatility:float, bias:float, expected_return:float, granularity:int, num_bars:int, num_depths:int, min_book_quantity:float, max_book_quantity:float, book_size:int, min_book_spacing:float, max_book_spacing:float, timestamps:List[int]=None):
        self.symbol = symbol
        self.timestamp_bar_map = {}
        self.volatility = volatility
        self.bias = bias
        self.expected_return = expected_return
        self.granularity = granularity
        self.num_bars = num_bars
        self.num_depths = num_depths
        self.min_book_quantity = min_book_quantity
        self.max_book_quantity = max_book_quantity
        self.book_size = book_size
        self.min_book_spacing = min_book_spacing
        self.max_book_spacing = max_book_spacing
        self.timestamps = timestamps if timestamps else self.get_timestamps()
        self.generate_bars_for_timestamps()
        self.create_depth_feeders()
    
    def __repr__(self):
        return('BarGenerator:<{}, num_bars: {}, granularity: {}'.format(self.symbol, self.num_bars, self.granularity))


    def generate_bars_for_timestamps(self):
        self.mid_prices = self.get_midprices()
        for i in range(0, len(self.timestamps)-1):
            open_p = self.mid_prices[i]
            close_p = self.mid_prices[i+1]
            high_p = (open_p * np.random.uniform(1, 1.001)) if open_p >= close_p else (close_p * np.random.uniform(1, 1.001))
            low_p = (open_p * np.random.uniform(0.999, 1)) if open_p < close_p else (close_p * np.random.uniform(0.999, 1))
            self.timestamp_bar_map[self.granularity*self.timestamps[i]] = Bar(timestamp=self.granularity*self.timestamps[i], _open=open_p, high=high_p, low=low_p, close=close_p, symbol=self.symbol)

    def get_midprices(self, bias=None): 
        """
        Generates a new midprice for this timestamp by using the old price and some exponential factor based on the parameters of the test
        """
        mid_price = bias if bias else self.bias
        mid_prices = []
        for timestamp in self.timestamps:
            timestamp = float(timestamp)
            delta = (self.granularity/31536000)
            epsilon = np.random.normal(0, 0.1, 1)[0]
            mid_price = mid_price * math.exp(self.expected_return * delta + self.volatility * math.sqrt(delta) * float(epsilon))
            mid_prices.append(mid_price)
        return mid_prices

    def get_timestamps(self):
        """
        Generates when the updates will be made to the book by distributing them randomly throughout the runtime. 
        """
        return range(1, self.num_bars + 2)

    def create_depth_feeders(self):
        self.depth_feeder = DepthFeeder(symbol=self.symbol, timestamp_depth_map={})
        for i, timestamp in enumerate(self.timestamp_bar_map):
            depth_timestamps = sorted(np.random.uniform(timestamp-self.granularity, timestamp, self.num_depths))
            for time in depth_timestamps:
                depth_midprice = np.random.normal((self.timestamp_bar_map[timestamp].high + self.timestamp_bar_map[timestamp].low)/2, 0.006)
                self.depth_feeder.timestamp_depth_map[time] = Depth(symbol=self.symbol, base=self.symbol.base, quote=self.symbol.quote, symbol_id=self.symbol.id, timestamp=time)
                self.depth_feeder.timestamp_depth_map[time].bids = self.create_book(DepthSideEnum.bids, depth_midprice)
                self.depth_feeder.timestamp_depth_map[time].asks = self.create_book(DepthSideEnum.asks, depth_midprice)

    def create_book(self, side, midprice):     
        levels = {}
        level_quantity = 0
        for i in range(0, self.book_size): 
            delta = np.random.uniform(self.min_book_spacing * midprice, self.max_book_spacing * midprice)
            level_quantity += np.random.uniform(self.min_book_quantity, self.max_book_quantity)
            if side == DepthSideEnum.bids:
                if midprice - delta > 0:
                    price = midprice - delta
                else: pass
            else: 
                price = midprice + delta
            levels[price] = level_quantity
            midprice = price
        return levels

    
class CorrelatedBarGenerator(BarGenerator): 
    def __init__(self, symbol, predictor:BarGenerator, predictor_parameters, offset:float, volatility:float, correlation:float, num_depths:int, min_book_quantity:float, max_book_quantity:float, book_size:int, min_book_spacing:float, max_book_spacing:float):
        self.predictor = predictor
        self.offset = offset
        self.correlation = correlation
        self.num_depths = num_depths
        self.min_book_quantity = min_book_quantity
        self.max_book_quantity = max_book_quantity
        self.book_size = book_size
        self.min_book_spacing = min_book_spacing
        self.max_book_spacing = max_book_spacing
        predictor_parameters['volatility'] = volatility
        super().__init__(symbol, **predictor_parameters)

    def get_midprices(self):
        cov_matrix = np.array([
            [1, self.correlation],
            [self.correlation, 1]
        ])
        mid_prices = super().get_midprices(bias=self.bias * self.offset)
        uncorrelated_prices = np.array([self.predictor.mid_prices, mid_prices]) #uncorrelated data
        chol = linalg.cholesky(cov_matrix, lower=True) #cholesky decomposition
        self.mid_prices = np.dot(chol, uncorrelated_prices) #compute correlated prices by finding dot product of C and uncorrelated data
        data = []
        for i in range(0, len(self.timestamps)):
            predictor, correlated = self.mid_prices[0][i], self.mid_prices[1][i]
            data.append((predictor, correlated))
        df = pd.DataFrame(data, columns = [0, 1])
        self.corr = df.corr().iloc[0][1]
        return self.mid_prices[1]
    

       
class StatisticalArbitrageTest(Test): 
    __mapper_args__ = { 
        'polymorphic_identity': TestTypeEnum.StatisticalArbitrage.value, 
    }

    def get_depth_feeders(self):
        raise ValueError("You have subscribed to the wrong channel, this test does not provide depths.")

    def read_configuration_from_file(self, config_file_location):
        config_file = open(os.getcwd() + config_file_location, "r")
        symbol_parameters = {}
        for line in config_file:
            if line[0] != "#" and 'fee' not in line and 'balance' not in line: #if this is not a comment
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
                self.fee = Fee(exchange=self.exchange, **{x.split('=')[0]: float(x.split('=')[1]) for x in line[4:].split(',')})
                self.fee.recording = True
            if 'balance' in line:
                variables = line.split(',')
                for x in variables[2:]:
                    token = x.split('=')[0]
                    balance = float(x.split('=')[1])
                    if token in self.balances.keys():
                        self.balances[token] = self.balances[token] + balance
                    elif token not in self.balances.keys():
                        self.balances[token] = balance
                    else:
                        raise Exception("Invalid token and balance")
                print(self.balances)
        config_file.close()
        return symbol_parameters

    def get_current_orderbook(self, timestamp, symbol_id):
        timestamp_depth_map = self.depth_feeders[symbol_id].timestamp_depth_map
        if timestamp in timestamp_depth_map.keys():
            return timestamp_depth_map[timestamp]
        else:
            timestamps = np.fromiter(timestamp_depth_map.keys(), dtype=float)
            neartime = timestamps[timestamps < timestamp].max()
            return timestamp_depth_map[neartime]


    def __init__(self, session, exchange, symbols: List[Symbol], backtest_config):
        super().__init__(TestTypeEnum.StatisticalArbitrage.value)
        self.exchange = exchange
        self.symbols = symbols
        self.bar_feeders = {}
        self.depth_feeders = {}
        self.predictor = None
        self.bar_stats = BarStatistics()
        self.corr = 0
        symbol_parameters = self.read_configuration_from_file(backtest_config["BACKTEST_CONFIG_FILE_LOCATION"])
        for symbol_id, parameters in symbol_parameters.items(): 
            symbol = [s for s in self.symbols if s.id == symbol_id][0]
            if 'correlation' not in parameters.keys():
                if self.predictor is not None: 
                    raise ValueError('Too many predictor symbols specified, all correlated symbols must have correlation fields.')
                self.predictor = BarGenerator(symbol, **symbol_parameters[symbol_id])
                self.predictor_parameters = parameters
                self.bar_feeders[symbol.id] = self.predictor
                self.depth_feeders[symbol.id] = self.predictor.depth_feeder
                #self.bar_stats.plot_moving_price(list(self.bar_feeders[symbol.id].timestamp_bar_map.values()), show=True,start=5)

            else: 
                if self.predictor is None: 
                    raise ValueError('The first symbol specified must be the predictor symbol.')
                #print('generate correlated')
                self.bar_feeders[symbol.id] = CorrelatedBarGenerator(symbol, self.predictor, self.predictor_parameters, **parameters)
                self.depth_feeders[symbol.id] = self.bar_feeders[symbol.id].depth_feeder
                self.corr = self.bar_feeders[symbol.id].corr
                print('correlation: {}'.format(self.corr))
                #self.bar_stats.plot_moving_price(list(self.bar_feeders[symbol.id].timestamp_bar_map.values()), show=True,start=5)