#standard imports
import aiohttp
import asyncio
import json

#enum imports
from enums.request_type import RequestTypeEnum
    

class Request():
    def __init__(self, headers=None):
        self.session = aiohttp.ClientSession(headers=headers)
        self.request_type_function_map = {
            RequestTypeEnum.POST: self.session.post,
            RequestTypeEnum.GET: self.session.get,
            RequestTypeEnum.DELETE: self.session.delete,
            RequestTypeEnum.PUT: self.session.put, 
            RequestTypeEnum.PATCH: self.session.patch
        }
        
    async def request(self, request_type, **kwargs):
        kwargs = {k:v for k,v in kwargs.items() if v is not None}
        query = kwargs['query']
        del kwargs['query']
        async with self.request_type_function_map[request_type](query, **kwargs) as response: 
            try:
                data = await response.json()
            except:
                error_text = await response.text()
                print(error_text)
                print("in error")
                raise Exception("HTTP EXCEPTION: {} {} ".format(response.status, error_text))
            await self.session.close()
            return data
    
    def close_session(self):
        self.session.close()