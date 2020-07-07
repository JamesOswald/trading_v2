from enum import Enum

class GranularityEnum(Enum):
    MINUTE_1 = 60
    MINUTE_3 = 180
    MINUTE_5 = 300
    MINUTE_15 = 900
    MINUTE_30 = 1800
    HOUR_1 = 3600
    HOUR_2 = 7200
    HOUR_4 = 14400
    HOUR_6 = 21600
    HOUR_8 = 28800
    HOUR_12 = 43200
    DAY_1 = 86400
    DAY_3 = 259200
    WEEK_1 = 604800
    MONTH_1 = 2592000