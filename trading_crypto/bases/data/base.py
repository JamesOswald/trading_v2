#standard imports
import json
import os 
import psycopg2

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
load_dotenv()

 
Base = declarative_base()
engine = create_engine(os.getenv("SQL_CONNECTION"))
Session = sessionmaker(bind=engine)


MDBase = declarative_base()
market_data_engine = create_engine(os.getenv("MD_SQL_CONNECTION"))
MDSession = sessionmaker(bind=market_data_engine)



 