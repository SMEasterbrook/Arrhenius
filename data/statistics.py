"""
A module for data processing and internal data display functions.
Provides functions that manipulate gridded data into other forms, display
grids as tables, and extract interesting statistics from gridded data such
as sample means.
"""

from typing import Tuple, Callable, Union
from math import sqrt, isnan
import numpy as np


def sum_table(table: Union[np.ndarray, int],
              modifier: Callable[[int], int] = lambda x: x)\
        -> Tuple[int, int]:
    """
    Calculate a sum of all elements in table. An optional second argument
    specifies a transformation that is performed on each element individually.

    Returns two numbers: The first is the sum over the elements, and the
    second is the number of elements considered. Any elements with value
    None or nan are not considered. If no elements in the whole table are
    valid, then 0 and 0 are returned.

    :param table:
        An array of numbers, including None and nan values
    :param modifier:
        An optional transformation to apply to each number
    :return:
        The sum of the elements in the table with the given transformation,
        and the number of elements that contributed to the sum
    """
    if isinstance(table, np.ndarray):
        total = 0
        num_valid_elems = 0

        # The sums and valid element counts in each subarray contribute
        # directly to the corresponding counts at this level.
        for subarray in table:
            sub_total, sub_valid_cells = sum_table(subarray, modifier)
            total += sub_total
            num_valid_elems += sub_valid_cells

        return total, num_valid_elems
    elif not isnan(table) and table is not None:
        # table is a single number.
        return modifier(table), 1
    else:
        # table is either None or nan, and thus invalid.
        return 0, 0


def mean(data: np.ndarray) -> float:
    """
    Returns the average value of all valid numeric elements in data.
    An element is valid if it is not None or nan.

    :param data:
        An array of numbers
    :return:
        The average amongst valid numbers
    """
    sum_cells, num_valid_cells = sum_table(data, lambda x: x)
    smpl_mean = sum_cells / num_valid_cells
    return smpl_mean


def variance(data: np.ndarray) -> float:
    """
    Returns the variance within all valid numeric elements in data.
    An element is valid if it is not None or nan.

    :param data:
        An array of numbers
    :return:
        The variance of the valid numbers
    """
    sum_sqrs, num_valid_cells = sum_table(data, lambda x: x ** 2)
    smpl_variance = sum_sqrs / num_valid_cells
    return smpl_variance


def std_dev(data: np.ndarray) -> float:
    """
    Returns the standard deviation within all valid numeric elements in data.
    An element is valid if it is not None or nan.

    :param data:
        An array of numbers
    :return:
        The standard deviation of the valid numbers
    """
    smpl_std_dev = sqrt(variance(data))
    return smpl_std_dev
