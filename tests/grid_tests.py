import unittest
from data.grid import GridDimensions


class GridDimensionsTest(unittest.TestCase):
    """
    A test class for GridDimensions. Ensures correct conversion between
    different tuple-based grid dimension representations, as well as a
    multitude of error conditions.
    """

    def test_grid_by_width(self):
        """
        Test error-free creation and return of a valid grid, with dimensions
        provided as cell widths.
        """
        grid = GridDimensions((180, 360), "width")

        dims_by_width = grid.dims_by_width()
        dims_by_width_expected = (180, 360)
        self.assertEqual(dims_by_width, dims_by_width_expected)

    def test_grid_by_count(self):
        """
        Test error-free creation and return of a valid grid, with dimensions
        provided as cell counts.
        """
        grid = GridDimensions((2, 2), "count")

        dims_by_count = grid.dims_by_count()
        dims_by_count_expected = (2, 2)
        self.assertEqual(dims_by_count, dims_by_count_expected)

    def test_grid_width_to_count(self):
        """
        Test error-free creation and return of a valid grid with dimensions
        provided as cell widths, and the correct conversion of the grid to
        a representation in cell counts.
        """
        grid = GridDimensions((90, 90), "width")

        dims_by_count = grid.dims_by_count()
        dims_by_count_expected = (2, 4)
        self.assertEqual(dims_by_count, dims_by_count_expected)

    def test_grid_count_to_width(self):
        """
        Test error-free creation and return of a valid grid with dimensions
        provided as cell counts, and the correct conversion of the grid to
        a representation in cell widths.
        """
        grid = GridDimensions((45, 180), "count")

        dims_by_width = grid.dims_by_width()
        dims_by_width_expected = (4, 2)
        self.assertEqual(dims_by_width, dims_by_width_expected)

    def test_float_grid_dims(self):
        """
        Test the error-free creation of a valid grid with floating point
        grid cell widths, and sensible conversion to a representation in
        cell counts.
        """
        grid = GridDimensions((0.5, 1.5), "width")

        dims_by_width = grid.dims_by_width()
        dims_by_width_expected = (0.5, 1.5)

        dims_by_count = grid.dims_by_count()
        dims_by_count_expected = (360, 240)

        self.assertEqual(dims_by_width, dims_by_width_expected)
        self.assertEqual(dims_by_count, dims_by_count_expected)

    def test_tiny_grid_cells(self):
        """
        Test correct conversion between grid representations when grid cell
        widths are very small.
        """
        grid = GridDimensions((2880, 2880), "count")

        dims_by_width = grid.dims_by_width()
        dims_by_width_expected = (0.0625, 0.125)

        dims_by_count = grid.dims_by_count()
        dims_by_count_expected = (2880, 2880)

        self.assertEqual(dims_by_width, dims_by_width_expected)
        self.assertEqual(dims_by_count, dims_by_count_expected)

    def test_short_tuple_error(self):
        """
        Test that an error is returned when grid dimensions are created with
        fewer than two elements in its dimension tuple.
        """
        with self.assertRaises(ValueError):
            grid = GridDimensions((), "width")

        with self.assertRaises(ValueError):
            grid = GridDimensions((1,), "width")

    def test_long_tuple_error(self):
        """
        Test that an error is returned when grid dimensions are created with
        more than two elements in its dimension tuple.
        :return:
        """
        with self.assertRaises(ValueError):
            grid = GridDimensions((1, 2, 3), "width")

    def test_invalid_grid_form_error(self):
        """
        Test that an error is returned when grid dimensions are created with
        a grid format that is not recognized.
        """
        with self.assertRaises(ValueError):
            grid = GridDimensions((1, 2), "")

        with self.assertRaises(ValueError):
            grid = GridDimensions((1, 2), "no-op")

    def test_floating_point_count_error(self):
        """
        Test that an error is returned when grid dimensions are created based on
        non-integer cell counts.
        """
        with self.assertRaises(ValueError):
            grid = GridDimensions((1.1, 1), "count")

        with self.assertRaises(ValueError):
            grid = GridDimensions((1, 12.5), "count")

    def test_out_of_bounds_lat_error(self):
        """
        Test that an error is returned when grid dimensions are created with
        latitude cell width greater than the number of degrees of latitude
        around the Earth.
        """
        with self.assertRaises(ValueError):
            grid = GridDimensions((360, 18), "width")

        with self.assertRaises(ValueError):
            grid = GridDimensions((180.1, 0.5), "width")

    def test_out_of_bounds_lon_error(self):
        """
        Test that an error is returned when grid dimensions are created with
        longitude cell width greater than the number of degrees of longitude
        around the Earth.
        """
        with self.assertRaises(ValueError):
            grid = GridDimensions((60, 480), "width")

        with self.assertRaises(ValueError):
            grid = GridDimensions((18, 360.1), "width")

    def test_max_grid_dimensions(self):
        """
        Test that a grid is successfully created when the maximum valid cell
        widths are provided.
        """
        grid = GridDimensions((180, 360), "width")

        dims_by_width = grid.dims_by_width()
        dims_by_width_expected = (180, 360)

        dims_by_count = grid.dims_by_count()
        dims_by_count_expected = (1, 1)

        self.assertEqual(dims_by_width, dims_by_width_expected)
        self.assertEqual(dims_by_count, dims_by_count_expected)



    def test_zero_lat_error(self):
        """
        Test that an error is returned when grid dimensions are created with
        a cell latitude width/count equal to zero.
        """
        with self.assertRaises(ValueError):
            grid = GridDimensions((0, 6), "width")

        with self.assertRaises(ValueError):
            grid = GridDimensions((0, 180), "count")

    def test_zero_lon_error(self):
        """
        Test that an error is returned when grid dimensions are created with
        a cell longitude width/count equal to zero.
        """
        with self.assertRaises(ValueError):
            grid = GridDimensions((9, 0), "width")

        with self.assertRaises(ValueError):
            grid = GridDimensions((2, 0), "count")

    def test_negative_lat_error(self):
        """
        Test that an error is returned when grid dimensions are created with
        a cell latitude width/count below zero.
        """
        with self.assertRaises(ValueError):
            grid = GridDimensions((-1, 6), "width")

        with self.assertRaises(ValueError):
            grid = GridDimensions((-2.5, 180), "count")

    def test_negative_lon_error(self):
        """
        Test that an error is returned when grid dimensions are created with
        a cell longitude width/count below zero.
         """
        with self.assertRaises(ValueError):
            grid = GridDimensions((4.5, -125), "width")

        with self.assertRaises(ValueError):
            grid = GridDimensions((90, -4.5), "count")

    def test_invalid_lat_dimensions_error(self):
        """
        Test that an error is returned when grid dimensions are used that
        produce a non-integral number of cells in the latitude dimension.
        """
        with self.assertRaises(ValueError):
            grid = GridDimensions((181, 45), "width")

    def test_invalid_lon_dimensions_error(self):
        """
        Test that an error is returned when grid dimensions are used that
        produce a non-integral number of cells in the longitude dimension.
        """
        with self.assertRaises(ValueError):
            grid = GridDimensions((10, 0.74))
