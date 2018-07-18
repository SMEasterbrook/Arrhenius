from core.cell_operations import calculate_transparency_three

from data.grid import GridDimensions, LatLongGrid
from data.collector import ClimateDataCollector
from data.display import ModelOutput

import data.provider as pr
import data.configuration as cnf

import numpy as np
from math import floor, log10
from typing import List, Dict


class ModelRunner:
    """
    A class that is used to run the Arrhenius climate model on the given
    grids of data.
    This object will run the model with the provided configurations
    and output controls.
    """
    config: Dict[str, object]
    output_controller: object
    grids: List['LatLongGrid']

    def __init__(self, config: Dict[str, object],
                 output_controller: object, grids: List['LatLongGrid']):
        """
        Initialize the model configurations, the output controller, and the
        grid of data to run the model upon.

        :param config:
            A dictionary containing the configuration options for the model
        :param output_controller:
            An object that controls the type and format of data that is output
        :param grids:
            A list of LatLongGrid objects, each element of which contains data
            needed to run the model
        """
        self.config = config
        self.output_controller = output_controller
        self.grids = grids

    def run_model(self, init_co2: float,
                  new_co2: float) -> None:
        """
        Calculate Earth's surface temperature change due to
        a change in CO2 levels.

        :param init_co2:
            The initial amount of CO2 in the atmosphere
        :param new_co2:
            The new amount of CO2 in the atmosphere
        """
        for grid in self.grids:
            for cell in grid:
                new_temp = self.calculate_cell_temperature(init_co2, new_co2, cell, self.config)
                cell.set_temperature(new_temp)

    def calculate_cell_temperature(self,
                                   init_co2: float,
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

        init_transparency = calculate_transparency_five(init_co2,
                                                   init_temperature,
                                                   relative_humidity,
                                                   co2_weight_func,
                                                   h2o_weight_func)
        k = calibrate_constant(init_temperature, albedo, init_transparency)

        mid_transparency = calculate_transparency_five(new_co2,
                                                  init_temperature,
                                                  relative_humidity,
                                                  co2_weight_func,
                                                  h2o_weight_func)
        mid_temperature = get_new_temperature(albedo, mid_transparency, k)
        final_transparency = calculate_transparency_five(new_co2,
                                                    mid_temperature,
                                                    relative_humidity,
                                                    co2_weight_func,
                                                    h2o_weight_func)
        final_temperature = get_new_temperature(albedo, final_transparency, k)
        return final_temperature

    def _calibrate_constant(self, temperature, albedo, transparency) -> float:
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

    def _get_new_temperature(self, albedo: float,
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

    conf = cnf.DEFAULT_CONFIG
    conf[cnf.CO2_WEIGHT] = cnf.WEIGHT_BY_PROXIMITY
    conf[cnf.H2O_WEIGHT] = cnf.WEIGHT_BY_PROXIMITY

    original_model = ModelRunner(conf, conf, grid_cells)
    original_model.run_model(1, 2)

    writer = ModelOutput("arrhenius_x2", grid_cells)
    writer.write_output()
