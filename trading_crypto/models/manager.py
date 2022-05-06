import os
import sys

from bases.data.base import Base
from models.worker import Worker
from sqlalchemy import Column, ForeignKey, Integer, String, Float
from sqlalchemy.orm import relationship
from enums.worker_type import WorkerTypeEnum

class Manager(Worker):
    __tablename__ = 'manager'
    id = Column(Integer, ForeignKey('worker.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity':WorkerTypeEnum.MANAGER.value
    }

    def __init__(self, name):
        super().__init__(name, WorkerTypeEnum.MANAGER.value)

    def __repr__(self):
        return ("Manager<{}>".format(self.name))