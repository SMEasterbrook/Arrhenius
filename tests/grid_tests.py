import unittest
from data.grid import GridDimensions, GridCell, LatLongGrid,\
    extract_multidimensional_grid_variable


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


class GridCellTest(unittest.TestCase):
    """
    A test class for GridCell. Ensures correct data tracking, including
    changes in any variables that are tracked.
    """

    def test_valid_init(self):
        """
        Test error-free creation of a valid grid cell, and proper returns from
        getter methods.
        """
        temp = 1
        r_hum = 75
        albedo = 1

        cell = GridCell(temp, r_hum, albedo)

        self.assertEqual(cell.get_temperature(), temp)
        self.assertEqual(cell.get_relative_humidity(), r_hum)
        self.assertEqual(cell.get_albedo(), albedo)
        self.assertEqual(cell.get_temperature_change(), 0)

    def test_temperature_change_tracks(self):
        """
        Test that changes to a grid cell's temperature are reflected properly
        in both its temperature value and temperature change value.
        """
        temp = 298
        r_hum = 37.25
        albedo = 0.5

        cell = GridCell(temp, r_hum, albedo)
        self.assertEqual(cell.get_temperature_change(), 0)

        cell.set_temperature(temp + 1)
        self.assertEqual(cell.get_temperature(), temp + 1)
        self.assertEqual(cell.get_temperature_change(), 1)

        cell.set_temperature(temp - 1)
        self.assertEqual(cell.get_temperature(), temp - 1)
        self.assertEqual(cell.get_temperature_change(), -1)

    def test_negative_temp_error(self):
        """
        Test that attempting to create a grid cell with negative temperature
        results in an error.
        """
        with self.assertRaises(ValueError):
            cell = GridCell(-50, 50, 0.1)

        with self.assertRaises(ValueError):
            cell = GridCell(-0.01, 25, 0.36)

    def test_negative_humidity_error(self):
        """
        Test that attempting to create a grid cell with negative relative
        humidity results in an error.
        """
        with self.assertRaises(ValueError):
            cell = GridCell(12, -62, 0.67)

        with self.assertRaises(ValueError):
            cell = GridCell(162, -0.01, 0.925)

    def test_out_of_bounds_humidity_error(self):
        """
        Test that attempting to create a grid cell with relative humidity
        above 100% results in an error.
        """
        with self.assertRaises(ValueError):
            cell = GridCell(26, 125, 0.22)

        with self.assertRaises(ValueError):
            cell = GridCell(83, 100.01, 0.4)

    def test_negative_albedo_error(self):
        """
        Test that attempting to create a grid cell with negative albedo
        results in an error.
        """
        with self.assertRaises(ValueError):
            cell = GridCell(37, 25, -1)

        with self.assertRaises(ValueError):
            cell = GridCell(70.6, 1.9, -0.01)

    def test_out_of_bounds_albedo_error(self):
        """
        Test that attempting to create a grid cell with albedo greater than 1
        results in an error.
        """
        with self.assertRaises(ValueError):
            cell = GridCell(87, 45, 2)

        with self.assertRaises(ValueError):
            cell = GridCell(51.6, 25.2, 1.01)

    def test_low_border_values(self):
        """
        Test that a grid cell can be created without error using low border
        values for all three variables, namely 0 for temperature, humidity,
        and albedo.
        """
        cell = GridCell(0, 0, 0)

        self.assertEqual(cell.get_temperature(), 0)
        self.assertEqual(cell.get_relative_humidity(), 0)
        self.assertEqual(cell.get_albedo(), 0)

    def test_high_border_values(self):
        """
        Test that a grid cell can be created without error using high border
        values for all three variables, using 100 for humidity and 1 for
        albedo. Temperature has no high border.
        """
        cell = GridCell(987654321, 100, 1)

        self.assertEqual(cell.get_temperature(), 987654321)
        self.assertEqual(cell.get_relative_humidity(), 100)
        self.assertEqual(cell.get_albedo(), 1)

    def test_invalid_temperature_change(self):
        """
        Test that an error is raised when a grid cell's temperature is changed
        to an invalid value after the cell is instantiated. Also ensures that
        the grid cell's temperature is unchanged after the attempt.
        """
        cell = GridCell(273.15, 65, 0.6)
        cell.set_temperature(274.15)

        with self.assertRaises(ValueError):
            cell.set_temperature(-1)

        self.assertEqual(cell.get_temperature(), 274.15)
        self.assertEqual(cell.get_temperature_change(), 1)

    def test_invalid_humidity_change(self):
        """
        Test that an error is raised when a grid cell's relative humidity is
        changed to an invalid value after the cell is instantiated. Also
        ensures that the grid cell's humidity is unchanged after the attempt.
        """
        cell = GridCell(273.15, 65, 0.6)

        with self.assertRaises(ValueError):
            cell.set_relative_humidity(-0.01)

        with self.assertRaises(ValueError):
            cell.set_relative_humidity(100.1)

        self.assertEqual(cell.get_relative_humidity(), 65)


class GridObjectTest(unittest.TestCase):
    """
    A test class for LatLongGrid. Ensures correct ordering of dimensions,
    catching of invalid input, return format, iteration, and more.
    """

    def test_valid_init_small(self):
        """
        Test error-free creation of a two-dimensional grid from an appropriate
        list of grid cells.
        """
        cells = [[GridCell(1, 1, 0.1)]]

        grid = LatLongGrid(cells)
        dims = grid.dimensions().dims_by_count()
        dims_expected = (1, 1)

        self.assertEqual(dims, dims_expected)

    def test_dimensions_small(self):
        """
        Test correct grid dimensions as returned by a grid's dimensions()
        method for various small grids.
        """
        cells = [[GridCell(1, 1, 0.1), GridCell(2, 2, 0.2)],
                 [GridCell(3, 3, 0.3), GridCell(4, 4, 0.4)]]

        # 2x2 grid example.
        grid = LatLongGrid(cells)
        dims = grid.dimensions().dims_by_count()
        dims_expected = (2, 2)
        self.assertEqual(dims, dims_expected)

        # Reduced grid example, with 1 dimension in latitude.
        grid = LatLongGrid(cells[1:])
        dims = grid.dimensions().dims_by_count()
        dims_expected = (1, 2)
        self.assertEqual(dims, dims_expected)

        # Reduced grid example, with 1 dimension in longitude.
        grid = LatLongGrid([[cells[0][0]], [cells[1][0]]])
        dims = grid.dimensions().dims_by_count()
        dims_expected = (2, 1)
        self.assertEqual(dims, dims_expected)

    def test_dimensions_large(self):
        """
        Test correct grid dimensions as returned by the grid dimensions()
        method for one larger grid.
        """
        cells = []
        lat, lon = (172, 269)

        for i in range(lat):
            row = []
            for j in range(lon):
                row.append(GridCell(1, 1, 1))
            cells.append(row)

        grid = LatLongGrid(cells)
        dims = grid.dimensions().dims_by_count()
        dims_expected = (lat, lon)
        self.assertEqual(dims, dims_expected)

    def test_get_coords_small(self):
        """
        Test that the grid get_coord method returns the grid cell instance at
        the requested coordinates, relative to the appropriate points.
        """
        cell_00 = GridCell(1, 1, 0.1)
        cell_01 = GridCell(2, 2, 0.2)
        cell_10 = GridCell(3, 3, 0.3)
        cell_11 = GridCell(4, 4, 0.4)

        cells = [[cell_00, cell_01],
                 [cell_10, cell_11]]

        grid = LatLongGrid(cells)
        cell_at_00 = grid.get_coord(0, 0)
        cell_at_01 = grid.get_coord(0, 1)
        cell_at_10 = grid.get_coord(1, 0)
        cell_at_11 = grid.get_coord(1, 1)

        self.assertEqual(cell_at_00, cell_00)
        self.assertEqual(cell_at_01, cell_01)
        self.assertEqual(cell_at_10, cell_10)
        self.assertEqual(cell_at_11, cell_11)

    def test_get_cell_out_of_bounds_error(self):
        """
        Test that the grid get_coords method raises errors when any indices
        are given that are outside of the bounds of the arrays.
        """
        cell_00 = GridCell(1, 1, 0.1)
        cell_01 = GridCell(2, 2, 0.2)
        cell_10 = GridCell(3, 3, 0.3)
        cell_11 = GridCell(4, 4, 0.4)

        cells = [[cell_00, cell_01],
                 [cell_10, cell_11]]

        grid = LatLongGrid(cells)

        with self.assertRaises(IndexError):
            grid.get_coord(-1, 0)
        with self.assertRaises(IndexError):
            grid.get_coord(0, -1)
        with self.assertRaises(IndexError):
            grid.get_coord(1, 2)
        with self.assertRaises(IndexError):
            grid.get_coord(2, 0)

    def test_set_coord_valid(self):
        """
        Test that the grid set_coord method uses coordinates that are
        consistent with get_coords, and that it updates the grid in the
        appropriate manner.
        """
        cell_00 = GridCell(1, 1, 0.1)
        cell_01 = GridCell(2, 2, 0.2)
        cell_10 = GridCell(3, 3, 0.3)
        cell_11 = GridCell(4, 4, 0.4)

        cell_00_new = GridCell(5, 5, 0.5)
        cell_10_new = GridCell(6, 6, 0.6)

        cells = [[cell_00, cell_01],
                 [cell_10, cell_11]]

        grid = LatLongGrid(cells)
        grid.set_coord(0, 0, cell_00_new)
        grid.set_coord(1, 0, cell_10_new)

        cell_at_00 = grid.get_coord(0, 0)
        cell_at_01 = grid.get_coord(0, 1)
        cell_at_10 = grid.get_coord(1, 0)
        cell_at_11 = grid.get_coord(1, 1)

        self.assertEqual(cell_at_00, cell_00_new)
        self.assertEqual(cell_at_01, cell_01)
        self.assertEqual(cell_at_10, cell_10_new)
        self.assertEqual(cell_at_11, cell_11)

    def test_iteration_order(self):
        """
        Test that iteration through a grid returns all grid cells and proceeds
        in left-to-right, top-to-bottom order.
        """
        cell_00 = GridCell(1, 1, 0.1)
        cell_01 = GridCell(2, 2, 0.2)
        cell_10 = GridCell(3, 3, 0.3)
        cell_11 = GridCell(4, 4, 0.4)

        cells = [[cell_00, cell_01],
                 [cell_10, cell_11]]

        grid = LatLongGrid(cells)
        iter_order = [cell for cell in grid]
        expected_iter_order = [cell_00, cell_01, cell_10, cell_11]

        self.assertEqual(iter_order, expected_iter_order)

    def test_extract_temperature(self):
        """
        Test that extracting temperature data from a grid returns an array
        structure of the right dimensions, containing the right temperature
        data in the right order.
        """
        cell_00 = GridCell(1, 2, 0.1)
        cell_01 = GridCell(2, 4, 0.2)
        cell_10 = GridCell(3, 6, 0.3)
        cell_11 = GridCell(4, 8, 0.4)

        cells = [[cell_00, cell_01],
                 [cell_10, cell_11]]

        grid = LatLongGrid(cells)
        temp_data = grid.extract_datapoint("temperature")
        expected_temp_data = [[1, 2],
                              [3, 4]]

        self.assertEqual(len(temp_data), 2)
        self.assertEqual(len(temp_data[0]), 2)

        # Loop for comparison, because extract_datapoint may return its data
        # in a non-list format such as an array.
        for i in range(len(cells)):
            for j in range(len(cells[0])):
                self.assertEqual(temp_data[i][j],
                                 expected_temp_data[i][j])

    def test_extract_temperature_change(self):
        """
        Test that extracting temperature change data from a grid returns an
        array structure of the right dimensions, containing the right delta
        temperature data in the right order.
        """
        cell_00 = GridCell(1, 2, 0.1)
        cell_01 = GridCell(2, 4, 0.2)
        cell_10 = GridCell(3, 6, 0.3)
        cell_11 = GridCell(4, 8, 0.4)

        cell_01.set_temperature(2.5)
        cell_10.set_temperature(4)
        cell_11.set_temperature(5.5)

        cells = [[cell_00, cell_01],
                 [cell_10, cell_11]]

        grid = LatLongGrid(cells)
        delta_temp_data = grid.extract_datapoint("delta_t")
        expected_delta_temp_data = [[0, 0.5],
                              [1, 1.5]]

        self.assertEqual(len(delta_temp_data), 2)
        self.assertEqual(len(delta_temp_data[0]), 2)

        # Loop for comparison, because extract_datapoint may return its data
        # in a non-list format such as an array.
        for i in range(len(cells)):
            for j in range(len(cells[0])):
                self.assertEqual(delta_temp_data[i][j],
                                 expected_delta_temp_data[i][j])

    def test_extract_humidity(self):
        """
        Test that extracting relative humidity data from a grid returns an
        array structure of the right dimensions, containing the expected
        humidity data in the right order.
        """
        cell_00 = GridCell(1, 2, 0.1)
        cell_01 = GridCell(2, 4, 0.2)
        cell_10 = GridCell(3, 6, 0.3)
        cell_11 = GridCell(4, 8, 0.4)

        cells = [[cell_00, cell_01],
                 [cell_10, cell_11]]

        grid = LatLongGrid(cells)
        humidity_data = grid.extract_datapoint("humidity")
        expected_humidity_data = [[2, 4],
                                  [6, 8]]

        self.assertEqual(len(humidity_data), 2)
        self.assertEqual(len(humidity_data[0]), 2)

        # Loop for comparison, because extract_datapoint may return its data
        # in a non-list format such as an array.
        for i in range(len(cells)):
            for j in range(len(cells[0])):
                self.assertEqual(humidity_data[i][j],
                                 expected_humidity_data[i][j])

    def test_extract_albedo(self):
        """
        Test that extracting albedo data from a grid returns an array
        structure of the right dimensions, containing the right albedo
        data in the right order.
        """
        cell_00 = GridCell(1, 2, 0.1)
        cell_01 = GridCell(2, 4, 0.2)
        cell_10 = GridCell(3, 6, 0.3)
        cell_11 = GridCell(4, 8, 0.4)

        cells = [[cell_00, cell_01],
                 [cell_10, cell_11]]

        grid = LatLongGrid(cells)
        albedo_data = grid.extract_datapoint("albedo")
        expected_albedo_data = [[0.1, 0.2],
                                [0.3, 0.4]]

        self.assertEqual(len(albedo_data), 2)
        self.assertEqual(len(albedo_data[0]), 2)

        # Loop for comparison, because extract_datapoint may return its data
        # in a non-list format such as an array.
        for i in range(len(cells)):
            for j in range(len(cells[0])):
                self.assertEqual(albedo_data[i][j],
                                 expected_albedo_data[i][j])

    def test_extract_three_dimensional_datapoint(self):
        """
        Test conversion of a one-level of grids into a three-dimensional
        structure of temperature data extracted from the grid. Checks
        correct ordering of data in the output.
        """
        cell_000 = GridCell(1, 2, 0.1)
        cell_001 = GridCell(2, 4, 0.2)
        cell_010 = GridCell(3, 6, 0.3)
        cell_011 = GridCell(4, 8, 0.4)

        cell_100 = GridCell(5, 10, 0.5)
        cell_101 = GridCell(6, 12, 0.6)
        cell_110 = GridCell(7, 14, 0.7)
        cell_111 = GridCell(8, 16, 0.8)

        cells0 = [[cell_000, cell_001],
                  [cell_010, cell_011]]
        cells1 = [[cell_100, cell_101],
                  [cell_110, cell_111]]

        grid0 = LatLongGrid(cells0)
        grid1 = LatLongGrid(cells1)

        grid0_temp_expected = [[1, 2],
                               [3, 4]]
        grid1_temp_expected = [[5, 6],
                               [7, 8]]

        temp_data = extract_multidimensional_grid_variable([grid0, grid1],
                                                           "temperature")

        self.assertEqual(len(temp_data), 2)
        self.assertEqual(len(temp_data[0]), 2)
        self.assertEqual(len(temp_data[0][0]), 2)

        for i in range(len(temp_data)):
            for j in range(len(temp_data[0])):
                self.assertEqual(temp_data[0][i][j],
                                 grid0_temp_expected[i][j])
                self.assertEqual(temp_data[1][i][j],
                                 grid1_temp_expected[i][j])
