from enum import Enum


class MoveStrategyType(Enum):
    ROUND_ROBIN = 0
    REMAINING_CAPACITY_LOWER_PRIORITY = 1
    REMAINING_CAPACITY_HIGHER_PRIORITY = 2
    RANDOM = 3


def move_strategy_type_converter(str_strategy: str):
    strategys = [MoveStrategyType.ROUND_ROBIN, MoveStrategyType.REMAINING_CAPACITY_LOWER_PRIORITY,
              MoveStrategyType.REMAINING_CAPACITY_HIGHER_PRIORITY, MoveStrategyType.RANDOM]
    for item in strategys:
        if str_strategy.upper() == item.name:
            return item
    return MoveStrategyType.ROUND_ROBIN
