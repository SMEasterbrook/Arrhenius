import unittest
from core.cell_operations import calculate_water_vapor

class TestCalculateWaterVapor(unittest.TestCase):

    def test_same_output_input(self):
        # low temp
        self.assertEqual(calculate_water_vapor(-262.15, 50),
                         calculate_water_vapor(-262.15, 50))
        # boundary humidity
        self.assertEqual(calculate_water_vapor(278.15, 0),
                         calculate_water_vapor(278.15, 0))
        # regular temp and humidity
        self.assertEqual(calculate_water_vapor(285.15, 40),
                         calculate_water_vapor(285.15, 40))
        self.assertEqual(calculate_water_vapor(295.15, 80),
                         calculate_water_vapor(295.15, 80))
        #boundary humidity
        self.assertEqual(calculate_water_vapor(295.15, 100),
                         calculate_water_vapor(295.15, 100))


    def test_out_of_bounds(self):
        # test negative temperature
        self.assertRaises(AttributeError, calculate_water_vapor, -5, 10)
        self.assertRaises(AttributeError, calculate_water_vapor, -10, 0)
        self.assertRaises(AttributeError, calculate_water_vapor, -15, 100)
        # test negative humidity
        self.assertRaises(AttributeError, calculate_water_vapor, 273.15, -10)
        # test relative humidity > 100
        self.assertRaises(AttributeError, calculate_water_vapor, 290.15, 105)

    def test_correct_output(self):
        DEVIATION_FRACTION = .1
        # test 0 humidity
        self.assertEqual(calculate_water_vapor(257.15, 0), 0)
        self.assertTrue(calculate_water_vapor(273.15, 0), 0)
        self.assertTrue(calculate_water_vapor(285.15, 0), 0)
        self.assertTrue(calculate_water_vapor(297.15, 0), 0)
        # low temperature, different humidities
        result = calculate_water_vapor(266.15, 10)
        self.assertTrue(abs(result - .03) <= DEVIATION_FRACTION * .03)
        result = calculate_water_vapor(263.15, 40)
        self.assertTrue(abs(result - .095) <= DEVIATION_FRACTION * .095)
        result = calculate_water_vapor(258.15, 75)
        self.assertTrue(abs(result - .121) <= DEVIATION_FRACTION * .121)
        result = calculate_water_vapor(250.15, 95)
        self.assertTrue(abs(result - .08) <= DEVIATION_FRACTION * .08)
        # test zero Celcius temperatures
        result = calculate_water_vapor(273.15, 10)
        self.assertTrue(abs(result - .048) <= DEVIATION_FRACTION * .048)
        result = calculate_water_vapor(273.15, 40)
        self.assertTrue(abs(result - .194) <= DEVIATION_FRACTION * .194)
        result = calculate_water_vapor(273.15, 75)
        self.assertTrue(abs(result - .364) <= DEVIATION_FRACTION * .364)
        result = calculate_water_vapor(273.15, 95)
        self.assertTrue(abs(result - .461) <= DEVIATION_FRACTION * .461)
        # test above zero Celcius temperature
        result = calculate_water_vapor(278.15, 10)
        self.assertTrue(abs(result - .068) <= DEVIATION_FRACTION * .068)
        result = calculate_water_vapor(297.15, 40)
        self.assertTrue(abs(result - .868) <= DEVIATION_FRACTION * .868)
        result = calculate_water_vapor(284.15, 75)
        self.assertTrue(abs(result - .75) <= DEVIATION_FRACTION * .75)
        result = calculate_water_vapor(291.15, 95)
        self.assertTrue(abs(result - 1.456) <= DEVIATION_FRACTION * 1.456)
        # test humidity = 100
        result = calculate_water_vapor(250.15, 100)
        self.assertTrue(abs(result - .084) <= DEVIATION_FRACTION * .084)
        result = calculate_water_vapor(268.15, 100)
        self.assertTrue(abs(result - .341) <= DEVIATION_FRACTION * .341)
        result = calculate_water_vapor(282.15, 100)
        self.assertTrue(abs(result - .88) <= DEVIATION_FRACTION * .88)
        result = calculate_water_vapor(289.15, 100)
        self.assertTrue(abs(result - 1.36) <= DEVIATION_FRACTION * 1.36)
        result = calculate_water_vapor(294.15, 100)
        self.assertTrue(abs(result - 1.828) <= DEVIATION_FRACTION * 1.828)
