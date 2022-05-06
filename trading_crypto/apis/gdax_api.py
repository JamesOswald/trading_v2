#standard imports
import asyncio
import json
import os
import time

from bases.api_base import ApiBase
from common.requests import Request

#enum imports
from enums.request_type import RequestTypeEnum

class GdaxApi(ApiBase):
    def __init__(self):
        super(GdaxApi, self).__init__()
        self.root_url = os.getenv("GDAX_ROOT_URL")
        self.api_key = os.getenv("GDAX_KEY_MAIN")
        self.api_secret = os.getenv("GDAX_KEY_SECRET")
        self.api_passphrase = os.getenv("GDAX_PASSPHRASE")
    
    def get_auth(self, method_type, url_path, data):
        '''
        Generates authentication headers for REST requests.
        '''
        #create message string
        timestamp = str(time.time())
        if data:
            message = timestamp + method_type.name + url_path + json.dumps(data)
        else:
            message = timestamp + method_type.name + url_path
        #get encoded signature
        signature = self.get_signature(message, self.api_secret)
        #return authentication headers
        return {
            'CB-ACCESS-SIGN': signature,
            'CB-ACCESS-TIMESTAMP': timestamp,
            'CB-ACCESS-KEY': self.api_key,
            'CB-ACCESS-PASSPHRASE': self.api_passphrase,
            'Content-Type': 'application/json'
        }
        
    def get_query(self, url_path, params):
        '''
        Generates query string for REST requests.
        '''
        if params: 
            query = "{}{}?{}".format(self.root_url, url_path, "&".join(["{}={}".format(key, value) for key,value in params.items()]))
        else: 
            query = "{}{}".format(self.root_url, url_path)
        return query
        
    async def perform_request(self, method_type, url_path, data=None, params=None, authenticate=False): 
        headers = {}
        if authenticate: 
            headers = self.get_auth(method_type, url_path, data)
        query = self.get_query(url_path, params)
        if method_type == RequestTypeEnum.POST:
            return await Request(headers).request(method_type, query=query, data=json.dumps(data))
        else:
            return await Request(headers).request(method_type, query=query)

    async def get_currencies(self):
        return await self.perform_request(RequestTypeEnum.GET, "/currencies")

    async def get_tradeable_assets(self):
        return await self.perform_request(RequestTypeEnum.GET, "/products")

    async def get_accounts(self):
        return await self.perform_request(RequestTypeEnum.GET, "/accounts", authenticate=True)
    
    async def get_fees(self):
        return await self.perform_request(RequestTypeEnum.GET, "/fees", authenticate=True)

    async def send_order(self, data):
        return await self.perform_request(RequestTypeEnum.POST, "/orders", authenticate=True, data=data)

    async def cancel_order(self, order_id):
        return await self.perform_request(RequestTypeEnum.DELETE, "/orders/{}".format(order_id), authenticate=True)
        #for cancelling ALL orders: return await self.perform_request(RequestTypeEnum.DELETE, "/orders", authenticate=True)

    async def get_orders(self):
        return await self.perform_request(RequestTypeEnum.GET, "/orders", authenticate=True)
    
    async def get_historic_data(self, ticker, params):
        return await self.perform_request(RequestTypeEnum.GET, "/products/{}/candles".format(ticker),params=params)

    async def get_time(self):
        return await self.perform_request(RequestTypeEnum.GET, "/time")