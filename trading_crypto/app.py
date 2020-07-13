import argparse
parser = argparse.ArgumentParser()
parser.add_argument("-s","--strategy", help="specify strategy to run", type=str)
parser.add_argument("-c", "--config", help="specify config.env file", type=str)
args = parser.parse_args()
from multiprocessing import Process
from strategy.pong import Pong
import asyncio 

strategies = {
    "pong" : Pong,
}

if __name__ == '__main__':
    if not args.strategy:
        raise Exception("No Strategy Provided")
    elif args.strategy in strategies.keys():
        strategies[args.strategy](args.config).start()
