from core.cell_operations import calculate_transparency

from data.grid import GridDimensions
from data.collector import ClimateDataCollector
from data.display import ModelOutput

import data.provider as pr
import data.configuration as cnf

from typing import List, Dict


def run_model(init_co2: float,
              new_co2: float,
              grids: List['LatLongGrid'],
              config: Dict[str, object] = cnf.DEFAULT_CONFIG) -> None:
    """
    Calculate Earth's surface temperature change due to
    a change in CO2 levels.

    :param init_co2:
        The initial amount of CO2 in the atmosphere
    :param new_co2:
        The new amount of CO2 in the atmosphere
    :param grids:
        The grid objects containing gridded temp and humidity data
    :param config:
        A dictionary of configuration options for this model run
    """
    for grid in grids:
        for cell in grid:
            new_temp = calculate_cell_temperature(init_co2, new_co2,
                                                  cell, config)
            cell.set_temperature(new_temp)


def calculate_cell_temperature(init_co2: float,
                               new_co2: float,
                               grid_cell: 'GridCell',
                               config: Dict[str, object]) -> float:
    """
    Calculate the change in temperature of a specific grid cell due to a
    change in CO2 levels in the atmosphere.

    :param init_co2:
        The initial amount of CO2 in the atmosphere
    :param new_co2:
        The new amount of CO2 in the atmosphere
    :param grid_cell:
        A GridCell object containing average temperature and relative humidity
    :param config:
        Configuration options for the model run
    :return:
        The change in surface temperature for the provided grid cell
        after the given change in CO2
    """
    co2_weight_func = cnf.get_transparency_weight_func(config[cnf.CO2_WEIGHT])
    h2o_weight_func = cnf.get_transparency_weight_func(config[cnf.H2O_WEIGHT])

    init_temperature = grid_cell.get_temperature()
    relative_humidity = grid_cell.get_relative_humidity()
    albedo = grid_cell.get_albedo()
    init_transparency = calculate_transparency(init_co2,
                                               init_temperature,
                                               relative_humidity,
                                               co2_weight_func,
                                               h2o_weight_func)
    k = calibrate_constant(init_temperature, albedo, init_transparency)

    mid_transparency = calculate_transparency(new_co2,
                                              init_temperature,
                                              relative_humidity,
                                              co2_weight_func,
                                              h2o_weight_func)
    mid_temperature = get_new_temperature(albedo, mid_transparency, k)
    final_transparency = calculate_transparency(new_co2,
                                                mid_temperature,
                                                relative_humidity,
                                                co2_weight_func,
                                                h2o_weight_func)
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
