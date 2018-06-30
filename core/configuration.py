from typing import Tuple, Dict, Callable


# Type aliases
Config = Dict[str, object]
WeightFunc = Callable[[float, float, float], Tuple[float, float]]


# Constants representing options for how to choose transparency table
# weights for CO2 and H2O transparency lookup.
WEIGHT_TO_CLOSEST = "close"
WEIGHT_TO_LOWEST = "low"
WEIGHT_TO_HIGHEST = "high"
WEIGHT_BY_PROXIMITY = "mean"


# Keys in configuration dictionaries.
YEAR = "year"
NUM_LAYERS = "layers"
NUM_ITERS = "iters"
AGGREGATE_LAT = "aggregate_lat"
AGGREGATE_LEVEL = "aggregate_level"
# Names of data providers to use.
TEMP_SRC = "temp_src"
HUMIDITY_SRC = "humidity_src"
ALBEDO_SRC = "albedo_src"
ABSORBANCE_SRC = "abs_src"
CO2_WEIGHT = "CO2_weight"
H2O_WEIGHT = "H2O_weight"

AGGREGATE_BEFORE = "before"
AGGREGATE_AFTER = "after"
AGGREGATE_NONE = None


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


def weight_by_lowest(lower_val: float,
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
    The smallest one is chosen. This is equivalent to always rounding the
    actual concentration down to the nearest option.

    :param lower_val:
        The smaller of two CO2 concentration options
    :param upper_val:
        The larger of two CO2 concentration options
    :param actual:
        A real value for CO2 concentration that is to be approximated
    :return:
        An assignment of weight to lower_val and upper_val, in that order
    """
    return 1, 0


def weight_by_highest(lower_val: float,
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
    The largest one is chosen. This is equivalent to always rounding the
    actual concentration up to the nearest option.

    :param lower_val:
        The smaller of two CO2 concentration options
    :param upper_val:
        The larger of two CO2 concentration options
    :param actual:
        A real value for CO2 concentration that is to be approximated
    :return:
        An assignment of weight to lower_val and upper_val, in that order
    """
    return 1, 0


def weight_by_mean(lower_val: float,
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
    Weights are chosen proportionally to how close the actual value is to each
    option, with whichever option is closer receiving a higher weight.
    Effectively, weights the options by proximity to the actual value.

    :param lower_val:
        The smaller of two CO2 concentration options
    :param upper_val:
        The larger of two CO2 concentration options
    :param actual:
        A real value for CO2 concentration that is to be approximated
    :return:
        An assignment of weight to lower_val and upper_val, in that order
    """
    if lower_val == upper_val:
        return 1, 0
    else:
        lower_diff = actual - lower_val
        upper_diff = upper_val - actual
        total_diff = upper_val - lower_val

        # Actual value being far from an option gives that option low weight.
        lower_weight = 1 - (lower_diff / total_diff)
        upper_weight = 1 - (upper_diff / total_diff)

        return lower_weight, upper_weight


_transparency_weight_converter: Dict[str, WeightFunc] = {
    WEIGHT_TO_CLOSEST: weight_by_closest,
    WEIGHT_TO_LOWEST: weight_by_lowest,
    WEIGHT_TO_HIGHEST: weight_by_highest,
    WEIGHT_BY_PROXIMITY: weight_by_mean,
}


def get_transparency_weight_func(name: str) -> WeightFunc:
    return _transparency_weight_converter[name]


DEFAULT_CONFIG: Config = {
    YEAR: 1895,
    NUM_LAYERS: 1,
    NUM_ITERS: 1,
    AGGREGATE_LAT: AGGREGATE_AFTER,
    AGGREGATE_LEVEL: AGGREGATE_NONE,
    TEMP_SRC: "arrhenius",
    HUMIDITY_SRC: "arrhenius",
    ALBEDO_SRC: "landmask",
    ABSORBANCE_SRC: "table",
    CO2_WEIGHT: WEIGHT_TO_CLOSEST,
    H2O_WEIGHT: WEIGHT_TO_CLOSEST,
}