import os
import sys

from bases.data.base import Base
from models.worker import Worker
from sqlalchemy import Column, ForeignKey, Integer, String, Float
from sqlalchemy.orm import relationship
from enums.worker_type import WorkerTypeEnum

class Strategy(Worker):
    __tablename__ = 'strategy'
    id = Column(Integer, ForeignKey('worker.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity':WorkerTypeEnum.STRATEGY.value
    }

    def __init__(self, name):
        super().__init__(name, WorkerTypeEnum.STRATEGY.value)

    def __repr__(self):
        return ("Strategy<{}>".format(self.strategy))