def calculate_B(CO2, temperature, relative_humidity):
    """
    Calculate the B value for a grid cell with the given data.

    :param CO2:
        The amount of CO2 in the atmosphere

    :param temperature:
        The average temperature of the grid cell

    :param relative_humidity:
        The relative humidity of the grid cell

    :return:
        The B value corresponding to a grid cell with the given conditions
    """
    # water_vapor = calculate_water_vapor(temperature, relative_humidity)
    # p = calculate_p(CO2, water_vapor)
    # Finish writing function by calculating B from pK and pW
    raise NotImplementedError


def calculate_water_vapor(temperature, relative_humidity):
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
    raise NotImplementedError


def calculate_p(CO2, water_vapor):
    """
    Calculate the p value for a grid cell with the given data.

    :param CO2:
        The amount of CO2 in the atmosphere

    :param water_vapor:
        The amount of water vapor in the air in Arrhenius' units

    :return:
        The p value for the CO2 and water vapor of a
    """
    raise NotImplementedError
