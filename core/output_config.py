from enum import Enum, auto
from typing import List, Tuple, Dict, Callable, Optional
from threading import local

# Type aliases
OutputTypeHandler = Callable[..., None]
CollectionHandler = Callable[..., None]


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


def prefix_print(data: object,
                 prefix: Optional[str] = None) -> None:
    """
    Print data in a formatted manner. Begin the line by printing the contents
    of the second argument, followed by a colon, if the second argument is
    provided and is not None. Otherwise just print the data.

    :param data:
        Data to be printed to console
    :param prefix:
        An optional string that may be printed before the data
    """
    if prefix is None:
        print(data)
    else:
        print(prefix + ":", data)


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
    For collections, additional information may be passed into the handler
    so that the collection can know about its contents.
    """
    def __init__(self: 'OutputController') -> None:
        """
        Create a new OutputController. Initially, no output types or
        collections are registered in the controller.
        """
        self._output_tree = {}

    def _navigate_collection_path(self: 'OutputController',
                                  collection_path: Tuple[str, ...]) -> Dict:
        """
        Returns the collection structure specified by the single argument.

        :param collection_path:
            A path to the collection in question through its ancestors
        :return:
            The collection defined by the path
        """
        collection = self._output_tree
        for collection_name in collection_path:
            collection = collection[collection_name]

        return collection

    def enable_output_type(self: 'OutputController',
                           output_type: 'OutputConfig',
                           parent_collections: Tuple[str, ...] = (),
                           handler: OutputTypeHandler = prefix_print) -> None:
        """
        Register an output type to allow its output to be processed.

        The output type will by default be applied to the upper-most level
        of the collection hierarchy, and will not be contained in any
        collection. However, a collection can be specified by a path to the
        collection to which the output type will be added, passed through the
        parameter parent_collections.

        When any data is submitted for output that is associated with the
        given output type, it will by default be printed to the console.
        If a handler is provided through the optional third argument,
        this handler will be invoked instead.

        Once an output type is enabled, it cannot be disabled. However, its
        handler can be changed by calling enable_output_type again with a
        different handler.

        :param output_type:
            The type of output being registered
        :param parent_collections:
            A tuple of all the collections in which the output type is nested,
            in order of appearance in the collections hierarchy.
        :param handler:
            A function that will be called on any output of that type
        """
        parent = self._navigate_collection_path(parent_collections)
        parent[output_type] = handler

    def change_handler_if_enabled(self: 'OutputController',
                                  output_type: 'OutputConfig',
                                  parent_collections: Tuple[str, ...] = (),
                                  handler: OutputTypeHandler = prefix_print)\
            -> None:
        """
        Set the handler function for output_type to handler, but only if
        output_type is already enabled.

        By default, output_type will be looked for in the top level of the
        collections hierarchy: that is, not in any collection at all. The
        optional third argument specifies the path to a collection in which
        to look for output_type and possibly change its handler. No other
        collections will be affected, nor will the top level of the
        collections hierarchy.

        :param output_type:
            The type of output being registered
        :param parent_collections:
            A tuple of all the collections in which the output type is nested,
            in order of appearance in the collections hierarchy.
        :param handler:
            A function that will be called on any output of that type
        """
        parent_collection = self._navigate_collection_path(parent_collections)

        if output_type in parent_collection:
            parent_collection[output_type] = handler

    def submit_output(self: 'OutputController',
                      output_type: 'OutputConfig',
                      data: object,
                      *bonus_args) -> None:
        """
        Submit data for output, associated with one type of output as
        described by an OutputConfig subclass. The output will be ignored
        if the output type is not registered with this instance.

        If the output type is registered with this instance, its handler
        function will be executed, taking the data parameter as its first
        argument. Any further arguments after the data will be passed into
        the handler function in the same order as they are passed into this
        method.

        :param output_type:
            The type of output the data is associated with
        :param data:
            Data to be output
        :param bonus_args:
            A series of any other arguments that will be passed into the
            handler function, in order of passing
        """
        if output_type in self._output_tree:
            handler = self._output_tree[output_type]
            handler(data, *bonus_args)

    def register_collection(self: 'OutputController',
                            collection_name: str,
                            supercollections: Tuple[str, ...] = (),
                            handler: Optional[CollectionHandler] = None)\
            -> None:
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

    def submit_collection_output(self: 'OutputController',
                                 collection_path: Tuple[str, ...],
                                 data: object,
                                 *bonus_args) -> None:
        """
        Submit data for output, associated with the collection described by
        the collection path argument.

        This operation is only valid if a handler function has been registered
        with the collection in question. If so, this handler is invoked with
        the provided data as its first argument. Any further arguments after
        the data will be passed into the handler function in the same order
        by which they are passed into this method.

        Precondition:
            A handler has been registered with this collection.

        :param collection_path:
            A path to the collection in question through its ancestors
        :param data:
            Data to be output
        :param bonus_args:
            A series of any other arguments that will be passed into the
            handler function, in order of passing
        """
        collection = self._navigate_collection_path(collection_path)

        if COLLECTION_HANDLERS in collection:
            handler = collection[COLLECTION_HANDLERS]

            parent_output_center = globals.output
            subcollection_output_center = _output_controller_from_dict(collection)
            globals.output = subcollection_output_center

            handler(data, *bonus_args)

            globals.output = parent_output_center
        else:
            raise LookupError("No handler function loaded for collection"
                              "{}".format(collection_path))


def _output_controller_from_dict(basis: Dict) -> 'OutputController':
    """
    Return an output controller configured based on the dictionary basis,
    which is structured like the internal representation of a collection
    within an output controller.

    Can generate an output controller to handle a collection within another.

    :param basis:
        A dictionary specifying collection structure
    :return:
        An output controller containing the above collection hierarchy
    """
    controller = OutputController()
    path = []

    def _add_to_output_controller(collection: Dict) -> None:
        """
        Enter the contents of collection, which is either a collection
        or a whole hierarchy of collections, into the controller object
        in the outer scope.

        :param collection:
            A dictionary representation of an output collection
        """
        for k, v in collection.items():
            if isinstance(v, dict):
                # v is a subcollection.
                # Register k as the name of the collection, with the
                # appropriate handler function.
                if COLLECTION_HANDLERS in v:
                    controller.register_collection(k, tuple(path),
                                                   v[COLLECTION_HANDLERS])
                else:
                    controller.register_collection(k, tuple(path))

                # Add the collection's name to the path and recursively add
                # the collection's contents to the output controller.
                path.append(k)
                _add_to_output_controller(v)
                path.pop()
            else:
                # Simply register the handler function v with the output type.
                controller.enable_output_type(k, tuple(path), v)

    _add_to_output_controller(basis)
    return controller


# Standard collection names.
PRIMARY_OUTPUT = "Out"
DATASET_VARS = "DS_Vars"
IMAGES = "Img"

# Full paths to standard collections.
PRIMARY_OUTPUT_PATH = (PRIMARY_OUTPUT,)
DATASET_VARS_PATH = (PRIMARY_OUTPUT, DATASET_VARS)
IMAGES_PATH = (PRIMARY_OUTPUT, IMAGES)


def empty_output_config() -> 'OutputController':
    """
    Returns a OutputController instance with basic collection structure
    initialized, but without any output types or handlers added.

    The basic structure is as follows:
    A collection with a name given by the PRIMARY_OUTPUT constant contains
    any configuration for final model output. It contains two child
    collections, whose names are given by the constants DATASET_VARS and
    IMAGES.

    The DATASET_VARS collection contains configuration for which variables
    are included in the dataset file produced after the model run. The IMAGES
    collection determines which variables are rendered as image file maps.

    Further changes or additions may be made to this instance.

    :return:
        An empty output controller, with basic collection structure
    """
    controller = OutputController()

    # Create empty collections.
    controller.register_collection(PRIMARY_OUTPUT)
    controller.register_collection(IMAGES, PRIMARY_OUTPUT_PATH)
    controller.register_collection(DATASET_VARS, PRIMARY_OUTPUT_PATH)

    return controller


def default_output_config() -> 'OutputController':
    """
    Returns an OutputController instance with default settings.

    Default settings includes the basic collection structure as described
    under empty_output_config, and no other collections. The dataset is
    set to output all variables, while no images will be produced.
    No console prints are enabled. This is intended for deployment purposes.

    No other variables are enabled. Further changes may be made to this
    instance.

    :return:
        An output controller with default settings
    """
    controller = empty_output_config()

    # Set primary output handler function.
    # Placeholder is print until a proper output function is developed.
    controller.register_collection(PRIMARY_OUTPUT, handler=print)

    # Add output types to collections.
    for output_type in ReportDatatype:
        controller.enable_output_type(output_type, DATASET_VARS_PATH)

    return controller


def development_output_config() -> 'OutputController':
    """
    Returns an OutputController instance with settings for development.

    Development settings includes the basic collection structure as described
    under empty_output_config, and no other collections. The PRIMARY_OUTPUT
    collection and its subcollections have debug status reports enabled, and
    output temperature change as their only variable.

    No other variables are enabled. Further changes may be made to this
    instance.

    :return:
        An output controller with development settings
    """
    controller = empty_output_config()

    # Set primary output handler function.
    # Placeholder is print until a proper output function is developed.
    controller.register_collection(PRIMARY_OUTPUT, handler=print)

    # Add output types to collections.
    controller.enable_output_type(Debug.PRINT_NOTICES, PRIMARY_OUTPUT_PATH)
    controller.enable_output_type(ReportDatatype.REPORT_TEMP_CHANGE,
                                  DATASET_VARS_PATH)
    controller.enable_output_type(Debug.PRINT_NOTICES,
                                  DATASET_VARS_PATH)
    controller.enable_output_type(ReportDatatype.REPORT_TEMP_CHANGE,
                                  IMAGES_PATH)
    controller.enable_output_type(Debug.PRINT_NOTICES,
                                  IMAGES_PATH)

    return controller


# Keys into thread-specific variables dictionary
OUTPUT = "Out_Center"

# Dictionary of thread-specific variables, accessible at global scope.
# Set up initial state.
globals = local()
globals.output = default_output_config()


def global_output_center() -> 'OutputController':
    """
    Returns the active thread-specific output controller object.

    :return:
        The global output controller
    """
    return globals.output


def set_output_center(output_center: 'OutputController') -> None:
    """
    Replace the active thread-specific output controller with output_center.
    Other threads will not see the change.

    :param output_center:
        A new output center to be used by this thread
    """
    globals.output = output_center
