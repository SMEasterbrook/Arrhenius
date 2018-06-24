from core.cell_operations import calculate_transparency

from data.grid import GridDimensions
from data.collector import ClimateDataCollector
from data.display import ModelOutput
import data.provider as pr

import numpy as np
from math import floor, log10
from typing import List


def run_model(init_co2: float,
              new_co2: float,
              grids: List['LatLongGrid']) -> None:
    """
    Calculate Earth's surface temperature change due to
    a change in CO2 levels.

    :param init_co2:
        The initial amount of CO2 in the atmosphere
    :param new_co2:
        The new amount of CO2 in the atmosphere
    :param grids:
        The grid objects containing gridded temp and humidity data
    """
    for grid in grids:
        for cell in grid:
            new_temp = calculate_cell_temperature(init_co2, new_co2, cell)
            cell.set_temperature(new_temp)


def calculate_cell_temperature(init_co2: float, new_co2: float,
                               grid_cell: 'GridCell') -> float:
    """
    Calculate the change in temperature of a specific grid cell due to a
    change in CO2 levels in the atmosphere.

    :param init_co2:
        The initial amount of CO2 in the atmosphere
    :param new_co2:
        The new amount of CO2 in the atmosphere
    :param grid_cell:
        A GridCell object containing average temperature and relative humidity
    :return:
        The change in surface temperature for the provided grid cell
        after the given change in CO2
    """
    init_temperature = grid_cell.get_temperature()
    relative_humidity = grid_cell.get_relative_humidity()
    albedo = grid_cell.get_albedo()
    init_transparency = calculate_transparency(init_co2,
                                               init_temperature,
                                               relative_humidity)
    k = calibrate_constant(init_temperature, albedo, init_transparency)

    mid_transparency = calculate_transparency(new_co2,
                                              init_temperature,
                                              relative_humidity)
    mid_temperature = get_new_temperature(albedo, mid_transparency, k)
    final_transparency = calculate_transparency(new_co2,
                                                mid_temperature,
                                                relative_humidity)
    final_temperature = get_new_temperature(albedo, final_transparency, k)
    return final_temperature


def calibrate_constant(temperature, albedo, transparency) -> float:
    """
    Calculate the constant K used in Arrhenius' temperature change equation
    using the initial values of temperature and absorption in a grid cell.

    :param temperature:
        The temperature of the grid cell
    :param albedo:
        The albedo of the grid cell
    :param transparency:
        The transparency of the grid cell

    :return:
        The calculated constant K
    """
    return pow(temperature, 4) * (1 + albedo * transparency)


def get_new_temperature(albedo: float,
                        new_transparency: float,
                        k: float) -> float:
    """
    Calculate the new temperature after a change in absorption coefficient

    :param albedo:
        The albedo of the grid cell
    :param new_transparency:
        The new value of the transparency for the grid cell
    :param k:
        A constant used in Arrhenius' temperature change equation

    :return:
        The change in temperature for a grid cell with the given change in B
    """
    denominator = 1 + albedo * new_transparency
    return pow((k / denominator), 1 / 4)


def latitude_band_avg(grid: 'LatLongGrid',
                      lat: int) -> None:
    """
    Returns the average temperature change for the latitude band specified.
    The second parameter gives the number of latitude bands between the
    one to print and the bottom of the map. For example, the southernmost
    latitude band is given by lat equal to 0.

    :param grid:
        A latitude longitude grid
    :param lat:
        The number of latitude bands between the one to be printed and the
        south pole
    :return:
        The average temperature change over the latitude band
    """

    grid_size = grid.dimensions().dims_by_count()
    row_total = 0
    for lon in range(grid_size[1]):
        row_total += grid.get_coord(lon, lat).get_temperature_change()

    return row_total / grid_size[1]


def format_row(headings: List,
               length: int = 10) -> str:
    temp = []
    for i in range(len(headings)):
        temp.append(str(headings[i]))

        if len(temp[i]) > length:
            temp[i] = temp[i][:length]
        elif len(temp[i]) < length:
            temp[i] = " " + temp[i]
            temp[i] = temp[i].ljust(length, " ")

    return "|".join(temp)


def convert_grids_to_table(grids: List['LatLongGrid']) -> np.ndarray:
    """
    Returns an array, representing the average temperature changes within the
    latitude bands in all grids provided.

    The array is structured such that the first index indicates latitude,
    measured in how many latitude bands exist between the index in question
    and the south pole. For example, index 0 into the second dimension of
    the array has 0 bands between it and the south pole, and is therefore
    the southernmost band.

    The second index in the array represents time, divided into as many
    segments as the grids were built on. That is, the length of the array's
    first dimension will be equal to the length of the list of grids passed
    in, as the length of that list is the number of time segments.

    :param grids:
        A list of latitude/longitude grids
    :return:
        An array of average temperature changes for each latitude band in
        the grids
    """
    grid_dims = grids[0].dimensions().dims_by_count()
    results_table = []

    for lat in range(grid_dims[0]):
        results_row = [latitude_band_avg(grid, lat) for grid in grids]
        results_table.append(results_row)

    return np.array(results_table)


def _format_row(cell_values: List,
                length: int = 10) -> str:
    """
    Convert a list of values into a string, formatted like a row in a table.

    The values in the list are separated by dividers, and are truncated or
    padded until their length is equal to the optional length parameter, or
    10 characters by default.

    :param cell_values:
        A list of values to be converted to a row in a table
    :param length:
        The length, in characters, of each entry in the table
    :return:
        A string with the values formatted into a table row
    """
    cells = []
    for i in range(len(cell_values)):
        cells.append(str(cell_values[i]))

        # Correct the string to be the appropriate length, padding with
        # whitespace when needed.
        if len(cells[i]) > length:
            cells[i] = cells[i][:length]
        elif len(cells[i]) < length:
            cells[i] = cells[i].ljust(length, " ")

    return " | ".join(cells)


def convert_grids_to_strs(grids: List['LatLongGrid']) -> List[str]:
    """
    Format the given latitude/longitude grids into a table of strings.

    The table contains averaged values latitude bands within each grid.
    It is returned as a list, where each index in the list is a row in the
    table. This is so that multiple tables can be concatenated horizontally,
    by joining corresponding rows from two different tables.

    The table's horizontal dimension represents time, with columns further to
    the right being later on. The table's vertical dimension represents
    latitude, with the top marking the northernmost bands and the bottom
    marking the southernmost bands.

    :param grids:
        A list of latitude/longitude grids
    :return:
        A table containing a single datapoint from each latitude band in the
        grids, with one row of the table per index in the list
    """
    headings = ["Division {}".format(i) for i in range(1, len(grids) + 1)]
    cell_length = int(floor(log10(len(grids)))) + 10

    table_strs = []

    for row in convert_grids_to_table(grids):
        table_strs.append(_format_row(row, cell_length))

    table_strs.append(_format_row(["-" * cell_length] * len(grids),
                                  cell_length))
    table_strs.append(_format_row(headings, cell_length))

    table_strs.reverse()
    return table_strs


def merge_str_tables(table1: List[str],
                     table2: List[str],
                     sep: str = " " * 12) -> List[str]:
    """
    Display two tables of results adjacent to each other.

    Table1 will take up its position on the left, and table2 on the right.
    The two will be separated horizontally by the optional sep parameter,
    or by 12 spaces if none is given.

    Precondition:
        len(table1) == len(table2)

    :param table1:
        The table positioned on the left
    :param table2:
        The table positioned on the right
    :param sep:
        The string that separates the two tables horizontally
    :return:
        A new table containing both original tables side by side
    """
    if len(table1) != len(table2):
        raise IndexError("Both tables must have the same length"
                         "(have {}, {})".format(len(table1), len(table2)))

    table3 = []
    for i in range(len(table1)):
        table3.append(sep.join([table1[i], table2[i]]))

    return table3


if __name__ == '__main__':
    grid_dims = GridDimensions((10, 20))
    grid_cells = ClimateDataCollector(grid_dims) \
        .use_temperature_source(pr.arrhenius_temperature_data) \
        .use_humidity_source(pr.arrhenius_humidity_data) \
        .use_albedo_source(pr.landmask_albedo_data) \
        .get_gridded_data()

    run_model(1, 2, grid_cells)

    writer = ModelOutput("arrhenius_x2", grid_cells)
    writer.write_output()
