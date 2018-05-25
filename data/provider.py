from data import custom_data_readers

import numpy as np

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


def berkeley_temperature_data() -> np.array:
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
    dataset = custom_data_readers.BerkeleyEarthTemperatureReader()

    data = dataset.read_newest('temperature')
    clmt = dataset.collect_untimed_data('climatology')

    for i in range(0, 12):
        # Store arrays locally to avoid repeatedly indexing dataset.
        data_by_month = data[i]
        clmt_by_month = clmt[i]

        for j in range(0, 180):
            data_by_lat = data_by_month[j]
            clmt_by_lat = clmt_by_month[j]

            for k in range(0, 360):
                # Only one array index required per addition instead
                # of three gives significant performance increases.
                data_by_lat[k] += clmt_by_lat[k]
    return data


def static_albedo_data():
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
    dataset = custom_data_readers.BerkeleyEarthTemperatureReader()

    # Berkeley Earth dataset includes variables indicating which 1-degree
    # latitude-longitude cells are primarily land.
    land_coords = dataset.collect_untimed_data('land_mask')
    # Land values have an albedo of 1. Fill in all for now.
    land_mask = np.ones((180, 360), dtype=float)

    # Correct array with the proper albedo in ocean cells.
    ocean_albedo = (1 - 0.075)
    for i in range(180):
        # Cache intermediary arrays to prevent excess indexing operations.
        coord_row = land_coords[i]
        mask_row = land_mask[i]

        for j in range(360):
            if coord_row[j] == 0:
                # Represents a primarily ocean-covered grid cell.
                mask_row[j] = ocean_albedo

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
