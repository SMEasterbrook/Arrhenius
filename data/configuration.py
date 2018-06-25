from typing import Tuple, Dict, Callable


# Type aliases
WeightFunc = Callable[[float, float, float], Tuple[float, float]]


# Constants representing options for how to choose transparency table
# weights for CO2 and H2O transparency lookup.
WEIGHT_TO_CLOSEST = "close"
WEIGHT_TO_LOWEST = "low"
WEIGHT_TO_HIGHEST = "high"
WEIGHT_BY_PROXIMITY = "mean"


# Keys in configuration dictionaries.
NUM_LAYERS = "Layers"
NUM_ITERS = "Iters"
CO2_WEIGHT = "CO2"
H2O_WEIGHT = "H2O"
AGGREGATE_LAT = "Agg_Lat"

AGGREGATE_BEFORE = "Before"
AGGREGATE_AFTER = "After"
AGGREGATE_NONE = "None"


def weight_by_closest(lower_val: float,
                      upper_val: float,
                      actual: float) -> Tuple[float, float]:
    """
    Given two discrete options for concentration values and an actual value
    for them to approximate, returns a percent weight for the lower value and
    the upper value, respectively.

    Used when transparency is calculated by way of table lookup, and only
    discrete indices are allowed.

    Here, lower_val and upper_val represent two concentration values that can
    be used in the table, while actual is the real atmospheric concentration.
    Whichever one is closest to actual is given 100% weight, while the other
    is given no weight.

    Precondition:
        lower_val <= desired <= upper_val

    :param lower_val:
        The smaller of two CO2 concentration options
    :param upper_val:
        The larger of two CO2 concentration options
    :param actual:
        A real value for CO2 concentration that is to be approximated
    :return:
        An assignment of weight to lower_val and upper_val, in that order
    """
    if upper_val - actual < actual - lower_val:
        return 0, 1
    else:
        return 1, 0


_transparency_weight_converter: Dict[str, WeightFunc] = {
    WEIGHT_TO_CLOSEST: weight_by_closest
}


def get_transparency_weight_func(name: str) -> WeightFunc:
    return _transparency_weight_converter[name]


DEFAULT_CONFIG = {
    NUM_LAYERS: 1,
    NUM_ITERS: 1,
    CO2_WEIGHT: WEIGHT_TO_CLOSEST,
    H2O_WEIGHT: WEIGHT_TO_CLOSEST,
    AGGREGATE_LAT: AGGREGATE_AFTER,
}
