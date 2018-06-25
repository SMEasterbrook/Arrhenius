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


class OutputController:
    """
    An control point for model output. Acts as a logging center, allowing
    configuration of which output forms are permitted for each model run in
    an individual fashion.

    Forms of output are identified with enum types that subclass OutputConfig.
    Each enum within the class is a separate output form, and act
    independently. An enum type can be registered, enabling any output that is
    associated with that type. Output for any non-registered types is not
    allowed to go forward.

    Collections of output types allow all the output types to be handled at
    the same time. Collections are registered using a string, and can contain
    multiple enum types and any number of other collections within them.

    Each collection or output type requires a handler function that is
    executed on any data that is associated with that collection or type.
    For collections, the collection's substructure is passed into the handler
    along with the data, so that the handler may know which output types were
    registered in the collection.
    """
    def __init__(self: 'OutputController',
                 model_run_title: str) -> None:
        """
        Create a new OutputController. Initially, no output types or
        collections are registered in the controller.

        A title parameter describes the model run, and should be unique and
        informative. The title may be used for some output types.

        :param model_run_title:
            The title of the model run
        """
        self._title = model_run_title
        self._collections = {}
        self._output_handlers = {}
