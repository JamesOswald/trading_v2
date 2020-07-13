import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String, Float, DateTime, Text, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from bases.data.base import Base
from time import time
from datetime import datetime 
from models.symbol import Symbol
from time import time
from models.backtester.test import Test


class StrategySession(Base):
    __tablename__='strategy_session'
    id=Column(Integer, primary_key=True)
    strategy_id = Column(Integer, ForeignKey('worker.id'))
    symbols = Column(ARRAY(Integer))
    channels= Column(ARRAY(Integer))
    exchanges= Column(ARRAY(Integer))
    time_created = Column(Integer, default=time())
    time_updated = Column(Integer, onupdate=time())
    time_end = Column(Integer,  nullable=True)
    test_file = Column(String, nullable=True)
    test_id = Column(Integer, ForeignKey('test.id'), nullable=True)
    test = relationship('Test')




    def __init__(self,strategy_id, symbols, depth_symbols, bar_symbols, trade_symbols, channels, exchanges, fee_in_route=None, test=None):
        self.strategy_id = strategy_id
        self.symbols = symbols
        self.depth_symbols = depth_symbols
        self.bar_symbols = bar_symbols
        self.trade_symbols = trade_symbols
        self.channels = channels
        self.exchanges = exchanges
        self.routes = []
        self.oms_routes = []
        self.fee_in_route = fee_in_route
        self.test = test
    

            
