
def convert_grid_format(grid):
    """
    Converts between two tuple-based representations of grid dimensions:
    one in which each number in the tuple represents the number of latitude/
    longitude cells in the grid, and one in which each number in the tuple
    represents the width or height of a cell in degrees.

    Returns a new tuple in the other form. To do so, the grid passed must be
    valid. That is, the 180 degrees of latitude and 360 degrees of longitude
    of the Earth must be able to be evenly divided up into grid cells of the
    sizes specified in the grid.

    :param grid: A set of tuple-based grid dimensions
    :return: A new set of tuple-based grid dimensions in the other format
            (see above)
    """
    if grid is None:
        raise ValueError("grid cannot be None")
    elif type(grid) != tuple and type(grid) != list:
        raise TypeError("grid must be a tuple or list of exactly 2 elements")
    elif len(grid) != 2:
        raise ValueError("grid must be a tuple or list of exactly 2 elements")
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
        within the grid cell. Location (latitude/longitude ranges) and size
        are not tracked inside the object, and must be maintained externally
        if they are required.

        :param temp:
            Average temperature, in degrees Celsius, within the grid cell
        :param r_hum:
            Average relative humidity within the grid cell
        :param albedo:
            Average surface albedo within the grid cell
        """
        self._temperature = temp
        self._rel_humidity = r_hum
        self._albedo = albedo

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

        :param new_temp:
            The new value, in degrees Celsius, for temperature in this cell
        """
        self._temperature = new_temp

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

        :param new_r_hum:
            The new value for relative humidity in this cell
        """
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
