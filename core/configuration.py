from typing import Union, Optional, Tuple, Dict, Callable
from threading import local
from os import path

from frozendict import frozendict
from datetime import datetime

import json
from jsonschema import validate
from jsonschema.exceptions import ValidationError
import xml.etree.ElementTree as ETree

from data.resources import MAIN_PATH
from data.provider import PROVIDERS
from data.grid import GridDimensions

# Type aliases
Config = 'ArrheniusConfig'
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
CO2_RANGE = "co2"
CO2_INIT = "from"
CO2_FINAL = "to"
NUM_LAYERS = "layers"
NUM_ITERS = "iters"
AGGREGATE_LAT = "aggregate_lat"
AGGREGATE_LEVEL = "aggregate_level"
COLORBAR_SCALE = "scale"
# Names of data providers to use.
TEMP_SRC = "temp_src"
HUMIDITY_SRC = "humidity_src"
ALBEDO_SRC = "albedo_src"
ABSORBANCE_SRC = "absorbance_src"
PRESSURE_SRC = "pressure_src"
CO2_WEIGHT = "CO2_weight"
H2O_WEIGHT = "H2O_weight"

# Keys for grid specification substructure.
GRID_DIMS = "dims"
GRID_TYPE = "repr"
GRID_FORMAT_LAT = "lat"
GRID_FORMAT_LON = "lon"

AGGREGATE_BEFORE = "before"
AGGREGATE_AFTER = "after"
AGGREGATE_NONE = "none"

ABS_SRC_TABLE = "table"
ABS_SRC_MODERN = "modern"
ABS_SRC_MULTILAYER = "multilayer"


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
JSON_DEFAULT = path.join(MAIN_PATH, 'core', 'default_config.json')
JSON_SCHEMA_FILE = path.join(MAIN_PATH, 'core', 'config_schema.json')

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


class InvalidConfigError(ValueError):
    """
    An exception class indicating invalid values for a configuration option,
    which were not checked by schema validation.

    Configuration options can be invalid if integers are out of range, if
    string enums do not take on an allowed value, or if nested objects do not
    have the right nesting structure. In all cases, the configuration set is
    considered unusable and the model run is rejected.

    These errors should typically be raised before a model run, and any
    attempt to parse to parse configuration from an external source should
    catch these errors.
    """
    pass


class ArrheniusConfig:
    """
    A condensed configuration object, based on a JSON configuration file. This
    object provides validity checks for various configuration options,
    consolidates or separates some options, and converts some string
    identifiers within the configuration file into the objects they represent.

    Instead of dictionary lookup, the object provides methods for accessing
    various configuration options. This approach allows a more thorough type
    contract for each option, specifying that one option is a Callable while
    another is an int. Simultaneously, it becomes easier to access and update
    options without having to define key constants, or use some from another
    module.

    For more specific use cases, the object allows the introduction of new
    options through standard dictionary notation. This can be used to create
    short-term options for testing, or custom control options where convenient.
    """
    def __init__(self: 'ArrheniusConfig',
                 basis: Dict) -> None:
        """
        Initialize a new Configuration instance, converting the configuration
        option keys in basis into the configurations they represent.

        Most configuration options are necessary to support full configuration.
        If any necessary options are not specified in basis, an
        InvalidConfigError will be raised. This type of error will also be
        raised if any values violate preconditions.

        :param basis:
            A JSON object specifying configuration options
        """
        self._settings = {}

        def attempt_load(loader: Callable,
                         *vars: Optional[str]) -> None:
            """
            Attemps to call the setter method given be loader to set
            configuration options associated with the keys given by all
            other parameters. Raises an InvalidConfigError if the relevant
            configuration options have not been given a value in basis.

            :param loader:
                The setter method to load the variables
            :param vars:
                The keys associated with the variables
            """
            for key in vars:
                if key not in basis:
                    raise InvalidConfigError("\"" + key + "\" is a required"
                                             " configuration field.")
            params = (basis[var] for var in vars)
            loader(*params)

        attempt_load(self.set_co2_bounds, "co2")
        attempt_load(self.set_grid, "grid")
        attempt_load(self.set_layers, "layers")
        attempt_load(self.set_iters, "iters")
        attempt_load(self.set_aggregations,
                     "aggregate_lat", "aggregate_level")
        attempt_load(self.set_providers, "temp_src", "humidity_src",
                                          "albedo_src", "absorbance_src")
        self.set_colorbar(basis.get("scale", (-8, 8)))

        try:
            attempt_load(self.set_year, "year")
        except InvalidConfigError:
            self._settings[YEAR] = datetime.now().year

        if self._settings[ABSORBANCE_SRC] == ABS_SRC_TABLE:
            attempt_load(self.set_table_auxiliaries,
                         "CO2_weight", "H2O_weight")
        else:
            # Set None values for all provider keys except pressure,
            # to prevent them from being changed.
            attempt_load(self.set_providers,
                         None, None, None, None, "pressure_src")

        try:
            attempt_load(self.set_run_id, "run_id")
        except InvalidConfigError:
            # Remove any keys from the dictionary that do not affect ID.
            for ignored_key in [COLORBAR_SCALE]:
                del basis[ignored_key]
            config_hash_val = abs(freeze_dict(basis).__hash__())

            # Convert to hexadecimal for compaction and remove the 0x from the front.
            self._settings[RUN_ID] = hex(config_hash_val)[2:]

    def __setitem__(self: 'ArrheniusConfig',
                    key: str,
                    value: object) -> None:
        """
        Sets a configuration attribute by the name of key to value.
        This can be used to add new, custom attributes to a configuration set.

        :param key:
            The name of the new attribute
        :param value:
            The value of the new attribute
        """
        self._settings[key] = value

    def __getitem__(self: 'ArrheniusConfig',
                    key: str) -> object:
        """
        Get the value of a configuration by the name of key. This applies to
        both preexisting attributes and custom attributes.

        :param key:
            The name of the attribute
        """
        try:
            return self._settings[key]
        except KeyError:
            raise AttributeError("No configuration option {} has been set"
                                 .format(key))

    def set_run_id(self: 'ArrheniusConfig',
                   run_id: str) -> None:
        """
        Sets a value for the model's ID value. If a value is not specified,
        then a an ID will be chosen automatically based on the configuration
        options.

        :param run_id:
            The model run's unique ID
        """
        if len(run_id) < 1:
            raise InvalidConfigError("\"run_id\" cannot be an empty string")

        self._settings[RUN_ID] = run_id

    def set_year(self: 'ArrheniusConfig',
                 year: int) -> None:
        """
        Sets a value for the year option, specifying which year to pull data
        from in modern or multilayer model runs. If this option is omitted,
        the current year will be chosen.

        :param year:
            The year from which model data will be pulled
        """
        self._settings[YEAR] = year

    def set_co2_bounds(self: 'ArrheniusConfig',
                       co2: Dict[str, float]) -> None:
        """
        Sets the values for initial and final CO2 concentration multiplier,
        relative to the value that is current to the chosen year option.

        Settings of these variables should be passed in a dictionary, mapping
        the string "to" to initial multiplier, and "from" to final multiplier.
        If either of these keys is omitted, or either value is non-positive,
        then an InvalidConfigError will be raised.

        :param co2:
            A dictionary giving initial and final CO2 multipliers.
        """
        for param in ["from", "to"]:
            if param not in co2:
                raise InvalidConfigError("\"" + param + "\" is a required"
                                         " field for CO2 configuration")

        if co2["from"] != 1:
            raise InvalidConfigError("Only initial CO2 values of 1.0 are"
                                     " currently supported (is {})."
                                     .format(co2["from"]))

        self._settings[CO2_INIT] = co2["from"]
        self._settings[CO2_FINAL] = co2["to"]

    def set_grid(self: 'ArrheniusConfig',
                 grid: Dict[str, Union[str, Dict[str, int]]]) -> None:
        """
        Sets the global grid that surface and atmospheric data will be
        represented on.

        Settings of these variables should be stored in a dictionary, mapping
        "repr" to the grid's representation type, and "dims" to a nested
        dictionary storing lat and lon values under those keys. If any of this
        structure is violated, or the values are invalid for constructing a
        grid, then an InvalidConfigError will be raised.

        :param grid:
            A dictionary giving grid dimension specifications
        """
        if "dims" not in grid:
            raise InvalidConfigError("\"dims\" is a required"
                                     " field for grid specification")

        dims = grid["dims"]
        for param in ["lat", "lon"]:
            if param not in dims:
                raise InvalidConfigError("\"" + param + "\" is a required"
                                         " field for grid dimensions")
        dims_tuple = (dims["lat"], dims["lon"])
        self._settings[GRID] = GridDimensions(dims_tuple, grid.get("repr", "width"))

    def set_layers(self: 'ArrheniusConfig',
                   layers: int) -> None:
        """
        Sets the number of layers that should be used in a multilayer model
        run. This option is disregarded in any single layer model run.

        :param layers:
            The number of layers in a multilayer model
        """
        if layers < 1:
            raise InvalidConfigError("Number of layers must be positive"
                                     " (is {})".format(layers))

        self._settings[NUM_LAYERS] = layers

    def set_iters(self: 'ArrheniusConfig',
                  iters: int) -> None:
        """
        Sets the number of calculation iterations for the humidity-
        transparency feedback effect.

        :param iters:
            The number of humidity recalculations per grid cell
        """
        if iters < 0:
            raise InvalidConfigError("Number of feedback iterations must be"
                                     " non-negative (is {})".format(iters))

        self._settings[NUM_ITERS] = iters

    def set_aggregations(self: 'ArrheniusConfig',
                         agg_lat: Optional[str] = None,
                         agg_level: Optional[str] = None) -> None:
        """
        Sets one or both of agg_lat and agg_level configuration options,
        whichever one(s) is/are not None. These options control conversion
        of model output into an equivalent representation with one latitude
        layer or one atmospheric layer, respectively.

        :param agg_lat:
            A key representing the setting of the aggregate latitude option
        :param agg_level:
            A key representing the setting of the aggregate level option
        """
        options = [AGGREGATE_BEFORE, AGGREGATE_AFTER, AGGREGATE_NONE]
        ops_example = "\n" + "\", \"".join(options[:-1])\
                      + "\", and \""+ str(options[-1]) + "\""

        if agg_lat is not None:
            if agg_lat not in options:
                raise InvalidConfigError("\"aggregate_lat\" must be one of "
                                         + ops_example + " (is \"{}\")."
                                         .format(agg_lat))
            self._settings[AGGREGATE_LAT] = agg_lat

        if agg_level is not None:
            if agg_level not in options:
                raise InvalidConfigError("\"aggregate_level\" must be one of "
                                         + ops_example + " (is \"{}\")."
                                         .format(agg_level))
            self._settings[AGGREGATE_LEVEL] = agg_level

    def set_providers(self: 'ArrheniusConfig',
                      temperature: Optional[str] = None,
                      humidity: Optional[str] = None,
                      albedo: Optional[str] = None,
                      absorbance: Optional[str] = None,
                      pressure: Optional[str] = None) -> None:
        """
        Sets one or more of the provider functions specified by keys passed
        through keyword arguments, whichever ones are provided and are not
        None. The absorbance option additionally gives the model's execution
        mode, whether it runs with old or new data, single or multiple layers.

        :param temperature:
            The key for a temperature provider function
        :param humidity:
            The key for a humidity provider function
        :param albedo:
            The key for an inverse albedo provider function
        :param absorbance:
            The absorption mode for the model run
        :param pressure:
            The key for a pressure provider function
        """
        temp_options = PROVIDERS["temperature"]
        humidity_options = PROVIDERS["humidity"]
        albedo_options = PROVIDERS["albedo"]
        pressure_options = PROVIDERS["pressure"]
        absorbance_options = [ABS_SRC_TABLE, ABS_SRC_MODERN,
                              ABS_SRC_MULTILAYER]

        if temperature is not None:
            if temperature not in temp_options:
                example = "\"" + "\", \"".join(temp_options.keys()[:-1]) \
                          + "\", and \"" + temp_options.keys()[-1] + "\""
                raise InvalidConfigError("Temperature provider must be on of "
                                         + example + " (is \"{}\")."
                                         .format(temperature))
            self._settings[TEMP_SRC] = temp_options[temperature]

        if humidity is not None:
            if humidity not in humidity_options:
                example = "\"" + "\", \"".join(humidity_options.keys()[:-1]) \
                          + "\", and \"" + humidity_options.keys()[-1] + "\""
                raise InvalidConfigError("Humidity provider must be on of "
                                         + example + " (is \"{}\")."
                                         .format(humidity))
            self._settings[HUMIDITY_SRC] = humidity_options[humidity]

        if albedo is not None:
            if albedo not in albedo_options:
                example = "\"" + "\", \"".join(albedo_options.keys()[:-1]) \
                          + "\", and \"" + albedo_options.keys()[-1] + "\""
                raise InvalidConfigError("Albedo provider must be on of "
                                         + example + " (is \"{}\")."
                                         .format(albedo))
            self._settings[ALBEDO_SRC] = albedo_options[albedo]

        if absorbance is not None:
            if absorbance not in absorbance_options:
                example = "\"" + "\", \"".join(absorbance_options[:-1]) \
                          + "\", and \"" + absorbance_options[-1] + "\""
                raise InvalidConfigError("Absorbance mode must be on of "
                                         + example + " (is \"{}\")."
                                         .format(absorbance))
            self._settings[ABSORBANCE_SRC] = absorbance

        if pressure is not None:
            if absorbance == ABS_SRC_TABLE:
                raise InvalidConfigError("Pressure provider \"{}\" is invalid"
                                         " for Arrhenius (\"{}\") data mode."
                                         .format(pressure, ABS_SRC_TABLE))

            if pressure not in pressure_options:
                example = "\"" + "\", \"".join(pressure_options.keys()[:-1]) \
                          + "\", and \"" + pressure_options.keys()[-1] + "\""
                raise InvalidConfigError("Pressure provider must be on of "
                                         + example + " (is \"{}\")."
                                         .format(pressure))
            self._settings[PRESSURE_SRC] = pressure_options[pressure]

    def set_table_auxiliaries(self: 'ArrheniusConfig',
                              co2_weight_func: Optional[str] = None,
                              h2o_weight_func: Optional[str] = None) -> None:
        """
        Sets which weight functions are used to interpolate the weights of
        transparencies for nearest CO2 and H2O values, respectively, for
        whichever parameters are provided and not None.

        :param co2_weight_func:
            The key for a transparency weighting function for CO2
        :param h2o_weight_func:
            The key for a transparency weighting function for H2O
        """
        options = list(_transparency_weight_converter.keys())

        if co2_weight_func in options:
            self._settings[CO2_WEIGHT] =\
                _transparency_weight_converter[co2_weight_func]
        else:
            example = "\"" + "\", \"".join(options[:-1])\
                      + "\", and \"" + options[-1] + "\""
            raise InvalidConfigError("CO2 weight function must be one of "
                                     + example + " (is \"{}\")."
                                     .format(co2_weight_func))

        if h2o_weight_func in options:
            self._settings[H2O_WEIGHT] =\
                _transparency_weight_converter[h2o_weight_func]
        else:
            example = "\"" + "\", \"".join(options[:-1]) \
                      + "\", and \"" + options[-1] + "\""
            raise InvalidConfigError("H2O weight function must be one of "
                                     + example + " (is \"{}\")."
                                     .format(h2o_weight_func))

    def set_colorbar(self: 'ArrheniusConfig',
                     colorbar_scale: Tuple[float, float]) -> None:
        """
        Sets the lower and upper bounds for the color scale in any images
        rendered during the model run, given by the first and second elements
        of colorbar_scale.

        :param colorbar_scale:
            The bounds on colour values for the model's images
        """
        if colorbar_scale[0] >= colorbar_scale[1]:
            raise InvalidConfigError("Lower bound of colorbar scale must"
                                     " be less than upper bound ({} >= {})"
                                     .format(colorbar_scale[0],
                                             colorbar_scale[1]))

        self._settings[COLORBAR_SCALE] = colorbar_scale

    def run_id(self: 'ArrheniusConfig') -> str:
        """
        Returns the unique ID for this model configuration.

        :return:
            The configuration's ID
        """
        return self._settings[RUN_ID]

    def year(self: 'ArrheniusConfig') -> int:
        """
        Returns the year from which data will be chosen for the upcoming
        model run. This parameter is ignored when original Arrhenius data
        is selected.

        :return:
            The year from which model data will be pulled
        """
        return self._settings[YEAR]

    def init_co2(self: 'ArrheniusConfig') -> float:
        """
        Returns the multiplier of atmospheric CO2 concentration for initial
        model state. The multiplier is relative to the concentration present
        at the year chosen, or in 1895 under Arrhenius data mode.

        :return:
            Initial CO2 concentration multiplier
        """
        return self._settings[CO2_INIT]

    def final_co2(self: 'ArrheniusConfig') -> float:
        """
        Returns the multiplier of atmospheric CO2 concentration for final
        model state. The multiplier is relative to the concentration present
        at the year chosen, or in 1895 under Arrhenius data mode.

        :return:
            Final CO2 concentration multiplier
        """
        return self._settings[CO2_FINAL]

    def grid(self: 'ArrheniusConfig') -> GridDimensions:
        """
        Returns the 2-dimensional latitude-longitude grid that all surface/
        atmospheric data is represented on. In the case of a multilayer
        atmosphere, each individual layer is represented on this grid.

        :return:
            The flat latitude/longitude grid for Earth data
        """
        return self._settings[GRID]

    def layers(self: 'ArrheniusConfig') -> int:
        """
        Returns the number of layers in a multilayer model. This option is
        ignored in Arrhenius mode, or single-layer modern data runs.

        :return:
            The number of layers in a multilayer model
        """
        return self._settings[NUM_LAYERS]

    def iterations(self: 'ArrheniusConfig') -> int:
        """
        Returns the number of calculation iterations for the humidity-
        transparency feedback effect.

        :return:
            The number of humidity recalculations per grid cell
        """
        return self._settings[NUM_ITERS]

    def aggregate_latitude(self: 'ArrheniusConfig') -> Optional[str]:
        """
        Returns the settings for latitude aggregation, specifying when/whether
        to replace rows of grid cells with average values over those rows. In a
        multilayer model, this mode applies to all layers individually.

        :return:
            The aggregate latitude option's setting
        """
        return self._settings[AGGREGATE_LAT]

    def aggregate_level(self: 'ArrheniusConfig') -> Optional[str]:
        """
        Returns the settings for level aggregation in a multilayer model,
        specifying when/whether to convert the multilayer data into a
        single-layer version.

        :return:
            The aggregate level option's setting
        """
        return self._settings[AGGREGATE_LEVEL]

    def model_mode(self: 'ArrheniusConfig') -> str:
        """
        Returns the absorption mode of the upcoming model run, which
        identifies whether Arrhenius' data, modern data, or multilayered
        data is used.

        :return:
            The model's absorption mode
        """
        return self._settings[ABSORBANCE_SRC]

    def temp_provider(self: 'ArrheniusConfig') -> Callable:
        """
        Returns the temperature provider function for the upcoming model run.
        That function returns temperature data to run the model on, regridded
        to its grid parameter.

        :return:
            A temperature provider function
        """
        return self._settings[TEMP_SRC]

    def humidity_provider(self: 'ArrheniusConfig') -> Callable:
        """
        Returns the elative humidity provider function for the upcoming model
        run. That function returns humidity data to run the model on, regridded
        to its grid parameter.

        :return:
            A relative humidity provider function
        """
        return self._settings[HUMIDITY_SRC]

    def albedo_provider(self: 'ArrheniusConfig') -> Callable:
        """
        Returns the inverse albedo provider function for the upcoming model
        run. That function returns data regridded to its grid parameter, each
        value representing 1 minus the albedo in the corresponding grid cell.

        :return:
            An inverse albedo provider function
        """
        return self._settings[ALBEDO_SRC]

    def pressure_provider(self: 'ArrheniusConfig') -> Callable:
        """
        Returns the pressure provider function for the upcoming modern model
        run. The function returns a vector of pressure values that mark the
        borders of atmospheric layers. These can be used to infer the heights
        of each layer.

        :return:
            An atmospheric pressure provider function
        """
        try:
            return self._settings[PRESSURE_SRC]
        except KeyError:
            raise AttributeError("No value specified for pressure_provider")

    def table_auxiliaries(self: 'ArrheniusConfig') -> (Callable, Callable):
        """
        Returns additional functions used in original Arrhenius data mode.
        First is a function used to assign weights to adjacent CO2 values.
        Second is the corresponding function for adjacent H2O values.

        :return:
            Weight functions for CO2 and H2O in Arrhenius mode, respectively
        """
        try:
            co2_function = self._settings[CO2_WEIGHT]
        except KeyError:
            raise AttributeError("No value specified for CO2 weight function")

        try:
            h2o_function = self._settings[H2O_WEIGHT]
        except KeyError:
            raise AttributeError("No value specified for H2O weight function")

        return co2_function, h2o_function

    def colorbar(self: 'ArrheniusConfig') -> Tuple[float, float]:
        """
        Returns the lower and upper bounds for the color scale in any images
        rendered during the model run.

        :return:
            The bounds on colour values for the model's images
        """
        return self._settings[COLORBAR_SCALE]


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
    try:
        validate(options, json_schema)
    except ValidationError as err:
        raise InvalidConfigError("Configuration failed to validate: "
                                 + err.message)

    return ArrheniusConfig(options)


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

    return ArrheniusConfig(options)


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


# Dictionary of thread-specific variables, accessible at global scope.
# Set up initial state.
globals = local()


def global_config() -> 'ArrheniusConfig':
    """
    Returns the thread's active configuration set.

    :return:
        The thread-global configuration
    """
    try:
        return globals.conf
    except AttributeError:
        default = default_config()
        globals.conf = default
        return default


def set_configuration(config: 'ArrheniusConfig') -> None:
    """
    Replace the active thread-specific configuration set with conf.
    Other threads will not see the change.

    :param config:
        A new configuration set to be used by this thread
    """
    globals.conf = config