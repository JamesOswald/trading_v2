#standard imports
import json
import os
import pickle as p
import time
import typing
import websocket

from bases.exchange_worker_base import ExchangeWorkerBase
from services.gdax_service import GdaxService
from multiprocessing import Manager, Pool, Process, Queue

try:
    import thread
except ImportError:
    import _thread as thread

#enum imports

#model imports

class GdaxWorker(ExchangeWorkerBase):
    def __init__(self):
        exchange_id = int(os.getenv("GDAX_EXCHANGE_ID"))
        super(GdaxWorker, self).__init__(exchange_id)
        self.gdax_service = GdaxService(self.exchange)
        self.incoming_depths = self.manager.dict()
        self.open_orders = self.manager.dict()

    def start(self):
        super().start()

        self.gdax_service.get_tokens()

        while True:
            sleep(1)