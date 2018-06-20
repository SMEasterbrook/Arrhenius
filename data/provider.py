from data import custom_readers
from data.grid import convert_grid_format
from typing import List, Tuple, Union

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
                         grid: tuple) -> np.ndarray:
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
                            grid: tuple,
                            dim_count: int) -> Union[List, np.ndarray]:
    """
    Translate a variable from its native grid to a requested grid dimensions.

    A variable may contain more dimensions that latitude or longitude, and
    may also contain level or time dimensions, for instance. If any such
    extra dimensions are present, specify how many there are in the dim_count
    parameter to identify at what level the latitude/longitude data is found.

    :param dataset:
        The NetCDF dataset object from which the data originates
    :param data_var:
        The dataset variable that is to be regridded
    :param grid:
        A tuple containing the number of latitude and longitude grades there
        are in the new grid
    :param dim_count:
        The number of dimensions other than latitude and longitude
    :return:
        The data, translated onto the specified grid
    """
    if grid is None:
        return data_var
    if dim_count < 0:
        raise ValueError("Grid inputs must have at least 2 dimensions")
    else:
        if dim_count == 0:
            return _adjust_latlong_grid(dataset, data_var, grid)
        else:
            new_grid = []

            # Temporary solution. Regrid each index separately and
            # reform array.
            for i in range(len(data_var)):
                new_grid.append(_regrid_netcdf_variable(dataset, data_var[i],
                                                        grid, dim_count - 1))

            return new_grid


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
    regridded_data = _regrid_netcdf_variable(dataset, data[:], grid, 1)

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
    regridded_data = _regrid_netcdf_variable(dataset, data[:], grid, 1)
    regridded_clmt = _regrid_netcdf_variable(dataset, clmt[:], grid, 1)

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
    regridded_data = _regrid_netcdf_variable(dataset, data[:], grid, 1)

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

    humidity = dataset.read_newest('shum')
    # Regrid the humidity variable to the specified grid, if necessary.
    regridded_humidity = _regrid_netcdf_variable(dataset, humidity[:, :, :],
                                                 grid, 1)

    return regridded_humidity


def static_albedo_data(grid: tuple = (180, 360),
                       grid_form: str = "count") -> np.ndarray:
    """
    A data provider returning 1-degree gridded surface albedo data
    for land and ocean. Uses Arrhenius' albedo scheme, in which all
    land has a constant albedo, and all water likewise has a constant
    albedo. In this case snow and clouds are ignored, although they
    would contribute to lower global average albedo.

    Data is returned in a numpy array. The first index represents
    latitude, with 0 being -90 and 179 being 90; the second index is
    longitude, specifications unknown.

    :return: Static surface albedo data by Arrhenius' scheme
    """
    dataset = custom_readers.BerkeleyEarthTemperatureReader()

    # Berkeley Earth dataset includes variables indicating which 1-degree
    # latitude-longitude cells are primarily land.
    land_coords = dataset.collect_untimed_data('land_mask')
    # Regrid the land/ocean variable to the specified grid, if necessary.
    regridded_land_coords = _regrid_netcdf_variable(dataset, land_coords[::],
                                                    grid, 0)

    # Land values have an albedo of 1. Fill in all for now.
    land_mask = np.ones((grid[0], grid[1]), dtype=float)

    # Correct array with the proper albedo in ocean cells.
    ocean_albedo = (1 - 0.075)
    for i in range(grid[0]):
        # Cache intermediary arrays to prevent excess indexing operations.
        coord_row = regridded_land_coords[i]
        mask_row = land_mask[i]

        for j in range(grid[1]):
            mask_row[j] = ocean_albedo + (coord_row[j]) * (1 - ocean_albedo)

    return land_mask


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
