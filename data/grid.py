
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
