#standard imports
import os
import pickle as p
import pika
import redis
import signal
import sys

from bases.data.sql import SQL
from common.generic_consumer import start_consumer_process
from common.mq_session import MQSession
from multiprocessing import Manager, Pool, Process, Queue
from services.utility.redis_service import RedisService
from time import sleep
from dotenv import load_dotenv
load_dotenv()

#model imports
from models.worker import Worker

class WorkerBase:
    def __init__(self, name=None, worker_id=None):
        signal.signal(signal.SIGINT, self.handler)
        self.manager = Manager()
        self.redis_service = RedisService()
        self.mq_session = MQSession()
        self.sql = SQL()
        self.session = self.sql.get_session()
        self.refresh_time = 5
        if name or worker_id:
            if name:
                self.worker = self.session.query(Worker).filter(Worker.name == name).one()
            if worker_id: 
                self.worker = self.session.query(Worker).filter(Worker.id == worker_id).one()
            #start heartbeat
            heartbeat_process = Process(target=self.heartbeat)
            heartbeat_process.start()
            # start waiting for other workers to fail
            start_consumer_process('heartbeat_resubscribe_{}'.format(self.worker.id), self.heartbeat_resubscribe_callback, self.mq_session)
        
        

    def handler(self,signum, frame):
        sys.exit(0)

    # if this worker has had a route chage, heartbeat is updeated to keep track of the current active communication channels that each worker has
    # that way, in the event of an error, the worker can resubscribe to these particlular route objects
    def heartbeat_update(self, worker_id, route, remove=False):
        _, channel = self.mq_session.session()
        channel.basic_publish(exchange='', routing_key='heartbeat_update', body=p.dumps((worker_id,route)))
        _.close()

    # publishes heartbeat to heartbeat worker every self.refresh_time seconds, if no heartbeat 
    # is recieved a kill command will be issued from heartbeat and 
    def heartbeat(self): 
        _, channel = self.mq_session.session()
        channel.basic_publish(exchange='', routing_key='heartbeat_init', body=p.dumps(self.worker))
        while True: 
            sleep(self.refresh_time)
            channel.basic_publish(exchange='', routing_key='heartbeat', body=p.dumps(self.worker.id))
        _.close()
    
    # if another worker is restarted by heartbeat, all communicating workers need to know about it, the body of this message has a route object in it  
    # and should be dealt with based on the specific type of worker that it is (i.e. if the route is for depth, and this is an exchange worker that is being notified that a strategy worker failed, 
    # ExchangeWorkerBase needs to resubscribe to the depth from the exchange)
    def heartbeat_resubscribe_callback(self, route, method, properties, body): 
       raise NotImplementedError

    def heartbeat_remove_callback(self, route, method, properties, body): 
        raise NotImplementedError