from typing import Tuple, Dict, Callable
from frozendict import frozendict

import json
from jsonschema import validate
import xml.etree.ElementTree as ETree

from data.provider import PROVIDERS
from data.grid import GridDimensions

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
RUN_ID = "ID"
YEAR = "year"
GRID = "grid"
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

# Keys for grid specification substructure.
GRID_DIMS = "dims"
GRID_TYPE = "repr"
GRID_FORMAT_LAT = "lat"
GRID_FORMAT_LON = "lon"

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


# Preloaded configuration files.
JSON_DEFAULT = "../core/default_config.json"
JSON_SCHEMA_FILE = "../core/config_schema.json"

json_schema = json.loads(open(JSON_SCHEMA_FILE, "r").read())


def freeze_dict(mutable_dict: Dict) -> frozendict:
    """
    Translates the standard Python dict mutable_dict into immutable form,
    including any other dictionaries that are values in the dict. Returns
    this immutable form of the dict.

    Note: Mutable objects, such as user-defined classes, cannot be converted
    into immutable form in the same way as other types. Therefore mutable_dict
    must not contain any user-defined classes as values.

    Additionally, list conversion is not supported yet, so mutable_dict must
    not contain any lists as values.

    :param mutable_dict:
        A standard Python dict
    :return:
        The original dict in immutable form
    """
    for k, v in mutable_dict.items():
        if isinstance(v, dict):
            mutable_dict[k] = freeze_dict(v)

    return frozendict(mutable_dict)



def from_json_string(json_data: str) -> Config:
    """
    Produce a configuration object from a string containing JSON-formatted
    data. Any strings that are used to identify functions are replaced by
    the appropriate functions.

    See specifications for input dictionary under configuration.py.

    :param json_data:
        A JSON string containing a configuration dictionary
    :return:
        A configuration object based on the JSON data
    """
    options = json.loads(json_data)
    validate(options, json_schema)

    return from_dict(options)


def from_xml_string(xml_data: str) -> Config:
    """
    Produce a configuration object from a string containing XML-formatted
    data. Any strings that are used to identify functions are replaced by
    the appropriate functions.

    See specifications for input dictionary under configuration.py.

    :param xml_data:
        An XML string containing a configuration dictionary
    :return:
        A configuration object based on the XML data
    """
    xml_tree = ETree.fromstring(xml_data)
    options = {child.tag: child.data.strip() for child in xml_tree}

    return from_dict(options)


def from_dict(options: Dict[str, str]) -> Config:
    """
    Returns a proper config object based on the config options dictionary,
    by replacing string identifiers with the objects they identify. The
    original dictionary is not modified in the process.

    For example, data provider functions are identified by string names in
    an original configuration input. These names are converted into the
    appropriate function objects in the final configuration object.

    :param options:
        A dictionary of configuration objects
    :return:
        A configuration object based on the dictionary, with some strings
        being replaced with non-serializable objects they identify.
    """
    config = {k: v for k, v in options.items()}

    # Generate a hash value from the options, which are all strings or
    # dicts. Each set of options should generate a unique hash.
    # Make all hash keys positive.
    config_hash_val = abs(freeze_dict(options).__hash__())
    # Convert to hexadecimal for compaction and remove the 0x from the front.
    config[RUN_ID] = hex(config_hash_val)[2:]

    # Transform grid specifications (strings) into a grid object.
    grid_dict = config[GRID][GRID_DIMS]
    grid_dims = (grid_dict[GRID_FORMAT_LAT], grid_dict[GRID_FORMAT_LON])
    config[GRID] = GridDimensions(grid_dims, config[GRID][GRID_TYPE])

    # For data providers, replace strings that identify functions with the
    # functions themselves.
    config[TEMP_SRC] = PROVIDERS['temperature'][config[TEMP_SRC]]
    config[HUMIDITY_SRC] = PROVIDERS['humidity'][config[HUMIDITY_SRC]]
    config[ALBEDO_SRC] = PROVIDERS['albedo'][config[ALBEDO_SRC]]

    # Replace string identifying transparency-weighting functions with the
    # functions themselves.
    for trans_weight_option in ['CO2_weight', 'H2O_weight']:
        if trans_weight_option in config:
            config[trans_weight_option] = \
                _transparency_weight_converter[config[trans_weight_option]]

    return config


def default_config() -> Config:
    """
    Returns a set of default configuration options for running the Arrhenius
    model. Approximates Arrhenius' original model run using his original data.

    See the default_config.json file for specification.

    :return:
        Default configuration options for the Arrhenius model
    """
    # Recover config options from a local JSON file.
    default_json_file = open(JSON_DEFAULT, "r")
    default_json_str = default_json_file.read()
    default_json_file.close()

    return from_json_string(default_json_str)
