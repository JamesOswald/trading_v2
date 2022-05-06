import random
import math
import numpy as np
import pandas as pd
import typing
from typing import List
from scipy import array, linalg, dot

#model imports
from models.backtester.bar_feeder import BarFeeder
from models.backtester.depth_feeder import DepthFeeder
from models.backtester.test import Test
from models.symbol import Symbol
from models.depth import Depth
from models.fee import Fee
from models.bar import Bar

#enum imports
from enums.depth_side import DepthSideEnum


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