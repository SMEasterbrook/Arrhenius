from data import custom_readers
from data.grid import convert_grid_format
from typing import Tuple

import numpy as np
import pyresample

"""
This module contains prebuilt and custom data providers, functions
that collect and format data from one of more datasets to construct a
meaningful array of data.

For instance, a provider function may access datasets on both land and
ocean surface temperatures to produce a global surface temperature
dataset, and do operations such as rearranging dimensions to make
the datasets consistent.

For every different data type needed, a new provider function should
be made that is specialized to that data type and its origin.
Additionally, stub or mock providers can be made for testing purposes.

Data providers do not need to be associated with databases or
datasets. Some may contain purely static values. These can be left
as publicly exposed constants unless encapsulation reasons dictate
otherwise.
"""


STATIC_ATM_PATHLENGTH = 1.61
STATIC_ATM_CO2 = 408.39 / 1000000
STATIC_ATM_H2O = None

STATIC_ATM_ABSORBANCE = 0.70


def _adjust_latlong_grid(dataset: 'custom_readers.NetCDFReader',
                         data_var: np.ndarray,
                         grid: Tuple[int, int] = (10, 20)) -> np.ndarray:
    """
    Translate a latitude-longitude variable from its native grid to the
    specified grid dimensions.

    If the grid is None, then no action will be taken and the original
    data will be returned.

    :param dataset:
        The NetCDF dataset reader object from which the data originates
    :param data_var:
        The dataset variable that is to be regridded
    :param grid:
        A tuple containing the number of latitude and longitude grades there
        are in the new grid
    :return:
        The dataset variable, translated onto the specified grid
    """
    # Read latitude and longitude widths directly from the dataset
    now_lat_size = len(dataset.latitude())
    now_lon_size = len(dataset.longitude())

    # AreaDefinitions represent latitude-longitude grids.
    # Most of the values in this constructor are unimportant, except for
    # the latitude and longitude dimensions.
    now_grid = pyresample.geometry.AreaDefinition(
        'blank', 'nothing', 'blank', {'proj': 'laea'},
        now_lon_size, now_lat_size, [0, 0, 1, 1]
    )

    final_grid = pyresample.geometry.AreaDefinition(
        'blank', 'nothing', 'blank', {'proj': 'laea'},
        grid[1], grid[0], [0, 0, 1, 1]
    )

    # Regrid the data using nearest neighbor sampling.
    now_img = pyresample.image.ImageContainerNearest(data_var, now_grid,
                                                     radius_of_influence=32)
    final_img = now_img.resample(final_grid)

    return final_img.image_data


def _regrid_netcdf_variable(dataset: 'custom_readers.NetCDFReader',
                            data_var: np.ndarray,
                            grid: Tuple[int, int] = (10, 20),
                            dim_count: int = 2) -> np.ndarray:
    """
    Translate a variable from its native grid to a requested grid dimensions.

    A variable may contain more dimensions that latitude or longitude, and
    may also contain level or time dimensions, for instance. If any such
    extra dimensions are present, specify how many total dimensions there are
    in the dim_count parameter to identify at what level the latitude/longitude
    data is found.

    Precondition:
        dim_count >= 2

    :param dataset:
        The NetCDF dataset object from which the data originates
    :param data_var:
        The dataset variable that is to be regridded
    :param grid:
        A tuple containing the number of latitude and longitude grades there
        are in the new grid
    :param dim_count:
        The number of dimensions in the data
    :return:
        The data, translated onto the specified grid
    """
    if grid is None:
        return data_var
    if dim_count < 2:
        raise ValueError("Grid inputs must have at least 2 dimensions")
    else:
        if dim_count == 2:
            return _adjust_latlong_grid(dataset, data_var, grid)
        else:
            new_grid = []

            # Temporary solution. Regrid each index separately and
            # reform array.
            for i in range(len(data_var)):
                new_grid.append(_regrid_netcdf_variable(dataset, data_var[i],
                                                        grid, dim_count - 1))

            return np.array(new_grid)


def _avg(data_var: np.ndarray):
    """
    Returns the average of the numeric element of the data array.

    :param data_var:
        An array of numeric elements
    :return:
        The average of the elements
    """
    total = 0
    for row in data_var:
        total += sum(row)

    return total / (len(data_var) * len(data_var[0]))


def _naive_regrid(data_var: np.ndarray,
                  grid: Tuple[int, int] = (10, 20),
                  grid_form: str = "width") -> np.ndarray:
    """
    Regrid the given variable in the simplest way possible: by averaging the
    values in the original grid that make up a cell in the new grid.

    For this method to work, a single grid cell in the new grid must exactly
    fit an integer number of cells from the original grid in both latitude
    and longitude direction. That is, the width and height of a grid cell
    in the new grid must be integer multiples of those in the original grid.

    The optional grid parameter is a two-element tuple specifying the
    dimensions of the grid to which the data will be converted. By default, the
    elements in the tuple represent the width of a grid cell in degrees
    latitude and degrees longitude, respectively.

    If the second optional argument grid_form is provided with value 'count',
    then the grid elements will be interpreted as the number of grid cells in
    a latitudinal band and a longitudinal band around the Earth, respectively.

    :param data_var:
        A set of gridded data
    :param grid:
        The grid onto which to convert the data
    :param grid_form:
        How to interpret the grid; either 'width' or 'count'.
    :return:
        The data converted naively to the new grid
    """

    if grid_form == "width":
        grid = convert_grid_format(grid)

    if len(data_var) % grid[0] != 0:
        raise ValueError("New grid latitude not an integer multiple of"
                         "initial grid latitude")
    elif len(data_var[0]) % grid[1] != 0:
        raise ValueError("New grid longitude not an integer multiple of"
                         "initial grid longitude")

    lats_per_cell = int(len(data_var) / grid[0])
    lons_per_cell = int(len(data_var[0]) / grid[1])

    # Loop over groups of grid cells in the original grid that are to be
    # combined into a single cell. Longitude order first, then latitude.
    regridded_data = []
    for i in range(0, 180, lats_per_cell):
        orig_row = data_var[i:(i + lats_per_cell)]
        regridded_row = []

        for j in range(0, 360, lons_per_cell):
            # Calculate the value for the new grid cell, which is the average
            # of the smaller grid cells contained within it.
            new_grid_cell = orig_row[:, j:(j + lons_per_cell)]
            regridded_cell_val = _avg(new_grid_cell)
            regridded_row.append(regridded_cell_val)

        regridded_data.append(regridded_row)

    return np.array(regridded_data)


def arrhenius_temperature_data(grid: Tuple[int, int] = (10, 20),
                               grid_form: str = "width") -> np.ndarray:
    """
    A data provider returning temperature data from Arrhenius' original
    1895 dataset.

    Data is gridded on a 10x20 degree latitude-longitude grid, and so any
    attempts to regrid to a finer grid will produce grainy results. Data is
    divided into four time segments of each a season long, for a total of
    one year of data coverage.

    Not all grid cells have values, especially in the Arctic and Antarctic
    circles. These missing values are present as NaN in the array returned.

    The data will default to a 10x20 degree grid, but can be converted to
    other grid dimensions through the two function parameters. Only grids
    containing integer multiples of the original grid are supported.

    The grid parameter must be a tuple of two elements, the first of which is
    for latitude and the second of which is for longitude. If the second
    parameter is equal to 'count', then the numbers in the tuple are
    interpreted as the number of grid cells in either dimension of the grid.
    If the second parameter is equal to 'width', then the numbers specify
    how many degrees each grid cell is in degrees latitude and longitude.

    :param grid:
        Tuple representing latitude and longitude dimensions of the grid
        on which the data is to be returned
    :param grid_form:
        Either the string 'count' if the numbers in the grid correspond to
        the number of cells in a row of the grid, or 'width' if the numbers
        give the widths of each cell in degrees
    :return:
        Temperature data from Arrhenius' original dataset
    """
    if grid_form == "width":
        grid = convert_grid_format(grid)
    elif grid_form != "count":
        raise ValueError("grid_form must be either 'width' or 'count'"
                         "(is {})".format(grid_form))

    dataset = custom_readers.ArrheniusDataReader()

    data = dataset.collect_untimed_data("temperature")
    # Regrid the humidity variable to the specified grid, if necessary.
    regridded_data = _regrid_netcdf_variable(dataset, data[:], grid, 3)

    return regridded_data


def berkeley_temperature_data(grid: tuple = (180, 360),
                              grid_form: str = "count") -> np.array:
    """
    A data provider returning temperature data from the Berkeley Earth
    temperature dataset. Includes 100% surface and ocean coverage in
    1-degree gridded format. Data is reported for the last full year,
    in monthly sections.

    Returned in a numpy array. First index corresponds to month, with
    0 being January and 11 being December; the second index is latitude,
    with 0 being 90 and 179 being 90; the third index is longitude,
    specifications unknown.

    The data will default to a 1-by-1-degree grid, but can be converted to
    other grid dimensions through the two function parameters. Only grids
    containing integer multiples of the original grid are supported.

    The grid parameter must be a tuple of two elements, the first of which is
    for latitude and the second of which is for longitude. If the second
    parameter is equal to 'count', then the numbers in the tuple are
    interpreted as the number of grid cells in either dimension of the grid.
    If the second parameter is equal to 'width', then the numbers specify
    how many degrees each grid cell is in degrees latitude and longitude.

    :param grid: Number of latitude and longitude cells in the grid in
                 which the data is to be returned
    :param grid_form: Either the string 'count' if the numbers in the grid
                      correspond to the number of cells in a row of the grid,
                      or 'width' if the numbers give the widths of each cell
    :return: Berkeley Earth surface temperature data on the selected grid
    """
    if grid_form == "width":
        grid = convert_grid_format(grid)
    elif grid_form != "count":
        raise ValueError("grid_form must be either 'width' or 'count'"
                         "(is {})".format(grid_form))

    dataset = custom_readers.BerkeleyEarthTemperatureReader()

    data = dataset.read_newest('temperature')
    clmt = dataset.collect_untimed_data('climatology')

    # Translate data from the default, 1 by 1 grid to any specified grid.
    regridded_data = _regrid_netcdf_variable(dataset, data[:], grid, 3)
    regridded_clmt = _regrid_netcdf_variable(dataset, clmt[:], grid, 3)

    for i in range(0, 12):
        # Store arrays locally to avoid repeatedly indexing dataset.
        data_by_month = regridded_data[i]
        clmt_by_month = regridded_clmt[i]

        for j in range(0, grid[0]):
            data_by_lat = data_by_month[j]
            clmt_by_lat = clmt_by_month[j]

            for k in range(0, grid[1]):
                # Only one array index required per addition instead
                # of three gives significant performance increases.
                data_by_lat[k] += clmt_by_lat[k]

    return regridded_data


def arrhenius_humidity_data(grid: Tuple[int, int] = (10, 20),
                            grid_form: str = "width") -> np.ndarray:
    """
    A data provider returning relative humidity data from Arrhenius' original
    1895 dataset.

    Data is gridded on a 10x20 degree latitude-longitude grid, and so any
    attempts to regrid to a finer grid will produce grainy results. Data is
    divided into four time segments of each a season long, for a total of
    one year of data coverage.

    Not all grid cells have values, especially in the Arctic and Antarctic
    circles. These missing values are present as NaN in the array returned.

    The data will default to a 10x20 degree grid, but can be converted to
    other grid dimensions through the two function parameters. Only grids
    containing integer multiples of the original grid are supported.

    The grid parameter must be a tuple of two elements, the first of which is
    for latitude and the second of which is for longitude. If the second
    parameter is equal to 'count', then the numbers in the tuple are
    interpreted as the number of grid cells in either dimension of the grid.
    If the second parameter is equal to 'width', then the numbers specify
    how many degrees each grid cell is in degrees latitude and longitude.

    :param grid:
        Tuple representing latitude and longitude dimensions of the grid
        on which the data is to be returned
    :param grid_form:
        Either the string 'count' if the numbers in the grid correspond to
        the number of cells in a row of the grid, or 'width' if the numbers
        give the widths of each cell in degrees
    :return:
        Relative humidity data from Arrhenius' original dataset
    """
    if grid_form == "width":
        grid = convert_grid_format(grid)
    elif grid_form != "count":
        raise ValueError("grid_form must be either 'width' or 'count'"
                         "(is {})".format(grid_form))

    dataset = custom_readers.ArrheniusDataReader()
    data = dataset.collect_untimed_data("rel_humidity")
    regridded_data = _regrid_netcdf_variable(dataset, data[:], grid, 3)

    return regridded_data


def ncar_humidity_data(grid: tuple = (180, 360),
                       grid_form: str = "count") -> np.ndarray:
    """
    A data provider returning (by default) 1-degree gridded relative
    humidity data at surface level. The data will be adjusted to a new
    grid if one is provided.

    Data is returned as a nested list structure. The outermost list has
    12 indices, and represents months of the year. For instance, index 0
    represents January, and index 9 is October. The second index is latitude,
    and the third is longitude.

    The data will default to a 1-by-1-degree grid, but can be converted to
    other grid dimensions through the two function parameters. Only grids
    containing integer multiples of the original grid are supported.

    The grid parameter must be a tuple of two elements, the first of which is
    for latitude and the second of which is for longitude. If the second
    parameter is equal to 'count', then the numbers in the tuple are
    interpreted as the number of grid cells in either dimension of the grid.
    If the second parameter is equal to 'width', then the numbers specify
    how many degrees each grid cell is in degrees latitude and longitude.

    :param grid: Number of latitude and longitude cells in the grid in
                 which the data is to be returned
    :param grid_form: Either the string 'count' if the numbers in the grid
                      correspond to the number of cells in a row of the grid,
                      or 'width' if the numbers give the widths of each cell
    :return: NCEP/NCAR surface relative humidity data
    """
    if grid_form == "width":
        grid = convert_grid_format(grid)
    elif grid_form != "count":
        raise ValueError("grid_form must be either 'width' or 'count'"
                         "(is {})".format(grid_form))

    dataset = custom_readers.NCEPHumidityReader()

    humidity = dataset.read_newest('shum')[:]
    # Regrid the humidity variable to the specified grid, if necessary.
    regridded_humidity = _regrid_netcdf_variable(dataset, humidity, grid, 3)

    return regridded_humidity


def landmask_albedo_data(temp_data: np.ndarray,
                         grid: Tuple[int, int] = (10, 20),
                         grid_form: str = "width") -> np.ndarray:
    """
    A data provider returning 1-degree gridded surface albedo data
    for land and ocean. Uses Arrhenius' albedo scheme, in which all
    land has a constant albedo, and all water likewise has a constant
    albedo. In this case clouds are ignored, although they would
    contribute to lower global average albedo.

    Data is returned in a numpy array. The first index represents
    latitude, and the second index is longitude.

    Gridded temperature data is required in the first parameter in
    order to identify which cells are covered in snow. This data
    should come from a temperature provider function that has been
    passed the same grid as this function.

    The returned albedo data will have the same time granularity as the
    temperature data it is based on (i.e. monthly value if the temperature
    is reported in monthly values).

    :return:
        Surface albedo data by Arrhenius' scheme
    """
    if grid_form == "width":
        grid = convert_grid_format(grid)
    elif grid_form != "count":
        raise ValueError("grid_form must be either 'width' or 'count'"
                         "(is {})".format(grid_form))

    dataset = custom_readers.BerkeleyEarthTemperatureReader()

    # Berkeley Earth dataset includes variables indicating which 1-degree
    # latitude-longitude cells are primarily land.
    land_coords = dataset.collect_untimed_data('land_mask')[:]
    # Regrid the land/ocean variable to the specified grid, if necessary.
    regridded_land_coords = _naive_regrid(land_coords, grid, "count")

    # Create an array of the same size as the grid, in which to store
    # grid cell albedo values.
    albedo_mask = np.ones((len(temp_data), grid[0], grid[1]), dtype=float)

    # Albedo values used by Arrhenius in his model calculations.
    ocean_albedo = (1.0 - 0.075)
    land_albedo = 1.0
    snow_albedo = 0.5

    # Intermediate array slices are cached at each for loop iteration
    # to prevent excess array indexing.
    for i in range(len(temp_data)):
        temp_time_segment = temp_data[i]

        for j in range(grid[0]):
            landmask_row = regridded_land_coords[j]
            temp_row = temp_time_segment[j]

            for k in range(grid[1]):
                land_percent = landmask_row[k]
                ocean_percent = 1 - land_percent

                # Grid cells are identified as containing snow based on having
                # land at a temperature below 0 degrees celsius.
                if temp_row[k] < 0:
                    # Any land in this cell is interpreted as being covered in
                    # snow.
                    albedo_mask[i][j][k] = land_percent * snow_albedo\
                                           + ocean_percent * ocean_albedo
                else:
                    # Any land in this cell is interpreted as being uncovered.
                    albedo_mask[i][j][k] = land_percent * land_albedo\
                                           + ocean_percent * ocean_albedo

    return albedo_mask


def static_absorbance_data() -> float:
    """
    A data provider that gives a single, global atmospheric heat absorbance
    value.

    This value is taken directly from Arrhenius' original paper, in which its
    derivation is unclear. Modern heat absorbance would have risen since
    Arrhenius' time.

    :return:
        Arrhenius' atmospheric absorbance coefficient
    """
    return STATIC_ATM_ABSORBANCE


REQUIRE_TEMP_DATA_INPUT = [landmask_albedo_data]
