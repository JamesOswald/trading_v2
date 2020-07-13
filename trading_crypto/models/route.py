from bases.data.base import Base
from enums import route_type
import json
import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy import (Column, DateTime, Float, ForeignKey, Integer, String,
                        Time)
from enums.route_type import RouteTypeEnum

#this class is for easy access to routes between workers

class Route(Base): 
    __tablename__='route'
    id = Column(Integer, primary_key=True)
    route_id=Column(UUID(as_uuid=True), unique=True, nullable=False)
    route_type_number=Column(Integer, default=RouteTypeEnum.OTHER.value)
    publisher_worker_id = Column(Integer, ForeignKey('worker.id'),nullable=False)
    consumer_worker_id = Column(Integer, ForeignKey('worker.id'), nullable=False)
    symbol_id = Column(Integer, ForeignKey('symbol.id'), nullable=True)
    strategy_session_id = Column(Integer, ForeignKey('strategy_session.id'), nullable=True)
    route_string = Column(String, nullable=False)
    custom_identifier = Column(String, nullable=True)
    symbol = relationship('Symbol', foreign_keys=[symbol_id])
    consumer = relationship('Worker', foreign_keys=[consumer_worker_id])
    publisher = relationship('Worker', foreign_keys=[publisher_worker_id])
    strategy_session_relationship = relationship('StrategySession')


    def __init__(self, route_type, publisher_worker=None, consumer_worker=None, channel=None, uid=None, symbol=None, strategy_session_id=None, custom_identifier=None, route_string=None):
        self.route_id = uid if uid else uuid.uuid4()
        self.route_type = route_type
        self.route_type_number = self.route_type.value
        if publisher_worker:
            self.publisher_worker = publisher_worker
            self.publisher_worker_id = self.publisher_worker.id
        if consumer_worker:
            self.consumer_worker = consumer_worker
            self.consumer_worker_id = self.consumer_worker.id
        self.custom_identifier = custom_identifier
        self.symbol = symbol
        self.strategy_session_id = strategy_session_id
        if self.symbol:
            self.symbol_id = self.symbol.id
        self.route_string = route_string if route_string else self.get_route_string()
    
    def __repr__(self):
        return 'Route<{}>'.format(self.get_route_string())

    def get_route_string(self): 
        if not self.custom_identifier and not self.symbol: 
            return "{}.{}:{}->{}".format(self.route_id, self.route_type.name, self.publisher_worker.id, self.consumer_worker.id)
        elif self.custom_identifier and not self.symbol:
            return "{}.{}:{}->{}:{}".format(self.route_id, self.route_type.name, self.publisher_worker.id, self.consumer_worker.id, self.custom_identifier)
        elif self.symbol and not self.custom_identifier:
            return "{}.{}:{}->{}:{}".format(self.route_id, self.route_type.name, self.publisher_worker.id, self.consumer_worker.id, self.symbol.ticker)
        elif self.symbol and self.custom_identifier:
            return "{}.{}:{}->{}:{}:{}".format(self.route_id, self.route_type.name, self.publisher_worker.id, self.consumer_worker.id, self.custom_identifier, self.symbol.ticker)