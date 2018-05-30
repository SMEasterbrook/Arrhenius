from data import custom_readers

import numpy as np
import pyresample
import matplotlib.pyplot as plt

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


def _adjust_to_grid(dataset, data_var, grid):
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
    if grid is None:
        return data_var
    else:
        # Read latitude and longitude widths directly from the dataset
        now_lat_size = len(dataset.collect_untimed_data('latitude'))
        now_lon_size = len(dataset.collect_untimed_data('longitude'))

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
        now_img = pyresample.image.ImageContainerNearest(data_var, now_grid, radius_of_influence=32)
        final_img = now_img.resample(final_grid)

        return final_img.image_data


def _regrid_variable(dataset, data_var, grid, dim_count):
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
    if dim_count < 0:
        raise ValueError("Grid inputs must have at least 2 dimensions")
    elif dim_count == 0:
        return _adjust_to_grid(dataset, data_var, grid)
    else:
        new_grid = []

        # Temporary solution. Regrid each index separately and reform array.
        for i in range(len(data_var)):
            new_grid.append(_regrid_variable(dataset, data_var[i], grid, dim_count - 1))

        return new_grid


def berkeley_temperature_data(grid=None) -> np.array:
    """
    A data provider returning temperature data from the Berkeley Earth
    temperature dataset. Includes 100% surface and ocean coverage in
    1-degree gridded format. Data is reported for the last full year,
    in monthly sections.

    Returned in a numpy array. First index corresponds to month, with
    0 being January and 11 being December; the second index is latitude,
    with 0 being 90 and 179 being 90; the third index is longitude,
    specifications unknown.

    :return: Berkeley Earth surface temperature data
    """
    dataset = custom_readers.BerkeleyEarthTemperatureReader()

    data = dataset.read_newest('temperature')
    clmt = dataset.collect_untimed_data('climatology')

    # Translate data from the default, 1 by 1 grid to any specified grid.
    regridded_data = _regrid_variable(dataset, data, grid, 3)
    regridded_clmt = _regrid_variable(dataset, clmt, grid, 3)

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


def static_albedo_data(grid):
    """
    A data provider returning 1-degree gridded surface albedo data
    for land and ocean. Uses Arrhenius' albedo scheme, in which all
    land has a constant albedo, and all water likewise has a constant
    albedo. In this case snow and clouds are ignored, although they
    would contribute to lower global average albedo.

    Data is returned in a numpy array. The first index represents
    latitude, with 0 being 90 and 179 being 90; the seconds index is
    longitude, specifications unknown.

    :return: Static surface albedo data by Arrhenius' scheme
    """
    dataset = custom_readers.BerkeleyEarthTemperatureReader()

    # Berkeley Earth dataset includes variables indicating which 1-degree
    # latitude-longitude cells are primarily land.
    land_coords = dataset.collect_untimed_data('land_mask')
    # Regrid the land/ocean variable to the specified grid, if necessary.
    regridded_land_coords = _adjust_to_grid(dataset, land_coords[::], grid)

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


def static_absorbance_data():
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
