import os
import sys

from bases.data.base import Base
from sqlalchemy import Column, ForeignKey, Integer, String, Float
from time import time

class Worker(Base):
    __tablename__="worker"
    id = Column(Integer, primary_key=True)
    name=Column(String, nullable=False)
    worker_type=Column(Integer, nullable = False)
    time_created = Column(Integer, default=time())
    time_updated = Column(Integer, onupdate=time())
    incoming_route_list = {}
    outgoing_route_list = {}

    __mapper_args__ = {
        'polymorphic_identity':0,
        'polymorphic_on': worker_type 
    }

    def __init__(self, name, worker_type):
        self.name = name
        self.worker_type = worker_type

    def __repr__(self):
        return ("Worker<{}>".format(self.name))

    