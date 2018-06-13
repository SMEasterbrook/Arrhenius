from grid import GridCell, convert_grid_format


class ClimateDataCollector:
    """
    Assembles various types of data, including surface temperature, albedo,
    and atmospheric absorbption coefficients, and ensures that data formatting
    is consistent between data types.

    Designed for flexibility in data sources, and allows for sources to be
    swapped out during execution. This may be used to try out different dataset
    files to test performance, or to input stub or mock data providers to help
    test functionality.
    """

    def __init__(self, grid=None):
        # Provider functions that produce various types of data
        self._temp_source = None
        self._humidity_source = None
        self._albedo_source = None
        self._absorbance_source = None

        # Cached, combined data from the above.
        self._grid_data = None
        self._absorbance_data = None

        if grid is None:
            # Default grid dimensions give 1 by 1 degree squares.
            self._grid = (180, 360)
        else:
            self.load_grid(grid)

    def load_grid(self, grid):
        """
        Select dimensions for a new latitude and longitude grid, to which
        all gridded data is fitted.

        The grid is reported as a tuple of two elements. The first element
        represents the latitudinal width of a single grid cell, in degrees.
        The second element represents the longitudinal width of a grid cell,
        also in degrees.

        For example, passing a tuple of (10, 10) would create a grid of
        10-by-10-degree squares, with 18 divisions of latitude and 36
        divisions of longitude.

        Although floating-point values are acceptable within the tuple (e.g.
        latitudinal width of 0.5 degrees) but the number of grid cells
        produced is rounded to an integer.

        :param grid:
            A tuple denoting the size of a grid cell
        """
        if grid is None:
            raise ValueError("grid must not be None")
        elif type(grid) != tuple:
            raise TypeError("grid must be of type tuple"
                            "(is {})".format(type(grid)))
        elif len(grid) != 2:
            raise ValueError("grid must contain exactly 2 elements"
                             "(contains {})".format(len(grid)))
        elif type(grid[0]) != float and type(grid[0]) != int:
            raise ValueError("grid elements must be numeric types"
                             "(element 0 is type {})".format(type(grid[0])))
        elif type(grid[1]) != float and type(grid[0]) != int:
            raise ValueError("grid elements must be numeric types"
                             "(element 1 is type {})".format(type(grid[1])))

        self._grid = convert_grid_format(grid)

    def use_temperature_source(self, temp_src):
        """
        Load a new temperature provider function, used as an access point to
        temperature data. Returns the collector object, so that repeated
        builder method calls can be continued.

        Calling this function voids any previously cached grid data, including
        relative humidity and albedo values.

        :param temp_src:
            A new temperature provider function
        :return:
            This ClimateDataCollector
        """
        self._temp_source = temp_src
        self._grid_data = None
        return self

    def use_humidity_source(self, r_hum_src):
        """
        Load a new relative humidity provider function, used as an access point
        to humidity data. Returns the collector object, so that repeated
        builder method calls can be continued.

        Calling this function voids any previously cached data, including
        temperature and albedo values.

        :param r_hum_src:
            A new relative humidity provider function
        :return:
            This ClimateDataCollector instance
        """
        self._humidity_source = r_hum_src
        self._grid_data = None
        return self

    def use_albedo_source(self, albedo_src):
        """
        Load a new albedo provider function, used as an access point to
        surface albedo data. Returns the collector object, so that repeated
        builder method calls can be continued.

        Calling this function voids any previously cached grid data, including
        temperature and relative humidity values.

        :param albedo_src:
            A new albedo provider function
        :return:
            This ClimateDataCollector
        """
        self._albedo_source = albedo_src
        self._grid_data = None
        return self

    def use_absorbance_source(self, absorbance_src):
        """
        Load a new absorbance provider function, used as an access point to
        atmospheric heat absorbance data. Returns the collector object, so
        that repeated builder method calls can be continued.

        Calling this function voids any previously cached absorbance data.

        :param absorbance_src:
            A new absorbance provider function
        :return:
            This ClimateDataCollector
        """
        self._absorbance_source = absorbance_src
        self._absorbance_data = None
        return self

    def get_gridded_data(self):
        """
        Combines and returns all 2-dimensional gridded surface data, including
        surface temperature and surface albedo.

        Data is returned in a 2-dimensional array of dictionaries, where each
        dictionary acts like a JSON object. The temperature field in the dict
        refers to an array of 12 monthly temperature values, with index 0
        being January and index 11 being December. The albedo field refers to
        the grid cell's surface albedo.

        Raises an exception if not all of the required data providers have
        been loaded through builder methods.

        :return:
            An array of 1-degree gridded surface data
        """
        if self._grid_data is not None:
            return self._grid_data
        elif self._temp_source is None:
            raise PermissionError("No temperature provider function selected")
        elif self._albedo_source is None:
            raise PermissionError("No albedo provider function selected")

        temp_data = self._temp_source(self._grid)
        r_hum_data = self._humidity_source(self._grid)
        albedo_data = self._albedo_source(self._grid)

        self._grid_data = []

        # Start building a 2-D nested list structure for output, row by row.
        for i in range(self._grid[0]):
            # Holding row lists in memory prevents excess list lookups.
            temp_row = temp_data[0][i]
            r_hum_row = r_hum_data[0][i]
            albedo_row = albedo_data[i]
            # Start creating a new list column for entry into the output list.
            longitude_row = []

            for j in range(self._grid[1]):
                temp = temp_row[j]
                r_hum = r_hum_row[j]
                albedo = albedo_row[j]

                # Create JSON-like grid cell dictionary with gridded data.
                grid_cell_obj = GridCell(temp, r_hum, albedo)

                # Add new objects into the 2-D nested lists.
                longitude_row.append(grid_cell_obj)
            self._grid_data.append(longitude_row)

        return self._grid_data

    def get_absorbance_data(self):
        """
        Builds and returns atmospheric absorbance data.

        This data may be in the form of a float, if the collector is using
        a simple absorbance provider function; otherwise, it may also return
        a 2-D grid with an absorbance value for different areas of the
        atmosphere. It should be possible to predict which type will be
        returned, given which absorbance provider function is in use.

        Raises an exception if not all of the required data providers have
        been loaded through builder methods.

        :return:
            Global or gridded atmospheric heat absorbance data
        """
        if self._absorbance_data is not None:
            return self._absorbance_data
        elif self._absorbance_source is None:
            raise PermissionError("No absorbance provider function selected")

        self._absorbance_data = self._absorbance_source()
        return self._absorbance_data
