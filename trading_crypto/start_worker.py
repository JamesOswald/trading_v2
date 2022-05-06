import argparse
import asyncio
import signal
import sys
import os
parser = argparse.ArgumentParser()
parser.add_argument("-w","--worker", help="specify worker to run", type=str)
args = parser.parse_args()

from manager.oms import OMS 
from workers.backtest_worker import BacktestWorker
from workers.gdax_worker import GdaxWorker, GdaxWS
# from workers.market_data_worker import MDWorker

from models.websocket import WebSocket

import asyncio

workers  = {
    'oms': OMS,
    'backtest' : BacktestWorker,
    'gdax': GdaxWorker
   # 'mdworker': MDWorker
}

def signal_handler():
    print("stopping")

if __name__ == '__main__':
    try:
        if not args.worker:
            raise Exception("No Worker Provided")
        elif args.worker == 'oms':
            oms = OMS()
            oms.start()
        elif args.worker in workers.keys():
            # ws = WebSocketClientFactory(os.getenv("GDAX_SOCKET_URL"))
            # ws.protocol = GdaxWS
            # connectWS(ws)
            # reactor.run()
            workers[args.worker]().start()
        else:
            raise Exception("Unknown Worker")
    except KeyboardInterrupt as ex:
        signal_handler()

 
 