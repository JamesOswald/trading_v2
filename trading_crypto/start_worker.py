import argparse
import asyncio
import signal
import sys
parser = argparse.ArgumentParser()
parser.add_argument("-w","--worker", help="specify worker to run", type=str)
args = parser.parse_args()

from workers.gdax_worker import GdaxWorker
# from workers.market_data_worker import MDWorker

import asyncio

workers  = {
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
            workers[args.worker]().start()
        else:
            raise Exception("Unknown Worker")
    except KeyboardInterrupt as ex:
        signal_handler()

 
 