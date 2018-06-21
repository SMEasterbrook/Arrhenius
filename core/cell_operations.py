# Constants for absolute humidity calculations
CONST_A = 4.6543
CONST_B = 1435.264
CONST_C = -64.848

TRANSPARENCY ={
    (1.0, .3): 37.2, (1.0, .5): 35.0, (1.0, 1.0): 30.7, (1.0, 1.5): 26.9,
    (1.0, 2.0): 23.9, (1.0, 3.0): 19.3, (1.0, 4.0): 16.0, (1.0, 6.0): 10.7,
    (1.0, 10.0): 8.9,
    (1.2, .3): 34.7, (1.2, .5): 32.7, (1.2, 1.0): 28.6, (1.2, 1.5): 25.1,
    (1.2, 2.0): 22.2, (1.2, 3.0): 17.8, (1.2, 4.0): 14.7, (1.2, 6.0): 9.7,
    (1.2, 10.0): 8.0,
    (1.5, .3):  31.5, (1.5, .5): 29.6, (1.5, 1.0): 25.9, (1.5, 1.5): 22.6,
    (1.5, 2.0): 19.9, (1.5, 3.0): 15.9, (1.5, 4.0): 13.0, (1.5, 6.0): 8.4,
    (1.5, 10.0): 6.9,
    (2.0, .3):  27.0, (2.0, .5): 25.3, (2.0, 1.0): 21.9, (2.0, 1.5): 19.1,
    (2.0, 2.0): 16.7, (2.0, 3.0): 13.1, (2.0, 4.0): 10.5, (2.0, 6.0): 6.6,
    (2.0, 10.0): 5.3,
    (2.5, .3):  23.5, (2.5, .5): 22.0, (2.5, 1.0): 19.0, (2.5, 1.5): 16.6,
    (2.5, 2.0): 14.4, (2.5, 3.0): 11.0, (2.5, 4.0): 8.7, (2.5, 6.0): 5.3,
    (2.5, 10.0): 4.2,
    (3.0, .3):  20.1, (3.0, .5): 18.8, (3.0, 1.0): 16.3, (3.0, 1.5): 14.2,
    (3.0, 2.0): 12.3, (3.0, 3.0): 9.3, (3.0, 4.0): 7.4, (3.0, 6.0): 4.2,
    (3.0, 10.0): 3.3,
    (4.0, .3):  15.8, (4.0, .5): 14.7, (4.0, 1.0): 12.7, (4.0, 1.5): 10.8,
    (4.0, 2.0): 9.3, (4.0, 3.0): 7.1, (4.0, 4.0): 5.6, (4.0, 6.0): 3.1,
    (4.0, 10.0): 2.0,
    (6.0, .3):  10.9, (6.0, .5): 10.2, (6.0, 1.0): 8.7, (6.0, 1.5): 7.3,
    (6.0, 2.0): 6.3, (6.0, 3.0): 4.8, (6.0, 4.0): 3.7, (6.0, 6.0): 1.9,
    (6.0, 10.0): .93,
    (10.0, .3):  6.6, (10.0, .5): 6.1, (10.0, 1.0): 5.2, (10.0, 1.5): 4.3,
    (10.0, 2.0): 3.5, (10.0, 3.0): 2.4, (10.0, 4.0): 1.8, (10.0, 6.0): 1.0,
    (10.0, 10.0): .26,
    (20.0, .3):  2.9, (20.0, .5): 2.5, (20.0, 1.0): 2.2, (20.0, 1.5): 1.8,
    (20.0, 2.0): 1.5, (20.0, 3.0): 1.0, (20.0, 4.0): .75, (20.0, 6.0): .39,
    (20.0, 10.0): .07,
    (40.0, .3):  .88, (40.0, .5): .81, (40.0, 1.0): .67, (40.0, 1.5): .56,
    (40.0, 2.0): .46, (40.0, 3.0): .32, (40.0, 4.0): .24, (40.0, 6.0): .12,
    (40.0, 10.0): .02
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
    (3.5, .3): 1.48, (3.5, .5): 1.48, (3.5, 1.0): 1.45, (3.5, 2.0): 1.42,
}

def calculate_transparency(CO2: float, temperature: float, relative_humidity: float):
    """
    Calculate the transparency for a grid cell with the given data.

    :param CO2:
        The amount of CO2 in the atmosphere

    :param temperature:
        The average temperature of the grid cell
    :param relative_humidity:
        The relative humidity of the grid cell

    :return:
        The B value corresponding to a grid cell with the given conditions
    """
    water_vapor = calculate_water_vapor(temperature, relative_humidity)
    p = calculate_mean_path(CO2, water_vapor)
    # find transparency percent from preprogrammed table
    keys = list(TRANSPARENCY.keys())
    closest_CO2 = keys[0][0]
    closest_water_vapor = keys[0][1]
    for key in keys:
        if abs(p * CO2 - key[0]) < abs(p * CO2 - closest_CO2):
            closest_CO2 = key[0]
        if abs(p * water_vapor - key[1]) < abs(p * water_vapor - closest_water_vapor):
            closest_water_vapor = key[1]

    transparency = TRANSPARENCY.get((closest_CO2, closest_water_vapor)) / 100
    return transparency


def calculate_water_vapor(temperature: float, relative_humidity: float):
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
    # use Antoine equation from 1888 to calculate saturation water vapor pressure
    # equation constants A, B, & C from:
    # https://webbook.nist.gov/cgi/cbook.cgi?ID=C7732185&Mask=4&Type=ANTOINE&Plot=on#ANTOINE
    temp_Kelvin = temperature
    pressure_saturation = 10 ** (CONST_A - (CONST_B/(temp_Kelvin + CONST_C)))
    #convert pressure from bar to Pascals
    pressure_saturation = pressure_saturation *100000
    pressure_water_vapor = relative_humidity / 100 * pressure_saturation
    absolute_humidity = 2.16679 * pressure_water_vapor / temp_Kelvin
    return absolute_humidity / 10


def calculate_mean_path(CO2: float, water_vapor: float):
    """
    Calculate the mean path coefficient for a grid cell with the given data.
    The mean path is the distance that all radiation that emanates from a
    single point would need to travel if the rays went straight instead of
    at different angles relative to the earth's surface.

    :param CO2:
        The amount of CO2 in the atmosphere
    :param water_vapor:
        The amount of water vapor in the air in Arrhenius' units
    :return:
        The p value for the CO2 and water vapor of a grid cell with
        the given values
    """
    keys = list(MEAN_PATH.keys())
    closest_water_vapor = keys[0][1]
    for key in keys:
        if abs(water_vapor - key[1]) < abs(water_vapor - closest_water_vapor):
            closest_water_vapor = key[1]

    return MEAN_PATH.get((CO2, closest_water_vapor))
