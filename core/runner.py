from core.cell_operations import calculate_transparency, calculate_modern_transparency

from data.grid import LatLongGrid, GridCell, GridDimensions, \
    extract_multidimensional_grid_variable
from data.collector import ClimateDataCollector
from data.display import write_model_output
from data.statistics import convert_grid_data_to_table, print_tables, mean, std_dev, variance, X2_EXPECTED

import core.configuration as cnf
import core.output_config as out_cnf

import core.multilayer as ml
import numpy as np
import math

from typing import List, Dict, Tuple

ATMOSPHERE_HEIGHT = 50.0


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
                 grids: List[List['LatLongGrid']] = None) -> None:
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
            .use_albedo_source(config[cnf.ALBEDO_SRC]) \
            .use_pressure_source(config[cnf.PRESSURE_SRC])

    def run_model(self, init_co2: float,
                  new_co2: float) -> List[List['LatLongGrid']]:
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
        if self.config[cnf.ABSORBANCE_SRC] == cnf.ABS_SRC_MULTILAYER:
            for time in self.grids:
                iterators = []
                pressures = []
                for grid in time:
                    iterators.append(grid.__iter__())
                    pressures.append(grid.get_pressure())
                pressures.pop(0)

                # merges terms in each iterator into a Tuple; returns
                # single iterator over Tuples
                cell_iterator = zip(*iterators)

                # replace dummy array below with pressures later!
                layer_dims = pressures_to_layer_dimensions(pressures)

                for layered_cell in cell_iterator:
                    new_temps = self.calculate_layered_cell_temperature(init_co2,
                                                                        new_co2,
                                                                        pressures,
                                                                        layer_dims,
                                                                        layered_cell)
                    for cell_num in range(len(layered_cell)):
                        layered_cell[cell_num].set_temperature(new_temps[cell_num])
                print("HAFAL")
                return self.grids

        else:
            counter = 1
            for grid in self.grids:
                place = "th" if (not 1 <= counter % 10 <= 3) \
                                and (not 10 < counter < 20) \
                    else "st" if counter % 10 == 1 \
                    else "nd" if counter % 10 == 2 \
                    else "rd"
                report = "Preparing model run on {}{} grid".format(counter, place)
                self.output_controller.submit_output(out_cnf.Debug.PRINT_NOTICES, report)

                if self.config[cnf.ABSORBANCE_SRC] == cnf.ABS_SRC_TABLE:
                    for cell in grid:
                        new_temp = self.calculate_arr_cell_temperature(init_co2,
                                                                       new_co2,
                                                                       cell)
                        cell.set_temperature(new_temp)

                elif self.config[cnf.ABSORBANCE_SRC] == cnf.ABS_SRC_MODERN:
                    for cell in grid:
                        new_temp = self.calculate_modern_cell_temperature(init_co2,
                                                                          new_co2,
                                                                          cell)
                        cell.set_temperature(new_temp)

                counter += 1

        # # Average values over each latitude band after the model run.
        # if self.config[cnf.AGGREGATE_LAT] == cnf.AGGREGATE_AFTER:
        #     self.grids = [grid.latitude_bands() for grid in self.grids]
        #
        # self.print_statistic_tables()
        #
        # # Finally, write model output to disk.
        # out_cnf.global_output_center().submit_collection_output(
        #     out_cnf.PRIMARY_OUTPUT_PATH,
        #     self.grids,
        #     self.config[cnf.RUN_ID]
        # )

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

    def calculate_layered_cell_temperature(self, init_co2: float,
                                           new_co2: float,
                                           pressures: List['float'],
                                           layer_dims: List[List[float]],
                                           layers: Tuple['GridCell']) -> List[float]:
        init_temps = [layers[0].get_temperature() + 273.15]
        init_transparencies = [1]

        for layer_num in range(len(layers) - 1):
            init_temps.append(layers[layer_num + 1].get_temperature() + 273.15)
            relative_humidity = layers[layer_num + 1].get_relative_humidity()
            transparency = calculate_modern_transparency(init_co2,
                                                         init_temps[layer_num + 1],
                                                         relative_humidity,
                                                         layer_dims[layer_num][0],
                                                         layer_dims[layer_num][1],
                                                         pressures[layer_num])
            init_transparencies.append(transparency)
        init_matrix = ml.build_multilayer_matrix(np.array(init_transparencies))
        coefficients = ml.calibrate_multilayer_matrix(init_matrix,
                                                      np.array(init_temps))
        mid_transparencies = [1]
        for layer_num in range(len(layers) - 1):
            relative_humidity = layers[layer_num + 1].get_relative_humidity()
            transparency = calculate_modern_transparency(new_co2,
                                                         init_temps[layer_num + 1],
                                                         relative_humidity,
                                                         layer_dims[layer_num][0],
                                                         layer_dims[layer_num][1],
                                                         pressures[layer_num])
            mid_transparencies.append(transparency)
        mid_matrix = ml.build_multilayer_matrix(np.array(mid_transparencies))
        mid_temps = ml.solve_multilayer_matrix(mid_matrix, coefficients)

        final_transparencies = [1]
        for layer_num in range(len(layers) - 1):
            relative_humidity = layers[layer_num + 1].get_relative_humidity()
            transparency = calculate_modern_transparency(new_co2,
                                                         mid_temps[layer_num + 1],
                                                         relative_humidity,
                                                         layer_dims[layer_num][0],
                                                         layer_dims[layer_num][1],
                                                         pressures[layer_num])
            final_transparencies.append(transparency)
        final_matrix = ml.build_multilayer_matrix(np.array(final_transparencies))
        final_temps = ml.solve_multilayer_matrix(final_matrix, coefficients)

        return final_temps - 273.15


def pressures_to_layer_dimensions(pressures: List[float]) -> List[List[float]]:
    """
    Converts a list of atmospheric pressures into a list of layer dimensions.
    Each entry at index i in the list holds a list of two dimensions for an
    atmospheric layer corresponding to the atmospheric pressure in index i of
    parameter list. These 2 dimensions are:
    -  the elevation/height of the top boundary of the layer (index 0)
    -  the thickness/depth of the layer (index 1)

    Uses the hypsometric equation to calculate elevation from atmospheric
    pressure.

    :param pressures:
        A list of atmospheric pressures. Should be sorted in descending order.
    :return:
        A list of elevation and depth for each atmospheric pressure layer.
    """
    layer_dimensions = [[0.0, 0.0]]
    for num in range(len(pressures)):
        # convert millibars to Pascals
        pressures[num] *= 100
        if pressures[num] > 0.0:
            elevation = (-287.053 * 288.15 / 9.80665) * math.log(pressures[num] / 101325) / 1000.0
            # adding layer_dimensions of index num + 1
            # so previous layer dims are at index num
            depth = elevation - layer_dimensions[num][0]
            layer_dimensions.append([elevation, depth])
        else:
            layer_dimensions.append([0.0, 0.0])

    return layer_dimensions[1:]


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
    title = "multilayer_1"
    grid = GridDimensions((4, 4), "count")
    conf = cnf.default_config()
    conf[cnf.RUN_ID] = title
    conf[cnf.AGGREGATE_LAT] = cnf.AGGREGATE_NONE
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
    grids = model.run_model(1, 2)

    write_model_output(grids[0], title)
