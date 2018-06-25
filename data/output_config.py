from enum import Enum, auto
from typing import Tuple, Dict, Callable, Optional

from data.configuration import Config


# Type aliases
OutputTypeHandler = Callable[[str, object], None]
CollectionHandler = Callable[[str, Config, object]]


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


# Keys in collection dictionaries
COLLECTION_SUBTYPES = "Contents"
COLLECTION_HANDLERS = "Handlers"


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
        self._output_types = {}

    def _navigate_collection_path(self: 'OutputController',
                                  collection_path: Tuple[str]) -> Dict:
        """
        Returns the collection structure specified by the single argument.

        :param collection_path:
            A path to the collection in question through its ancestors
        :return:
            The collection defined by the path
        """
        collection = self._collections
        for collection_name in collection_path:
            collection = collection[collection_name]

        return collection

    def enable_output_type(self: 'OutputController',
                           output_type: 'OutputConfig',
                           handler: OutputTypeHandler = print) -> None:
        """
        Register an output type to allow its output to be processed.

        When any data is submitted for output that is associated with the
        given output type, it will by default be printed to the console.
        If a handler is provided through the optional second argument,
        this handler will be invoked instead.

        Once an output type is enabled, it cannot be disabled. However, its
        handler can be changed by calling enable_output_type again with a
        different handler.

        :param output_type:
            The type of output being registered
        :param handler:
            A function that will be called on any output of that type
        """
        self._output_types[output_type] = handler

    def submit_output(self: 'OutputController',
                      output_type: 'OutputConfig',
                      data: object) -> None:
        """
        Submit data for output, associated with one type of output as
        described by an OutputConfig subclass. The output will be ignored
        if the output type is not registered with this instance.

        If the output type is registered with this instance, its handler
        function will be executed, taking this model run's title as its
        first argument, and the data as its second argument.

        :param output_type:
            The type of output the data is associated with
        :param data:
            Data to be output
        """
        if output_type in self._output_types:
            handler = self._output_types[output_type]
            handler(self._title, data)

    def register_collection(self: 'OutputController',
                            collection_name: str,
                            supercollections: Tuple[str] = (),
                            handler: Optional[CollectionHandler] = None) -> None:
        """
        Creates a new collection in the collection directory, without any
        output types registered in it.

        If the collection already exists, it is not overwritten, but its
        handler function may be replaced if a new one is provided.

        A collection can have contain three types of structures: it can hold
        a set of output types that are considered active; it can hold a
        handler function that is invoked on any data that is associated with
        the collection; and it can hold further collections inside of it.

        The optional supercollections parameter specifies the ancestor
        collections under which the new one is to be created, in order of
        appearance in the collections directory structure. If not provided,
        the new collection will be created at the top level of the directory.

        The optional handler parameter gives the option to specify a handler
        function that is invoked when data is associated with the collection.
        If not provided, the collection will not have a handler, which is
        permissible as long as one of its ancestors has a handler.

        :param collection_name:
            The name of the new collection
        :param supercollections:
            A path to the parent of the new collection, through its ancestors
        :param handler:
            A function that will be called on any output to this collection
        """
        parent_collection = self._navigate_collection_path(supercollections)

        # Add the new collection if not present, but do not overwrite if
        # already present.
        if collection_name in parent_collection:
            collection = parent_collection[collection_name]
        else:
            collection = {}
            parent_collection[collection_name] = collection

        # Only add a handler entry into the dict if a handler is specified.
        if handler is not None:
            collection[COLLECTION_HANDLERS] = handler

    def enable_collection_type(self: 'OutputController',
                               collection_path: Tuple[str],
                               output_type: 'OutputConfig') -> None:
        """
        Record that a given output type is enabled within a collection.

        This output type will be allowed when data is received that is
        associated with the collection. However, how the data is output
        depends on the collection's handler function, and may not be
        specified for the output type alone.

        :param collection_path:
            A path to the collection in question through its ancestors
        :param output_type:
            The type of output being registered
        """
        collection = self._navigate_collection_path(collection_path)

        # Accumulate output types in a set. The set may not be present when
        # the first output type is registered, and may need to be created.
        if COLLECTION_SUBTYPES not in collection:
            collection[COLLECTION_SUBTYPES] = {output_type}
        else:
            collection[COLLECTION_SUBTYPES].add(output_type)

    def submit_collection_output(self: 'OutputController',
                                 collection_path: Tuple[str],
                                 data: object) -> None:
        """
        Submit data for output, associated with the collection described by
        the collection path argument.

        This operation is only valid if a handler function has been registered
        with the collection in question. If so, this handler is invoked with
        the model run's title as its first argument, a dict containing the
        collection's substructure as its second argument, and the data as its
        third argument.

        The second argument, the collection structure, contains information
        such as child collections, and a set of output types that are enabled
        within the collection.

        Precondition:
            A handler has been registered with this collection.

        :param collection_path:
            A path to the collection in question through its ancestors
        :param data:
            Data to be output
        """
        collection = self._navigate_collection_path(collection_path)
        handler = collection[COLLECTION_HANDLERS]
        handler(self._title, collection, data)
