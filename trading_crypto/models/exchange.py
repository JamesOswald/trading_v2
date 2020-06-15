import os
import sys

from bases.data.base import Base
from sqlalchemy import Column, ForeignKey, Integer, String, Float
from sqlalchemy.orm import relationship

class Exchange(Base):
    __tablename__="exchange"
    id = Column(Integer, primary_key=True)
    exchange=Column(String, ForeignKey("worker.name"), nullable=False)
    worker = relationship("Worker")

    def __init__(self, id, exchange):
        self.exchange = exchange

    def __repr__(self):
        return ("Exchange<{}>".format(self.exchange))