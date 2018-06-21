import cell_operations
from typing import List


def run_model(init_CO2: float, new_CO2: float, grid_cells: List[List[List['GridCell']]]) -> None:
    """
    Calculate Earth's surface temperature change due to
    a change in CO2 levels.

    :param init_CO2:
        The initial amount of CO2 in the atmosphere
    :param new_CO2:
        The new amount of CO2 in the atmosphere
    :param grid_cells:
        The grid cell objects containing gridded temp and humidity data
    """
    for grid in grid_cells:
        for latitude in grid:
            for cell in latitude:
                new_temp = calculate_cell_temperature_change(init_CO2, new_CO2, cell)
                cell.set_temperature_change(new_temp)

    print_avg_lat_changes(grid_cells)


def calculate_cell_temperature_change(init_CO2: float, new_CO2: float,
                                      grid_cell: 'GridCell') -> float:
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
    albedo = grid_cell.get_albedo()
    init_absorb = cell_operations.calculate_absorption_coefficient(init_CO2,
                                                                   init_temperature,
                                                                   relative_humidity)
    K = calibrate_constant(init_temperature, albedo, init_absorb)

    mid_absorb = cell_operations.calculate_absorption_coefficient(new_CO2,
                                                                  init_temperature,
                                                                  relative_humidity)
    mid_temperature = get_new_temperature(albedo, mid_absorb, K)
    final_absorb = cell_operations.calculate_absorption_coefficient(new_CO2,
                                                                    mid_temperature,
                                                                    relative_humidity)
    final_temperature_change = get_new_temperature(albedo, final_absorb, K) \
                               - init_temperature
    return final_temperature_change


def calibrate_constant(temperature, albedo, absorption) -> float:
    """
    Calculate the constant K used in Arrhenius' temperature change equation
    using the initial values of temperature and absorption in a grid cell.

    :param temperature:
        The temperature of the grid cell
    :param albedo:
        The albedo of the grid cell
    :param absorption:
        The absorption coefficient of the grid cell

    :return:
        The calculated constant K
    """
    return pow(temperature, 4) * (1 + (1 - albedo) * (1 - absorption))


def get_new_temperature(albedo: float, new_absorption: float, K: float) -> float:
    """
    Calculate the new temperature after a change in absorption coefficient

    :param albedo:
        The albedo of the grid cell
    :param new_absorption:
        The new value of the absorption coefficient for the grid cell
    :param K:
        A constant used in Srrhenius' temperature change equation

    :return:
        The change in temperature for a grid cell with the given change in B
    """
    denominator = 1 + (1 - albedo) * (1 - new_absorption)
    return pow((K / denominator), 1 / 4)


def print_avg_lat_changes(grid_cells: List[List[List['GridCell']]]) -> None:
    """
    Print the average temperature change for each latitude band
    in each provided grid

    :param grid_cells: A list of grid
    """

    grid_number = 1
    result = ""
    for grid in grid_cells:
        result = result + "===== Grid " + str(grid_number) + " ===== \n"
        for latitude in grid:
            avg_temp_change = 0
            count = 0
            for cell in latitude:
                avg_temp_change += cell.get_temperature_change()
                count += 1
            avg_temp_change = avg_temp_change / count
            result = result + "\t\t" + str(latitude[0].get_latitude()) \
                     + ": " + str(avg_temp_change) + " degrees Celcius \n"
    print(result)
