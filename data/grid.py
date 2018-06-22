import numpy as np
from typing import List, Tuple, Union


"""
This module contains functions and classes related to maintaining gridded data.

Gridded data divides the Earth's surface into cells, each with a certain width
in latitude and longitude degrees. Each grid cell records its own value for any
variables, such as temperature and humidity. Since grid cells typically
represent a large area of the Earth's surface, these variables are generally
averaged across the cell.

Functions in this module are involved in converting between different grid
formats, and storing gridded data in a way that allows for efficient retrieval.
"""


def convert_grid_format(grid: Tuple[int, int]) -> Tuple[int, int]:
    """
    Converts between two tuple-based representations of grid dimensions:
    one in which each number in the tuple represents the number of latitude/
    longitude cells in the grid, and one in which each number in the tuple
    represents the width or height of a cell in degrees.

    Returns a new tuple in the other form. To do so, the grid passed must be
    valid. That is, the 180 degrees of latitude and 360 degrees of longitude
    of the Earth must be able to be evenly divided up into grid cells of the
    sizes specified in the grid.

    Preconditions:
        grid is a tuple with two integer elements.
        grid[0] divides evenly into 180 (forms an integer number of latitude
            bands).
        grid[1] divides evenly into 360 (forms an integer number of longitude
            bands).

    :param grid: A set of tuple-based grid dimensions
    :return: A new set of tuple-based grid dimensions in the other format
            (see above)
    """
    if grid is None:
        raise ValueError("grid cannot be None")
    elif type(grid) != tuple:
        raise TypeError("grid must be a tuple of exactly 2 elements")
    elif len(grid) != 2:
        raise ValueError("grid must be a tuple of exactly 2 elements")
    elif 180 % grid[0] != 0:
        raise ValueError("Latitude width must be a divisor of 180")
    elif 360 % grid[1] != 0:
        raise ValueError("Longitude width must be a divisor of 360")
    else:
        new_lat = int(180 / grid[0])
        new_lon = int(360 / grid[1])

        return new_lat, new_lon


def extract_multidimensional_grid_variable(grids: Union[list, 'LatLongGrid'],
                                           datapoint: str,
                                           dim_count: int = 3) -> np.ndarray:
    """
    Extract a datapoint from a multidimensional nested list of grids,
    returning an array of that datapoint. The array will have the same
    dimensions as the original list, extended with the dimensions of the
    grids contained.

    For example, calling the function with a list of four 10x20 grids, and
    requesting the variable 'temperature', will return a 4x10x20 array of
    temperature values of cells in the four grids.

    An optional parameter dim_count allows specification of the number of
    total dimensions to the data. A single grid instance is considered to have
    two dimensions, latitude and longitude. A list of grids has three
    dimensions, a list of list of grids has four, etc. Be careful to match up
    the dim_count parameter's value with the actual number of dimensions of the
    data, or else errors will be raised.

    Precondition:
        dim_count >= 2

    :param grids:
        Either an instance of LatLongGrid if dim_count == 2, or a nested list
        of LatLongGrid if dim_count > 2
    :param datapoint:
        The name of the data variable requested from the grids
    :param dim_count:
        The number of dimensions to the data
    :return:
        An array containing the requested datapoint, structured in the same
        dimensions as the original grids argument
    """
    if dim_count < 2:
        raise ValueError("Grids must posess at least two dimensions"
                         "(provided {})".format(dim_count))
    elif dim_count == 2:
        return grids.extract_datapoint(datapoint)
    else:
        grid_values = []

        for grid in grids:
            grid_values.append(extract_multidimensional_grid_variable(
                grid, datapoint, dim_count - 1))

        return np.array(grid_values)


class GridDimensions:
    """
    A representation of dimensions in a flat latitude/longitude grid.

    Grid dimensions can be described in multiple ways. For example, a grid
    can be defined by having cells that are all 1 degree latitude by 1 degree
    longitude, or the same grid can be equivalently be described as having
    180 cells in a latitude band and 360 cells in a longitude band. This class
    serves as an access point and conversion medium between grid dimension
    types.

    This class is not a grid in itself, and contains no data aside from the
    dimensions of a grid.
    """
    def __init__(self: 'GridDimensions',
                 dims: Tuple[int, int],
                 dims_form: str = "width") -> None:
        """
        Initialize a new set of grid dimensions based on the tuple parameter.

        By default, the two elements in the tuple are interpreted width and
        height of a grid cell in the grid, in degrees latitude and degrees
        longitude respectively. From this, the real dimensions of the grid
        can be found. This behaviour is also maintained if the optional second
        parameter is included with value 'width'.

        If the optional second parameter is given value 'count', then the
        numbers in the tuple are interpreted as the number of grid cells in
        a latitude band and a longitude band, respectively.

        If the second parameter is given any value other than 'width' or
        'count', an error will be raised.

        :param dims:
            A tuple of two numbers that indicate the size of the grid
        :param dims_form:
            A string describing how to interpret the grid dimensions
        """
        # Integrity checks for dims
        if type(dims) != tuple:
            raise TypeError("dims must be a tuple of exactly 2 elements"
                            "(is type {})".format(type(dims)))
        elif len(dims) != 2:
            raise ValueError("dims must be a tuple of exactly 2 elements"
                             "(is length {})".format(len(dims)))
        elif type(dims[0]) != int:
            raise TypeError("All elements of dims must be integers"
                            "(element 0 is type {})".format(type(dims[0])))
        elif type(dims[1]) != int:
            raise TypeError("All elements of dims must be integers"
                            "(element 1 is type {}".format(type(dims[1])))

        # Integrity checks for dims_form
        if dims_form == "width":
            self._grid_by_count = convert_grid_format(dims)
        elif dims_form == "count":
            self._grid_by_count = dims
        else:
            raise ValueError("dims_form must be either 'width' or 'count'"
                             "(is {})".format(dims_form))


class GridCell:
    """
    A single cell within a latitude-longitude grid overlaid over Planet Earth.

    Each cell has a temperature, a relative humidity value, and an albedo.
    Where applicable, a grid cell represents only a single atmospheric layer,
    so that multiple grid cells may occupy the same latitude and longitude
    if they have different latitudes.
    """
    def __init__(self: 'GridCell',
                 temp: float,
                 r_hum: float,
                 albedo: float) -> None:
        """
        Instantiate a new GridCell object with values for all the variables
        within the grid cell. Location (latitude/longitude) and surface area
        are not tracked inside the object, and must be maintained externally
        if they are required.

        Preconditions:
            0 <= temp
            0.0 <= r_hum <= 100.0
            0.0 <= albedo <= 1.0

        :param temp:
            Average temperature, in Kelvin, within the grid cell
        :param r_hum:
            Average relative humidity within the grid cell, in percent
        :param albedo:
            Average surface albedo within the grid cell
        """
        if temp < 0:
            raise ValueError("Value for temperature must be greater than 0"
                             "(is {})".format(temp))
        elif r_hum < 0 or r_hum > 100:
            raise ValueError("Value for relative humidity must fall in"
                             "[0, 100] (is {})".format(r_hum))
        elif albedo < 0 or albedo > 1:
            raise ValueError("Value for albedo must fall in [0, 1] (is {})"
                             .format(albedo))

        self._temperature = temp
        self._rel_humidity = r_hum
        self._albedo = albedo

        self._delta_temp = 0

    def __str__(self: 'GridCell') -> str:
        """
        Returns a str representation of this grid cell and data it contains.

        :return:
            A str representing this grid cell
        """
        return "Temperature: {} deg.  --  Humidity: {}%  --  Albedo: {}"\
            .format(self._temperature, self._rel_humidity, self._albedo)

    def get_temperature(self: 'GridCell') -> float:
        """
        Returns the average temperature of this grid cell.

        :return:
            The average temperature within the cell, in degrees Celsius
        """
        return self._temperature

    def set_temperature(self: 'GridCell',
                        new_temp: float) -> None:
        """
        Set a new value for the temperature within this grid cell.

        Precondition:
            -273.0 <= new_temp

        :param new_temp:
            The new value, in Kelvin, for temperature in this cell
        """
        if new_temp < 0:
            raise ValueError("Value for temperature must be greater than -273"
                             "(is {})".format(new_temp))

        self._delta_temp += (new_temp - self._temperature)
        self._temperature = new_temp

    def get_temperature_change(self: 'GridCell') -> float:
        """
        Returns the difference between the grid cell's original temperature
        and its current temperature.

        :return:
            The temperature change this grid cell has seen since its creation
        """
        return self._delta_temp

    def get_relative_humidity(self: 'GridCell') -> float:
        """
        Returns the average relative humidity of this grid cell.

        :return:
            The average relative humidity of this grid cell
        """
        return self._rel_humidity

    def set_relative_humidity(self: 'GridCell',
                              new_r_hum: float) -> None:
        """
        Set a new value for the relative humidity within this grid cell.

        Precondition:
            0.0 <= new_r_hum <= 100.0

        :param new_r_hum:
            The new value for relative humidity in this cell
        """
        if new_r_hum < 0 or new_r_hum > 100:
            raise ValueError("Value for relative humidity must fall in"
                             "[0, 100] (is {})".format(new_r_hum))

        self._rel_humidity = new_r_hum

    def get_albedo(self: 'GridCell') -> float:
        """
        Returns the average surface albedo of this grid cell. Zero denotes
        that the cell reflects all light, and 1 that it absorbs all light.

        Non-surface grid cells (those at a non-zero altitude) have 0 albedo,
        since cloud albedo is ignored.

        :return:
            The average surface albedo within the cell
        """
        return self._albedo


# Converter from string to GridCell method for accessing the attribute named
# by the string. Used so that multiple short-forms can be used for each
# attribute, such as 'temp' for temperature.
VAR_NAME_TO_EXTRACTOR = {
    'temperature': GridCell.get_temperature,
    'humidity': GridCell.get_relative_humidity,
    'albedo': GridCell.get_albedo,
    'delta_t': GridCell.get_temperature_change
}


class LatLongGrid:
    """
    A full latitude-longitude grid, covering the surface of the Earth.

    The grid is two-dimensional only, and does not include altitude levels.
    It also represents only a snapshot in time. Additional dimensions, such
    as atmospheric levels, can be supported by stacking multiple LatLongGrids
    on top of each other.

    Each cell in the grid stored its own set of data. Grid cells do not
    influence adjacent grid cells.

    Data for each cell is stored within an instance of the GridCell class.
    An instance of this class should be provided fdr each cell in the grid.
    The cells may be mutated to change values within the grid without needing
    to create additional GridCell instances.
    """
    def __init__(self: 'LatLongGrid',
                 data: List[List[GridCell]]) -> None:
        """
        Instantiate a new LatLongGrid instance. The dimensions of the grid
        are inferred from the shape of the nested list in the second parameter.

        The data defines the dimensions of the grid, which cannot be changed
        later on. However, cells in the grid can be changed after the grid is
        created, either by mutation or replacement.

        :param data:
            A nested list containing gridded data
        """
        self._data = data

        # Iterator and caching attributes
        self._most_recent_row = None
        self._most_recent_row_num = -1
        self._most_recent_col_num = -1

    def __iter__(self: 'LatLongGrid'):
        """
        Returns an iterator over data in the grid.

        The iterator begins in the furthest southwest coordinates, and returns
        longitudinal bands one after another, heading north. For example, in a
        grid with 10-by-20 degree cells, the iterator will start by returning
        the cell centered at (-85, -170) latitude and longitude. It will then
        return the cell at (-85, -150) latitude and longitude, then (-85, -130)
        and so on until longitude 180 is reached or exceeded. Then it will
        repeat its eastward sweep for latitude -75, then -65, and so on until
        latitude 90 is reached or exceeded.

        :return:
            An iterator over the cells in this grid, in the order described
            above
        """
        for i in range(len(self._data)):
            row = self._data[i]

            for j in range(len(row)):
                yield row[j]

    def grid_dimensions(self: 'LatLongGrid',
                        grid_form: str = "width") -> Tuple[int, int]:
        """
        Returns a two-element tuple containing the dimensions of the grid.
        The first element represent latitude, and the second represents
        longitude.

        The optional grid_form argument allows specification of the format
        of the grid returned. If given the value 'width' (default), then each
        number in the tuple represents the width of a single grid cell in
        degrees; if given the value 'count', then each number in the grid
        is how many cells it takes to circle the globe in the appropriate
        dimension.

        Returns (0, 0) if no data has been provided from which to form a grid.

        :return:
            A tuple containing the dimensions of this grid
        """
        if self._data is None:
            return 0, 0
        else:
            grid_by_count = (len(self._data), len(self._data[0]))

            if grid_form == "width":
                return convert_grid_format(grid_by_count)
            elif grid_form == "count":
                return grid_by_count
            else:
                raise ValueError("Grid form must be either 'width' or 'count'"
                                 "(is {})".format(grid_form))

    def set_coord(self: 'LatLongGrid',
                  x: int,
                  y: int,
                  val) -> None:
        """
        Set a new value for the cell in the grid that is x cells from the left
        and y cells from the bottom of the grid.

        Preconditions:
            0 <= x < width of the grid
            0 <= y < height of the grid

        :param x:
            The distance of the cell from the leftmost edge of the grid
        :param y:
            The distance of the cell from the bottom of the grid
        :param val:
            The new value for the grid cell at that position
        """
        if x < 0 or x > len(self._data[0]):
            raise ValueError("X coordinate must be within the boundaries ({},"
                             "{}), is {}".format(0, (len(self._data[0])), x))
        elif y < 0 or y > len(self._data):
            raise ValueError("Y coordinate must be within the boundaries ({},"
                             "{}), is {}".format(0, (len(self._data)), y))

        # Cache the most recently accessed row to prevent excessive list/array
        # indexing in subsequent calls.
        if self._most_recent_row_num != y:
            self._most_recent_row_num = y
            self._most_recent_row = self._data[y]

        self._most_recent_row[x] = val

    def get_coord(self: 'LatLongGrid',
                  x: int,
                  y: int) -> GridCell:
        """
        Returns the grid cell at the position that is x cells from the left
        and y cells from the bottom of the grid.

        Preconditions:
            0 <= x < width of the grid
            0 <= y < height of the grid

        :param x:
            The distance of the cell from the leftmost edge of the grid
        :param y:
            The distance of the cell from the bottom of the grid
        :return:
            The grid cell located at that position
        """
        if x < 0 or x > len(self._data[0]):
            raise ValueError("X coordinate must be within the boundaries {},"
                             "is {}".format(0, (len(self._data[0])), x))
        elif y < 0 or y > len(self._data):
            raise ValueError("Y coordinate must be within the boundaries {},"
                             "is {}".format(0, (len(self._data)), y))

        # Cache the most recently accessed row to prevent excessive list/array
        # indexing in subsequent calls.
        if self._most_recent_row_num != y:
            self._most_recent_row_num = y
            self._most_recent_row = self._data[y]

        return self._most_recent_row[x]

    def extract_datapoint(self: 'LatLongGrid',
                          datapoint: str) -> np.ndarray:
        """
        Produce a gridded array of the same shape as this grid, but containing
        only the specified datapoint in each cell.

        For example, if called on a grid of dimensions 180x360 with argument
        'temperature', returns a 180x360 array containing the temperature
        values in each cell.

        Precondition:
            datapoint matches up with a attribute in GridCell (i.e. datapoint
            is in ['temperature', 'humidity', 'albedo'])

        :param datapoint:
            The name of the GridCell variable to be returned
        :return:
            A array of equivalent dimensions to the grid, containing only
            values for the requested variable
        """
        converted_data = []

        # Stores the GridCell getter method to get the requested attribute.
        extractor_func = VAR_NAME_TO_EXTRACTOR[datapoint]

        # Loop through grid cells to get the requested datapoint from each.
        for row in self._data:
            converted_row = []
            for cell in row:
                converted_row.append(extractor_func(cell))

            converted_data.append(converted_row)

        return np.array(converted_data)
