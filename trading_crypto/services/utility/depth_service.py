#standard imports
from bases.service_base import ServiceBase
from data.sql import SQL
from sqlalchemy import and_
from statistics import mean, variance
from typing import List

#enum imports
from enums.worker_type import WorkerTypeEnum

#model imports
from models.symbol import Symbol
from models.token import Token
from models.worker import Worker
from models.depth import Depth

class DepthService(ServiceBase):
    def __init__(self, session):
        super().__init__()
        if not session:
            self.session = self.sql.get_session()
        else:
            self.session = session

    def get_depth_by_id(self, depth_id):
        return self.session.query(Depth).filter(Depth.id == depth_id)
    
    def get_depths_over_period(self, start_timestamp:int=None, end_timestamp:int=None, symbol_id:int=None, test_id:int=None):
        queries = []

        if end_timestamp: 
            queries.append(Depth.timestamp < end_timestamp)
        if start_timestamp: 
            queries.append(Depth.timestamp > start_timestamp)
        if symbol_id: 
            queries.append(Depth.symbol_id == symbol_id)
        if test_id: 
            queries.append(Depth.test_id == test_id)

        return self.session.query(Depth).filter(*queries)
    
    def get_all_depth_mid_prices(self, depths:List[Depth]):
        return [depth.get_mid_price() for depth in depths]
    
    def get_standard_mean_and_variance(self, depths:List[Depth]=None): 
        depths = self.get_all_depth_mid_prices(depths)
        return(mean(depths), variance(depths))
        