#standard imports
import copy
import numpy as np
import typing

from bases.data.base import Base
from common.statistics import online_weighted_moving_average
from matplotlib import pyplot as plt
from sqlalchemy import Column, Float, ForeignKey, Integer, String, Boolean
from sqlalchemy.orm import relationship

#enum imports
from enums.depth_side import DepthSideEnum

#model imports
from models.order import Order
from models.symbol import Symbol
from models.token import Token
from models.text_pickle_type import TextPickleType

class DepthLevel():
    def __init__(self, bid_price=0, bid_quantity=0, ask_price=0, ask_quantity=0, level=-1):
        self.bid_price = bid_price
        self.ask_price = ask_price
        self.ask_quantity = ask_quantity
        self.level = level

class Depth(Base):
    __tablename__='depth'
    id = Column(Integer, primary_key=True)
    symbol_id=Column(Integer, ForeignKey('symbol.id'), nullable=False)
    base=Column(String, ForeignKey("token.ticker"), nullable=False)
    quote=Column(String, ForeignKey("token.ticker"), nullable=False)
    base_id=Column(Integer, ForeignKey("token.id"), nullable=False)
    quote_id=Column(Integer, ForeignKey("token.id"), nullable=False)
    bids=Column(TextPickleType()) #{float(price): float(quantity)}
    asks=Column(TextPickleType()) #{float(price): float(quantity)}
    timestamp=Column(Float, nullable=True)
    symbol = relationship("Symbol")
    base_ticker = relationship("Token", foreign_keys=[base])
    quote_ticker = relationship("Token", foreign_keys=[quote])
    base_obj = relationship("Token", foreign_keys=[base_id])
    quote_obj = relationship("Token", foreign_keys=[quote_id])
    

    def __init__(self, symbol, timestamp=0):
        if type(symbol) == int:
            self.symbol_id = symbol
        else:
            self.symbol = symbol
        self.base_id = self.symbol.base_id
        self.quote_id = self.symbol.quote_id
        self.bids  = {}
        self.asks  = {}
        self.timestamp = timestamp
        self.recording = True 
         
    def __repr__(self):
        return "Depth<{}>".format(self.print_spread())

    def add_bid(self, price, quantity):
        if price in self.bids.keys():
            self.bids[float(price)] += float(quantity)
        else:
            self.bids[float(price)] = float(quantity)
        self.bids = self.sort_book(self.bids, desc=True)
    
    def set_bid(self, price, quantity, sort_book=True):
        self.bids[float(price)] = float(quantity)
        if sort_book:
            self.bids = self.sort_book(self.bids, desc=True)
    
    def set_ask(self, price, quantity, sort_book=True):
        self.asks[float(price)] = float(quantity)
        if sort_book:
            self.asks = self.sort_book(self.asks)

    def set_remove_bid(self, price, sort_book=True):
        if float(price) in self.bids.keys():
            self.bids.pop(float(price))
            if sort_book:
                self.bids = self.sort_book(self.bids, desc=True)

    def set_remove_ask(self, price, sort_book=True):
        if float(price) in self.asks.keys():
            self.asks.pop(float(price))
            if sort_book:
                self.asks = self.sort_book(self.asks)
            
    #Dont use this
    def remove_ask(self, price, quantity):
        if price in self.asks and self.asks[price]-quantity > 0:
            self.asks[price] -= float(quantity)
            return
        elif price in self.asks and self.asks[price]-quantity <= 0:
            del self.asks[price]
            return
        self.asks = self.sort_book(self.asks, desc=True)
    
    def get_sorted_side(self, bid=True):
        if bid: 
            return self.sort_book(self.bids)
        else: 
            return self.sort_book(self.asks)

    def sort_book(self, book, desc=False):
        return {k:book[k] for k in sorted(book, reverse=desc)}
    
    def clear_book(self):
        self.asks = {}
        self.bids = {}

    def trim(self, value):
        min_bid = list(self.bids.keys())[value-1]
        max_ask = list(self.asks.keys())[value-1]
        trimmed_depth = Depth(self.symbol, self.base, self.quote, self.symbol_id)
        trimmed_depth.bids = {k: v for k, v in self.bids.items() if k >= min_bid}
        trimmed_depth.asks = {k: v for k, v in self.asks.items() if k <= max_ask}
        return trimmed_depth

    def get_inside_bid(self):
        price = np.max(list(self.bids.keys()))
        quantity = self.bids[price]
        return price, quantity

    def get_inside_ask(self):
        price = np.min(list(self.asks.keys()))
        quantity = self.asks[price]
        return price, quantity

    def get_level(self, take_level):
        level = DepthLevel()
        level.bid_price = list(self.bids.keys())[take_level]
        level.bid_quantity = self.bids[list(self.bids.keys())[take_level]]
        level.ask_price =list(self.asks.keys())[take_level]
        level.ask_quantity = self.asks[list(self.asks.keys())[take_level]]
        level.level = take_level
        return level
    
    def print_spread(self):
        bid = self.get_inside_bid()
        ask = self.get_inside_ask()
        return('{}: b: {}: {} a: {}:{}'.format(self.symbol.ticker, bid[0], bid[1], ask[0], ask[1]))

    def get_mid_price(self):
        bid = self.get_inside_bid()[0]
        ask = self.get_inside_ask()[0]
        return ((ask - bid) / 2.0) + bid

    def is_crossed(self):
        if list(self.bids.keys())[0] > list(self.asks.keys())[0]:
            return True
        return False

    def plot_book(self): 
        self.sort_book(self.bids,  desc=True)
        self.sort_book(self.asks)
        
        bid_prices = list(self.bids.keys()) 
        bid_quantities = list(self.bids.values())
        ask_prices = list(self.asks.keys())
        ask_quantities = list(self.asks.values())

        plt.fill_between(bid_prices, bid_quantities, step="pre", alpha=0.4)
        plt.fill_between(ask_prices,ask_quantities, step="pre", alpha=0.4)
        plt.plot(bid_prices, bid_quantities, label="bids", drawstyle="steps")
        plt.plot(ask_prices, ask_quantities, label="asks", drawstyle="steps")
        plt.ylabel("Quantity ({})".format(self.base))
        plt.xlabel("Price ({})".format(self.quote))
        plt.legend()
        plt.show()
    
    def parse_side_dictionary(self, session=None):
        """
        Convert the database representation of the bids and asks into proper bid ask objects, fetches the symbol object if a session is provided
        """
        self.bids = self.sort_book({float(price):quantity for price, quantity in self.bids.items()}, desc=True)
        self.asks = self.sort_book({float(price):quantity for price, quantity in self.bids.items()})
        if session:
            self.symbol = session.query(Symbol).filter(Symbol.id == self.symbol_id).one()
        return self

    def take_from_ask(self, quote_quantity, modify_book: bool=False, create_orders: bool=False) -> (float, float, float): 
        """
        Takes from the ask, returns the average price paid (in quote), the total purchaced quantity (in base) 
        and the leftover quantity (in the case that the quote is not fully used and the entire book is consumed)
        optionally, this returns a list of orders to complete this trade
        """
        total_purchased_base_quantity = 0
        average_price = 0
        if modify_book:
            book = self.asks
        else:
            book = copy.deepcopy(self.asks)
        for level_price, level_quantity in list(book.items()):
            if level_price * level_quantity <= quote_quantity: # we buy the entire ask level
                purchased_quantity = level_quantity # we purchased this entire level
                quote_quantity -= level_price * level_quantity # we purchased level_price worth of the base and have reduced the amount we have left to purchase with by level_price
                book.pop(level_price)
            else: # the price is higher than the quote_quantity we are buying with
                #We can only purchase some i.e. if we have 5000 to buy with and it costs 10000 then we can buy half the level.
                purchased_quantity = quote_quantity / level_price
                book[level_price] -= purchased_quantity
                quote_quantity = 0
            total_purchased_base_quantity += purchased_quantity
            average_price = online_weighted_moving_average(average_price, total_purchased_base_quantity, level_price, purchased_quantity)
            if quote_quantity == 0: 
                break           
        return average_price, total_purchased_base_quantity, quote_quantity  

    def take_from_bid(self, base_quantity, modify_book: bool=False, create_orders: bool=False) -> (float, float, float):
        """
        Takes from the bid
        """
        total_purchased_quote_quantity = 0
        average_price = 0
        if modify_book: 
            book = self.bids
        else: 
            book = copy.deepcopy(self.bids)
        for level_price, level_quantity in list(book.items()): 
            if  level_quantity <= base_quantity: # we consume the entire level
                purchased_quantity = level_price * level_quantity # amount of quote that we recieve from selling level_quantity
                book.pop(level_price)
                base_quantity -= level_quantity
            else: # the level is larger than the quote
                purchased_quantity = base_quantity * level_price
                book[level_price] -= base_quantity
                base_quantity = 0
            total_purchased_quote_quantity += purchased_quantity       
            average_price = online_weighted_moving_average(average_price, total_purchased_quote_quantity, level_price, purchased_quantity)
            if base_quantity == 0:
                break

        return average_price, total_purchased_quote_quantity, base_quantity
