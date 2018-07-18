import unittest
from core.runner import ModelRunner


class TestCalculateCellTemperature(unittest.TestCase):

    def test_same_output_input(self):
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

    def test_bounds(self):
        raise NotImplementedError

    def test_correct_output(self):
        raise NotImplementedError
