from typing import List, Tuple, Callable, Union
from data.grid import LatLongGrid, GridCell, convert_grid_format

from data.provider import REQUIRE_TEMP_DATA_INPUT


# Type aliases
CDC = 'ClimateDataCollector'


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

    def __init__(self: CDC,
                 grid: Tuple[int, int] = (10, 20)) -> None:
        """
        Instantiate a new ClimateDataCollector instance.

        Takes an optional parameter grid, which is a tuple of two integers.
        Passing this grid parameter is equivalent to calling the constructor
        with no arguments, and then calling load_grid with the same grid.

        :param grid:
            An optional tuple representing the grid on which data should be
            placed
        """
        # Provider functions that produce various types of data
        self._temp_source = None
        self._humidity_source = None
        self._albedo_source = None
        self._absorbance_source = None

        # Cached, combined data from the above.
        self._grid_data = None
        self._absorbance_data = None

        self._grid = None
        self.load_grid(grid)

    def load_grid(self: CDC,
                  grid: Tuple[int, int],
                  grid_form: str = "width") -> CDC:
        """
        Select dimensions for a new latitude and longitude grid, to which
        all gridded data is fitted. Returns the collector object, so that
        repeated builder method calls can be continued.

        The grid is reported as a tuple of two elements. How the elements
        are interpreted depends on the value of the optional parameter.
        By default, and if the optional parameter is given the value 'width',
        the first element represents the latitudinal width of a single grid
        cell in degrees. The second element represents the longitudinal width
        of a grid cell, also in degrees.

        If the optional parameter is given the value 'count', then the first
        element in the tuple is interpreted as the number of grid cells
        required to circle the Earth horizontally, and the second element as
        the number of grid cells required to circle the Earth vertically.

        For example, passing a tuple of (10, 10) would create a grid of
        10-by-10-degree squares, with 18 divisions of latitude and 36
        divisions of longitude.

        Although floating-point values are acceptable within the tuple (e.g.
        latitudinal width of 0.5 degrees) but the number of grid cells
        produced is rounded to an integer.

        Preconditions:
            len(grid) == 2
            grid_form == 'width' or grid_form == 'count'

        :param grid:
            A tuple denoting the size of a grid cell
        :param grid_form:
            The format in which to interpret the grid, either
            'width' or 'count'.
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

        if grid_form == "width":
            self._grid = convert_grid_format(grid)
        elif grid_form == "count":
            self._grid = grid
        else:
            raise ValueError("grid_form must be either 'width' or 'count',"
                             "is {}".format(grid_form))
        self._grid_data = None
        return self

    def use_temperature_source(self: CDC,
                               temp_src: Callable) -> CDC:
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

    def use_humidity_source(self: CDC,
                            r_hum_src: Callable) -> CDC:
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

    def use_albedo_source(self: CDC,
                          albedo_src: Callable) -> CDC:
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

    def use_absorbance_source(self: CDC,
                              absorbance_src: Callable) -> CDC:
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

    def get_gridded_data(self: CDC) -> List['LatLongGrid']:
        """
        Combines and returns all gridded surface data, including surface
        temperature, relative humidity, and surface albedo. The data is
        returned having been converted to the grid loaded most recently.

        It is assumed that temperature, relative humidity, and albedo are time
        dependent. That is, the data arrays for those variables have three
        dimensions, the first of which is time. It is expected that these two
        data have the same gradations of their time dimensions, e.g.
        temperature and humidity are both measured in 3-month segments.

        Raises an exception if not all of the required data providers have
        been loaded through builder methods.

        :return:
            An array of gridded surface data
        """
        if self._grid_data is not None:
            # A grid was constructed with the same grid and data sources,
            # and nothing has changed since.
            return self._grid_data
        elif self._temp_source is None:
            raise PermissionError("No temperature provider function selected")
        elif self._albedo_source is None:
            raise PermissionError("No albedo provider function selected")

        temp_data = self._temp_source(self._grid, "count")
        r_hum_data = self._humidity_source(self._grid, "count")

        if len(temp_data) != len(r_hum_data):
            raise ValueError("Temperature and humidity must have the same"
                             "time dimensions")

        if self._albedo_source in REQUIRE_TEMP_DATA_INPUT:
            albedo_data = self._albedo_source(temp_data, self._grid, "count")
        else:
            albedo_data = self._albedo_source(self._grid, "count")
        self._grid_data = []

        # Start building a 2-D nested list structure for output, row by roW.
        for i in range(len(temp_data)):
            temp_time_segment = temp_data[i]
            r_hum_time_segment = r_hum_data[i]
            albedo_time_segment = albedo_data[i]

            time_segment_row = []
            for j in range(self._grid[0]):
                # Holding row lists in memory prevents excess list lookups.
                temp_row = temp_time_segment[j]
                r_hum_row = r_hum_time_segment[j]
                albedo_row = albedo_time_segment[j]
                # Start creating a new list column for entry into the output
                # list.
                longitude_row = []

                for k in range(self._grid[1]):
                    # Package the data from this grid cell into a GridCell
                    # object.
                    temp = temp_row[k]
                    r_hum = r_hum_row[k]
                    albedo = albedo_row[k]

                    grid_cell_obj = GridCell(temp, r_hum, albedo)

                    # Add new GridCell objects into the 2-D nested lists.
                    longitude_row.append(grid_cell_obj)
                time_segment_row.append(longitude_row)

            # Store data for this time gradation in a LatLongGrid object.
            new_grid_data = LatLongGrid(time_segment_row)
            self._grid_data.append(new_grid_data)

        return self._grid_data

    def get_absorbance_data(self: CDC) -> Union[List[List[float]], float]:
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
