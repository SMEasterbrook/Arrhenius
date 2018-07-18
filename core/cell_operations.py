import numpy as np
from data.configuration import WeightFunc


# Constants for absolute humidity calculations
CONST_A = 4.6543
CONST_B = 1435.264
CONST_C = -64.848

# transparency calculation data
RELATIVE_INTENSITIES = np.array([3.4, 11.6, 24.8, 45.9, 84.0, 121.7, 161.0,
                                 189.0, 210.0, 210.0, 188.0, 147.0, 105.0,
                                 103.0, 99.0, 60.0, 51.0, 65.0, 62.0,
                                 43.0, 39.0])

TOTAL_INTENSITY = RELATIVE_INTENSITIES.sum()

# absorption coefficient data
CO2_COEFFICIENTS = np.array([0.0, -.0296, -.0559, -.1070, -.3412, -.2035,
                             -.2438, -.3760, -.1877, -.0931, -.0280, -.0416,
                             -.2067, -.2466, -.2571, -.1652, -.0940, -.1992,
                             -.1742, -.0188, -.0891])
WATER_VAPOR_COEFFICIENTS = np.array([-.1455, -.1105, -.0952, -.0862, -.0068,
                                     -.3114, -.2362, -.1933, -.3198, -.1576,
                                     -.1661, -.2036, -.0484, 0.0, -.0507, 0.0,
                                     -.1184, -.0628, -.1408, -.1817, -.1444])

ANGLE_CORRECTIONS = np.array([np.pi / 12, np.pi / 6,
                              np.pi / 4, np.pi / 3,
                              (5 * np.pi) / 12, np.pi / 2])

TRANSPARENCY = {
    (1.0, .3): .372, (1.0, .5): .350, (1.0, 1.0): .307, (1.0, 1.5): .269,
    (1.0, 2.0): .239, (1.0, 3.0): .193, (1.0, 4.0): .160, (1.0, 6.0): .107,
    (1.0, 10.0): .089,
    (1.2, .3): .347, (1.2, .5): .327, (1.2, 1.0): .286, (1.2, 1.5): .251,
    (1.2, 2.0): .222, (1.2, 3.0): .178, (1.2, 4.0): .147, (1.2, 6.0): .097,
    (1.2, 10.0): .080,
    (1.5, .3):  .315, (1.5, .5): .296, (1.5, 1.0): .259, (1.5, 1.5): .226,
    (1.5, 2.0): .199, (1.5, 3.0): .159, (1.5, 4.0): .130, (1.5, 6.0): .084,
    (1.5, 10.0): .069,
    (2.0, .3):  .270, (2.0, .5): .253, (2.0, 1.0): .219, (2.0, 1.5): .191,
    (2.0, 2.0): .167, (2.0, 3.0): .131, (2.0, 4.0): .105, (2.0, 6.0): .066,
    (2.0, 10.0): .053,
    (2.5, .3):  .235, (2.5, .5): .220, (2.5, 1.0): .190, (2.5, 1.5): .166,
    (2.5, 2.0): .144, (2.5, 3.0): .110, (2.5, 4.0): .087, (2.5, 6.0): .053,
    (2.5, 10.0): .042,
    (3.0, .3):  .201, (3.0, .5): .188, (3.0, 1.0): .163, (3.0, 1.5): .142,
    (3.0, 2.0): .123, (3.0, 3.0): .093, (3.0, 4.0): .074, (3.0, 6.0): .042,
    (3.0, 10.0): .033,
    (4.0, .3):  .158, (4.0, .5): .147, (4.0, 1.0): .127, (4.0, 1.5): .108,
    (4.0, 2.0): .093, (4.0, 3.0): .071, (4.0, 4.0): .056, (4.0, 6.0): .031,
    (4.0, 10.0): .020,
    (6.0, .3):  .109, (6.0, .5): .102, (6.0, 1.0): .087, (6.0, 1.5): .073,
    (6.0, 2.0): .063, (6.0, 3.0): .048, (6.0, 4.0): .037, (6.0, 6.0): .019,
    (6.0, 10.0): .0093,
    (10.0, .3):  .066, (10.0, .5): .061, (10.0, 1.0): .052, (10.0, 1.5): .043,
    (10.0, 2.0): .035, (10.0, 3.0): .024, (10.0, 4.0): .018, (10.0, 6.0): .010,
    (10.0, 10.0): .0026,
    (20.0, .3):  .029, (20.0, .5): .025, (20.0, 1.0): .022, (20.0, 1.5): .018,
    (20.0, 2.0): .015, (20.0, 3.0): .010, (20.0, 4.0): .0075,
    (20.0, 6.0): .0039, (20.0, 10.0): .0007,
    (40.0, .3):  .0088, (40.0, .5): .0081, (40.0, 1.0): .0067,
    (40.0, 1.5): .0056, (40.0, 2.0): .0046, (40.0, 3.0): .0032,
    (40.0, 4.0): .0024, (40.0, 6.0): .0012, (40.0, 10.0): .0002
}

MEAN_PATH = {
    (.67, .3): 1.69, (.67, .5): 1.68, (.67, 1.0): 1.64, (.67, 2.0): 1.57,
    (.67, 3.0): 1.53,
    (1.0, .3): 1.66, (1.0, .5): 1.65, (1.0, 1.0): 1.61, (1.0, 2.0): 1.55,
    (1.0, 3.0): 1.51,
    (1.5, .3):  1.62, (1.5, .5): 1.61, (1.5, 1.0): 1.57, (1.5, 2.0): 1.51,
    (1.5, 3.0): 1.47,
    (2.0, .3):  1.58, (2.0, .5): 1.57, (2.0, 1.0): 1.52, (2.0, 2.0): 1.46,
    (2.0, 3.0): 1.43,
    (2.5, .3):  1.56, (2.5, .5): 1.54, (2.5, 1.0): 1.50, (2.5, 2.0): 1.45,
    (2.5, 3.0): 1.41,
    (3.0, .3):  1.52, (3.0, .5): 1.51, (3.0, 1.0): 1.47, (3.0, 2.0): 1.44,
    (3.0, 3.0): 1.4,
    (3.5, .3): 1.48, (3.5, .5): 1.48, (3.5, 1.0): 1.45, (3.5, 2.0): 1.42
}


def calculate_transparency(co2: float,
                           temperature: float,
                           relative_humidity: float,
                           co2_weight_func: WeightFunc,
                           h2o_weight_func: WeightFunc) -> float:
    """
    Calculate the transparency for a grid cell with the given data.

    :param co2:
        The amount of CO2 in the atmosphere
    :param temperature:
        The average temperature of the grid cell
    :param relative_humidity:
        The relative humidity of the grid cell
    :param co2_weight_func:
        Function that determine the weights of low and high estimations
        for CO2 transparency
    :param h2o_weight_func:
        Function that determine the weights of low and high estimations
        for H2O transparency
    :return:
        The B value corresponding to a grid cell with the given conditions
    """
    h2o = calculate_water_vapor(temperature, relative_humidity)
    p = calculate_mean_path(co2, h2o)

    # find transparency percent from preprogrammed table
    keys = list(TRANSPARENCY.keys())
    lower_co2_ind = -1
    lower_h2o_ind = -1
    for i in range(len(keys)):
        if keys[i][0] < p * co2:
            lower_co2_ind = i
        if keys[i][1] < p * h2o:
            lower_h2o_ind = i

    lower_co2 = keys[max(0, lower_co2_ind)][0]
    upper_co2 = keys[min(len(keys) - 1, lower_co2_ind + 1)][0]

    lower_h2o = keys[max(0, lower_h2o_ind)][1]
    upper_h2o = keys[min(len(keys) - 1, lower_h2o_ind + 1)][1]

    lower_co2_weight, upper_co2_weight = \
        co2_weight_func(lower_co2, upper_co2, p * co2)

    lower_h2o_weight, upper_h2o_weight = \
        h2o_weight_func(lower_h2o, upper_h2o, p * h2o)

    co2_lower_h2o_lower = TRANSPARENCY.get((lower_co2, lower_h2o))
    co2_upper_h2o_lower = TRANSPARENCY.get((upper_co2, lower_h2o))
    co2_lower_h2o_upper = TRANSPARENCY.get((lower_co2, upper_h2o))
    co2_upper_h2o_upper = TRANSPARENCY.get((upper_co2, upper_h2o))

    transparency = co2_lower_h2o_lower * (lower_co2_weight * lower_h2o_weight)\
        + co2_lower_h2o_upper * (lower_co2_weight * upper_h2o_weight)\
        + co2_upper_h2o_lower * (upper_co2_weight * lower_h2o_weight)\
        + co2_upper_h2o_upper * (upper_co2_weight * upper_h2o_weight)

    return transparency


def calculate_transparency_two(co2: float,
                               temperature: float,
                               relative_humidity: float) -> float:
    water_vapor = calculate_water_vapor(temperature, relative_humidity)
    remaining_intensities = 0
    total_intensity = TOTAL_INTENSITY * ANGLE_CORRECTIONS.size

    for angle_correction in ANGLE_CORRECTIONS:
        corrected_co2 = co2 * (1 / np.sin(angle_correction))
        corrected_water_vapor = water_vapor * (1 / np.sin(angle_correction))
        corrected_rel_intensities = RELATIVE_INTENSITIES * np.cos((np.pi / 2) - angle_correction)
        total_absorb_coefficients = CO2_COEFFICIENTS * corrected_co2 + \
                                    WATER_VAPOR_COEFFICIENTS * \
                                    corrected_water_vapor
        co2_coefficients = CO2_COEFFICIENTS * corrected_co2
        h2o_coefficients = WATER_VAPOR_COEFFICIENTS * corrected_water_vapor

        remaining_intensities += corrected_rel_intensities * \
                     np.power(10, co2_coefficients) * np.power(10, h2o_coefficients)

    return remaining_intensities.sum() / total_intensity


def calculate_transparency_three(co2: float, temperature: float,
                                 relative_humidity: float):
    benchmark = np.array([27.2, 34.5, 29.6, 26.4, 27.5, 24.5, 13.5, 21.4,
                          44.4, 59.0, 70, 75.5, 62.9, 56.4, 51.4, 39.1, 37.9,
                          36.3, 32.7, 29.8, 21.9])
    water_vapor = calculate_water_vapor(temperature, relative_humidity)
    remaining_intensities = 0

    for angle in ANGLE_CORRECTIONS:
        corrected_co2 = co2 * (1 / np.sin(angle))
        corrected_water_vapor = water_vapor * (1 / np.sin(angle))
        absorption_differences = (corrected_co2 * CO2_COEFFICIENTS) \
                                 + (corrected_water_vapor * WATER_VAPOR_COEFFICIENTS) \
                                 - CO2_COEFFICIENTS \
                                 - (.3 * WATER_VAPOR_COEFFICIENTS)
        ratios = np.power(10, absorption_differences)
        remaining_intensities += (benchmark * ratios)
    return remaining_intensities.sum() / (benchmark.sum() / .372 *ANGLE_CORRECTIONS.size)


def calculate_transparency_four(co2: float, temperature: float, relative_humidity: float):
    benchmark = np.array([27.2, 34.5, 29.6, 26.4, 27.5, 24.5, 13.5, 21.4,
                          44.4, 59.0, 70, 75.5, 62.9, 56.4, 51.4, 39.1, 37.9,
                          36.3, 32.7, 29.8, 21.9])

    water_vapor = calculate_water_vapor(temperature, relative_humidity)
    total_transparencies = 0

    for angle in ANGLE_CORRECTIONS:
        corrected_original_intensities = benchmark * np.cos((np.pi / 2) - angle)

        corrected_co2 = co2 * (1 / np.sin(angle))
        corrected_water_vapor = water_vapor * (1 / np.sin(angle))
        co2_coefficients = CO2_COEFFICIENTS * corrected_co2
        h2o_coefficients = WATER_VAPOR_COEFFICIENTS * corrected_water_vapor
        remaining_intensities = corrected_original_intensities * np.power(10, co2_coefficients + h2o_coefficients)
        total_transparencies += remaining_intensities.sum() / corrected_original_intensities.sum() \
                                * np.sin(angle) * np.cos(angle)
    return total_transparencies


def _vert_trans(co2: float, water_vapor: float, correction_factor: float) -> float:
    benchmark = np.array([27.2, 34.5, 29.6, 26.4, 27.5, 24.5, 13.5, 21.4,
                          44.4, 59.0, 70, 75.5, 62.9, 56.4, 51.4, 39.1, 37.9,
                          36.3, 32.7, 29.8, 21.9]) * correction_factor
    remaining_intensities = benchmark * np.power(10, co2 * CO2_COEFFICIENTS) \
                            * np.power(10, water_vapor * WATER_VAPOR_COEFFICIENTS)

    return remaining_intensities.sum() / RELATIVE_INTENSITIES.sum()


def calculate_transparency_five(co2: float, temperature: float, relative_humidity: float) -> float:
    h2o = calculate_water_vapor(temperature, relative_humidity)
    total_transparency = 0
    for angle in ANGLE_CORRECTIONS:
        corrected_co2 = co2 * (1 / np.sin(angle))
        corrected_h2o = h2o * (1 / np.sin(angle))

        total_transparency += _vert_trans(corrected_co2, corrected_h2o, np.cos((np.pi / 2) - angle)) * np.cos(angle) * np.sin(angle)
    return total_transparency


def calculate_water_vapor(temperature: float,
                          relative_humidity: float) -> float:
    """
    Calculate the amount of water vapor in a grid cell with the given data.

    :param temperature:
        The average temperature of the grid cell
    :param relative_humidity:
        The relative humidity of the grid cell
    :return:
        The amount of water vapor traversed by a vertical radiation ray
        in Arrhenius' units. The unit = 1 when absolute humidity is
        10 grams per cubic meter.
    """
    # use Antoine equation from 1888 to calculate saturation water vapor
    # pressure equation constants A, B, & C from:
    # https://webbook.nist.gov/cgi/cbook.cgi?ID=C7732185&Mask=4
    #                                        &Type=ANTOINE&Plot=on#ANTOINE
    if temperature < 0 or relative_humidity < 0 or relative_humidity > 100:
        raise AttributeError

    pressure_saturation = 10 ** (CONST_A - (CONST_B/(temperature + CONST_C)))

    # convert pressure from bar to Pascals
    pressure_saturation = pressure_saturation * 100000
    pressure_water_vapor = relative_humidity / 100 * pressure_saturation

    absolute_humidity = 2.16679 * pressure_water_vapor / temperature
    return absolute_humidity / 10


def calculate_mean_path(co2: float,
                        water_vapor: float) -> float:
    """
    Calculate the mean path coefficient for a grid cell with the given data.
    The mean path is the distance that all radiation that emanates from a
    single point would need to travel if the rays went straight instead of
    at different angles relative to the earth's surface.

    :param co2:
        The amount of CO2 in the atmosphere in Arrhenius' units
    :param water_vapor:
        The amount of water vapor in the air in Arrhenius' units
    :return:
        The p value for the CO2 and water vapor of a grid cell with
        the given values
    """
    if co2 < 0 or water_vapor < 0:
        raise AttributeError

    co2_valid = False

    keys = list(MEAN_PATH.keys())
    closest_water_vapor = keys[0][1]
    for key in keys:
        if co2 == key[0]:
            co2_valid = True
        if abs(water_vapor - key[1]) < abs(water_vapor - closest_water_vapor):
            closest_water_vapor = key[1]

    if co2_valid is False:
        raise AttributeError

    return MEAN_PATH.get((co2, closest_water_vapor))
