from enum import IntEnum 

class OrderTypeEnum(IntEnum):
    LIMIT=0
    MARKET=1
    STOP_LOSS=2
    ICEBERG=3
    STOP_LOSS_LIMIT = 4
    TAKE_PROFIT=5
    TAKE_PROFIT_LIMIT=6
    LIMIT_MAKER=7
    CANCEL=99
    UNKNOWN=100
    
    