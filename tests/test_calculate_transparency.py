import unittest
from core.cell_operations import calculate_transparency

class TestCalculateTransparency(unittest.TestCase):

    def test_same_output_input(self):
        """
        Test that the same input yields the same input
        """
        self.assertTrue(calculate_transparency(1.0, 279.15, 70) == calculate_transparency(1.0, 279.15, 70))
        self.assertTrue(calculate_transparency(.2, 279.15, 70) == calculate_transparency(.2, 279.15, 70))
        self.assertTrue(calculate_transparency(1.0, 290.15, 70) == calculate_transparency(1.0, 290.15, 70))
        self.assertTrue(calculate_transparency(1.0, 279.15, 43) == calculate_transparency(1.0, 279.15, 43))

    def test_bounds(self):
        """
        Test that an AttributeError is raised when the bounds of this function.
        """
        self.assertRaises(AttributeError, calculate_transparency(-1, 273.15, 77))
        self.assertRaises(AttributeError, calculate_transparency(1, -1, 77))
        self.assertRaises(AttributeError, calculate_transparency(1, 280, -10))
        self.assertRaises(AttributeError, calculate_transparency(1, 280, 114))

    def test_correct_output(self):
        """
        Test that the function gives the right output
        """
        self.assertEqual(calculate_transparency(1, 293.15, 78), .199)
        self.assertEqual(calculate_transparency(3.5, 278.15, 40), .109)

