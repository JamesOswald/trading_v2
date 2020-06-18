from enum import IntEnum
#enum [Ack, PartialFill, IocNoFill, FullyFill, Canceled, Expired, FailedBlocking, FailedMatching, IocExpire]
class OrderStatusEnum(IntEnum):
    NEW = 0
    FILLED=1
    PARTIAL_FILL=2
    CANCELLED=3
    OPEN=5
    REJECTED=6
    EXPIRE=7
    IOC_NO_FILL=8
    IOC_EXPIRE=9
    FAILED_MATCHING=10
    ACK=100
    NOACK=101
