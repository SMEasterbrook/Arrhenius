from typing import Tuple


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
            -273.0 <= temp
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
            raise ValueError("Value for relative humidity must fall in [0, 100]"
                             "(is {})".format(r_hum))
        elif albedo < 0 or albedo > 1:
            raise ValueError("Value for albedo must fall in [0, 1] (is {})"
                             .format(albedo))

        self._temperature = temp
        self._rel_humidity = r_hum
        self._albedo = albedo

        self._delta_temp = 0

    def __str__(self: 'GridCell'):
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
            raise ValueError("Value for relative humidity must fall in [0, 100]"
                             "(is {})".format(new_r_hum))

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
