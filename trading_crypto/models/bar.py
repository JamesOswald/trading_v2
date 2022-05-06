import os
import sys

from bases.data.base import Base
from sqlalchemy import Column, Float, ForeignKey, Integer, String, Boolean
from sqlalchemy.orm import relationship

#model imports
from models.symbol import Symbol
from models.token import Token
#from models.backtester.test import Test

class Bar(Base): 
    __tablename__='bar'
    id = Column(Integer, primary_key=True)
    _open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=True)
    symbol_id = Column(Integer, ForeignKey('symbol.id'), nullable=False)
    #test_id = Column(Integer, ForeignKey('test.id'), nullable=True)
    timestamp = Column(Integer, nullable=False)
    symbol = relationship('Symbol')
    #test = relationship('Test')

    def __init__(self, timestamp, _open, high, low, close, symbol, volume=None, test=None):
        self._open = _open
        self.high = high
        self.low = low
        self.close = close
        self.symbol = symbol
        self.volume = volume
        self.timestamp = timestamp
        self.test = test
    
    def get_mid_price(self):
        return self.mid_price
    
    def set_mid_price(self):
        self.mid_price = ((self.high + self.low) / 2) + self.low
        return self.mid_price

    def __repr__(self):
        return "Bar<o: {} c: {} h: {} l: {} symbol: {} vol: {} timestamp: {}>".format(self._open, self.close, self.high, self.low, self.symbol, self.volume, self.timestamp)
        


