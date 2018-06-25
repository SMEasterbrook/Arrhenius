from enum import Enum, auto


class OutputConfig(Enum):
    """
    An enum indicating a model output type, be it through printing, logging,
    or various types of file writing. Subclasses can be created to represent
    related categories of output.
    """
    pass


class ReportDatatype(OutputConfig):
    """
    An output category for output of primary model data based on the gridded
    data on which the model is run. Output can be triggered before or after
    the model has made calculations on the grid.

    These enum types align with data contained in each cell of the grids.
    As such, there is one-to-one correspondence between datapoints in the
    grid cells and these enums.
    """
    # Grid cell temperature.
    REPORT_TEMP = 'temperature'
    # Grid cell temperature change over the model run.
    REPORT_TEMP_CHANGE = 'delta_t'
    # Grid cell relative humidity.
    REPORT_HUMIDITY = 'humidity'
    # Grid cell humidity change over the model run.
    REPORT_HUMIDITY_CHANGE = 'delta_hum'
    # Grid cell albedo.
    REPORT_ALBEDO = 'albedo'


class SpecialReportData(OutputConfig):
    """
    An output category for non-primary model output, typically with special
    requirements. For instance, may require two pieces of data for comparison.

    These data types do not align with grid cell data, and are generally used
    for larger, tabular data forms.
    """
    # Output differences between temperature change and expected values
    # according to a separate model run.
    REPORT_DELTA_TEMP_DEVIATIONS = auto()
    # Combined output for temperature change, along with differences between
    # temperature change and expected values according to other model runs.
    REPORT_DELTA_TEMP_PLUS_DEVIATIONS = auto()


class AccuracyMetrics(OutputConfig):
    """
    An output category for statistical analysis of results. May include sample
    means, variances, or measures of similarity to some expected results.
    """
    # Average of temperature change deviations from expected values.
    TEMP_DELTA_AVG_DEVIATION = auto()
    # Standard deviation of temperature change from expected values.
    TEMP_DELTA_STD_DEVIATION = auto()
    # Variance of temperature change difference from expected value.
    TEMP_DELTA_VARIANCE = auto()


class Debug(OutputConfig):
    """
    An output category for miscellaneous debug information.
    """
    # Prints grid cells along with the temperature change over the model run.
    GRID_CELL_DELTA_TEMP = auto()
    # Prints grid cells along with the transparency change over the model run.
    GRID_CELL_DELTA_TRANSPARENCY = auto()
    # Prints progress information at important stages in the model run.
    PRINT_NOTICES = auto()
