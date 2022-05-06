from models.backtester.test import Test
from models.backtester.depth_feeder import DepthFeeder
from models.enums.test_type import TestTypeEnum
from models.symbol import Symbol
from typing import List
import typing
from data.sql import SQL
from sqlalchemy import (Column, DateTime, Float, ForeignKey, Integer, String,
                        Time)
from time import time
from sqlalchemy.orm import relationship, column_property
from models.depth import Depth
from models.fee import Fee
class SavedTestRunner(Test): 
    __mapper_args__ = {
        'polymorphic_identity':TestTypeEnum.SavedTest.value,
    }
    original_test_id = Column(Integer, ForeignKey('test.id'))
    test = relationship('Test', remote_side='Test.id')

    def __init__(self, session, exchange, symbols: List[Symbol], backtest_config):
        self.symbols = symbols
        self.exchange = exchange
        self.session = session
        super().__init__(TestTypeEnum.SavedTest.value)
        self.original_test_id = int(backtest_config["BACKTEST_PREVIOUS_TEST_ID"])
        self.test = self.session.query(Test).filter(Test.id == self.original_test_id).one()
        self.depths = self.session.query(Depth).filter(Depth.test_id == self.original_test_id).all()
        self.fee = self.session.query(Fee).filter(Fee.test_id == self.original_test_id).one()
        self.fee.recording = False
        self.fee.symbol = None
        self.fee.exchange = self.exchange

        for depth in self.depths: 
            depth.parse_side_dictionary(session)
        for depth in self.depths: 
            depth.recording = False
        for symbol in self.symbols: 
            self.add_depth_feeder(symbol)

        self.session = None # avoid multiprocessing pickling errors 
           

    def add_depth_feeder(self, symbol): 
        if not self.depth_feeders: 
            self.depth_feeders = {}
        timestamp_depth_map = {depth.timestamp: depth for depth in self.depths if depth.symbol_id == symbol.id}
        
        self.depth_feeders[symbol.id] = DepthFeeder(symbol, timestamp_depth_map)
    
    def cleanup(self, session):
        for depth in self.depths: 
            depth.test_id = self.original_test_id
        session.commit()
        
