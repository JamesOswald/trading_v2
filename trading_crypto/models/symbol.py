import os
import sys

from bases.data.base import Base
from sqlalchemy import Column, Float, ForeignKey, Integer, String, Boolean
from sqlalchemy.orm import relationship

#model imports
from models.token import Token

class Symbol(Base):
    __tablename__='symbol'
    id=Column(Integer, primary_key=True)
    ticker=Column(String, nullable=False)
    tick_size=Column(Float)
    base_id=Column(Integer, ForeignKey('token.id'), nullable=False)
    quote_id=Column(Integer, ForeignKey('token.id'), nullable=False)
    exchange_id=Column(Integer, ForeignKey('exchange.id'), nullable=False)
    base = relationship('Token', foreign_keys=[base_id])
    quote = relationship('Token', foreign_keys=[quote_id])
    exchange = relationship('Exchange')

    def __init__(self, ticker="", tick_size=0, base_id=None, quote_id=None, exchange_id=0):
        self.ticker = ticker
        self.tick_size = tick_size
        self.base_id = base_id
        self.quote_id = quote_id
        self.exchange_id = exchange_id

    def get_symbol_string(self):
        if (self.is_future or self.is_option):
            return self.ticker
        return "{}/{}".format(self.base, self.quote)

    def get_symbol_route(self, session_id):
        if (self.is_future or self.is_option):
            return "{}.{}".format(self.ticker, session_id)
        return "{}.{}.{}".format(self.base, self.quote, session_id)

    def get_symbol_exchange_route(self):
        if (self.is_future or self.is_option):
            return "{}.{}".format(self.exchange_id, self.ticker)
        return "{}.{}.{}".format(self.exchange_id, self.base, self.quote)

    def get_token_ids(self):
        return [self.base_id, self.quote_id]
    
    def __repr__(self):
        return "Symbol<{}>".format(self.ticker)

    def get_other_token_id(self, token_id):
        if self.base_id == token_id:
            return self.quote_id
        elif self.quote_id == token_id:
            return self.base_id
        return None

