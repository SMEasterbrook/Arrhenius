import unittest
import numpy as np

from os import path, remove
from pathlib import Path
from shutil import rmtree
from netCDF4 import Dataset

from data.writer import NetCDFWriter


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
