from core.cell_operations import calculate_transparency, calculate_modern_transparency

from data.grid import LatLongGrid, GridCell, \
    extract_multidimensional_grid_variable
from data.collector import ClimateDataCollector
from data.display import write_model_output
from data.statistics import convert_grid_data_to_table, print_tables, mean, std_dev, variance

import core.configuration as cnf
import core.output_config as out_cnf
import numpy as np

from data.statistics import X2_EXPECTED
# from lowtran import horiztrans

from typing import List, Dict

ATMOSPHERE_HEIGHT = 100.0

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
                 output_controller: 'OutputController',
                 grids: List['LatLongGrid'] = None) -> None:
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

        self.output_controller.register_collection(out_cnf.PRIMARY_OUTPUT,
                                                   handler=write_model_output)

        self.collector = ClimateDataCollector(config[cnf.GRID]) \
            .use_temperature_source(config[cnf.TEMP_SRC]) \
            .use_humidity_source(config[cnf.HUMIDITY_SRC]) \
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
        data_source = "modern"

        if self.grids is None:
            year_of_interest = self.config[cnf.YEAR]
            self.grids = self.collector.get_gridded_data(year_of_interest)

        # Average values over each latitude band before the model run.
        if self.config[cnf.AGGREGATE_LAT] == cnf.AGGREGATE_BEFORE:
            self.grids = [grid.latitude_bands() for grid in self.grids]

        # Run the body of the model, calculating temperature changes for each
        # cell in the grid.
        counter = 1
        for grid in self.grids:
            place = "th" if (not 1 <= counter % 10 <= 3) \
                            and (not 10 < counter < 20) \
                else "st" if counter % 10 == 1 \
                else "nd" if counter % 10 == 2 \
                else "rd"
            report = "Preparing model run on {}{} grid".format(counter, place)
            self.output_controller.submit_output(out_cnf.Debug.PRINT_NOTICES, report)

            if data_source == "arrhenius":
                for cell in grid:
                    new_temp = self.calculate_arr_cell_temperature(init_co2,
                                                                   new_co2,
                                                                   cell)
                    cell.set_temperature(new_temp)

            elif data_source == "modern":
                for cell in grid:
                    new_temp = self.calculate_modern_cell_temperature(init_co2,
                                                                      new_co2,
                                                                      cell)
                    cell.set_temperature(new_temp)

            counter += 1

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
        temp_name = out_cnf.ReportDatatype.REPORT_TEMP.value
        delta_t_name = out_cnf.ReportDatatype.REPORT_TEMP_CHANGE.value

        temp_data = \
            extract_multidimensional_grid_variable(self.grids, temp_name)
        temp_table = convert_grid_data_to_table(temp_data)

        output_center.submit_output(out_cnf.ReportDatatype.REPORT_TEMP,
                                    temp_table)

        delta_temp_data = \
            extract_multidimensional_grid_variable(self.grids, delta_t_name)
        delta_temp_table = convert_grid_data_to_table(delta_temp_data)

        # Print tables of data.
        output_center.submit_output(
            out_cnf.ReportDatatype.REPORT_TEMP_CHANGE,
            delta_temp_table
        )

        expected = X2_EXPECTED
        diff = expected - delta_temp_table

        output_center.submit_output(
            out_cnf.SpecialReportData.REPORT_DELTA_TEMP_DEVIATIONS,
            diff
        )

        output_center.submit_output(
            out_cnf.AccuracyMetrics.TEMP_DELTA_AVG_DEVIATION,
            mean(diff)
        )

        output_center.submit_output(
            out_cnf.AccuracyMetrics.TEMP_DELTA_STD_DEVIATION,
            std_dev(diff)
        )

    def calculate_arr_cell_temperature(self: 'ModelRun',
                                   init_co2: float,
                                   new_co2: float,
                                   grid_cell: 'GridCell') -> float:
        """
        Calculate the change in temperature of a specific grid cell due to a
        change in CO2 levels in the atmosphere. Uses Arrhenius' absorption
        data.

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

        init_temperature = grid_cell.get_temperature() + 273.15
        relative_humidity = grid_cell.get_relative_humidity()
        albedo = grid_cell.get_albedo()

        init_transparency = calculate_transparency(init_co2,
                                                   cell_temperature,
                                                   relative_humidity,
                                                   co2_weight_func,
                                                   h2o_weight_func)
        k = calibrate_constant(cell_temperature, albedo, init_transparency)

        mid_transparency = calculate_transparency(new_co2,
                                                  cell_temperature,
                                                  relative_humidity,
                                                  co2_weight_func,
                                                  h2o_weight_func)
        mid_temperature = get_new_temperature(albedo, mid_transparency, k)
        final_transparency = calculate_transparency(new_co2,
                                                    cell_temperature,
                                                    relative_humidity,
                                                    co2_weight_func,
                                                    h2o_weight_func)
        final_temperature = get_new_temperature(albedo, final_transparency, k)

        delta_temp_report = "{}  ~~~~  Delta T: {} K" \
            .format(grid_cell, final_temperature - init_temperature)
        delta_trans_report = "{}  ~~~~  Delta Transparency: {} K" \
            .format(grid_cell, final_temperature - init_temperature)
        self.output_controller.submit_output(out_cnf.Debug.GRID_CELL_DELTA_TEMP,
                                             delta_temp_report)
        self.output_controller.submit_output(out_cnf.Debug.GRID_CELL_DELTA_TRANSPARENCY,
                                             delta_trans_report)

        return final_temperature - 273.15

    def calculate_modern_cell_temperature(self: 'ModelRun',
                                   init_co2: float,
                                   new_co2: float,
                                   grid_cell: 'GridCell') -> float:
        """
        Calculate the change in temperature of a specific grid cell due to a
        change in CO2 levels in the atmosphere. Uses Arrhenius' absorption
        data.

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

        init_temperature = grid_cell.get_temperature() + 273.15
        relative_humidity = grid_cell.get_relative_humidity()
        albedo = grid_cell.get_albedo()

        init_transparency = calculate_modern_transparency(init_co2,
                                                          init_temperature,
                                                          relative_humidity,
                                                          ATMOSPHERE_HEIGHT / 2,
                                                          ATMOSPHERE_HEIGHT)
        k = calibrate_constant(init_temperature, albedo, init_transparency)

        mid_transparency = calculate_modern_transparency(new_co2,
                                                         init_temperature,
                                                         relative_humidity,
                                                         ATMOSPHERE_HEIGHT / 2,
                                                         ATMOSPHERE_HEIGHT)
        mid_temperature = get_new_temperature(albedo, mid_transparency, k)
        final_transparency = calculate_modern_transparency(new_co2,
                                                           mid_temperature,
                                                           relative_humidity,
                                                           ATMOSPHERE_HEIGHT / 2,
                                                           ATMOSPHERE_HEIGHT)
        final_temperature = get_new_temperature(albedo, final_transparency, k)

        delta_temp_report = "{}  ~~~~  Delta T: {} K" \
            .format(grid_cell, final_temperature - init_temperature)
        delta_trans_report = "{}  ~~~~  Delta Transparency: {} K" \
            .format(grid_cell, final_temperature - init_temperature)
        self.output_controller.submit_output(out_cnf.Debug.GRID_CELL_DELTA_TEMP,
                                             delta_temp_report)
        self.output_controller.submit_output(out_cnf.Debug.GRID_CELL_DELTA_TRANSPARENCY,
                                             delta_trans_report)
        return final_temperature - 273.15



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


def get_coefficients() -> List[np.array]:
    coefficients = []
    coefficients.append(np.array([0.0, -.0296, -.0559, -.1070, -.3412, -.2035,
                                  -.2438, -.3760, -.1877, -.0931, -.0280, -.0416,
                                  -.2067, -.2466, -.2571, -.1652, -.0940, -.1992,
                                  -.1742, -.0188, -.0891]))
    coefficients.append(np.array([-.1455, -.1105, -.0952, -.0862, -.0068,
                                  -.3114, -.2362, -.1933, -.3198, -.1576,
                                  -.1661, -.2036, -.0484, 0.0, -.0507, 0.0,
                                  -.1184, -.0628, -.1408, -.1817, -.1444]))
    return coefficients


def get_intensities() -> np.array:
    return np.array([27.2, 34.5, 29.6, 26.4, 27.5, 24.5, 13.5, 21.4,
                     44.4, 59.0, 70, 75.5, 62.9, 56.4, 51.4, 39.1, 37.9,
                     36.3, 32.7, 29.8, 21.9])


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
    conf[cnf.AGGREGATE_LAT] = cnf.AGGREGATE_BEFORE
    conf[cnf.CO2_WEIGHT] = cnf.weight_by_mean
    conf[cnf.H2O_WEIGHT] = cnf.weight_by_mean

    out_cont = out_cnf.development_output_config()

    out_cont.enable_output_type(
        out_cnf.ReportDatatype.REPORT_TEMP_CHANGE,
        handler=print_tables
    )

    out_cont.enable_output_type(out_cnf.AccuracyMetrics.TEMP_DELTA_AVG_DEVIATION)
    out_cont.enable_output_type(out_cnf.AccuracyMetrics.TEMP_DELTA_STD_DEVIATION)
    out_cont.enable_output_type(out_cnf.AccuracyMetrics.TEMP_DELTA_VARIANCE)

    model = ModelRun(conf, out_cont)
    grids = model.run_model(1, 3)
