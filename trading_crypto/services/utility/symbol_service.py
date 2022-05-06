#standard imports
from bases.service_base import ServiceBase
from bases.data.sql import SQL
from sqlalchemy import and_

#enum imports
from enums.worker_type import WorkerTypeEnum

#model imports
from models.symbol import Symbol
from models.token import Token
from models.worker import Worker


class SymbolService(ServiceBase):
    def __init__(self, session=None):
        super().__init__()
        if not session:
            self.session = self.sql.get_session()
        else:
            self.session = session

    def get_symbol_by_id(self, id):
        query = self.session.query(Symbol).filter(Symbol.id == id).one()
        #self.session.expunge_all()
        return query

    # def get_exchanges_all(self):
    #     query = self.session.query(Worker).filter(Worker.worker_type == WorkerTypeEnum.EXCHANGE.value)
    #     #self.session.expunge_all()
    #     return query

    def get_symbols_all(self):
        query = self.session.query(Symbol).all()
        #self.session.expunge_all()
        return query
        
    def get_symbols_from_array(self, symbol_ids):
        query = self.session.query(Symbol).filter(Symbol.id.in_(symbol_ids)).all()
        #self.session.expunge_all()
        return query

    def get_symbol_by_name(self, ticker, exchange_id):
        query = self.session.query(Symbol).filter(Symbol.ticker == ticker, Symbol.exchange_id == exchange_id).one()
        #self.session.expunge_all()
        return query

    def get_symbols_from_string(self, symbol_string):
        symbol_ids = symbol_string.split(',')
        query = self.session.query(Symbol).filter(Symbol.id.in_(symbol_ids)).all()
        #self.session.expunge_all()
        return query
        
    def get_symbols_by_exchange(self, exchange_id, expunge=True):
        query = self.session.query(Symbol).filter(Symbol.exchange_id == exchange_id).all()
        # if expunge:
        #self.session.expunge_all()
        return query
    
    def get_symbol_by_tokens(self, base_token: Token, quote_token: Token) -> Symbol: 
        query = self.session.query(Symbol).filter(and_(Symbol.base_id == base_token.id, Symbol.quote_id == quote_token.id)).first()
        #self.session.expunge_all()
        return query