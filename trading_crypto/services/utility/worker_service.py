#standard imports
import typing
from bases.service_base import ServiceBase
from typing import List

#enum imports
from enums.worker_type import WorkerTypeEnum

#model imports
from models.worker import Worker

class WorkerService(ServiceBase):
    def __init__(self, session=None):
        super().__init__()
        if session: 
            self.session = session
        else:
            self.session = self.sql.get_session()

    def get_all_workers(self, expunge=True) -> List[Worker]:
        query = self.session.query(Worker).all()
        if expunge:
            self.session.expunge_all()
        return query
    
    def get_worker_by_name(self, name: str, expunge=True) -> Worker:
        query = self.session.query(Worker).filter(Worker.name == name).one()
        if expunge: 
            self.session.expunge_all()
        return query

    def get_workers_by_type(self, worker_type: WorkerTypeEnum, expunge=True) -> List[Worker]:
        query = self.session.query(Worker).filter(Worker.worker_type == worker_type.value).all()
        if expunge: 
            self.session.expunge_all()
        return query

    def get_worker_by_id(self, worker_id: int, expunge=True) -> Worker:
        query = self.session.query(Worker).filter(Worker.id == worker_id).one()
        if expunge: 
            self.session.expunge_all()
        return query
    
    def get_workers_from_id_array(self, worker_ids: List[int], expunge=True) -> List[Worker]:
        query = self.session.query(Worker).filter(Worker.id.in_(worker_ids)).all()
        if expunge: 
            self.session.expunge_all()
        return query
    

