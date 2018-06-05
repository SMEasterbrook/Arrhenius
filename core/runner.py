from core import cell_operations


def run_model(init_CO2, new_CO2, grid_cells):
    """
    Calculate Earth's surface temperature change due to
    a change in CO2 levels.

    :param init_CO2:
        The initial amount of CO2 in the atmosphere

    :param new_CO2:
        The new amount of CO2 in the atmosphere

    :param grid_cells:
        The grid cell objects containing gridded temp and humidity data

    :return:
        The new surface temperature for each provided grid cell
    """
    raise NotImplementedError


def get_cell_temperature_change(init_CO2, new_CO2, grid_cell):
    """
    Calculate the change in temperature of a specific grid cell due to a
    change in CO2 levels in the atmosphere.

    :param init_CO2:
        The initial amount of CO2 in the atmosphere

    :param new_CO2:
        The new amount of CO2 in the atmosphere

    :param grid_cell:
        A GridCell object containing average temperature and relative humidity

    :return:
        The change in surface temperature for the provided grid cell
        after the given change in CO2
    """
    init_temperature = grid_cell.get_temperature()
    relative_humidity = grid_cell.get_relative_humidity()
    init_B = cell_operations.calculate_B(init_CO2, init_temperature,
                                         relative_humidity)
    after_CO2_change_B = cell_operations.calculate_B(new_CO2, init_temperature,
                                                     relative_humidity)
    temperature_change = get_temperature_change(init_B, after_CO2_change_B)
    final_B = cell_operations.calculate_B(new_CO2,
                                          init_temperature + temperature_change,
                                          relative_humidity)
    temperature_change = temperature_change \
                         + get_temperature_change(after_CO2_change_B, final_B)
    return temperature_change


def get_temperature_change(init_B, new_B):
    """
    Calculate the temperature change of a grid cell due to a change in B

    :param init_B:
        The initial value of B for the grid cell

    :param new_B:
        The new value of B for the grid cell

    :return:
        The change in temperature for a grid cell with the given change in B
    """
    raise NotImplementedError
