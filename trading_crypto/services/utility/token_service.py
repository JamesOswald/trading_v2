#standard imports
import typing
from bases.service_base import ServiceBase
from sqlalchemy import or_, and_
from typing import List

# model imports
from models.token import Token
from models.symbol import Symbol

class TokenService(ServiceBase):
    def __init__(self, session=None):
        super().__init__()
        if not session:
            self.session = self.sql.get_session()
        else: 
            self.session = session

    def get_tokens_all(self):
        query = self.session.query(Token).all()
        self.session.expunge_all()
        return query

    def get_tokens_by_exchange(self, exchange_id):
        query = self.session.query(Token).filter(Token.exchange_id == exchange_id).all()
        self.session.expunge_all()
        return query

    def get_tokens_by_id(self, token_id: int) -> Token:
        query = self.session.query(Token).filter(Token.id == token_id).one()
        self.session.expunge_all()
        return query
    
    def get_all_symbols_for_token(self, token: Token) -> List[Symbol]:
        """
        Returns all symbols that use a specific token
        """
        query = self.session.query(Symbol).filter(or_(Symbol.base_id == token.id, Symbol.quote_id == token.id)).all()
        self.session.expunge_all()
        return query

    def get_tokens_by_token_ids(self, token_ids):
        query = self.session.query(Token).filter(Token.id.in_(token_ids)).all()
        self.session.expunge_all()
        return query
    
    def get_tokens_by_exchange_ids(self, exchange_ids):
        query = self.session.query(Token).filter(Token.exchange_id.in_(exchange_ids)).all()
        self.session.expunge_all()
        return query
