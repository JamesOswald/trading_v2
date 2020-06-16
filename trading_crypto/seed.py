#standard imports
import asyncio

from bases.data.base import Session, engine, Base
from bases.data.sql import SQL
from bases.data.base import MDSession, market_data_engine, MDBase
from common.get_or_create import get_or_create
from services.gdax_service import GdaxService

#enum imports
from enums.worker_type import WorkerTypeEnum

#model imports
from models.symbol import Symbol
from models.worker import Worker
from models.token import Token 




MDBase.metadata.create_all(market_data_engine)

Base.metadata.create_all(engine)

session = Session()

# get_or_create(session, Worker, id = 1, name='OMS', worker_type=WorkerTypeEnum.OMS.value)

get_or_create(session, Worker, id = 1, name='GDAX', worker_type=WorkerTypeEnum.EXCHANGE.value)

# get_or_create(session, Worker, id = 2, name='HEARTBEAT', worker_type=WorkerTypeEnum.HEARTBEAT.value)

# get_or_create(session, Worker, id = 3, name="PONG",  worker_type=WorkerTypeEnum.STRATEGY.value)

# get_or_create(session, Worker, id = 4, name="bittrex", worker_type=WorkerTypeEnum.EXCHANGE.value)

# get_or_create(session, Worker, id = 5, name="kraken",  worker_type=WorkerTypeEnum.EXCHANGE.value)

# get_or_create(session, Worker, id = 6, name="binance", worker_type=WorkerTypeEnum.EXCHANGE.value)

# get_or_create(session, Worker, id = 7, name="qume", worker_type=WorkerTypeEnum.EXCHANGE.value)

# get_or_create(session, Worker, id = 8, name="md_recorder", worker_type=WorkerTypeEnum.STRATEGY.value)

# get_or_create(session, Worker, id = 9, name="arb_tracker", worker_type=WorkerTypeEnum.STRATEGY.value)

# get_or_create(session, Worker, id = 10, name="backtester", worker_type=WorkerTypeEnum.EXCHANGE.value)

# get_or_create(session, Worker, id = 11, name="gdax", worker_type=WorkerTypeEnum.EXCHANGE.value)

# get_or_create(session, Worker, id = 12, name="bitmax", worker_type=WorkerTypeEnum.EXCHANGE.value)

# get_or_create(session, Worker, id = 13, name="stat_arb", worker_type=WorkerTypeEnum.STRATEGY.value)

# get_or_create(session, Worker, id = 14, name="bitmex", worker_type=WorkerTypeEnum.EXCHANGE.value)

session.commit()

# BittrexService().get_tokens()
# BittrexService().get_market_pairs()

# exchange = session.query(Worker).filter(Worker.id == 5).one()
# KrakenService(exchange=exchange).get_tokens()
# KrakenService(exchange=exchange).get_market_pairs()

# exchange = session.query(Worker).filter(Worker.id == 6).one()
# BinanceService(exchange=exchange).get_exchange_info(update_symbols=True)

exchange = session.query(Worker).filter(Worker.id == 1).one()
GdaxService(exchange=exchange).get_tokens()
#GdaxService(exchange=exchange).get_market_pairs()

# exchange = session.query(Worker).filter(Worker.id == 12).one()
# BitmaxService(exchange=exchange).get_tokens()
# BitmaxService(exchange=exchange).get_market_pairs()

# ### Backtester ### 
# backtester = session.query(Worker).filter(Worker.name == 'backtester').one()

# btc_token = get_or_create(session, Token,
#     name="Bitcoin", ticker="BTC", symbol="BTC", exchange_id=backtester.id)
# usdt_token = get_or_create(session, Token,
# name="Tether", ticker="USDT", symbol="USDT", exchange_id=backtester.id)
# usdc_token = get_or_create(session, Token,
#     name="USDC", ticker="USDC", symbol="USDC", exchange_id=backtester.id)
# eth_token = get_or_create(session, Token,
#     name="Ethereum", ticker="ETH", symbol="ETH", exchange_id=backtester.id)
# bnb_token = get_or_create(session, Token,
#     name="Binance Coin", ticker="BNB", symbol="BNB", exchange_id=backtester.id)

# #BTCUSDT
# get_or_create(session, Symbol, 
#                 base = btc_token.ticker, 
#                 quote= usdt_token.ticker,
#                 ticker='{}{}'.format(btc_token.ticker, usdt_token.ticker), 
#                 base_id=btc_token.id,
#                 quote_id=usdt_token.id, 
#                 exchange_id=backtester.id)

# #BTCUSDC
# get_or_create(session, Symbol, 
#                 base = btc_token.ticker, 
#                 quote= usdc_token.ticker,
#                 ticker='{}{}'.format(btc_token.ticker, usdc_token.ticker), 
#                 base_id=btc_token.id,
#                 quote_id=usdc_token.id, 
#                 exchange_id=backtester.id)

# #ETHUSDT
# get_or_create(session, Symbol, 
#                 base = eth_token.ticker, 
#                 quote= usdt_token.ticker,
#                 ticker='{}{}'.format(eth_token.ticker, usdt_token.ticker), 
#                 base_id=eth_token.id,
#                 quote_id=usdt_token.id, 
#                 exchange_id=backtester.id)

# #ETHUSDC
# get_or_create(session, Symbol, 
#                 base = eth_token.ticker, 
#                 quote= usdc_token.ticker,
#                 ticker='{}{}'.format(eth_token.ticker, usdc_token.ticker), 
#                 base_id=eth_token.id,
#                 quote_id=usdc_token.id, 
#                 exchange_id=backtester.id)

# #ETHBTC
# get_or_create(session, Symbol, 
#                 base = eth_token.ticker, 
#                 quote= btc_token.ticker,
#                 ticker='{}{}'.format(eth_token.ticker, btc_token.ticker), 
#                 base_id=eth_token.id,
#                 quote_id=btc_token.id, 
#                 exchange_id=backtester.id)

# #USDCUSDT
# get_or_create(session, Symbol, 
#                 base = usdc_token.ticker, 
#                 quote= usdt_token.ticker,
#                 ticker='{}{}'.format(usdc_token.ticker, usdt_token.ticker), 
#                 base_id=usdc_token.id,
#                 quote_id=usdt_token.id, 
#                 exchange_id=backtester.id)
# print('Backtester Seeded')

# session.commit()
session.close()


