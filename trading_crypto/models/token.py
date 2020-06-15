#standard imports
import os
import sys

from bases.data.base import Base
from sqlalchemy import Column, Float, ForeignKey, Integer, String, Boolean
from sqlalchemy.orm import relationship

#model imports
from models.exchange import Exchange


class Token(Base):
    __tablename__='tokens'
    id=Column(Integer, primary_key=True)
    ticker=Column(String)
    free=Column(Float, nullable=False)
    locked=Column(Float, nullable=False)
    total=Column(Float, nullable=False)
    exchange_id=Column(Integer, ForeignKey('exchange.id'), nullable=False)
    exchange = relationship('Exchange')

    def __init__(self, ticker="", free=0, locked=0, total=0, exchange_id=-1):
        self.ticker = ticker
        self.free = free
        self.locked = locked
        self.total = free + locked
        self.exchange_id = exchange_id

    def __repr__(self):
        return "Token<{}>".format(self.ticker)
        