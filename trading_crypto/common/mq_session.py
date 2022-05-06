import os
import pika

from dotenv import load_dotenv
load_dotenv()

class MQSession:
    def __init__(self):
        return
        
    def session(self):
            parameters = pika.ConnectionParameters(host=os.getenv('RABBITMQ_HOST'), connection_attempts=20, retry_delay=1),
            connection = pika.BlockingConnection(parameters)
            channel = connection.channel()
            return [connection, channel]
            
