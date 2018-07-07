from core.cell_operations import calculate_transparency

from data.grid import LatLongGrid, GridCell,\
    extract_multidimensional_grid_variable
from data.collector import ClimateDataCollector
from data.display import write_model_output
from data.statistics import convert_grid_data_to_table, print_tables

import core.configuration as cnf
import core.output_config as out_cnf

from typing import List, Dict


class ModelRun:
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
                 output_controller: object, grids: List['LatLongGrid'] = None):
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

        self.collector = ClimateDataCollector(config[cnf.GRID])\
            .use_temperature_source(config[cnf.TEMP_SRC])\
            .use_humidity_source(config[cnf.HUMIDITY_SRC])\
            .use_albedo_source(config[cnf.ALBEDO_SRC])

    def run_model(self, init_co2: float,
                  new_co2: float) -> List['LatLongGrid']:
        """
        Calculate Earth's surface temperature change due to a change in
        CO2 levels from init_co2 to new_co2.

        Returns a list of grids, each of which represents the state of the
        Earth's surface over a range of time. The grids contain data produced
        from the model run.

        :param init_co2:
            The initial amount of CO2 in the atmosphere
        :param new_co2:
            The new amount of CO2 in the atmosphere
        :return:
            The state of the Earth's surface based on the model's calculations
        """
        out_cnf.set_output_center(self.output_controller)

        if self.grids is None:
            year_of_interest = self.config[cnf.YEAR]
            self.grids = self.collector.get_gridded_data(year_of_interest)

        # Average values over each latitude band before the model run.
        if self.config[cnf.AGGREGATE_LAT] == cnf.AGGREGATE_BEFORE:
            self.grids = [grid.latitude_bands() for grid in self.grids]

        # Run the body of the model, calculating temperature changes for each
        # cell in the grid.
        for grid in self.grids:
            for cell in grid:
                new_temp = self.calculate_cell_temperature(init_co2, new_co2,
                                                           cell)
                cell.set_temperature(new_temp)

        # Average values over each latitude band after the model run.
        if self.config[cnf.AGGREGATE_LAT] == cnf.AGGREGATE_AFTER:
            self.grids = [grid.latitude_bands() for grid in self.grids]

        self.print_statistic_tables()

        # Finally, write model output to disk.
        out_cnf.global_output_center().submit_collection_output(
            out_cnf.PRIMARY_OUTPUT_PATH,
            self.grids,
            self.config[cnf.RUN_ID]
        )

        return self.grids

    def print_statistic_tables(self: 'ModelRun') -> None:
        """
        Display a series of tables and statistics based on model run results.
        Which outputs are displayed is determined by the current output
        controller, and its settings under the SpecialReportDatatype and
        ReportDatatype categories.
        """
        output_center = out_cnf.global_output_center()

        # Prepare data tables.
        delta_t_name = out_cnf.ReportDatatype.REPORT_TEMP_CHANGE.value
        delta_temp_data = \
            extract_multidimensional_grid_variable(self.grids, delta_t_name)
        delta_temp_table = convert_grid_data_to_table(delta_temp_data)

        # Print tables of data.
        output_center.submit_output(
            out_cnf.SpecialReportData.REPORT_DELTA_TEMP_DEVIATIONS,
            delta_temp_table
        )

    def calculate_cell_temperature(self: 'ModelRun',
                                   init_co2: float,
                                   new_co2: float,
                                   grid_cell: 'GridCell') -> float:
        """
        Calculate the change in temperature of a specific grid cell due to a
        change in CO2 levels in the atmosphere.

        :param init_co2:
            The initial amount of CO2 in the atmosphere
        :param new_co2:
            The new amount of CO2 in the atmosphere
        :param grid_cell:
            A GridCell object containing average temperature and
            relative humidity
        :return:
            The change in surface temperature for the provided grid cell
            after the given change in CO2
        """
        co2_weight_func = self.config[cnf.CO2_WEIGHT]
        h2o_weight_func = self.config[cnf.H2O_WEIGHT]

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


def calibrate_constant(temperature: float,
                       albedo: float,
                       transparency: float) -> float:
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
    title = "arrhenius_x2"
    conf = cnf.default_config()
    conf[cnf.AGGREGATE_LAT] = cnf.AGGREGATE_AFTER
    conf[cnf.CO2_WEIGHT] = cnf.weight_by_mean
    conf[cnf.H2O_WEIGHT] = cnf.weight_by_mean

    out_cont = out_cnf.default_output_config()
    out_cont.register_collection(out_cnf.PRIMARY_OUTPUT,
                                 handler=write_model_output)
    out_cont.enable_output_type(
        out_cnf.SpecialReportData.REPORT_DELTA_TEMP_DEVIATIONS,
        handler=print_tables
    )

    model = ModelRun(conf, out_cont)
    grids = model.run_model(1, 2)
