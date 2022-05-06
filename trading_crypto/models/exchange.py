import os
import sys

from bases.data.base import Base
from models.worker import Worker
from sqlalchemy import Column, ForeignKey, Integer, String, Float
from sqlalchemy.orm import relationship
from enums.worker_type import WorkerTypeEnum

class Exchange(Worker):
    __tablename__ = 'exchange'
    id = Column(Integer, ForeignKey('worker.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity':WorkerTypeEnum.EXCHANGE.value
    }

    def __init__(self, name):
        super().__init__(name, WorkerTypeEnum.EXCHANGE.value)

    def __repr__(self):
        return ("Exchange<{}>".format(self.name))