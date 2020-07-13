from enum import Enum

class RouteTypeEnum(Enum):
    STRATEGY_SUBMIT_ORDER = 1 
    STRATEGY_RECIEVE_ORDER = 2
    STRATEGY_RECIEVE_DEPTH = 3 
    STRATEGY_RECIEVE_BAR = 4
    STRATEGY_REVIEVE_TRADE = 5 
    STRATEGY_RECIEVE_BALANCE = 6
    OMS_SUBMIT_ORDER = 7
    OMS_RECIEVE_ORDER = 8
    OMS_RECIEVE_BALANCE = 9
    OTHER = 11