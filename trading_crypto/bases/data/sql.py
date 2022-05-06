import os
import psycopg2

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
load_dotenv()

class SQL():
    def __init__(self, connection_string = None):
        self.engine=create_engine(os.getenv("SQL_CONNECTION"))
        if connection_string:
            self.engine = create_engine(connection_string)
        self.session = sessionmaker(bind=self.engine)
        self.base = declarative_base()
    
    def get_session(self):
        self.session = sessionmaker(bind=self.engine)()
        return self.session
    
    def end_session(self):
        if self.session != None:
            self.session.close()