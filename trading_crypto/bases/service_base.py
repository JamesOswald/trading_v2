import asyncio
import os
import pika

from common.mq_session import MQSession
from data.sql import SQL
from dotenv import load_dotenv
load_dotenv()

class ServiceBase():
    def __init__(self):
        self.mq_session = MQSession()
        self.sql = SQL()
        
    def send_async_request(self, func, *args):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        data = loop.run_until_complete(func(*args))
        return data   
        