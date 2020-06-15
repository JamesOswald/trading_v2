import os
import redis
import typing

from typing import List
from dotenv import load_dotenv
load_dotenv()

class RedisService():
    def __init__(self):
        self.host=os.getenv("REDIS_HOST")
        self.port=int(os.getenv("REDIS_PORT"))
        self.password=os.getenv("REDIS_PASSWORD")
        self.sessions={}

    def create_session(self, db=0):
        try: 
            return self.sessions[db]
        except: 
            self.sessions[db] = redis.StrictRedis(host=self.host, 
            port=self.port, password=self.password, ssl=False)
            return self.sessions[db]

    def set_value(self, key, value, db=0, expire=None):
        self.sessions[db].set(key, value, ex=expire)
            
        
    def get_value(self, key, db=0):
        return self.sessions[db].get(key)

    def get_values(self, key: List, db=0):
        return self.sessions[db].mget(key)
    
    def flushdb(self, db=0):
        self.sessions[db].flushdb(db)
    
    def flushall(self):
        self.sessions[0].flushall()
