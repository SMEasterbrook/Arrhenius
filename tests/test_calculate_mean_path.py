import unittest

from core.cell_operations import calculate_mean_path

class TestResults(unittest.TestCase):
    def test_same_output_input(self):
        """
        Test that the same input yields the same output
        """
        self.assertEqual(calculate_mean_path(1, 1), calculate_mean_path(1, 1))
        self.assertEqual(calculate_mean_path(.67, 3), calculate_mean_path(.67, 3))

    def test_out_of_bounds(self):
        """
        Test that if the given co2 or water vapor values are under 0, an error
        is raised
        """
        self.assertRaises(AttributeError, calculate_mean_path(-1, 2))
        self.assertRaises(AttributeError, calculate_mean_path(1, -.5))
        self.assertRaises(AttributeError, calculate_mean_path(1.25, 1.0))

    def test_correct_output(self):
        # test values below lowest table boundary
        self.assertEqual(calculate_mean_path(.67, .2), 1.69)
        self.assertEqual(calculate_mean_path(1, .1), 1.66)
        # test values above table boundaries
        self.assertEqual(calculate_mean_path(3.0, 3.0), 1.4)
        self.assertEqual(calculate_mean_path(3.5, 2.3), 1.42)
        # test values in middle that match Dict values
        self.assertEqual(calculate_mean_path(1.5, 2.0), 1.51)
        self.assertEqual(calculate_mean_path(.67, .3), 1.69)
        self.assertEqual(calculate_mean_path(3.5, 2.0), 1.42)
        self.assertEqual(calculate_mean_path(2.5, .3), 1.56)
        self.assertEqual(calculate_mean_path(1.5, 3.0), 1.47)
        # test h2o values that don't match Dict values
        self.assertEqual(calculate_mean_path(1.5, 1.5), 1.57)
        self.assertEqual(calculate_mean_path(3.5, 1.75), 1.42)
        self.assertEqual(calculate_mean_path(1.5, .35), 1.62)
