from enum import Enum

class WorkerTypeEnum(Enum):
    MANAGER = 1
    HEARTBEAT = 2
    EXCHANGE = 3
    STRATEGY = 4
    MATH = 5
    