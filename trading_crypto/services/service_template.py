#standard imports
#from apis.sample_api import SampleApi
from bases.service_base import ServiceBase
from bases.data.base import Session
from common.get_or_create import get_or_create
from common.mq_session import MQSession
from common.request_throttle import RequestThrottle
from common.two_way_dict import TwoWayDict
from datetime import datetime, timedelta
from services.utility.token_service import TokenService
from services.utility.symbol_service import SymbolService

#enum imports
from enums.order.order_side_enum import OrderSideEnum
from enums.order.order_status_enum import OrderStatusEnum
from enums.order.order_type_enum import OrderTypeEnum
from enums.order.order_tif_enum import OrderTifEnum
from enums.granularity_enum import GranularityEnum

#model imports
from models.token import Token
from models.symbol import Symbol
from models.fee import Fee
from models.bar import Bar
from models.order import Order

class NameService(ServiceBase):
    #throttle queues
    sample_queue = 'sample_queue'

    def __init__(self, exchange):
        super(NameService, self).__init__()
        #self.api = NameApi
        self.exchange = exchange
        self.tokens = TokenService().get_tokens_by_exchange(exchange_id=self.exchange.id) or []
        self.symbols = SymbolService().get_symbols_by_exchange(exchange_id=self.exchange.id) or []

        self.OrderSideMap = TwoWayDict()
        #self.OrderSideMap['buy'] = OrderSideEnum.BUY
        #self.OrderSideMap['sell'] = OrderSideEnum.SELL
        #other OrderSideEnums

        self.OrderTypeMap = TwoWayDict()
        self.OrderTypeMap['limit'] = OrderTypeEnum.LIMIT                        
        self.OrderTypeMap['market'] = OrderTypeEnum.MARKET
        #other OrderTypeEnums    

        self.OrderTifMap = TwoWayDict()
        self.OrderTifMap['GTC'] = OrderTifEnum.GTC
        self.OrderTifMap['GTE'] = OrderTifEnum.GTE
        self.OrderTifMap['IOC'] = OrderTifEnum.IOC
        self.OrderTifMap['FOK'] = OrderTifEnum.FOK
        self.OrderTifMap['NOACK'] = OrderTifEnum.NOACK
        #other OrderTifEnums

    #@RequestThrottle(sample_queue, weight=-1, expiry_time=-1, limit=-1)
    # def get_time(self): if exchange has get time

    @RequestThrottle(sample_queue, weight=-1, expiry_time=-1, limit=-1)
    def get_tokens(self):
        """
        Gets all exchange tokens and saves to database
        """
        tokens = []
        #
        #
        #
        print("{}: tokens saved".format(self.exchange.name))
        return tokens

    @RequestThrottle(sample_queue, weight=-1, expiry_time=-1, limit=-1)
    def get_market_pairs(self):
        """
        Gets all exchange symbols and saves to database
        """
        symbols = []
        #
        #
        #
        print("{}: updated market pairs".format(self.exchange.name))
        return symbols

    @RequestThrottle(sample_queue, weight=-1, expiry_time=-1, limit=-1)
    def get_historic_data(self, symbol: Symbol, granularity: GranularityEnum, start: int=None, end: int=None) -> Bar:
        """
        Gets historical bar data for a given symbol
        """
        #change if granularity not in params
        if granularity not in {GranularityEnum.MINUTE_1, GranularityEnum.MINUTE_5, GranularityEnum.MINUTE_15, GranularityEnum.HOUR_1, GranularityEnum.HOUR_6, GranularityEnum.DAY_1}: 
            raise ValueError('Granularity must be in the set {60, 300, 900, 3600, 21600, 86400}')
        bars = []
        return bars

    @RequestThrottle(sample_queue, weight=-1, expiry_time=-1, limit=-1)
    def get_balances(self, tokens):
        """
        Gets all balances for tokens
        """
        return tokens

    @RequestThrottle(sample_queue, weight=-1, expiry_time=-1, limit=-1)
    def get_fees(self):
        """
        Gets all exchange fees
        """
        fee = Fee(exchange=self.exchange, maker=-1, taker=-1)
        return Fee

    @RequestThrottle(sample_queue, weight=-1, expiry_time=-1, limit=-1)
    def send_order(self, order):
        pass

    #other functions