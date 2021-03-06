from data import custom_readers
from data.grid import GridDimensions
from typing import Union

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


def _adjust_latlong_grid(data_var: np.ndarray,
                         grid: 'GridDimensions') -> np.ndarray:
    """
    Translate a latitude-longitude variable from its native grid to the
    specified grid dimensions.
    :param data_var:
        The dataset variable that is to be regridded
    :param grid:
        The dimensions of the grid to which the data will be converted
    :return:
        The dataset variable, translated onto the specified grid
    """
    # Read latitude and longitude widths directly from the dataset
    now_lat_size = len(data_var)
    now_lon_size = len(data_var[0])

    # AreaDefinitions represent latitude-longitude grids.
    # Most of the values in this constructor are unimportant, except for
    # the latitude and longitude dimensions.
    now_grid = pyresample.geometry.AreaDefinition(
        'blank', 'nothing', 'blank', {'proj': 'laea'},
        now_lon_size, now_lat_size, [0, 0, 1, 1]
    )

    new_dims = grid.dims_by_count()
    final_grid = pyresample.geometry.AreaDefinition(
        'blank', 'nothing', 'blank', {'proj': 'laea'},
        new_dims[1], new_dims[0], [0, 0, 1, 1]
    )

    # Regrid the data using nearest neighbor sampling.
    now_img = pyresample.image.ImageContainerNearest(data_var, now_grid,
                                                     radius_of_influence=32)
    final_img = now_img.resample(final_grid)

    return final_img.image_data


def _regrid_netcdf_variable(data_var: np.ndarray,
                            grid: Union['GridDimensions', None],
                            dim_count: int = 2) -> np.ndarray:
    """
    Translate a variable from its native grid to a requested grid dimensions.
    A variable may contain more dimensions that latitude or longitude, and
    may also contain level or time dimensions, for instance. If any such
    extra dimensions are present, specify how many total dimensions there are
    in the dim_count parameter to identify at what level the latitude/longitude
    data is found.
    If the grid is None, then no action will be taken and the original
    data will be returned.
    Precondition:
        dim_count >= 2
    :param data_var:
        The dataset variable that is to be regridded
    :param grid:
        The dimensions of the grid to which the data will be converted
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
            return _adjust_latlong_grid(data_var, grid)
        else:
            new_grid = []

            # Temporary solution. Regrid each index separately and
            # reform array.
            for i in range(len(data_var)):
                new_grid.append(_regrid_netcdf_variable(data_var[i], grid,
                                                        dim_count - 1))

            return np.array(new_grid)


def _avg(data_var: np.ndarray) -> float:
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
                  grid: 'GridDimensions') -> np.ndarray:
    """
    Regrid the given variable in the simplest way possible: by averaging the
    values in the original grid that make up a cell in the new grid.
    For this method to work, a single grid cell in the new grid must exactly
    fit an integer number of cells from the original grid in both latitude
    and longitude direction. That is, the width and height of a grid cell
    in the new grid must be integer multiples of those in the original grid.
    :param data_var:
        A set of gridded data
    :param grid:
        The grid onto which to convert the data
    :return:
        The data converted naively to the new grid
    """

    new_dims = grid.dims_by_count()
    if len(data_var) % new_dims[0] != 0:
        raise ValueError("New grid latitude not an integer multiple of"
                         "initial grid latitude")
    elif len(data_var[0]) % new_dims[1] != 0:
        raise ValueError("New grid longitude not an integer multiple of"
                         "initial grid longitude")

    lats_per_cell = int(len(data_var) / new_dims[0])
    lons_per_cell = int(len(data_var[0]) / new_dims[1])

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


def arrhenius_temperature_data(grid: 'GridDimensions'
                               = GridDimensions((10, 20)),
                               year: int = None) -> np.ndarray:
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
    other grid dimensions through the function parameter grid. Only grids
    containing integer multiples of the original grid are supported.
    :param grid:
        The dimensions of the grid onto which the data is to be converted
    :return:
        Temperature data from Arrhenius' original dataset
    """
    dataset = custom_readers.ArrheniusDataReader()

    data = dataset.collect_untimed_data("temperature")[:]
    # Regrid the humidity variable to the specified grid, if necessary.
    regridded_data = _regrid_netcdf_variable(data, grid, 3)

    return regridded_data


def berkeley_temperature_data(grid: 'GridDimensions'
                              = GridDimensions((10, 20)),
                              year: int = None) -> np.array:
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
    other grid dimensions through the function parameter grid. Only grids
    containing integer multiples of the original grid are supported.
    :param grid:
        The dimensions of the grid onto which the data is to be converted
    :return:
        Berkeley Earth surface temperature data on the selected grid
    """
    dataset = custom_readers.BerkeleyEarthTemperatureReader()

    if year is None:
        data = dataset.read_newest('temperature')[:]
    else:
        data = dataset.collect_timed_data('temperature', year)
    clmt = dataset.collect_untimed_data('climatology')[:]

    # Translate data from the default, 1 by 1 grid to any specified grid.
    regridded_data = _regrid_netcdf_variable(data, grid, 3)
    regridded_clmt = _regrid_netcdf_variable(clmt, grid, 3)
    grid_dims = grid.dims_by_count()

    for i in range(0, 12):
        # Store arrays locally to avoid repeatedly indexing dataset.
        data_by_month = regridded_data[i]
        clmt_by_month = regridded_clmt[i]

        for j in range(0, grid_dims[0]):
            data_by_lat = data_by_month[j]
            clmt_by_lat = clmt_by_month[j]

            for k in range(0, grid_dims[1]):
                # Only one array index required per addition instead
                # of three gives significant performance increases.
                data_by_lat[k] += clmt_by_lat[k]

    return regridded_data


def arrhenius_humidity_data(grid: 'GridDimensions'
                              = GridDimensions((10, 20)),
                            year: int = None) -> np.array:
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
    :param grid:
        The dimensions of the grid onto which the data will be converted
    :return:
        Relative humidity data from Arrhenius' original dataset
    """
    dataset = custom_readers.ArrheniusDataReader()
    data = dataset.collect_untimed_data("rel_humidity")[:]
    regridded_data = _regrid_netcdf_variable(data, grid, 3)

    return regridded_data


def ncar_humidity_data(grid: 'GridDimensions'
                       = GridDimensions((10, 20)),
                       year: int = None) -> np.array:
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
    :param grid:
        The dimensions of the grid onto which the data will be converted
    :return:
        NCEP/NCAR surface relative humidity data
    """
    dataset = custom_readers.NCEPReader('water')

    humidity = dataset.collect_timed_layered_data('rhum', year)

    # Regrid the humidity variable to the specified grid, if necessary.
    regridded_humidity = _regrid_netcdf_variable(humidity, grid, 4)

    grid_by_count = grid.dims_by_count()
    top_atm_shape = (humidity.shape[0], 5, grid_by_count[0], grid_by_count[1])
    high_layer_humidity = np.zeros(top_atm_shape)
    regridded_humidity = np.hstack((regridded_humidity, high_layer_humidity))

    return regridded_humidity


def ncar_temperature_data(grid: 'GridDimensions'
                          = GridDimensions((10, 20)),
                          year: int = None) -> np.array:
    """

    :param grid:
    :type grid:
    :param year:
    :type year:
    :return:
    :rtype:
    """
    dataset = custom_readers.NCEPReader('temperature')

    temp = dataset.collect_timed_layered_data('air', year)

    # Regrid the humidity variable to the specified grid, if necessary.
    regridded_temp = _regrid_netcdf_variable(temp, grid, 4)
    ground_temp = regridded_temp[:, 0, ...]
    ground_temp = ground_temp[:, np.newaxis, ...]
    regridded_temp = np.hstack((ground_temp, regridded_temp))

    return regridded_temp


def ncar_pressure_levels() -> np.array:
    """

    :param grid:
    :type grid:
    :param year:
    :type year:
    :return:
    :rtype:
    """
    dataset = custom_readers.NCEPReader('temperature')
    return dataset.pressure()


def landmask_albedo_data(temp_data: np.ndarray,
                         grid: 'GridDimensions'
                         = GridDimensions((10, 20))) -> np.ndarray:
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
    passed the same grid as this function. That is, the temperature
    data should be on the same grid as the albedo data will be
    converted to.

    The returned albedo data will have the same time granularity as the
    temperature data it is based on (i.e. monthly value if the temperature
    is reported in monthly values).

    :param temp_data:
        Gridded surface temperature data, on the same grid as the data will
        be converted to
    :param grid:
        The dimensions of the grid onto which the data will be converted
    :return:
        Surface albedo data by Arrhenius' scheme
    """
    dataset = custom_readers.BerkeleyEarthTemperatureReader()

    # Berkeley Earth dataset includes variables indicating which 1-degree
    # latitude-longitude cells are primarily land.
    land_coords = dataset.collect_untimed_data('land_mask')[:]
    # Regrid the land/ocean variable to the specified grid, if necessary.
    regridded_land_coords = _naive_regrid(land_coords, grid)
    grid_dims = grid.dims_by_count()

    # Create an array of the same size as the grid, in which to store
    # grid cell albedo values.
    albedo_mask = np.ones((len(temp_data), grid_dims[0],
                           grid_dims[1]), dtype=float)

    # (Inverse) albedo values used by Arrhenius in his model calculations.
    ocean_albedo_inverse = 0.925
    land_albedo_inverse = 1.0
    snow_albedo_inverse = 0.5

    ocean_albedo = 1 - ocean_albedo_inverse
    land_albedo = 1 - land_albedo_inverse
    snow_albedo = 1 - snow_albedo_inverse

    # Intermediate array slices are cached at each for loop iteration
    # to prevent excess array indexing.
    for i in range(len(temp_data)):
        if len(temp_data.shape) == 3:
            temp_time_segment = temp_data[i]
        else:
            temp_time_segment = temp_data[i, ..., 0, :, :]

        for j in range(grid_dims[0]):
            landmask_row = regridded_land_coords[j]
            temp_row = temp_time_segment[j]

            for k in range(grid_dims[1]):
                land_percent = landmask_row[k]
                ocean_percent = 1 - land_percent

                # Grid cells are identified as containing snow based on having
                # land at a temperature below 0 degrees celsius.
                if temp_row[k] < -15:
                    # Any land in this cell is interpreted as being covered in
                    # snow.
                    albedo_mask[i][j][k] = land_percent * snow_albedo\
                                           + ocean_percent * ocean_albedo
                else:
                    # Any land in this cell is interpreted as being uncovered.
                    albedo_mask[i][j][k] = land_percent * land_albedo\
                                           + ocean_percent * ocean_albedo

    return albedo_mask


def constant_albedo_data(temp_data: np.ndarray,
                         grid: 'GridDimensions'
                         = GridDimensions((10, 20))) -> np.ndarray:
    """
    Returns an array of absorption values for grid cells under the specified
    grid, and with the same number of time units as temp_data. Assumes that
    all grid cells have a constant absorption of 1.0, that is, that the whole
    Earth is a black body. Albedo being the inverse of absorption, the returned
    albedo mask has a constant value of 0.0. This assumption may have been made
    by Arrhenius for simplicity in the original model.

    :param temp_data:
        Temperature data for the run, straight from the dataset
    :param grid:
        The dimensions of the grid onto which the data will be converted
    :return:
        A grid of 0's satisfying the shape of the existing data.
    """
    grid_count = grid.dims_by_count()
    grid_shape = (len(temp_data), grid_count[0], grid_count[1])
    return np.zeros(grid_shape)


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


REQUIRE_TEMP_DATA_INPUT = [landmask_albedo_data, constant_albedo_data]


PROVIDERS = {
    "temperature": {
        "arrhenius": arrhenius_temperature_data,
        "berkeley": berkeley_temperature_data,
        "ncar": ncar_temperature_data,
    },
    "humidity": {
        "arrhenius": arrhenius_humidity_data,
        "ncar": ncar_humidity_data,
    },
    "albedo": {
        "landmask": landmask_albedo_data,
        "flat": constant_albedo_data,
    },
    "pressure": {
        "ncar": ncar_pressure_levels,
    },
}


if __name__ == '__main__':
    grid = GridDimensions((10, 20), "width")
    g = ncar_humidity_data(grid, 1950)
