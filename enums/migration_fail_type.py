from enum import Enum


class MigrationFailType(Enum):
    ROUND_ROBIN = 0
    REMAINING_CAPACITY_LOWER_PRIORITY = 1
    REMAINING_CAPACITY_HIGHER_PRIORITY = 2
    RANDOM = 3