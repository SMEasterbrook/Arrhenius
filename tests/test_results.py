import unittest

from core.runner import ModelRunner
from data.grid import GridDimensions
from data.collector import ClimateDataCollector
import data.provider as pr
import tests.helpers as h
import data.configuration as cnf
X067_EXPECTED = [[nan, nan, nan, nan],
                 [nan, nan, nan, nan],
                 [nan, nan, nan, nan],
                 [-3.2, -3.3, nan, nan],
                 [-3.4, -3.4, -3.3, -3.4],
                 [-3.3, -3.3, -3.4, -3.4],
                 [-3.1, -3.2, -3.3, -3.2],
                 [-3.1, -3.1, -3.2, -3.1],
                 [-3.0, -3.0, -3.1, -3.0],
                 [-3.1, -3.0, -3.0, -3.0],
                 [-3.1, -3.1, -3.0, -3.1],
                 [-3.3, -3.2, -3.1, -3.1],
                 [-3.4, -3.4, -3.2, -3.3],
                 [-3.2, -3.3, -3.3, -3.4],
                 [-3.0, -3.2, -3.4, -3.3],
                 [-2.9, -3.0, -3.4, -3.1],
                 [nan, nan, nan, nan],
                 [nan, nan, nan, nan]]


X1_EXPECTED = [nan, nan, nan, nan] * 3\
    + [0, 0, nan, nan]\
    + [[0] * 4] * 12\
    + [nan, nan, nan, nan] * 2


X15_EXPECTED = [[nan, nan, nan, nan],
                [nan, nan, nan, nan],
                [nan, nan, nan, nan],
                [3.8, 3.7, nan, nan],
                [3.6, 3.7, 3.8, 3.7],
                [3.4, 3.5, 3.7, 3.5],
                [3.2, 3.2, 3.4, 3.3],
                [3.2, 3.2, 3.2, 3.2],
                [3.1, 3.1, 3.2, 3.2],
                [3.2, 3.2, 3.1, 3.1],
                [3.5, 3.2, 3.1, 3.2],
                [3.5, 3.3, 3.2, 3.5],
                [3.7, 3.6, 3.3, 3.5],
                [3.7, 3.8, 3.4, 3.7],
                [3.4, 3.7, 3.6, 3.8],
                [3.3, 3.4, 3.8, 3.6],
                [nan, nan, nan, nan],
                [nan, nan, nan, nan]]


X2_EXPECTED = [[nan, nan, nan, nan],
               [nan, nan, nan, nan],
               [nan, nan, nan, nan],
               [6.0, 6.1, nan, nan],
               [5.8, 6.0, 6.0, 6.0],
               [5.5, 5.6, 5.8, 5.6],
               [5.2, 5.3, 5.5, 5.4],
               [5.0, 5.0, 5.2, 5.1],
               [4.9, 4.9, 5.0, 5.0],
               [5.0, 5.0, 4.9, 4.9],
               [5.2, 5.0, 4.9, 5.0],
               [5.6, 5.4, 5.0, 5.2],
               [6.0, 5.8, 5.4, 5.6],
               [6.1, 6.1, 5.5, 6.0],
               [6.1, 6.1, 5.8, 6.1],
               [6.0, 6.1, 6.0, 6.1],
               [nan, nan, nan, nan],
               [nan, nan, nan, nan]]


X25_EXPECTED = [[nan, nan, nan, nan],
                [nan, nan, nan, nan],
                [nan, nan, nan, nan],
                [7.9, 8.0, nan, nan],
                [7.7, 7.9, 7.9, 7.9],
                [7.0, 7.2, 7.7, 7.4],
                [6.7, 6.8, 7.0, 7.0],
                [6.6, 6.6, 6.7, 6.7],
                [6.4, 6.4, 6.6, 6.6],
                [6.6, 6.4, 6.3, 6.4],
                [6.7, 6.6, 6.3, 6.6],
                [7.2, 7.0, 6.6, 6.7],
                [7.9, 7.6, 6.9, 7.3],
                [8.0, 7.9, 7.0, 7.9],
                [8.0, 8.0, 7.6, 7.8],
                [7.9, 8.0, 7.9, 8.0],
                [nan, nan, nan, nan],
                [nan, nan, nan, nan]]


X3_EXPECTED = [[nan, nan, nan, nan],
               [nan, nan, nan, nan],
               [nan, nan, nan, nan],
               [9.4, 9.5, nan, nan],
               [9.1, 9.2, 9.4, 9.3],
               [8.6, 8.7, 9.1, 8.8],
               [7.9, 8.1, 8.6, 8.3],
               [7.4, 7.5, 8.0, 7.6],
               [7.3, 7.3, 7.4, 7.4],
               [7.4, 7.3, 7.2, 7.3],
               [7.9, 7.5, 7.2, 7.5],
               [8.7, 8.3, 7.5, 7.9],
               [9.3, 9.0, 8.2, 8.8],
               [9.5, 9.4, 8.6, 8.8],
               [9.3, 9.5, 8.9, 9.5],
               [9.1, 9.3, 9.4, 9.4],
               [nan, nan, nan, nan],
               [nan, nan, nan, nan]]

MEAN_ERROR = 1.0
STD_ERROR = .5

class TestResults(unittest.TestCase):

    def test_same_output_input(self):
        """
        Test that running the model with the same inputs yields
        the same outputs.
        """
        # test co2 increase
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

        grid_cells_2 = ClimateDataCollector(grid_dims) \
            .use_temperature_source(pr.arrhenius_temperature_data) \
            .use_humidity_source(pr.arrhenius_humidity_data) \
            .use_albedo_source(pr.landmask_albedo_data) \
            .get_gridded_data()
        conf = cnf.DEFAULT_CONFIG
        conf[cnf.CO2_WEIGHT] = cnf.WEIGHT_BY_PROXIMITY
        conf[cnf.H2O_WEIGHT] = cnf.WEIGHT_BY_PROXIMITY

        original_model_2 = ModelRunner(conf, conf, grid_cells_2)
        original_model_2.run_model(1, 2)
        self.assertEqual(original_model.grids, original_model_2.grids)

        # test co2 decrease
        grid_cells = ClimateDataCollector(grid_dims) \
            .use_temperature_source(pr.arrhenius_temperature_data) \
            .use_humidity_source(pr.arrhenius_humidity_data) \
            .use_albedo_source(pr.landmask_albedo_data) \
            .get_gridded_data()
        conf = cnf.DEFAULT_CONFIG
        conf[cnf.CO2_WEIGHT] = cnf.WEIGHT_BY_PROXIMITY
        conf[cnf.H2O_WEIGHT] = cnf.WEIGHT_BY_PROXIMITY

        original_model = ModelRunner(conf, conf, grid_cells)
        original_model.run_model(1, .5)

        grid_cells_2 = ClimateDataCollector(grid_dims) \
            .use_temperature_source(pr.arrhenius_temperature_data) \
            .use_humidity_source(pr.arrhenius_humidity_data) \
            .use_albedo_source(pr.landmask_albedo_data) \
            .get_gridded_data()
        conf = cnf.DEFAULT_CONFIG
        conf[cnf.CO2_WEIGHT] = cnf.WEIGHT_BY_PROXIMITY
        conf[cnf.H2O_WEIGHT] = cnf.WEIGHT_BY_PROXIMITY
        original_model_2 = ModelRunner(conf, conf, grid_cells_2)
        original_model_2.run_model(1, .5)
        self.assertEqual(original_model.grids, original_model_2.grids)

        # test no co2 change
        grid_cells = ClimateDataCollector(grid_dims) \
            .use_temperature_source(pr.arrhenius_temperature_data) \
            .use_humidity_source(pr.arrhenius_humidity_data) \
            .use_albedo_source(pr.landmask_albedo_data) \
            .get_gridded_data()
        conf = cnf.DEFAULT_CONFIG
        conf[cnf.CO2_WEIGHT] = cnf.WEIGHT_BY_PROXIMITY
        conf[cnf.H2O_WEIGHT] = cnf.WEIGHT_BY_PROXIMITY

        original_model = ModelRunner(conf, conf, grid_cells)
        original_model.run_model(2, 2)

        grid_cells_2 = ClimateDataCollector(grid_dims) \
            .use_temperature_source(pr.arrhenius_temperature_data) \
            .use_humidity_source(pr.arrhenius_humidity_data) \
            .use_albedo_source(pr.landmask_albedo_data) \
            .get_gridded_data()
        conf = cnf.DEFAULT_CONFIG
        conf[cnf.CO2_WEIGHT] = cnf.WEIGHT_BY_PROXIMITY
        conf[cnf.H2O_WEIGHT] = cnf.WEIGHT_BY_PROXIMITY

        original_model_2 = ModelRunner(conf, conf, grid_cells_2)
        original_model_2.run_model(2, 2)
        self.assertEqual(original_model.grids, original_model_2.grids)

    def test_correct_sign(self):
        """Test that all temp changes are positive values when co2 increases,
        all temp changes are negative when co2 decreases,
        and all temp changes are 0 when co2 doesn't change.
        """
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
        grid_cells = h.convert_grids_to_table(original_model.grids)
        self.assertTrue((grid_cells > 0).all())

        grid_cells = ClimateDataCollector(grid_dims) \
            .use_temperature_source(pr.arrhenius_temperature_data) \
            .use_humidity_source(pr.arrhenius_humidity_data) \
            .use_albedo_source(pr.landmask_albedo_data) \
            .get_gridded_data()
        conf = cnf.DEFAULT_CONFIG
        conf[cnf.CO2_WEIGHT] = cnf.WEIGHT_BY_PROXIMITY
        conf[cnf.H2O_WEIGHT] = cnf.WEIGHT_BY_PROXIMITY

        original_model = ModelRunner(conf, conf, grid_cells)
        original_model.run_model(1, .3)
        grid_cells = h.convert_grids_to_table(original_model.grids)
        self.assertTrue((grid_cells < 0).all())

        grid_cells = ClimateDataCollector(grid_dims) \
            .use_temperature_source(pr.arrhenius_temperature_data) \
            .use_humidity_source(pr.arrhenius_humidity_data) \
            .use_albedo_source(pr.landmask_albedo_data) \
            .get_gridded_data()
        conf = cnf.DEFAULT_CONFIG
        conf[cnf.CO2_WEIGHT] = cnf.WEIGHT_BY_PROXIMITY
        conf[cnf.H2O_WEIGHT] = cnf.WEIGHT_BY_PROXIMITY

        original_model = ModelRunner(conf, conf, grid_cells)
        original_model.run_model(1, 1)
        grid_cells = h.convert_grids_to_table(original_model.grids)
        self.assertTrue((grid_cells == 0).all())

    def test_versus_original_results(self):

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
        original_model.run_model(1, .67)
        averages = h.convert_grids_to_table(original_model.grids)
        differences = abs(averages - X067_EXPECTED)
        assert abs(differences.mean) < MEAN_ERROR
        assert differences.std < STD_ERROR

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
        original_model.run_model(1, 1)
        averages = h.convert_grids_to_table(original_model.grids)
        differences = abs(averages - X1_EXPECTED)
        assert abs(differences.mean) < MEAN_ERROR
        assert differences.std < STD_ERROR

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
        original_model.run_model(1, 1.5)
        averages = h.convert_grids_to_table(original_model.grids)
        differences = abs(averages - X15_EXPECTED)
        assert abs(differences.mean) < MEAN_ERROR
        assert differences.std < STD_ERROR

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
        averages = h.convert_grids_to_table(original_model.grids)
        differences = abs(averages - X2_EXPECTED)
        assert abs(differences.mean) < MEAN_ERROR
        assert differences.std < STD_ERROR

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
        run_model(1, 2.5)
        averages = h.convert_grids_to_table(original_model.grids)
        differences = abs(averages - X25_EXPECTED)
        assert abs(differences.mean) < MEAN_ERROR
        assert differences.std < STD_ERROR

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
        original_model.run_model(1, 3)
        averages = h.convert_grids_to_table(original_model.grids)
        differences = abs(averages - X3_EXPECTED)
        assert abs(differences.mean) < MEAN_ERROR
        assert differences.std < STD_ERROR
