import pika

from common.mq_session import MQSession
from time import sleep

class RequestThrottle(): 
    def __init__(self, throttle_queue, weight, expiry_time, limit):
        """
        :param: global rabbitmq channel to publish with
        :throttle_queue: string name
        """
        self.throttle_queue_string = throttle_queue
        self.weight = weight 
        self.expiry_time = expiry_time 
        self.limit = limit
    
    def __call__(self, func): 
        def wrapped_func(*args): 
            connection, channel = MQSession().session()
            self.throttle_queue = channel.queue_declare(queue=self.throttle_queue_string)
            while self.throttle_queue.method.message_count >= self.limit: 
                self.throttle_queue = channel.queue_declare(queue=self.throttle_queue_string)
                print('Rate limit reached, waiting.')
                sleep(0.25)
            for i in range(self.weight):
                channel.basic_publish(exchange='', routing_key=self.throttle_queue_string, body=func.__name__, properties=pika.BasicProperties(expiration=str(self.expiry_time)))
            connection.close()   
            return func(*args)              
        return wrapped_func