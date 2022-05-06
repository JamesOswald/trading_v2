import random
import math
import numpy as np
from typing import List
import typing

#model imports
from models.backtester.bar_generator import BarGenerator, CorrelatedBarGenerator
from models.backtester.test import Test
from models.symbol import Symbol
from models.depth import Depth

#enum imports
from enums.test_type import TestTypeEnum

class StatisticalArbitrageTest(Test): 
    __mapper_args__ = { 
        'polymorphic_identity': TestTypeEnum.StatisticalArbitrage.value, 
    }

    def get_depth_feeders(self):
        raise ValueError("You have subscribed to the wrong channel, this test does not provide depths.")

    def get_current_orderbook(self, timestamp, symbol_id):
        timestamp_depth_map = self.depth_feeders[symbol_id].timestamp_depth_map
        if timestamp in timestamp_depth_map.keys():
            return timestamp_depth_map[timestamp]
        else:
            timestamps = np.fromiter(timestamp_depth_map.keys(), dtype=float)
            neartime = timestamps[timestamps < timestamp].max()
            return timestamp_depth_map[neartime]


    def __init__(self, session, exchange, symbols: List[Symbol], backtest_config):
        super().__init__(TestTypeEnum.StatisticalArbitrage.value, backtest_config)
        self.exchange = exchange
        self.symbols = symbols
        self.bar_feeders = {}
        self.depth_feeders = {}
        self.predictor = None
        self.corr = 0
        symbol_parameters = backtest_config["SYMBOL_PARAMETERS"]
        for symbol_id, parameters in symbol_parameters.items(): 
            symbol = [s for s in self.symbols if s.id == int(symbol_id)][0]
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