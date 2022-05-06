import os
import sys
from datetime import datetime
from time import time

from bases.data.base import Base
from sqlalchemy import (Column, DateTime, Float, ForeignKey, Integer, String,
                        Time)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

#enum imports
from enums.order.order_status_enum import OrderStatusEnum
from enums.order.order_tif_enum import OrderTifEnum
from enums.order.order_type_enum import OrderTypeEnum

class Order(Base):
    __tablename__='order'
    id = Column(Integer, primary_key=True)
    uuid = Column(UUID(as_uuid=True), unique=True, nullable=False)
    symbol_id = Column(Integer, ForeignKey('symbol.id'), nullable=False)
    base_id = Column(Integer, ForeignKey('token.id'), nullable=False)
    quote_id = Column(Integer, ForeignKey('token.id'), nullable=False)
    order_side = Column(Integer, nullable=False)
    order_type = Column(Integer, nullable=False)
    base_quantity = Column(Float(precision=8,asdecimal=False), nullable=False)
    quote_quantity = Column(Float(precision=8,asdecimal=False), nullable=True)
    price=Column(Float(precision=8,asdecimal=False), nullable=True)
    quantity_filled=Column(Float, default=0.0)
    order_status = Column(Integer, nullable=False)
    time_in_force=Column(Integer, default=OrderTifEnum.NOACK)
    create_timestamp = Column(Integer, default=time())
    update_timestamp = Column(Integer, onupdate=time())
    exchange_order_id=Column(String)
    exchange_id=Column(Integer, ForeignKey('exchange.id'),nullable=False)
    #strategy_id=Column(Integer, ForeignKey('strategy.id'))
    #session_id=Column(Integer, ForeignKey('strategy_session.id'))
    #strategy = relationship('Worker', foreign_keys=[strategy_id]) #TODO
    #strategy_session = relationship('StrategySession')
    exchange = relationship('Exchange', foreign_keys=[exchange_id])
    symbol = relationship('Symbol')
    base = relationship('Token', foreign_keys=[base_id])
    quote = relationship('Token', foreign_keys=[quote_id])
    #test_id = Column(Integer, ForeignKey('test.id'), nullable=True)
    #test = relationship("Test", back_populates="orders")
  

    def __init__(self, uid="", symbol_id=0, 
    order_side=0, order_type=100, order_status=100, quote_quantity=0,
    base_quantity=0, price=0, quantity_filled=0, 
    exchange_order_id="", 
    exchange_id=0, 
    session_id=0, fee=0, fee_asset="",
    time_in_force=OrderTifEnum.NOACK, 
    create_timestamp=time(),
    time_updated = time()):
        self.symbol_id = symbol_id
        self.uuid = uid if uid else uuid.uuid4()
        self.order_side = order_side
        self.order_type = order_type
        self.order_status = order_status
        self.exchange_order_id=exchange_order_id
        self.exchange_id = exchange_id
        #self.strategy_id = strategy_id
        self.quote_quantity = quote_quantity
        self.base_quantity = base_quantity
        self.price = price
        self.quantity_filled = quantity_filled
        self.session_id=session_id
        # self.fee=fee 
        # self.fee_asset=fee_asset
        self.time_in_force = time_in_force
        self.create_timestamp = create_timestamp
        if quote_quantity == 0 and base_quantity == 0:
            raise ValueError("Quote quantity and quantity cannot both be zero.")
