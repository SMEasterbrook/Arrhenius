import numpy as np


def build_multilayer_matrix(transparencies):
    """
    Returns a matrix representing a system of energy balance equations in a
    multilayer atmosphere. The equation at index i represents the energy
    balance equation for layer i; layer 0 is considered to be the ground.

    Transparencies should be a vector of length n+1, where n is the number
    of layers in the model. It is interpreted as a single column in the
    atmosphere, i.e. a single cell in a grid.

    The matrix that is returned has no attached solution vector. A solution
    vector can be obtained by the values for each system of equation with
    real values of temperature and transparency.

    Given this solution vector, the solution to the system of equations gives
    temperatures for each layer to the power of four.

    :param transparencies:
        A vector of transparency values for each atmospheric layer.
    :return:
        A square (n+1) x (n+1) coefficient matrix representing atmospheric
        balance equations in the atmosphere.
    """
    # Number of atmospheric layers (excluding space).
    n = transparencies.shape[0] - 1
    absorptivities = 1 - transparencies

    # path_transparencies[j, i] represents the fraction of energy emitted from
    # the top of layer j that arrives at the bottom of layer i unabsorbed.
    path_transparencies = np.zeros((n+1, n+1))
    for i in range(1, n+1):
        # Compute the fraction of energy reaching layer i from all layers j
        # stored in the path_transparencies[:, i-1] vector by multiplying the
        # fraction that makes it from j to (i - 1) by the transparency of
        # layer (i - 1).
        path_transparencies[:, i] = path_transparencies[:, i - 1] \
                                    * transparencies[i - 1]
        # Document that transfer from layer (i - 1) to i is uninterrupted.
        path_transparencies[i - 1, i] = 1

    # Compute the fraction of energy making it from the top of layer i to
    # space by multiplying the fraction between layers i and n (top layer)
    # by the transparency of the top layer.
    transparencies_to_space = path_transparencies[:, n].copy()\
                              * transparencies[n]
    # Energy transfer between the top layer and space is uninterrupted.
    transparencies_to_space[n] = 1

    # Get the actual energy transfer coefficient between each layer and space
    # by multiplying the emissivity of the layer (same as its absorptivity)
    # and the absorptivity of space (assumed 1) with the transparency between
    # the two.
    paths_to_space = np.multiply(transparencies_to_space, absorptivities)

    # Do the equivalent calculation between any two atmospheric layers, except
    # multiplying by the upper layer's absorptivity instead of 1. Multiplies
    # each element at index [i, j] by the absorptivities of those two layers.
    path_coefficients = path_transparencies.copy() * absorptivities \
                        * absorptivities[:, np.newaxis]

    # Assemble the matrix form using energy balance equations.
    atm_balance_matrix = np.ones((n+1, n+1))
    for i in range(n+1):
        if i > 0:
            # Copy the negation of the energy transfer coefficients to fill in
            # the beginning of the matrix row, up to the diagonal, with terms
            # of increasing source layer (first index in path_coefficients).
            atm_balance_matrix[i, :i] = -path_coefficients[0:i, i]
        if i < n:
            # Fill in the matrix row after the diagonal with terms of
            # increasing destination layer (second index in path_coefficients).
            atm_balance_matrix[i, i+1:] = -path_coefficients[i, i+1:]

        # Fill in the matrix diagonals.
        atm_balance_matrix[i, i] = paths_to_space[i]\
                                   + path_coefficients[i, i+1:].sum()\
                                   + path_coefficients[0:i, i].sum()
    return atm_balance_matrix


def calibrate_multilayer_matrix(atm_balance_matrix, temperatures):
    """
    Returns a vector of K coefficients that represent the solutions to the
    system of n+1 linear equations given by atm_balance_matrix, with
    temperatures giving the fourth-roots of the n+1 variables in the system.

    In both atm_balance_matrix and temperatures, each of the n+1 indices in
    the vector/matrix row corresponds to either one of the n atmospheric
    layers, or the ground. In the case of atm_balance_matrix, each row is the
    energy balance equation for the associated layer. Each index in
    temperatures is the temperature of that layer.

    :param atm_balance_matrix:
        A coefficient matrix for a system of energy balance equations
        based on fourth-power temperature variables.
    :param temperatures:
        An assignment of values to the variables in the matrix.
    :return:
        A vector of constants, each equal to the result of a linear equation
        when solved with the given temperature values.
    """
    four_power_temperatures = temperatures ** 4
    constants_vector = np.dot(atm_balance_matrix, four_power_temperatures)
    return constants_vector


def solve_multilayer_matrix(atm_balance_matrix, constants):
    """
    Returns a vector of temperature values that solve the system of energy
    balance equations given by coefficient matrix atm_balance_matrix and
    constant vector constants. Since the variables in the matrix are fourth
    powers of temperature, the vector returned contains fourth-roots of the
    values that solve the matrix.

    There should be only one assignment of temperatures that solves this
    system of equations. Otherwise, an error will be raised.

    :param atm_balance_matrix:
        A coefficient matrix for a system of energy balance equations
        based on fourth-power temperature variables.
    :param constants:
        A vector containing constant solutions to each linear equation in
        atm_balance_matrix.
    :return:
        A vector of temperature values that solves the system of equations.
    """
    four_power_solutions = np.linalg.solve(atm_balance_matrix, constants)
    return four_power_solutions ** (1 / 4)
