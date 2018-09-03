from data.grid import LatLongGrid, GridCell,\
    extract_multidimensional_grid_variable
from data.collector import ClimateDataCollector
from data.display import write_model_output
from data.statistics import convert_grid_data_to_table, print_tables,\
    mean, std_dev, variance, X2_EXPECTED

from core.cell_operations import calculate_transparency,\
    calculate_modern_transparency
import core.configuration as cnf
import core.output_config as out_cnf

import core.multilayer as ml
import numpy as np
import math

from typing import Optional, Union, List, Tuple
from sys import argv
from getopt import getopt, GetoptError

ATMOSPHERE_HEIGHT = 50.0


GriddedData = Union[LatLongGrid, List]


class ModelRun:
    """
    A class that is used to run the Arrhenius climate model on the given
    grids of data.
    This object will run the model with the provided configurations
    and output controls.
    """

    def __init__(self: 'ModelRun',
                 config: 'ArrheniusConfig',
                 output_controller: 'OutputController') -> None:
        """
        Initialize model configuration options to prepare for model runs.

        :param config:
            A dictionary containing configuration options for the model
        :param output_controller:
            An object that controls which types of outputs are allowed
        """
        self.config = config
        self.output_controller = output_controller

        self.output_controller.register_collection(out_cnf.PRIMARY_OUTPUT,
                                                   handler=write_model_output)

        self.collector = ClimateDataCollector(config.grid()) \
            .use_temperature_source(config.temp_provider()) \
            .use_humidity_source(config.humidity_provider()) \
            .use_albedo_source(config.albedo_provider())

        try:
            self.collector.use_pressure_source(config.pressure_provider())
        except AttributeError:
            pass

    def run_model(self: 'ModelRun',
                  expected: Optional[np.ndarray] = None) -> GriddedData:
        """
        Calculate Earth's surface temperature change due to a change in
        CO2 levels given in the model runner's configuration.

        Returns a list of grids, each of which represents the state of the
        Earth's surface over a range of time. The grids contain data produced
        from the model run.

        :param expected:
            An array of expected temperature change values in table format
        :return:
            The state of the Earth's surface based on the model's calculations
        """
        cnf.set_configuration(self.config)
        out_cnf.set_output_center(self.output_controller)

        year_of_interest = self.config.year()
        self.grids = self.collector.get_gridded_data(year_of_interest)

        init_co2 = self.config.init_co2()
        final_co2 = self.config.final_co2()
        iterations = self.config.iterations()

        # Average values over each latitude band before the model run.
        if self.config.aggregate_latitude() == cnf.AGGREGATE_BEFORE:
            self.grids = multigrid_latitude_bands(self.grids)

        # Run the body of the model, calculating temperature changes for each
        # cell in the grid.
        counter = 1
        for time_seg in self.grids:
            place = "th" if (not 1 <= counter % 10 <= 3) \
                            and (not 10 < counter < 20) \
                else "st" if counter % 10 == 1 \
                else "nd" if counter % 10 == 2 \
                else "rd"
            report = "Preparing model run on {}{} grid".format(counter, place)
            self.output_controller.submit_output(out_cnf.Debug.PRINT_NOTICES, report)

            if self.config.model_mode() == cnf.ABS_SRC_MULTILAYER:
                self.compute_multilayer(time_seg, init_co2,
                                        final_co2, iterations)

            else:
                self.compute_single_layer(time_seg[0], init_co2,
                                          final_co2, iterations)

            counter += 1

        # Average values over each latitude band after the model run.
        if self.config.aggregate_latitude() == cnf.AGGREGATE_AFTER:
            self.grids = multigrid_latitude_bands(self.grids)

        ground_layer = [time_seg[0] for time_seg in self.grids]

        print_solo_statistics(ground_layer)
        if expected is not None:
            print_relation_statistics(ground_layer, expected)

        # Finally, write model output to disk.
        out_cnf.global_output_center().submit_collection_output(
            out_cnf.PRIMARY_OUTPUT_PATH,
            ground_layer
        )

        return self.grids

    def compute_single_layer(self: 'ModelRun',
                             grid: 'LatLongGrid',
                             init_co2: float,
                             final_co2: float,
                             iterations: int = 1) -> None:
        """
        Perform a series of model calculations on the surface data in grid,
        computing temperature difference after changing from init_co2 to
        final_co2 atmospheric carbon dioxide concentrations. Both these
        concentrations are multipliers of the atmosphere that was modern to
        the gridded data provided.

        Values of init_co2 other than 1 are not supported.

        The recalculation is sensitive to configuration options, and will
        choose whichever transparency data mode was specified therein.

        Changes are recorded by updating the temperature values for each cell
        in the grid, and nothing is returned.

        :param grid:
            A single layer of gridded data containing temperature, humidity,
            and surface albedo
        :param init_co2:
            A multiplier of atmospheric CO2 concentration for initial state
        :param final_co2:
            A multiplier of atmospheric CO2 concentration for final state
        :param iterations:
            The number of feedback loop calculated for the effects between
            humidity and atmospheric temperatures
        """
        if self.config.model_mode() == cnf.ABS_SRC_TABLE:
            temp_recalculator = self.calculate_arr_cell_temperature
        elif self.config.model_mode() == cnf.ABS_SRC_MODERN:
            temp_recalculator = self.calculate_modern_cell_temperature
        else:
            raise ValueError("Unsupported temperature function for model mode"
                             "{}: {}".format(self.config.model_mode(),
                                             self.config.temp_provider()))

        for cell in grid:
            new_temp = temp_recalculator(init_co2, final_co2, cell, iterations)
            cell.set_temperature(new_temp)

    def compute_multilayer(self: 'ModelRun',
                           grid_column: List['LatLongGrid'],
                           init_co2: float,
                           final_co2: float,
                           iterations: int = 1) -> None:
        """
        Perform a series of model calculations on a list of multiple ground
        and atmospheric layers inside grid_column, computing temperature
        difference for all layers after changing from init_co2 to final_co2
        atmospheric carbon dioxide concentrations. Both these concentrations
        are multipliers of the atmosphere that was modern to the gridded data
        provided.

        As the surface counts as a layer on its own, even a one-layer
        atmosphere requires a list of two grids: one for surface, one for the
        atmosphere. In general, an n-layer atmosphere requires n+1 grids. The
        first index must be the surface grid, the second index the first
        atmospheric layer, and so on.

        The surface layer grid can omit humidity and pressure values;
        atmospheric grids may omit albedo values.

        Changes are recorded by updating the temperature values for each cell
        in the grid, and nothing is returned.

        :param grid_column:
            A list of surface and atmosphere data grids, in order of height
        :param init_co2:
            A multiplier of atmospheric CO2 concentration for initial state
        :param final_co2:
            A multiplier of atmospheric CO2 concentration for final state
        :param iterations:
            The number of feedback loop calculated for the effects between
            humidity and atmospheric temperatures
        """
        iterators = []
        pressures = []
        for grid in grid_column:
            iterators.append(grid.__iter__())
            pressures.append(grid.get_pressure())
        # Remove first element in the pressure list, as the surface has
        # no defined pressure.
        pressures.pop(0)

        # Prepare an iterator over a whole atmospheric column of grid cells.
        cell_iterator = zip(*iterators)

        layer_dims = pressures_to_layer_dimensions(pressures)

        for atm_column in cell_iterator:
            new_temps = self.calculate_layered_cell_temperature(init_co2,
                                                                final_co2,
                                                                pressures,
                                                                layer_dims,
                                                                atm_column,
                                                                iterations)
            for cell_num in range(len(atm_column)):
                atm_column[cell_num].set_temperature(new_temps[cell_num])

    def calculate_arr_cell_temperature(self: 'ModelRun',
                                       init_co2: float,
                                       new_co2: float,
                                       grid_cell: 'GridCell',
                                       iterations: int) -> float:
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
        :param iterations:
            The number of feedback loop calculated for the effects between
            humidity and atmospheric temperatures
        :return:
            The change in surface temperature for the provided grid cell
            after the given change in CO2
        """
        co2_weight_func, h2o_weight_func = self.config.table_auxiliaries()

        temperature = grid_cell.get_temperature() + 273.15
        init_temperature = temperature
        relative_humidity = grid_cell.get_relative_humidity()
        albedo = grid_cell.get_albedo()

        transparency = calculate_transparency(init_co2,
                                              temperature,
                                              relative_humidity,
                                              co2_weight_func,
                                              h2o_weight_func)
        k = calibrate_constant(init_temperature, albedo, transparency)

        for i in range(iterations + 1):
            transparency = calculate_transparency(new_co2,
                                                  temperature,
                                                  relative_humidity,
                                                  co2_weight_func,
                                                  h2o_weight_func)
            temperature = get_new_temperature(albedo, transparency, k)

        delta_temp_report = "{}  ~~~~  Delta T: {} K" \
            .format(grid_cell, temperature - init_temperature)
        delta_trans_report = "{}  ~~~~  Delta Transparency: {} K" \
            .format(grid_cell, temperature - init_temperature)
        self.output_controller.submit_output(out_cnf.Debug.GRID_CELL_DELTA_TEMP,
                                             delta_temp_report)
        self.output_controller.submit_output(out_cnf.Debug.GRID_CELL_DELTA_TRANSPARENCY,
                                             delta_trans_report)

        return temperature - 273.15

    def calculate_modern_cell_temperature(self: 'ModelRun',
                                          init_co2: float,
                                          new_co2: float,
                                          grid_cell: 'GridCell',
                                          iterations: int) -> float:
        """
        Calculate the change in temperature of a specific grid cell due to a
        change in CO2 levels in the atmosphere. Uses modern absorption data.

        :param init_co2:
            The initial amount of CO2 in the atmosphere
        :param new_co2:
            The new amount of CO2 in the atmosphere
        :param grid_cell:
            A GridCell object containing average temperature and
            relative humidity
        :param iterations:
            The number of feedback loop calculated for the effects between
            humidity and atmospheric temperatures
        :return:
            The change in surface temperature for the provided grid cell
            after the given change in CO2
        """
        init_temperature = grid_cell.get_temperature() + 273.15
        temperature = init_temperature
        relative_humidity = grid_cell.get_relative_humidity()
        albedo = grid_cell.get_albedo()

        transparency = calculate_modern_transparency(init_co2,
                                                     temperature,
                                                     relative_humidity,
                                                     ATMOSPHERE_HEIGHT / 2,
                                                     ATMOSPHERE_HEIGHT)
        k = calibrate_constant(temperature, albedo, transparency)

        for i in range(iterations + 1):
            transparency = calculate_modern_transparency(new_co2,
                                                         temperature,
                                                         relative_humidity,
                                                         ATMOSPHERE_HEIGHT / 2,
                                                         ATMOSPHERE_HEIGHT)
            temperature = get_new_temperature(albedo, transparency, k)

        delta_temp_report = "{}  ~~~~  Delta T: {} K" \
            .format(grid_cell, temperature - init_temperature)
        delta_trans_report = "{}  ~~~~  Delta Transparency: {} K" \
            .format(grid_cell, temperature - init_temperature)
        self.output_controller.submit_output(out_cnf.Debug.GRID_CELL_DELTA_TEMP,
                                             delta_temp_report)
        self.output_controller.submit_output(out_cnf.Debug.GRID_CELL_DELTA_TRANSPARENCY,
                                             delta_trans_report)
        return temperature - 273.15

    def calculate_layered_cell_temperature(self: 'ModelRun',
                                           init_co2: float,
                                           new_co2: float,
                                           pressures: List['float'],
                                           layer_dims: List[List[float]],
                                           layers: Tuple['GridCell'],
                                           iterations: int) -> List[float]:
        """
        Calculate the change in temperature in all of a column of grid cells
        in a multi-layer atmosphere due to a change in CO2 concentration. Uses
        modern absorption and atmospheric data.

        :param init_co2:
            The initial amount of CO2 in the atmosphere
        :param new_co2:
            The new amount of CO2 in the atmosphere
        :param pressures:
            A column of pressures at increasing heights in the atmosphere
        :param layer_dims:
            A vector of 2-tuples, containing the bottom altitude and the
            thickness of each atmospheric layer
        :param layers:
            A column of GridCell objects for ground and atmospheric layers,
            in increasing order of height
        :param iterations:
            The number of feedback loop calculated for the effects between
            humidity and atmospheric temperatures
        :return:
            A vector of temperature changes caused by the change in CO2,
            parallel with the grid cells in the atmospheric column
        """
        surface_cell = layers[0]
        temperatures = [surface_cell.get_temperature() + 273.15]
        init_temperature = temperatures[0]
        transparencies = [surface_cell.get_albedo()]

        for layer_num in range(len(layers) - 1):
            temperatures.append(layers[layer_num + 1].get_temperature() + 273.15)
            relative_humidity = layers[layer_num + 1].get_relative_humidity()
            transparency = calculate_modern_transparency(init_co2,
                                                         temperatures[layer_num + 1],
                                                         relative_humidity,
                                                         layer_dims[layer_num][0],
                                                         layer_dims[layer_num][1],
                                                         pressures[layer_num])
            transparencies.append(transparency)
        init_transparency = transparencies[1]

        atm_matrix = ml.build_multilayer_matrix(np.array(transparencies))
        coefficients = ml.calibrate_multilayer_matrix(atm_matrix,
                                                      np.array(temperatures))

        for i in range(iterations + 1):
            transparencies = [surface_cell.get_albedo()]
            for layer_num in range(len(layers) - 1):
                relative_humidity = layers[layer_num + 1].get_relative_humidity()
                transparency = calculate_modern_transparency(new_co2,
                                                             temperatures[layer_num + 1],
                                                             relative_humidity,
                                                             layer_dims[layer_num][0],
                                                             layer_dims[layer_num][1],
                                                             pressures[layer_num])
                transparencies.append(transparency)
            atm_matrix = ml.build_multilayer_matrix(np.array(transparencies))
            temperatures = ml.solve_multilayer_matrix(atm_matrix, coefficients)

        delta_temp_report = "{}  ~~~~  Delta T: {} K" \
            .format(layers[0], temperatures[0] - init_temperature)
        delta_trans_report = "{}  ~~~~  Delta Transparency: {} K" \
            .format(layers[1], transparencies[1] - init_transparency)
        self.output_controller.submit_output(out_cnf.Debug.GRID_CELL_DELTA_TEMP,
                                             delta_temp_report)
        self.output_controller.submit_output(out_cnf.Debug.GRID_CELL_DELTA_TRANSPARENCY,
                                             delta_trans_report)

        return temperatures - 273.15


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


def multigrid_latitude_bands(grids: GriddedData) -> GriddedData:
    """
    Returns a nested list of grid objects, arranged in the same way as
    the parameter grids, except with each grid's values averaged over
    each latitude band. That is, each grid in the nested list returned
    has cells 180 degrees of latitude wide.

    :param grids:
        A nested list of grids.
    :return:
        A parallel nested list of grids averaged by latitude bands
    """
    if isinstance(grids, LatLongGrid):
        return grids.latitude_bands()
    else:
        compressed_grids = []

        for subarray in grids:
            compressed_grids.append(multigrid_latitude_bands(subarray))

        return compressed_grids


def print_solo_statistics(data: GriddedData) -> None:
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
        extract_multidimensional_grid_variable(data, temp_name)
    temp_table = convert_grid_data_to_table(temp_data)

    output_center.submit_output(out_cnf.ReportDatatype.REPORT_TEMP,
                                temp_table)

    delta_temp_data = \
        extract_multidimensional_grid_variable(data, delta_t_name)
    delta_temp_table = convert_grid_data_to_table(delta_temp_data)

    # Print tables of data.
    output_center.submit_output(
        out_cnf.ReportDatatype.REPORT_TEMP_CHANGE,
        delta_temp_table
    )


def print_relation_statistics(data: GriddedData,
                              expected: np.ndarray) -> None:
    """
    Print a series of tables and statistics based on the relation between
    model run results, given by data, and an array of expected results for
    temperature change, given by the parameter expected.

    The expected results must have dimensions appropriate to the model data
    in table format. Table format reduces the number of dimensions of the data
    by one, by aggregating latitude bands. Otherwise, the dimensions of the
    data remain in the same order (time, level, longitude).

    :param data:
        A nested list of model run results
    :param expected:
        An array of expected temperature change values for the model run
    """
    delta_t_name = out_cnf.ReportDatatype.REPORT_TEMP_CHANGE.value
    delta_temp_data = \
        extract_multidimensional_grid_variable(data, delta_t_name)
    delta_temp_table = convert_grid_data_to_table(delta_temp_data)

    output_center = out_cnf.global_output_center()
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

    output_center.submit_output(
        out_cnf.AccuracyMetrics.TEMP_DELTA_VARIANCE,
        variance(diff)
    )


if __name__ == '__main__':
    if len(argv) > 1:
        try:
            # Command-line arguments must consist of a -c followed by the
            # JSON filename containing configuration options.
            options, args = getopt(argv[1:], "c:")
            options_map = {op[0]: op[1] for op in options}

            # Parse config options from file.
            json_filepath = options_map["-c"]

            with open(json_filepath, "r") as json_file:
                conf = cnf.from_json_string(json_file.read())
        except (KeyError, GetoptError):
            # Only catch errors resulting from improper argument passing:
            # Invalid config errors should propagate.
            print("Usage: python runner.py -c <config_file>")
            exit(1)

    else:
        # If no arguments are given, use default config.
        conf = cnf.default_config()

    title = "arrhenius_x2"
    conf.set_run_id(title)
    conf.set_aggregations(agg_lat=cnf.AGGREGATE_NONE)
    conf.set_table_auxiliaries(cnf.WEIGHT_BY_PROXIMITY,
                               cnf.WEIGHT_BY_PROXIMITY)

    out_cont = out_cnf.development_output_config()

    out_cont.enable_output_type(
        out_cnf.ReportDatatype.REPORT_TEMP_CHANGE,
        handler=print_tables
    )

    out_cont.enable_output_type(out_cnf.AccuracyMetrics.TEMP_DELTA_AVG_DEVIATION)
    out_cont.enable_output_type(out_cnf.AccuracyMetrics.TEMP_DELTA_STD_DEVIATION)
    out_cont.enable_output_type(out_cnf.AccuracyMetrics.TEMP_DELTA_VARIANCE)

    model = ModelRun(conf, out_cont)
    grids = model.run_model(X2_EXPECTED)
