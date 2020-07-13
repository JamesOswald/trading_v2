from bases.data.base import Base
from sqlalchemy import Column, Integer, ForeignKey, String, Float, Table, Boolean
from sqlalchemy.orm import relationship
import typing
from typing import List
from enums.channel import ChannelEnum
from common.int_enum_type import IntEnum
from models.symbol import Symbol
import json

class Channel(Base):
    __tablename__='channel'
    id = Column(Integer, nullable=False, primary_key=True)
    channel_type = Column(IntEnum(ChannelEnum), nullable=False)
    strategy_config_id = Column(Integer, ForeignKey('strategy_config'), nullable=False) 
    strategy_config = relationship('StrategyConfig', back_populates='channels', nullable=True)
    symbols = relationship('Symbol', secondary=channel_symbol_association)

    def __init__(self, channel_type, strategy_config=None, symbols=[]):
        self.symbols = symbols
        self.channel_type = channel_type 
        self.strategy_config = strategy_config

channel_symbol_association = Table('channel_symbol_association', Base.metadata, 
    Column('channel_id', Integer, ForeignKey('channel.id')),
    Column('symbol_id', Integer, ForeignKey('symbol.id'))
)

class StrategyConfig(Base):
    __tablename__='strategy_config'
    id = Column(Integer, nullable=False, primary_key=True)
    strategy_id = Column(Integer, ForeignKey('strategy.id'), nullable=False)
    strategy = relationship('Strategy', back_populates='config')
    channels = relationship('Channel', backref='strategy_config')
    is_backtest = Column(Boolean, nullable=False)
    meta = Column(Boolean, nullable=False)
    
    def __init__(self, strategy_id, channels, is_backtest, meta):
        self.strategy_id = strategy_id
        self.channels = channels
        self.is_backtest = is_backtest
        self.meta = meta 
    
    @classmethod
    def from_json(cls, session, config_path):
        with open(config_path) as config_file:
            config = json.load(config_file)
            channels = {}
            for symbol_id, channel_nums in config['SYMBOLS'].items():
                symbol = session.query(Symbol).filter(Symbol.id == symbol_id).one()
                for channel_num in channel_nums:
                    enum_value = ChannelEnum(channel_num)
                    if enum_value not in channels.keys():
                        channels[enum_value] = Channel(enum_value)
                    channels[enum_value].symbols.append(symbol)
        
        return cls.__init__(config['ID'], list(channels.values()), config['RUNNING_BACKTEST'], config['META'])
       

    
        