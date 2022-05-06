import pika
import os

from multiprocessing import Process
from dotenv import load_dotenv
load_dotenv()

def generic_consumer(queue, callback, mq_session): 
    connection, channel = mq_session.session()
    channel.queue_declare(queue=queue)
    print("subscribing to: {}".format(queue))
    channel.basic_consume(queue=queue, auto_ack=True, on_message_callback=callback)
    channel.start_consuming()
    print("{} consumer stopped".format(queue))
    connection.close()


def start_consumer_process(queue, callback, mq_session):
    w = Process(target=generic_consumer, args=(queue, callback, mq_session,))
    w.start()
