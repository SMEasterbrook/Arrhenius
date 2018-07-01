import unittest
import numpy as np

from os import path, remove
from pathlib import Path
from shutil import rmtree
from netCDF4 import Dataset

from data.reader import NetCDFReader, TimeboundNetCDFReader
from data.writer import NetCDFWriter

# Directory for test datasets for file reading.
READ_INPUT_DIR = "read_in"

# Frequently used variable names.
READ_VAR_NAME = "data"
UNTIMED_VAR_NAME = "untimed"


def create_basic_timeless_dataset(name: str,
                                  data: np.ndarray) -> None:
    """
    Write a NetCDF file to disk, with up to three dimensions titled 'layer',
    'latitude', and 'longitude'. Number of dimensions is based on the data
    array passed in. Writes the data variable to the dataset, under the
    variable with the name given by READ_VAR_NAME. Also created dimension
    variables with dummy data.

    :param name:
        The name of the NetCDF file, including file extension
    :param data:
        Data to be written to the dataset's only variable
    """
    rel_path = path.join(READ_INPUT_DIR, name)
    # Create an empty dataset on disk.
    dataset = Dataset(rel_path, mode="w")

    # Produce the last few dimensions in the list below, equal to the number
    # of dimensions to the input data.
    dims = ['layer', 'latitude', 'longitude'][3-data.ndim:]
    # Keep track of the ith nested layer in the array, to know its length
    # when determining the length of each dimension.
    slice = data
    for i in range(len(dims)):
        dataset.createDimension(dims[i], data.shape[i])

        # Create dimension variable and write dummy data.
        var = dataset.createVariable(dims[i], np.int32, (dims[i],))
        var[:] = range(len(slice))
        slice = slice[0]

    # Write the main data variable, using all available dimensions.
    var = dataset.createVariable(READ_VAR_NAME, np.int32, dims)
    var[:] = data
    dataset.close()


def create_basic_timebound_dataset(name: str,
                                   data: np.ndarray) -> None:
    """
    Write a NetCDF file to disk, with up to three dimensions titled 'layer',
    'latitude', and 'longitude'. An additional dimension, 'time', is added
    as the highest dimension. Total number of dimensions is based on the data
    array passed in. Writes the data variable to the dataset, under the
    variable with the name given by READ_VAR_NAME. Contains an additional
    variable under the name of UNTIMED_VAR_NAME, which is bound to the
    latitude and longitude dimensions only. Also created dimension variables
    with dummy data.

    :param name:
        The name of the NetCDF file, including file extension
    :param data:
        Data to be written to the dataset's time-dependent variable
    """
    rel_path = path.join(READ_INPUT_DIR, name)
    dataset = Dataset(rel_path, mode="w")

    # Produce the last few dimensions in the list below, equal to the number
    # of dimensions to the input data minus the one reserved for the time
    # dimension.
    dims = ['layer', 'latitude', 'longitude'][3 - data.ndim + 1:]
    dims.insert(0, 'time')

    # Keep track of the ith nested layer in the array, to know its length
    # when determining the length of each dimension.
    slice = data
    for i in range(len(dims)):
        dataset.createDimension(dims[i], data.shape[i])

        # Create dimension variable and write dummy data.
        var = dataset.createVariable(dims[i], np.int32, (dims[i],))
        var[:] = range(len(slice))
        slice = slice[0]

    # Write the dataset's only time-dependent variable.
    var = dataset.createVariable(READ_VAR_NAME, np.int32, dims)
    var[:] = data

    # Write an additional variable, which is time-independent.
    lat_len = len(dataset.variables['latitude'])
    lon_len = len(dataset.variables['longitude'])
    timeless_var = dataset.createVariable(UNTIMED_VAR_NAME, np.int32,
                                          ['latitude', 'longitude'])
    # Give the variable dummy data which is not symmetric across either
    # dimension.
    timeless_var[:] = [range(i, lat_len + i) for i in range(lon_len)]
    dataset.close()


class BasicTimeboundReader(TimeboundNetCDFReader):
    """
    A simple extension of the TimeboundNetCDFReader class, giving an
    implementation for the one abstract function in that class:
    collect_timed_data.
    """

    def collect_timed_data(self: 'TimeboundNetCDFReader',
                           datapoint: str,
                           year: int) -> np.ndarray:
        """
        Returns the data under the specified variable, taken from the selected
        year. In this case, the year is taken to be a direct index into the
        data returned by the variable name.

        :param datapoint:
            The name of the variable requested from the dataset
        :param year:
            The year from which to collect data
        :return:
            The requested data, limited to that from the selected year
        """
        self._open_dataset()

        data = self._dataset()
        var = data.variables[datapoint]
        # Assume the year can be used directly as an index into the data.
        return var[year, ...]

# File names for test dataset files.
DATASET1_NAME = "one_unit.nc"
DATASET5_NAME = "five_bands.nc"
DATASET6_NAME = "two_by_three.nc"
DATASET12_NAME = "four_by_three.nc"

# Relative paths to test dataset files, based on file names.
DATASET1 = path.join(READ_INPUT_DIR, DATASET1_NAME)
DATASET5 = path.join(READ_INPUT_DIR, DATASET5_NAME)
DATASET6 = path.join(READ_INPUT_DIR, DATASET6_NAME)
DATASET12 = path.join(READ_INPUT_DIR, DATASET12_NAME)


class TimelessNetCDFInputTest(unittest.TestCase):
    """
    A test class for NetCDFReader. Ensures that time-independent data can be
    read correctly from existing NetCDF datasets, and multidimensional data
    is processed and returned correctly.
    """

    @classmethod
    def setUpClass(cls):
        """
        Prepare for a run of file reading tests by creating a series of
        mock testing datasets for reading, located in a temporary test
        directory.
        """
        local_path = Path(READ_INPUT_DIR)
        local_path.mkdir(exist_ok=True)

        create_basic_timeless_dataset(DATASET1_NAME, np.array([[1]]))
        create_basic_timeless_dataset(DATASET5_NAME, np.array([[1], [2], [3], [4], [5]]))
        create_basic_timeless_dataset(DATASET6_NAME, np.array([[1, 2], [3, 4], [5, 6]]))
        create_basic_timeless_dataset(DATASET12_NAME, np.array([[[1, 2], [3, 4]],
                                                               [[5, 6], [7, 8]],
                                                               [[9, 10], [11, 12]]]))

    @classmethod
    def tearDownClass(cls):
        """
        Remove the temporary input file directory, deleting any of the
        test files inside.
        """
        rmtree(READ_INPUT_DIR)

    def test_read_single(self):
        """
        Test that a very simple dataset can be read successfully, opening the
        dataset and returning the only datapoint inside.
        """
        reader = NetCDFReader(DATASET1)
        data = reader.collect_untimed_data(READ_VAR_NAME)
        reader.close()

        self.assertEqual(data.shape, (1, 1))
        self.assertEqual(data[0, 0], 1)

    def test_latitude(self):
        """
        Test that latitude data is stored correctly, and its data is
        retrieved by the latitude method without interference by any other
        dimensions.
        """
        # Test with a single datapoint.
        reader1 = NetCDFReader(DATASET1)
        lat1 = reader1.latitude()
        reader1.close()
        self.assertEqual(1, len(lat1))
        self.assertEqual(0, lat1[0])

        # Test with multiple points in latitude, but only one in longitude.
        reader5 = NetCDFReader(DATASET5)
        lat5 = reader5.latitude()
        reader5.close()
        self.assertEqual(5, len(lat5))
        self.assertEqual(0, lat5[0])
        self.assertEqual(1, lat5[1])
        self.assertEqual(2, lat5[2])
        self.assertEqual(3, lat5[3])
        self.assertEqual(4, lat5[4])

        # Test with multiple points in both latitude and longitude.
        reader6 = NetCDFReader(DATASET6)
        lat6 = reader6.latitude()
        reader6.close()
        self.assertEqual(3, len(lat6))
        self.assertEqual(0, lat6[0])
        self.assertEqual(1, lat6[1])
        self.assertEqual(2, lat6[2])

        # Test with three dimensions, including multiple points in latitude
        # and longitude.
        reader12 = NetCDFReader(DATASET12)
        lat12 = reader12.latitude()
        reader12.close()
        self.assertEqual(2, len(lat12))
        self.assertEqual(0, lat12[0])
        self.assertEqual(1, lat12[1])

    def test_longitude(self):
        """
        Test that longitude data is stored correctly, and its data is
        retrieved by the longitude method without interference by any other
        dimensions.
        """
        # Test with a single point in longitude and latitude.
        reader1 = NetCDFReader(DATASET1)
        lon1 = reader1.longitude()
        reader1.close()
        self.assertEqual(1, len(lon1))
        self.assertEqual(0, lon1[0])

        # Test with a single point in longitude, but more in latitude.
        reader5 = NetCDFReader(DATASET5)
        lon5 = reader5.longitude()
        reader5.close()
        self.assertEqual(1, len(lon5))
        self.assertEqual(0, lon5[0])

        # Test with multiple points in both longitude and latitude.
        reader6 = NetCDFReader(DATASET6)
        lon6 = reader6.longitude()
        reader6.close()
        self.assertEqual(2, len(lon6))
        self.assertEqual(0, lon6[0])
        self.assertEqual(1, lon6[1])

        # Test with three dimensions, including multiple points in longitude
        # and latitude.
        reader12 = NetCDFReader(DATASET12)
        lon12 = reader12.longitude()
        reader12.close()
        self.assertEqual(2, len(lon12))
        self.assertEqual(0, lon12[0])
        self.assertEqual(1, lon12[1])

    def test_data_1d(self):
        """
        Test that one-dimensional variable data is successfully written to
        file and can be retrieved on a later read. Ensures correct ordering
        of data in the file.
        """
        # Simple test with only one datapoint.
        reader1 = NetCDFReader(DATASET1)
        data1 = reader1.collect_untimed_data(READ_VAR_NAME)
        reader1.close()

        self.assertEqual(data1.shape, (1, 1))
        self.assertEqual(data1[0, 0], 1)

        # Test with multiple values in one dimension.
        reader5 = NetCDFReader(DATASET5)
        data5 = reader5.collect_untimed_data(READ_VAR_NAME)
        reader5.close()

        self.assertEqual(data5.shape, (5, 1))
        # Check a few values to demonstrate that the return value lines up
        # with expected value.
        self.assertEqual(data5[0, 0], 1)
        self.assertEqual(data5[1, 0], 2)
        self.assertEqual(data5[2, 0], 3)
        self.assertEqual(data5[3, 0], 4)
        self.assertEqual(data5[4, 0], 5)

    def test_data_2d(self):
        """
        Test that three-dimensional (latitude/longitude) data is handled
        properly, and can be successfully retrieved in the right order
        on a later read.
        """
        reader6 = NetCDFReader(DATASET6)
        data6 = reader6.collect_untimed_data(READ_VAR_NAME)
        reader6.close()

        self.assertEqual(data6.shape, (3, 2))
        # Check a few values to demonstrate that the return value lines up
        # with expected value.
        self.assertEqual(data6[0, 0], 1)
        self.assertEqual(data6[0, 1], 2)
        self.assertEqual(data6[1, 0], 3)
        self.assertEqual(data6[1, 1], 4)
        self.assertEqual(data6[2, 0], 5)
        self.assertEqual(data6[2, 1], 6)

    def test_data_3d(self):
        """
        Test that three-dimensional (level/latitude/longitude) data is
        handled properly, and can be successfully retrieved in the right
        order on a later read.
        """
        reader12 = NetCDFReader(DATASET12)
        data12 = reader12.collect_untimed_data(READ_VAR_NAME)
        reader12.close()

        self.assertEqual(data12.shape, (3, 2, 2))
        # Check a few values to demonstrate that the return value lines up
        # with expected value.
        self.assertEqual(data12[0, 0, 0], 1)
        self.assertEqual(data12[0, 0, 1], 2)
        self.assertEqual(data12[0, 1, 0], 3)
        self.assertEqual(data12[1, 0, 0], 5)
        self.assertEqual(data12[1, 1, 0], 7)


# File names for time-dependent test dataset files.
TIME_DATASET1_NAME = "one_unit_timed.nc"
TIME_DATASET5_NAME = "five_seasons.nc"
TIME_DATASET6_NAME = "two_by_three_timed.nc"
TIME_DATASET12_NAME = "four_by_three_timed.nc"
TIME_DATASET48_NAME = "four_dims.nc"

# Relative paths to time-dependent test datasets, based on the file names.
TIME_DATASET1 = path.join(READ_INPUT_DIR, TIME_DATASET1_NAME)
TIME_DATASET5 = path.join(READ_INPUT_DIR, TIME_DATASET5_NAME)
TIME_DATASET6 = path.join(READ_INPUT_DIR, TIME_DATASET6_NAME)
TIME_DATASET12 = path.join(READ_INPUT_DIR, TIME_DATASET12_NAME)
TIME_DATASET48 = path.join(READ_INPUT_DIR, TIME_DATASET48_NAME)


class TimeboundNetCDFInputTest(unittest.TestCase):
    """
    A test class for TimeboundNetCDFReader. Ensures that both time-dependent
    and time-independent data can be read correctly, no matter the number of
    dimensions involved.
    """
    @classmethod
    def setUpClass(cls):
        """
        Prepare for a run of file reading tests by creating a series of
        mock testing datasets for reading, located in a temporary test
        directory.
        """
        local_path = Path(READ_INPUT_DIR)
        local_path.mkdir(exist_ok=True)

        # Mock datasets for test cases: cover single-datapoint files, two-
        # dimensional and three-dimensional data plus a dimension for time.
        create_basic_timebound_dataset(TIME_DATASET1_NAME, np.array([[[1]]]))
        create_basic_timebound_dataset(TIME_DATASET5_NAME, np.array([[[1]], [[2]], [[3]], [[4]], [[5]]]))
        create_basic_timebound_dataset(TIME_DATASET6_NAME, np.array([[[1, 2]], [[3, 4]], [[5, 6]]]))
        create_basic_timebound_dataset(TIME_DATASET12_NAME, np.array([[[1, 2], [3, 4]],
                                                                      [[5, 6], [7, 8]],
                                                                      [[9, 10], [11, 12]]]))
        create_basic_timebound_dataset(TIME_DATASET48_NAME, np.array([[[[1, 2], [3, 4], [5, 6]],
                                                                     [[7, 8], [9, 10], [11, 12]],
                                                                     [[13, 14], [15, 16], [17, 18]],
                                                                     [[19, 20], [21, 22], [23, 24]]],
                                                                    [[[25, 26], [27, 28], [29, 30]],
                                                                     [[31, 32], [33, 34], [35, 36]],
                                                                     [[37, 38], [39, 40], [41, 42]],
                                                                     [[43, 44], [45, 46], [47, 48]]]]))

    @classmethod
    def tearDownClass(cls):
        """
        Remove the temporary input file directory, deleting any of the
        test files inside.
        """
        rmtree(READ_INPUT_DIR)

    def test_read_single(self):
        """
        Test that a very simple dataset can be read successfully, opening the
        dataset and returning the only datapoint inside.
        """
        reader = TimeboundNetCDFReader(TIME_DATASET1)
        data = reader.collect_untimed_data(UNTIMED_VAR_NAME)
        reader.close()

        self.assertEqual(data.shape, (1, 1))
        self.assertEqual(data[0, 0], 0)

    def test_latitude(self):
        """
        Test that the latitude variable can be successfully returned,
        irrespective of any other dimensions on top of it. Checks that
        the values of the latitude variable can be successfully read.
        """
        # Test on single-datapoint dataset.
        reader1 = TimeboundNetCDFReader(TIME_DATASET1)
        lat1 = reader1.latitude()
        reader1.close()
        self.assertEqual(1, len(lat1))
        self.assertEqual(0, lat1[0])

        # Test on a dataset with only a time dimension, and only one unit of
        # latitude in length.
        reader5 = TimeboundNetCDFReader(TIME_DATASET5)
        lat5 = reader5.latitude()
        reader5.close()
        self.assertEqual(1, len(lat5))
        self.assertEqual(0, lat5[0])

        # Test on a dataset with two dimensions plus a time dimension, with
        # multiple units of latitude length.
        reader12 = TimeboundNetCDFReader(TIME_DATASET12)
        lat12 = reader12.latitude()
        reader12.close()
        self.assertEqual(2, len(lat12))
        self.assertEqual(0, lat12[0])
        self.assertEqual(1, lat12[1])

        # Test on a dataset with more dimensions that just latitude,
        # longitude, and time.
        reader48 = TimeboundNetCDFReader(TIME_DATASET48)
        lat48 = reader48.latitude()
        reader48.close()
        self.assertEqual(3, len(lat48))
        self.assertEqual(0, lat48[0])
        self.assertEqual(1, lat48[1])
        self.assertEqual(2, lat48[2])

    def test_longitude(self):
        """
        Test that the latitude variable can be successfully returned,
        irrespective of any other dimensions on top of it. Checks that
        the values of the latitude variable can be successfully read.
        """
        # Test on a dataset with only a single datapoint.
        reader1 = NetCDFReader(TIME_DATASET1)
        lon1 = reader1.longitude()
        reader1.close()
        self.assertEqual(1, len(lon1))
        self.assertEqual(0, lon1[0])

        # Test on a dataset with only a time dimension, and only one unit of
        # longitude in length.
        reader5 = NetCDFReader(TIME_DATASET5)
        lon5 = reader5.longitude()
        reader5.close()
        self.assertEqual(1, len(lon5))
        self.assertEqual(0, lon5[0])

        # Test on a dataset with two dimensions plus a time dimension, with
        # multiple units of longitude length.
        reader12 = NetCDFReader(TIME_DATASET12)
        lon12 = reader12.longitude()
        reader12.close()
        self.assertEqual(2, len(lon12))
        self.assertEqual(0, lon12[0])
        self.assertEqual(1, lon12[1])

        # Test on a dataset with more dimensions that just latitude,
        # longitude, and time.
        reader48 = NetCDFReader(TIME_DATASET48)
        lon48 = reader48.longitude()
        reader48.close()
        self.assertEqual(2, len(lon48))
        self.assertEqual(0, lon48[0])
        self.assertEqual(1, lon48[1])

    def test_untimed_data_0d(self):
        """
        Test that time independent data can be retrieved successfully, as in a
        normal time independent reader instance. Special case where latitude
        and longitude lengths are both 1, giving only a single entry for
        time independent data.
        """
        reader5 = TimeboundNetCDFReader(TIME_DATASET5)
        data5 = reader5.collect_untimed_data(UNTIMED_VAR_NAME)
        reader5.close()

        self.assertEqual(data5.shape, (1, 1))
        # Check that various points in the data match the values expected
        # at those points, based on the arrays that defined the data.
        self.assertEqual(0, data5[0, 0])

    def test_untimed_data_2d(self):
        """
        Test that time independent data is returned correctly with dimensions
        of length greater than 1, and respects the dimensions on which it was
        built by being returned in the correct order.
        """
        reader12 = NetCDFReader(TIME_DATASET12)
        data12 = reader12.collect_untimed_data(READ_VAR_NAME)
        reader12.close()

        self.assertEqual(data12.shape, (3, 2, 2))
        # Check that various points in the data match the values expected
        # at those points, based on the arrays that defined the data.
        self.assertEqual(data12[0, 0, 0], 1)
        self.assertEqual(data12[0, 0, 1], 2)
        self.assertEqual(data12[1, 1, 0], 7)
        self.assertEqual(data12[1, 1, 1], 8)
        self.assertEqual(data12[2, 0, 1], 10)
        self.assertEqual(data12[2, 1, 0], 11)

    def test_timed_data_1d(self):
        """
        Test that time-dependent data is returned properly, where each time
        unit only contain a single datapoint. Ensures that different time
        queries produce different results.
        """
        reader5 = BasicTimeboundReader(TIME_DATASET5)
        data5_ind4 = reader5.collect_timed_data(READ_VAR_NAME, 4)
        data5_ind1 = reader5.collect_timed_data(READ_VAR_NAME, 1)
        reader5.close()

        self.assertEqual(data5_ind4.shape, (1, 1))
        self.assertEqual(data5_ind4[0, 0], 5)

        self.assertEqual(data5_ind1.shape, (1, 1))
        self.assertEqual(data5_ind1[0, 0], 2)

    def test_timed_data_2d(self):
        """
        Test that time-dependent data is returned properly, where each time
        unit gives a two-dimensional shape. Ensure the shape of the data is
        correct according to what was originally written.
        """
        # Test where one of the two dimensions has length 1.
        reader6 = BasicTimeboundReader(TIME_DATASET6)
        data6 = reader6.collect_timed_data(READ_VAR_NAME, 2)
        reader6.close()

        self.assertEqual((1, 2), data6.shape)
        self.assertEqual(5, data6[0][0])
        self.assertEqual(6, data6[0][1])

        # Test where both dimensions have length greater than 1.
        reader12 = BasicTimeboundReader(TIME_DATASET12)
        data12 = reader12.collect_timed_data(READ_VAR_NAME, 0)
        reader12.close()

        self.assertEqual((2, 2), data12.shape)
        # Check that various points in the data match the values expected
        # at those points, based on the arrays that defined the data.
        self.assertEqual(1, data12[0][0])
        self.assertEqual(2, data12[0][1])
        self.assertEqual(3, data12[1][0])
        self.assertEqual(4, data12[1][1])

    def test_timed_data_3d(self):
        """
        Test that time-dependent data is returned correctly when there are
        more dimensions that just latitude and longitude. Assumes that the
        top-level dimension is time.
        """
        reader48 = BasicTimeboundReader(TIME_DATASET48)
        data48 = reader48.collect_timed_data(READ_VAR_NAME, 1)
        reader48.close()

        self.assertEqual((4, 3, 2), data48.shape)

        # Check that various points in the data match the values expected
        # at those points, based on the arrays that defined the data.
        self.assertEqual(25, data48[0][0][0])
        self.assertEqual(26, data48[0][0][1])
        self.assertEqual(28, data48[0][1][1])
        self.assertEqual(29, data48[0][2][0])
        self.assertEqual(32, data48[1][0][1])
        self.assertEqual(33, data48[1][1][0])
        self.assertEqual(42, data48[2][2][1])
        self.assertEqual(45, data48[3][1][0])


# Directory to which to write datasets for testing.
WRITE_OUTPUT_DIR = "write_out"


class NetCDFWriterTest(unittest.TestCase):
    """
    A test class for NetCDFWriter. Ensures that files are written to the
    correct locations, that invariants hold on writing data, and that
    the data can be read back successfully afterward.
    """

    @classmethod
    def setUpClass(cls):
        """
        Create a temporary directory to store output files for testing.
        """
        out_path = Path(WRITE_OUTPUT_DIR)
        out_path.mkdir(exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        """
        Remove the temporary testing directory, and any test datasets inside.
        """
        rmtree(WRITE_OUTPUT_DIR)

    def test_no_data(self):
        """
        Test that an empty NetCDF dataset can be written to a directory,
        without any dimensions, variables, attributes, or data.
        """
        writer = NetCDFWriter()

        filepath = path.join(WRITE_OUTPUT_DIR, "empty.nc")
        writer.write(filepath)

    def test_data_requires_variable(self):
        """
        Test that an error is raised when data is submitted to a variable
        that does not exist.
        """
        # Test with no variables.
        writer = NetCDFWriter()
        with self.assertRaises(KeyError):
            writer.data("dummy", np.array([1]))

        # Test with no variables but a dimension of the same name.
        writer.dimension("dummy", np.int32, 1)
        with self.assertRaises(KeyError):
            writer.data("dummy", np.array([1]))

        # Test with a variable of a different name.
        writer.variable("fake", np.int32, ["dummy"])
        with self.assertRaises(KeyError):
            writer.data("dummy", np.array([1]))

        # Test that no errors are raised when a correct variable exists.
        writer.variable("dummy", np.int32, ["dummy"])
        writer.data("dummy", np.array([1]))

    def test_variable_requires_dimension(self):
        """
        Test that an error is raised when a variable is created that refers
        to a dimension that does not exist.
        """
        # Test with an empty dataset.
        writer = NetCDFWriter()
        with self.assertRaises(ValueError):
            writer.variable("dummy", np.int32, ["dummy"])

        # Test with a dimension of a different name.
        writer.dimension("fake", np.int32, 5)
        with self.assertRaises(ValueError):
            writer.variable("dummy", np.int32, ["dummy"])

        # Test that no errors are raised when a correct dimension exists.
        writer.dimension("dummy", np.int32, 4)
        writer.variable("dummy", np.int32, ["dummy"])

    def test_variable_attribute_requires_variable(self):
        """
        Test that an error is raised when an attribute is given to a variable
        that does not exist.
        """
        # Test on an empty dataset.
        writer = NetCDFWriter()
        with self.assertRaises(ValueError):
            writer.variable_attribute("dummy", "description",
                                      "A dummy variable")

        # Test with one dimension of the same name.
        writer.dimension("dummy", np.int32, 1)
        with self.assertRaises(ValueError):
            writer.variable_attribute("dummy", "description",
                                      "A dummy variable")

        # Test with a variable with a different name.
        writer.variable("fake", np.int32, ["dummy"])
        with self.assertRaises(ValueError):
            writer.variable_attribute("dummy", "description",
                                      "A dummy variable")

        # Test that no errors are raised when a correct variable exists.
        writer.variable("dummy", np.int32, ["dummy"])
        writer.variable_attribute("dummy", "description", "A dummy variable")

    def test_produces_file(self):
        """
        Test that writing a dataset produces a new file in the right location.
        """
        writer = NetCDFWriter()

        filepath = path.join(WRITE_OUTPUT_DIR, "single_point.nc")
        # Delete any preexisting file of the same name.
        try:
            remove(filepath)
        except OSError:
            pass

        writer.write(filepath)
        self.assertTrue(path.isfile(filepath))

    def test_global_attributes(self):
        """
        Test that global dataset attributes can be produced, and successfully
        read back from another read of the file.
        """
        writer = NetCDFWriter()
        writer.global_attribute("description", "A unittest case")
        writer.global_attribute("source", "Arrhenius project unittests")
        writer.global_attribute("history", "Written June 27, 2018")

        filepath = path.join(WRITE_OUTPUT_DIR, "global_attrs.nc")
        writer.write(filepath)

        # Read back the file with a trusted NetCDF library.
        ds = Dataset(filepath, "r")

        # Check expected contents of the three attributes written earlier.
        self.assertEqual(3, len(vars(ds)))
        self.assertEqual(ds.description, "A unittest case")
        self.assertEqual(ds.source, "Arrhenius project unittests")
        self.assertEqual(ds.history, "Written June 27, 2018")

        ds.close()

    def test_dimensions(self):
        """
        Test that dimensions can be produced in a dataset, and successfully be
        read back from another read of the file.
        """
        writer = NetCDFWriter()
        writer.dimension("short", np.int16, 1)
        writer.dimension("medium", np.int32, 10)
        writer.dimension("long", np.int64, 100)

        filepath = path.join(WRITE_OUTPUT_DIR, "dimensions.nc")
        writer.write(filepath)

        # Read the file in with a trusted NetCDF reader.
        ds = Dataset(filepath, "r")
        dims = ds.dimensions

        self.assertEqual(3, len(dims))

        # Check that the dimensions have the same values as were written
        # earlier.
        self.assertIn("short", dims)
        self.assertEqual(1, len(dims["short"]))
        self.assertIn("medium", dims)
        self.assertEqual(10, len(dims["medium"]))
        self.assertIn("long", dims)
        self.assertEqual(100, len(dims["long"]))

        ds.close()

    def test_unlimited_dimensions(self):
        """
        Test that providing a None value for dimension length produces an
        unlimited variable that can be successfully read back in later.
        """
        writer = NetCDFWriter()
        writer.dimension("inf", np.int8, None)

        filepath = path.join(WRITE_OUTPUT_DIR, "unlimited.nc")
        writer.write(filepath)

        # Read the file again to make sure the intended changes persisted.
        ds = Dataset(filepath)
        dims = ds.dimensions

        # Check that the dimension has the expected properties.
        self.assertEqual(1, len(dims))
        self.assertIn("inf", dims)
        self.assertTrue(dims["inf"].isunlimited())

        ds.close()

    def test_dimension_variables(self):
        """
        Test that creating a dimension also creates the corresponding
        variable, and provides reasonable values for it. Tests that these
        variables can be read successfully on a later read of the file.
        """
        writer = NetCDFWriter()
        writer.dimension("x", np.float32, 10, (0, 10))
        writer.dimension("y", np.int32, 15, (10, 40))

        filepath = path.join(WRITE_OUTPUT_DIR, "cartesian.nc")
        writer.write(filepath)

        # Read the file a second time with a trusted NetCDF reader.
        ds = Dataset(filepath)
        vars = ds.variables

        self.assertEqual(2, len(vars))
        self.assertIn("x", vars)
        self.assertIn("y", vars)

        # Check that dimension variable properties are correct.
        self.assertEqual(10, vars["x"].size)
        self.assertEqual(np.float32, vars["x"].dtype)
        self.assertEqual(15, vars["y"].size)
        self.assertEqual(np.int32, vars["y"].dtype)

        # Check that the dimension variables have the right range of values,
        # from their lower limit to their upper limit in even increments.
        for i in range(10):
            self.assertEqual(i + 0.5, vars["x"][i])
        for i in range(15):
            self.assertEqual(2*i + 11, vars["y"][i])

        ds.close()

    def test_variable_dimensions(self):
        """
        Test that variables can be created with varying numbers of dimensions,
        and that they accept data with the corresponding number of dimensions.
        Test reading back data to ensure proper persistence.
        """
        writer = NetCDFWriter()
        writer.dimension("x", np.int16, 10)
        writer.dimension("y", np.int16, 10)

        # Examples with 0, 1, and multiple dimensions.
        writer.variable("no_dims", np.int16, [])
        writer.variable("line", np.int16, ["x"])
        writer.variable("plane", np.int16, ["x", "y"])

        # Each variable receives data of the same number of dimensions as
        # the variable itself.
        writer.data("no_dims", np.array(1))
        writer.data("line", np.array(range(10)))
        writer.data("plane", np.array([range(i, i + 10) for i in range(10)]))

        filepath = path.join(WRITE_OUTPUT_DIR, "cartesian2.nc")
        writer.write(filepath)

        # Read the dataset back in with a trusted library.
        ds = Dataset(filepath)
        vars = ds.variables

        # Ensure only the right variables are present (including two dimension
        # variables and the three added manually)
        self.assertEqual(5, len(vars))
        self.assertIn("x", vars)
        self.assertIn("y", vars)
        self.assertIn("no_dims", vars)
        self.assertIn("line", vars)
        self.assertIn("plane", vars)

        # Proper variable values for the 0-dimensional variable.
        self.assertEqual(1, vars["no_dims"].size)
        self.assertEqual(1, vars["no_dims"][:])

        # Proper variable values for the 1-dimensional variable.
        self.assertEqual(10, vars["line"].size)
        self.assertEqual((10,), vars["line"].shape)
        self.assertEqual(0, vars["line"][0])
        self.assertEqual(4, vars["line"][4])
        self.assertEqual(9, vars["line"][9])

        # Proper variable values for the 2-dimensional variable.
        self.assertEqual(100, vars["plane"].size)
        self.assertEqual((10, 10), vars["plane"].shape)
        self.assertEqual(0, vars["plane"][0, 0])
        self.assertEqual(5, vars["plane"][0, 5])
        self.assertEqual(2, vars["plane"][1, 1])
        self.assertEqual(6, vars["plane"][2, 4])
        self.assertEqual(12, vars["plane"][5, 7])
        self.assertEqual(11, vars["plane"][8, 3])
        self.assertEqual(9, vars["plane"][9, 0])
        self.assertEqual(18, vars["plane"][9, 9])

        ds.close()

    def test_variable_attributes(self):
        """
        Test that attributes can be added to an existing variable, and that
        they can be successfully read back and accessed in future reads of the
        dataset.
        """
        writer = NetCDFWriter()
        writer.dimension("x", np.int16, 100)
        writer.variable("dimensionless", np.int8, [])
        writer.variable("dimensional", np.int16, ["x"])
        writer.variable("no_attrs", np.int32, ["x"])

        # Add arbitrary data to each variable so that the write can be
        # successful.
        writer.data("dimensionless", np.array(5))
        writer.data("dimensional", np.array(range(100)))
        writer.data("no_attrs", np.array(range(100, 400, 3)))

        writer.variable_attribute("dimensionless", "description", "No data available")
        writer.variable_attribute("dimensionless", "units", "No units")
        writer.variable_attribute("dimensional", "description", "A coordinate on the x-axis")
        writer.variable_attribute("dimensional", "units", "meters")

        filepath = path.join(WRITE_OUTPUT_DIR, "var_attrs.nc")
        writer.write(filepath)

        # Read back the three variables using a trusted library.
        ds = Dataset(filepath)
        dimless = ds.variables["dimensionless"]
        dimful = ds.variables["dimensional"]
        no_attrs = ds.variables["no_attrs"]

        # Ensure each variable has exactly the right number of attributes, and
        # that these attributes have the right values.
        self.assertEqual(2, len(vars(dimless)))
        self.assertEqual("No data available", dimless.description)
        self.assertEqual("No units", dimless.units)
        self.assertEqual(2, len(vars(dimful)))
        self.assertEqual("A coordinate on the x-axis", dimful.description)
        self.assertEqual("meters", dimful.units)
        self.assertEqual(0, len(vars(no_attrs)))

        ds.close()
