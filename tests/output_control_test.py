import unittest
from typing import Tuple, Union
from data.output_config import ReportDatatype, SpecialReportData,\
    AccuracyMetrics, Debug, OutputConfig, COLLECTION_SUBTYPES,\
    COLLECTION_HANDLERS, PRIMARY_OUTPUT_PATH, IMAGES_PATH, empty_output_config
from data.configuration import Config

# All classes of OutputConfig output types.
ENUM_TYPES = [ReportDatatype, SpecialReportData, AccuracyMetrics, Debug]

# A title for the process feeding the output controller.
TEST_NAME = "test_module_run"


def ignore_output(title: str,
                  data: object) -> None:
    """
    A function with no effect, with the right signature to act as an output
    type handler function. Effectively causes the output to be ignored.
    """
    pass


def ignore_collection_output(title: str,
                             config: Config,
                             data: object) -> None:
    """
    A function with no effect, with the right signature to act as a collection
    handler function. Effectively causes the output to be ignored.
    """
    pass


class OutputControlTest(unittest.TestCase):
    """
    A test class for OutputController. Uses spy functions to track invocations
    of output handlers, ensuring that the right calls are made to the right
    output types. Ensures collections are managed properly, and verifies
    collection output behaviour.
    """
    def __init__(self, *args, **kwargs):
        super(OutputControlTest, self).__init__(*args, **kwargs)

        # Initialize variables. Values do not matter, as they will be
        # overwritten by the setUp method.
        self.output_controller = empty_output_config(TEST_NAME)
        self.recent_output_type = None
        self.recent_data = None

        # Maps each output type to the number of times an output has been made
        # to that output type, including as an enabled type in a collection.
        self.updates = {}

    def setUp(self):
        """
        Reset the state of all instance variables before running an upcoming
        test. Namely, clears any registered output handlers and clears memory
        of any previous data for tracking output function calls.
        """
        self.output_controller = empty_output_config(TEST_NAME)
        self.recent_output_type = None
        self.recent_data = None
        self.updates = {}

        # Reset update counts to each output type.
        for enum_type in ENUM_TYPES:
            for enum in enum_type:
                self.updates[enum] = 0

    def release_mock_output(self: 'OutputControlTest',
                            data_type: Union['OutputConfig', Tuple[str, ...]],
                            data: object) -> None:
        """
        Submits the data to the output controller, under the specified output
        type or collection. Also records the data type, which can be used
        later to identify output types have been accessed in order to add
        them to the updates counter dictionary.

        :param data_type:
            The output type or collection path associated with the data
        :param data:
            Data for output
        """
        # Record data type for access within the spy methods.
        self.recent_output_type = data_type

        # Now call the output controller's output submission methods.
        if isinstance(data_type, tuple):
            self.output_controller.submit_collection_output(data_type, data)
        elif isinstance(data_type, OutputConfig):
            self.output_controller.submit_output(data_type, data)

    def receive_mock_output(self: 'OutputControlTest',
                            title: str,
                            data: object) -> None:
        """
        Registers an output event by incrementing the update counter within
        the update counter dictionary for the most recently accessed output
        type. Also records the data that was passed to this update.

        :param title:
            The name of the testing session
        :param data:
            Data intended for output
        """
        self.assertEqual(TEST_NAME, title)
        self.updates[self.recent_output_type] += 1
        self.recent_data = data

    def receive_mock_collection_output(self: 'OutputControlTest',
                                       title: str,
                                       config: Config,
                                       data: object) -> None:
        """
        Registers an output event by incrementing the update counter in the
        update counter dictionary for every output type enabled within this
        collection. Also registers this same information for all
        subcollections. Records the data that was passed to this update.

        :param title:
            The name of the testing session
        :param config:
            A dictionary representing the structure of the collection this
            output was passed to
        :param data:
            Data intended for output
        """
        self.assertEqual(TEST_NAME, title)

        for k, v in config.items():
            if k == COLLECTION_SUBTYPES:
                # Record updates for all enabled output types.
                for subtype in v:
                    self.updates[subtype] += 1

            elif k != COLLECTION_HANDLERS:
                # v is a subcollection: recursively update update counts for
                # all its enabled output types.
                self.receive_mock_collection_output(title, v, data)
        self.recent_data = data

    def test_unregistered_type_is_ignored(self):
        """
        Test that output is ignored for output types that are not registered.
        """
        self.release_mock_output(ReportDatatype.REPORT_TEMP_CHANGE,
                                 [[[1]]])
        self.release_mock_output(SpecialReportData.
                                 REPORT_DELTA_TEMP_PLUS_DEVIATIONS,
                                 [[1]])
        self.release_mock_output(AccuracyMetrics.TEMP_DELTA_STD_DEVIATION,
                                 [[1]])
        self.release_mock_output(Debug.PRINT_NOTICES, [1])

        self.assertIsNone(self.recent_data)
        self.assertEqual(0, self.updates[ReportDatatype.
                         REPORT_TEMP_CHANGE])
        self.assertEqual(0, self.updates[SpecialReportData.
                         REPORT_DELTA_TEMP_PLUS_DEVIATIONS])
        self.assertEqual(0, self.updates[AccuracyMetrics.
                         TEMP_DELTA_STD_DEVIATION])
        self.assertEqual(0, self.updates[Debug.PRINT_NOTICES])

    def test_registered_type_is_accepted(self):
        """
        Test that output is accepted for output types that are registered.
        """
        # Enable a couple of output types.
        self.output_controller.enable_output_type(Debug.PRINT_NOTICES,
                                                  self.receive_mock_output)
        self.output_controller.enable_output_type(AccuracyMetrics.
                                                  TEMP_DELTA_STD_DEVIATION,
                                                  self.receive_mock_output)

        # Submit output to only one of the enabled output types.
        self.release_mock_output(Debug.PRINT_NOTICES, [1])

        # Check that only one of the two output types recorded updates.
        self.assertEqual([1], self.recent_data)
        self.assertEqual(1, self.updates[Debug.PRINT_NOTICES])

        self.assertEqual(0, self.updates[AccuracyMetrics.
                         TEMP_DELTA_STD_DEVIATION])
        self.assertEqual(0, self.updates[Debug.GRID_CELL_DELTA_TEMP])

    def test_change_type_handler(self):
        """
        Test that handler functions can be modified by registering an output
        type again. One of these handlers will increment the output type's
        update count, and the other will not.
        """
        # Record an update to one of the output types.
        self.output_controller.enable_output_type(Debug.PRINT_NOTICES,
                                                  self.receive_mock_output)
        self.release_mock_output(Debug.PRINT_NOTICES, 5)

        self.assertEqual(5, self.recent_data)
        self.assertEqual(1, self.updates[Debug.PRINT_NOTICES])

        # Swap out the output handler to one that will take no actions.
        self.output_controller.enable_output_type(Debug.PRINT_NOTICES,
                                                  ignore_output)
        self.release_mock_output(Debug.PRINT_NOTICES, 6)

        # Confirm that no updates were recorded, and so the original handler
        # was not invoked again.
        self.assertEqual(5, self.recent_data)
        self.assertEqual(1, self.updates[Debug.PRINT_NOTICES])

    def test_unregistered_collection_output_error(self):
        """
        Test that an error is raised when trying to submit output to a
        collection that does not have a handler. Ensure that no updates
        are recorded, indicating that no spy handler method was invoked.
        """
        with self.assertRaises(LookupError):
            self.release_mock_output(PRIMARY_OUTPUT_PATH, [1])

        self.assertIsNone(self.recent_data)
        for update_count in self.updates.values():
            self.assertEqual(0, update_count)

    def test_top_level_collection(self):
        """
        Test that submitting data to a collection allows the handler function
        to identify the enabled output types within that collection, where the
        collection has no parent collection. Does not test the application to
        subcollections.
        """
        active_types = [ReportDatatype.REPORT_TEMP_CHANGE,
                        ReportDatatype.REPORT_TEMP,
                        ReportDatatype.REPORT_HUMIDITY]

        # Load the top-level collection with several output types.
        self.output_controller.\
            register_collection(PRIMARY_OUTPUT_PATH[0],
                                handler=self.receive_mock_collection_output)
        for active_type in active_types:
            self.output_controller.enable_collection_type(PRIMARY_OUTPUT_PATH,
                                                          active_type)

        self.release_mock_output(PRIMARY_OUTPUT_PATH, [10])

        # Demonstrate that all of the enabled types were able to be updated
        # by the spy handler method.
        self.assertEqual([10], self.recent_data)
        for active_type in active_types:
            self.assertEqual(1, self.updates[active_type])

        # Show that an output type that was not enabled in the collection
        # is unchanged.
        self.assertEqual(0, self.updates[ReportDatatype.REPORT_ALBEDO])

    def test_change_collection_handler(self):
        """
        Test that handler functions can be modified by registering a
        collection type again. One of these handlers will increment the
        output type's update count, and the other will not.
        """
        active_types = [ReportDatatype.REPORT_TEMP_CHANGE,
                        ReportDatatype.REPORT_TEMP,
                        ReportDatatype.REPORT_HUMIDITY]

        # Load the collection with several enabled output types.
        self.output_controller.\
            register_collection(PRIMARY_OUTPUT_PATH[0],
                                handler=self.receive_mock_collection_output)
        for active_type in active_types:
            self.output_controller.enable_collection_type(PRIMARY_OUTPUT_PATH,
                                                          active_type)

        self.release_mock_output(PRIMARY_OUTPUT_PATH, [10])

        # Swap out the collection's handler and submit another, different set
        # of output.
        self.output_controller.\
            register_collection(PRIMARY_OUTPUT_PATH[0],
                                handler=ignore_collection_output)
        self.release_mock_output(PRIMARY_OUTPUT_PATH, [12])

        # Confirm that no updates were recorded, and so the original handler
        # was not invoked again.
        self.assertEqual([10], self.recent_data)
        for active_type in active_types:
            self.assertEqual(1, self.updates[active_type])

    def test_empty_collection_is_ignored(self):
        """
        Test that no updates are recorded when output is submitted to a
        collection that has no enabled output types.
        """
        self.output_controller.\
            register_collection(PRIMARY_OUTPUT_PATH[0],
                                handler=self.receive_mock_collection_output)
        self.output_controller.submit_collection_output(PRIMARY_OUTPUT_PATH,
                                                        [15])

        # The piece of data that was submitted for output (the list) will have
        # been received and recorded, but no output types will have been
        # enabled, so none of them will be updated.
        self.assertEqual([15], self.recent_data)
        for output_count in self.updates.values():
            self.assertEqual(0, output_count)

    def test_submit_to_subcategory(self):
        """
        Test that submitting data to a collection does not cause updates to
        enabled output types in its parent collection.
        """
        # Output types that are enabled in the parent collection.
        parent_types = [Debug.PRINT_NOTICES]

        # Output types that are enabled in the subcollection.
        active_types = [ReportDatatype.REPORT_TEMP_CHANGE,
                        ReportDatatype.REPORT_TEMP,
                        ReportDatatype.REPORT_HUMIDITY]

        # Enable output types into the collections as described above.
        # Make sure both collections are using the spy handler method.
        self.output_controller.\
            register_collection(PRIMARY_OUTPUT_PATH[0],
                                handler=self.receive_mock_collection_output)
        self.output_controller.\
            register_collection(IMAGES_PATH[1],
                                supercollections=PRIMARY_OUTPUT_PATH,
                                handler=self.receive_mock_collection_output)
        for active_type in parent_types:
            self.output_controller.enable_collection_type(PRIMARY_OUTPUT_PATH,
                                                          active_type)
        for active_type in active_types:
            self.output_controller.enable_collection_type(IMAGES_PATH,
                                                          active_type)

        # Submit output to the subcollection, not the parent collection.
        self.release_mock_output(IMAGES_PATH, [25])

        # Check that only the child collection had updates recorded.
        self.assertEqual([25], self.recent_data)
        for active_type in active_types:
            self.assertEqual(1, self.updates[active_type])
        for active_type in parent_types:
            self.assertEqual(0, self.updates[active_type])

    def test_parent_receives_subcategory(self):
        """
        Test that submitting data to a collection allows the handler function
        to identify the enabled output types within subcollections.
        """
        # Output types that are enabled in the parent collection.
        parent_types = [Debug.PRINT_NOTICES]

        # Output types that are enabled in the subcollection.
        active_types = [ReportDatatype.REPORT_TEMP,
                        ReportDatatype.REPORT_HUMIDITY]

        # Output types that are enabled in both the subcollection and the
        # parent collection. Must occur in neither of the above lists.
        doubled_types = [ReportDatatype.REPORT_TEMP_CHANGE]

        # Enable output types into the collections as described above.
        self.output_controller.\
            register_collection(PRIMARY_OUTPUT_PATH[0],
                                handler=self.receive_mock_collection_output)
        # The subcollection has no handler function.
        self.output_controller.\
            register_collection(IMAGES_PATH[1],
                                supercollections=PRIMARY_OUTPUT_PATH)

        for active_type in parent_types:
            self.output_controller.enable_collection_type(PRIMARY_OUTPUT_PATH,
                                                          active_type)
        for active_type in active_types:
            self.output_controller.enable_collection_type(IMAGES_PATH,
                                                          active_type)
        for active_type in doubled_types:
            self.output_controller.enable_collection_type(PRIMARY_OUTPUT_PATH,
                                                          active_type)
            self.output_controller.enable_collection_type(IMAGES_PATH,
                                                          active_type)

        self.release_mock_output(PRIMARY_OUTPUT_PATH, [50])

        # Show that all enabled types saw updates, and that the output types
        # in both collections were updated once for each.
        self.assertEqual([50], self.recent_data)
        for active_type in active_types:
            self.assertEqual(1, self.updates[active_type])
        for active_type in parent_types:
            self.assertEqual(1, self.updates[active_type])
        for active_type in doubled_types:
            self.assertEqual(2, self.updates[active_type])
