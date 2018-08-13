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


# Type aliases.
TupleGridDims = Tuple[Union[int, float], Union[int, float]]


def convert_grid_format(grid: TupleGridDims) -> TupleGridDims:
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

    :param grid:
        A set of tuple-based grid dimensions
    :return:
        A new set of tuple-based grid dimensions in the other format
        (see above)
    """
    new_lat = 180 / grid[0]
    new_lon = 360 / grid[1]

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
                 dims: TupleGridDims,
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
        elif type(dims[0]) not in {float, int}:
            raise TypeError("All elements of dims must be numeric"
                            "(element 0 is type {})".format(type(dims[0])))
        elif type(dims[1]) not in {float, int}:
            raise TypeError("All elements of dims must be numeric"
                            "(element 1 is type {}".format(type(dims[1])))
        elif dims[0] <= 0:
            raise ValueError("Latitude dimension value must be positive"
                             "(is {})".format(dims[0]))
        elif dims[1] <= 0:
            raise ValueError("Longitude dimension value must be positive"
                             "(is {})".format(dims[0]))

        # Integrity checks on dims that depend on the value of dims_form
        if dims_form == "width":
            if dims[0] > 180:
                raise ValueError("Latitude width exceeds maximum of 180"
                                 "(is {})".format(dims[0]))
            elif dims[1] > 360:
                raise ValueError("Longitude width exceeds maximum of 360"
                                 "(is {})".format(dims[1]))
            elif 180 % dims[0] != 0:
                raise ValueError("Latitude dimension does not produce"
                                 "integral number of grid cells"
                                 "(produces {})".format(180 / dims[0]))
            elif 360 % dims[1] != 0:
                raise ValueError("Longitude dimension does not produce"
                                 "integral number of grid cells"
                                 "(produces {})".format(360 / dims[1]))
        elif dims_form == "count":
            # Counts may only be integral
            if dims[0] % 1 != 0:
                raise ValueError("Number of latitude cells must be integral"
                                 "(is {})".format(dims[0]))
            elif dims[1] % 1 != 0:
                raise ValueError("Number of longitude cells must be integral"
                                 "(is {})".format(dims[1]))
        else:
            raise ValueError("dims_form must be either 'width' or 'count'"
                             "(is {})".format(dims_form))

        self._grid_by_count = convert_grid_format(dims)\
            if dims_form == "width"\
            else dims

    def dims_by_width(self: 'GridDimensions') -> TupleGridDims:
        """
        Return a representation of the grid dimensions in the form of a
        two-element tuple, where the elements represent the width and height
        of a single cell in the grid, in degrees latitude and degrees
        longitude respectively.

        :return:
            The grid dimensions in terms of cell sizes
        """
        return convert_grid_format(self._grid_by_count)

    def dims_by_count(self: 'GridDimensions') -> Tuple[int, int]:
        """
        Return a representation of the grid dimensions in the form of a
        two-element tuple, where the elements represent the number of cells
        in a latitudinal band and a longitudinal band, respectively.

        :return:
            The grid dimensions in terms of number of cells required to
            circle the globe
        """
        grid_by_count = self._grid_by_count
        int_lat = int(self._grid_by_count[0])
        int_lon = int(self._grid_by_count[1])

        return int_lat, int_lon


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
            -273 <= temp
            0.0 <= r_hum <= 100.0
            0.0 <= albedo <= 1.0

        :param temp:
            Average temperature, in degrees Celsius, within the grid cell
        :param r_hum:
            Average relative humidity within the grid cell, in percent
        :param albedo:
            Average surface albedo within the grid cell
        """
        if temp < -273:
            raise ValueError("Value for temperature must be greater than -273"
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
            The new value, in degrees Celsius, for temperature in this cell
        """
        if new_temp < -273:
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
                 data: List[List[GridCell]], pressure: float = 0.0) -> None:
        """
        Instantiate a new LatLongGrid instance. The dimensions of the grid
        are inferred from the shape of the nested list in the second parameter.

        The data defines the dimensions of the grid, which cannot be changed
        later on. However, cells in the grid can be changed after the grid is
        created, either by mutation or replacement.

        :param data:
            A nested list containing gridded data
        :param pressure:
            Optional parameter that is only used in runs of the model using
            the modern absorption source. The pressure of the atmosphere
            should be in millibars. Defaults to 0.0 if not explicitly
            specified
        """
        self._data = data
        self._pressure = pressure

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

    def dimensions(self: 'LatLongGrid') -> Union['GridDimensions', None]:
        """
        Returns a set of grid dimensions that matches the size of the data
        that forms the grid.

        Returns None if no data has been provided from which to form a grid.

        :return:
            The dimensions of this instance's gridded data
        """
        if self._data is None:
            return None
        else:
            grid_by_count = (len(self._data), len(self._data[0]))
            return GridDimensions(grid_by_count, "count")

    def set_coord(self: 'LatLongGrid',
                  lat: int,
                  lon: int,
                  val) -> None:
        """
        Set a new value for the cell in the grid that is lon cells from the left
        and lat cells from the top of the grid.

        Preconditions:
            0 <= lat < height of the grid
            0 <= lon < width of the grid

        :param lat:
            The distance of the cell from the top of the grid
        :param lon:
            The distance of the cell from the leftmost edge of the grid
        :param val:
            The new value for the grid cell at that position
        """
        if lat < 0 or lat >= len(self._data):
            raise IndexError("Latitude coordinate must be within boundaries"
                             "{}, is {}".format(0, (len(self._data)), lat))
        elif lon < 0 or lon >= len(self._data[0]):
            raise IndexError("Longitude coordinate must be within boundaries"
                             "{}, is {}".format(0, (len(self._data[0])), lon))

        # Cache the most recently accessed row to prevent excessive list/array
        # indexing in subsequent calls.
        if self._most_recent_row_num != lat:
            self._most_recent_row_num = lat
            self._most_recent_row = self._data[lat]

        self._most_recent_row[lon] = val

    def get_coord(self: 'LatLongGrid',
                  lat: int,
                  lon: int) -> GridCell:
        """
        Returns the grid cell at the position that is lon cells from the left
        and lat cells from the top of the grid.

        Preconditions:
            0 <= lat < height of the grid
            0 <= lon < width of the grid

        :param lat:
            The distance of the cell from the top of the grid
        :param lon:
            The distance of the cell from the leftmost edge of the grid
        :return:
            The grid cell located at that position
        """
        if lat < 0 or lat >= len(self._data):
            raise IndexError("Latitude coordinate must be within boundaries"
                             "{}, is {}".format(0, (len(self._data)), lat))
        elif lon < 0 or lon >= len(self._data[0]):
            raise IndexError("Longitude coordinate must be within boundaries"
                             "{}, is {}".format(0, (len(self._data[0])), lon))

        # Cache the most recently accessed row to prevent excessive list/array
        # indexing in subsequent calls.
        if self._most_recent_row_num != lat:
            self._most_recent_row_num = lat
            self._most_recent_row = self._data[lat]

        return self._most_recent_row[lon]

    def set_pressure(self, press: float) -> None:
        """
        Set a new value for the atmospheric pressure of the grid
        object in millibars.

        :param press:
            The pressure of the atmosphere in millibars
        """
        self._pressure = press

    def get_pressure(self) -> float:
        """
        :return:
            The pressure of the atmosphere as a float with units of millibars
        """
        return self._pressure

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

    def latitude_bands(self: 'LatLongGrid') -> 'LatLongGrid':
        """
        Average out all values within each latitudinal band in the grid,
        returning a new grid with those values.

        The new grid will have the same number of latitude gradations as
        the original. However, it will have only a single column of longitude.

        Temperature, humidity, and albedo in each band are the means of the
        respective variables in each grid cell in the row. Temperature change
        is given by the difference between average final temperature and
        average initial temperature over each cell in the band.

        :return:
            A grid equivalent to this one, with one column of latitude.
        """
        new_cells = []

        for lat_index in range(len(self._data)):
            # Accumulator variables for initial temperature, final temperature
            # and all other variables that the new latitude band will inherit.
            pre_temp_sum = 0
            post_temp_sum = 0
            humidity_sum = 0
            albedo_sum = 0

            # Do no count null cells or those with missing values.
            num_valid_cells = 0

            for cell in self._data[lat_index]:
                if cell is not None:
                    # Add the current cell's variables to accumulators.
                    post_temp_sum += cell.get_temperature()
                    pre_temp_sum += cell.get_temperature()\
                        - cell.get_temperature_change()
                    humidity_sum += cell.get_relative_humidity()
                    albedo_sum += cell.get_albedo()

                    num_valid_cells += 1

            # Protect from zero-division errors by filling a null value into
            # the grid where no valid cells existed in the row.
            if num_valid_cells > 0:
                # Calculate means for every variable, and load into a
                # grid cell.
                combined_cell = GridCell(pre_temp_sum / num_valid_cells,
                                           humidity_sum / num_valid_cells,
                                           albedo_sum / num_valid_cells)

                # Set the grid cell's temperature from its initial mean to
                # the final mean, allowing the grid cell to record the
                # temperature change.
                combined_cell.set_temperature(post_temp_sum / num_valid_cells)
                new_cells.append([combined_cell])
            else:
                new_cells.append([None])

        return LatLongGrid(new_cells)
