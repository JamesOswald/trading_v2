import os
import sys

from bases.data.base import Base
from sqlalchemy import Column, Float, ForeignKey, Integer, String, Boolean
from sqlalchemy.orm import relationship

#model imports
from models.symbol import Symbol
from models.worker import Worker


class Fee(Base):
    __tablename__='fee'
    id=Column(Integer, primary_key=True)
    maker = Column(Float)
    taker = Column(Float)
    exchange_id = Column(Integer, ForeignKey('exchange.id'), nullable=False)
    symbol_id = Column(Integer, ForeignKey('symbol.id'), nullable=True)
    #test_id = Column(Integer, ForeignKey('test.id'), nullable=True)
    #test = relationship('Test')
    exchange = relationship('Exchange', foreign_keys=[exchange_id])
    symbol = relationship('Symbol')

    def __init__(self, exchange, maker, taker, symbol=None):
        self.exchange = exchange
        self.maker = maker
        self.taker = taker
        self.symbol = symbol
    
    def __repr__(self):
        if self.symbol: 
            return "Fee<{}: maker: {} taker: {}>".format(self.symbol, self.maker, self.taker)
        else:
            return "Fee<{}: maker: {} taker: {}>".format(self.exchange, self.maker, self.taker)