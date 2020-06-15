from enum import Enum

class RequestTypeEnum(Enum):
    GET = 'GET',
    POST = 'POST',
    PUT = 'PUT',
    PATCH = 'PATCH', 
    DELETE = 'DELETE'