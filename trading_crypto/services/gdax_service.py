#standard imports
from apis.gdax_api import GdaxApi
from bases.service_base import ServiceBase
from common.mq_session import MQSession
from common.request_throttle import RequestThrottle
from common.two_way_dict import TwoWayDict

#enum imports


#model imports

class GdaxService(ServiceBase):
    connection, channel = MQSession().session()
    public_throttle_queue = 'gdax_public_throttle_queue'
    private_throttle_queue = 'gdax_private_throttle_queue'

    def __init__(self, exchange):
            super(GdaxService, self).__init__()
        self.api = GdaxApi()
        self.exchange = exchange
        self.tokens = TokenService().get_tokens_by_exchange(exchange_id=self.exchange.id) or []
        self.symbols = SymbolService().get_symbols_by_exchange(exchange_id=self.exchange.id) or []

        self.OrderSideMap = TwoWayDict()
        self.OrderSideMap['buy'] = OrderSideEnum.BUY
        self.OrderSideMap['sell'] = OrderSideEnum.SELL
        
        self.OrderTypeMap = TwoWayDict()
        self.OrderTypeMap['limit'] = OrderTypeEnum.LIMIT                        
        self.OrderTypeMap['market'] = OrderTypeEnum.MARKET    

        self.OrderTifMap = TwoWayDict()
        self.OrderTifMap['GTC'] = OrderTifEnum.GTC
        self.OrderTifMap['GTE'] = OrderTifEnum.GTE
        self.OrderTifMap['IOC'] = OrderTifEnum.IOC
        self.OrderTifMap['FOK'] = OrderTifEnum.FOK
        self.OrderTifMap['NOACK'] = OrderTifEnum.NOACK

    @RequestThrottle(public_throttle_queue, weight=1, expiry_time=334, limit=3)
    def get_tokens(self):
        tokens = []
        data = self.send_async_request(self.api.get_currencies)
        session = Session()
        for currency in data: 
            tokens.append(get_or_create(session, Token,
            ticker=currency['id'], 
            exchange_id=self.exchange.id))
        
        session.commit()
        session.close()      
        print("Gdax: tokens saved")
        return tokens