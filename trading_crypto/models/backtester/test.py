#standard imports
from bases.data.base import Base
from sqlalchemy import (Column, DateTime, Float, ForeignKey, Integer, String, Time)
from sqlalchemy.orm import relationship
from time import time

#enum imports
from enums.test_type import TestTypeEnum

#model imports
from models.order import Order

class Test(Base):
    __tablename__='test'
    id = Column(Integer, primary_key=True)
    test_type = Column(Integer, nullable=False)
    # orders = relationship('Order')
    # depths = relationship('Depth')
    time_created = Column(Integer, default=time())
    time_updated = Column(Integer, onupdate=time())
    depth_feeders = {}

    __mapper_args__ = {
        'polymorphic_identity':0,
        'polymorphic_on': test_type
    }

    def __repr__(self):
        return "Test<{}:{}>".format(TestTypeEnum(self.test_type),self.id)

    def __init__(self, test_type, backtest_config, depths=[], bars=[], orders=[], depth_feeders={}, bar_feeders={}, balances={}):
        self.test_type = test_type 
        self.backtest_config = backtest_config
        self.depths = depths
        self.bars = bars
        self.orders = orders
        self.depth_feeders = depth_feeders
        self.bar_feeders = bar_feeders
        self.balances = balances

    def read_configuration_from_file(self, config_file):
        raise NotImplementedError

    def get_current_orderbook(self, timestamp):
        raise NotImplementedError

    def create_bars(self):
        pass

    def create_depth(self):
        pass

    def get_depth_feeders(self):
        return self.depth_feeders
    
    def get_bar_feeders(self):
        return self.bar_feeders

    def cleanup(self, session): 
        """
        Any post processing required to cleanup the test should be performed here, this is called after all depths have been administered
        """
        pass



    




        
    