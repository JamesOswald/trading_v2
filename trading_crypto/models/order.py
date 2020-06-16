import os
import sys
from datetime import datetime
from time import time

from data.base import Base
from models.enums.orders.order_status_enum import OrderStatusEnum
from models.enums.orders.order_tif_enum import OrderTifEnum
from models.enums.orders.order_type_enum import OrderTypeEnum
from sqlalchemy import (Column, DateTime, Float, ForeignKey, Integer, String,
                        Time)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid


class Order(Base):
    __tablename__='order'
    id = Column(Integer, primary_key=True)
    uuid = Column(UUID(as_uuid=True), unique=True, nullable=False)
    side=Column(Integer, nullable=False)
    order_type=Column(Integer, nullable=False)
    status=Column(Integer, nullable=False)
    quote_quantity=Column(Float(precision=8,asdecimal=False), nullable=True)
    quantity=Column(Float(precision=8,asdecimal=False), nullable=False)
    price=Column(Float(precision=8,asdecimal=False), nullable=True)
    quantity_filled=Column(Float, default=0.0)
    exchange_order_id=Column(String)
    exchange_id=Column(Integer, ForeignKey('exchange.id'),nullable=False)
    strategy_id=Column(Integer, ForeignKey('strategy.id'))
    session_id=Column(Integer, ForeignKey('strategy_session.id'))
    symbol_id = Column(Integer, ForeignKey('symbols.id'), nullable=False)
    fee = Column(Float, default=0.0)
    fee_asset = Column(String(50))
    time_in_force=Column(Integer, default=OrderTifEnum.NOACK)
    order_create_time=Column(Integer, default=time())
    time_created = Column(Integer, default=time())
    time_updated = Column(Integer, onupdate=time())
    strategy = relationship('Worker', foreign_keys=[strategy_id]) #TODO
    strategy_session = relationship('StrategySession')
    exchange = relationship('Exchange', foreign_keys=[exchange_id])
    symbols = relationship('Symbol')
    test_id = Column(Integer, ForeignKey('test.id'), nullable=True)
    test = relationship("Test", back_populates="orders")
  

    def __init__(self, uid="", symbol_id=0, 
    side=0, order_type=100, status=100, quote_quantity=0,
    quantity=0, price=0, quantity_filled=0, 
    exchange_order_id="", 
    exchange_id=0, strategy_id=0, 
    session_id=0, fee=0, fee_asset="",
    time_in_force=OrderTifEnum.NOACK, 
    order_create_time=time(),
    time_updated = time()):
        self.symbol_id = symbol_id
        self.uuid = uid if uid else uuid.uuid4()
        self.side = side
        self.order_type = order_type
        self.status = status
        self.exchange_order_id=exchange_order_id
        self.exchange_id = exchange_id
        self.strategy_id = strategy_id
        self.quote_quantity = quote_quantity
        self.quantity = quantity
        self.price = price
        self.quantity_filled = quantity_filled
        self.session_id=session_id
        self.fee=fee 
        self.fee_asset=fee_asset
        self.time_in_force = time_in_force
        self.order_create_time = order_create_time
        if quote_quantity == 0 and quantity == 0:
            raise ValueError("Quote quantity and quantity cannot both be zero.")
