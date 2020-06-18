#standard imports
from apis.gdax_api import GdaxApi
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

class GdaxService(ServiceBase):
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

    #public requests
    @RequestThrottle(public_throttle_queue, weight=1, expiry_time=334, limit=3)
    def get_time(self):
        """
        Gets exchange epoch time
        """
        data = self.send_async_request(self.api.get_time)
        epoch = data['epoch']
        return epoch

    @RequestThrottle(public_throttle_queue, weight=1, expiry_time=334, limit=3)
    def get_tokens(self):
        """
        Gets all exchange tokens and saves to database
        """
        tokens = []
        data = self.send_async_request(self.api.get_currencies)
        session = Session()
        for currency in data: 
            tokens.append(get_or_create(session, Token,
            ticker=currency['id'], 
            exchange_id=self.exchange.id))
        self.get_balances(tokens)
        session.commit()
        session.close()      
        print("{}: tokens saved".format(self.exchange.name))
        return tokens

    @RequestThrottle(public_throttle_queue, weight=1, expiry_time=334, limit=3)
    def get_market_pairs(self):
        """
        Gets all exchange symbols and saves to database
        """
        data = self.send_async_request(self.api.get_tradeable_assets)
        session = Session()
        symbols = []
        token_service = TokenService(session=session)
        tokens = token_service.get_tokens_by_exchange(self.exchange.id)
        for pair in data:
            symbols.append(get_or_create(session, Symbol,
            ticker=pair['id'],
            tick_size=float(pair['quote_increment']),
            base_id=([t for t in tokens if t.ticker == pair['base_currency']][0]).id,
            quote_id=([t for t in tokens if t.ticker == pair['quote_currency']][0]).id,
            exchange_id=self.exchange.id
            ))

        session.commit()
        session.close()
        print("{}: updated market pairs".format(self.exchange.name))
        return symbols

    @RequestThrottle(public_throttle_queue, weight=1, expiry_time=334, limit=3)
    def get_historic_data(self, symbol: Symbol, granularity: GranularityEnum, start: int=None, end: int=None) -> Bar:
        """
        Gets historical bar data for a given symbol
        """
        if granularity not in {GranularityEnum.MINUTE_1, GranularityEnum.MINUTE_5, GranularityEnum.MINUTE_15, GranularityEnum.HOUR_1, GranularityEnum.HOUR_6, GranularityEnum.DAY_1}: 
            raise ValueError('Granularity must be in the set {60, 300, 900, 3600, 21600, 86400}')
        params = { 
            'granularity': granularity.value
        } 
        if start and end:
            params['start'] = datetime.utcfromtimestamp(start)
            params['end'] = datetime.utcfromtimestamp(end)
        
        data = self.send_async_request(self.api.get_historic_data, symbol.ticker, params)
        bars = []
        for exchange_bar in data:
            bars.append(Bar(exchange_bar[0], float(exchange_bar[3]), float(exchange_bar[2]), float(exchange_bar[1]), float(exchange_bar[4]), symbol, volume=float(exchange_bar[5])))
        return bars

    #private requests
    @RequestThrottle(private_throttle_queue, weight=1, expiry_time=200, limit=5)
    def get_balances(self, tokens):
        """
        Gets all balances for tokens
        """
        data = self.send_async_request(self.api.get_accounts)
        for account in data:
            if float(account['balance']) != 0:
                token = [t for t in tokens if t.ticker == account['currency']][0]
                token.free = float(account['available']),
                token.locked = float(account['hold'])
        print("{}: updated balances".format(self.exchange.name))
        return tokens

    @RequestThrottle(private_throttle_queue, weight=1, expiry_time=200, limit=5)
    def get_fees(self):
        data = self.send_async_request(self.api.get_fees)
        fee = Fee(exchange=self.exchange, maker=float(data['maker_fee_rate']), taker=float(data['taker_fee_rate']))
        return fee

    @RequestThrottle(private_throttle_queue, weight=1, expiry_time=200, limit=5)
    def send_order(self, order):
        symbol = [s for s in self.symbols if s.id == order.symbol_id][0]
        if order.order_side == OrderSideEnum.BUY or order.order_side == OrderSideEnum.SELL:
            body = {
                'type' : self.OrderTypeMap[order.order_type],
                'product_id' : symbol.ticker,
                'side' : self.OrderSideMap[order.order_side],
                #'stp' : ,
                #'stop' : ,
                #'stop_price' : ,
                #'client_oid' :
            }
            if self.OrderTypeMap[order.order_type] == 'limit':
                body.update({
                    'price' : order.price,
                    'size' : order.base_quantity
                    #'time_in_force' : ,
                    #'cancel_after' : ,
                    #'post_only' : 
                })
            elif self.OrderTypeMap[order.order_type] == 'market':
                if order.quantity:
                    body.update({
                        'size' : order.base_quantity
                    })
                elif order.quote:
                    body.update({
                        'funds' : order.quote_quantity
                    })
                else:
                    raise Exception("MARKET ORDERS REQUIRES ONE OF SIZE OR FUNDS")
            data = self.send_async_request(self.api.send_order, (body))
            if 'id' in data.keys():
                order.exchange_order_id = data['id']
                order.order_status = OrderStatusEnum.OPEN
                order.time_in_force = self.OrderTifMap[data['time_in_force']]
                order.create_timestamp = data['created_at']
                order.quantity_filled = data['filled_size']
            else:
                raise Exception("ORDER NOT PLACED: {}".format(data))
            return order
        elif order.order_side == OrderSideEnum.CANCEL:
            order_id = order.exchange_order_id
            data = self.send_async_request(self.api.cancel_order, (order_id))
            print("ORDER CANCELLED: {}".format(order_id))

        return order

    @RequestThrottle(private_throttle_queue, weight=1, expiry_time=200, limit=5)
    def get_orders(self):
        package = self.send_async_request(self.api.get_orders)
        for data in package:
            print('-'*10)
            print(data['id'])
            print(data['product_id'])
            print(data['type'] + "\n")


