from enum import IntEnum

class OrderTifEnum(IntEnum):
    GTC=0
    GTE=1
    IOC=2
    FOK=3
    NOACK=100