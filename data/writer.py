from netCDF4 import Dataset
from typing import List, Tuple, Union
from numpy import ndarray


DIM_TYPE_KEY = 'type'
DIM_SIZE_KEY = 'size'

VAR_TYPE_KEY = 'type'
VAR_DIMS_KEY = 'dims'


class NetCDFWriter:
    """
    A general NetCDF data writer, capable of writing various formats
    of NetCDF files with multiple dimensions and variables.
    """

    def __init__(self: 'NetCDFWriter') -> None:
        """
        Create a new NetCDFWriter instance.
        """
        self._data = {}
        self._dimensions = {}
        self._variables = {}

    def add_dimension(self: 'NetCDFWriter',
                      dim: Tuple[Union[str, type, int]]) -> 'NetCDFWriter':
        """
        Adds a new variable dimension to the end of the current list
        of dimensions.

        A variable dimension must be a tuple of length 3, where the first
        element is a str, the second is a type, and the third is an int.

        The first element of each tuple, the str, represents the name of
        the dimension (e.g. latitude, time). The type element is the type
        that will be stored (e.g. numpy.int32). The third int type is the
        size of the dimension, or the expected number of elements. Leave as
        None for an unlimited size dimension.

        :param dim:
            A new variable dimension
        :return:
            This NetCDFWriter instance
        """
        if dim is None:
            raise ValueError("dim cannot be None")
        elif type(dim) != tuple:
            raise TypeError("dim must be of type tuple")
        elif len(dim) != 3:
            raise ValueError("dim must contain exactly 3 elements")
        elif type(dim[0]) != str \
                or type(dim[1]) != type\
                or type(dim[2]) != int:
            raise ValueError("dim must contain a str followed by "
                             "a type followed by an int")
        elif dim[0] in self._dimensions:
            raise ValueError("Dimension {} already present".format(dim[0]))

        self._dimensions[dim[0]] = {
            DIM_TYPE_KEY: dim[1],
            DIM_SIZE_KEY: dim[2]
        }

        return self

    def add_variable(self: 'NetCDFWriter',
                     var_meta: Tuple[Union[str, type, List[str]]]) -> 'NetCDFWriter':
        """
        Load a new set of metadata for the variable to be written.

        This metadata must be in the form of a tuple containing three elements.
        The first element, a str, is the name of the variable. The second, a
        type, is the type (e.g. numpy.int32) with which the data will be
        written. The third element, a list of str, contains the dimensions on
        which the variable is based, in the order in which they appear in the
        variable's data array. For instance, the dimension associated with the
        primary index in the data array should be the first element in the list.

        :param var_meta:
            Metadata about the main variable that will be written
        :return:
            This NetCDFWriter instance
        """
        if var_meta is None:
            raise ValueError("var_meta cannot be None")
        elif type(var_meta) != tuple:
            raise TypeError("var_meta must be of type tuple")
        elif len(var_meta) != 2 or\
                (type(var_meta[0]) != str and type(var_meta[1]) != type):
            raise ValueError("var_meta must contain two elements:\
                              a str followed by a type")

        self._variables[var_meta[0]] = {
            VAR_TYPE_KEY: var_meta[1],
            VAR_DIMS_KEY: var_meta[2]
        }

        return self

    def data(self: 'NetCDFWriter',
             data: ndarray,
             var_name: str) -> 'NetCDFWriter':
        """
        Submit a set of data that can be written to a NetCDF file.

        The data should be passed in as either an array or an array-like
        structure. The number of dimensions to the array should be equal
        to the number of dimensions associated with variable var_name.

        Precondition:
            var_name has already been registered as a variable

        :param data:
            A new variable worth of data to add into the NetCDF file
        :param var_name:
            The name of the variable with which the data will be associated
        :return:
            This NetCDFWriter instance
        """
        if data is None:
            raise ValueError("data cannot be None")
        elif type(data) != list:
            raise TypeError("data must be of type list")
        elif var_name not in self._variables:
            raise KeyError("var_name ({}) has not been registered as a"
                           "variable".format(var_name))

        self._data[var_name] = data
        return self

    def write(self: 'NetCDFWriter',
              filepath: str,
              format: str = 'NETCDF4') -> None:
        """
        Use the dimensions, variable data, and variable metadata to write a
        NetCDF file with the specified format. This file is placed in the
        output directory specified in the resources.py file.

        Throws an error if not all the required pieces (dimensions, data,
        metadata) have been entered. These pieces are not reset after the
        function exits, and so it can be called successively with different
        file name arguments without having to reload data.

        :param filepath:
            An absolute or relative path to the NetCDF file to be produced
        :param format:
            The file format for the NetCDF file (defaults to NetCDF4)
        """
        if self._data is None:
            raise ValueError("No data has been submitted to be written")
        elif len(self._dimensions) == 0:
            raise ValueError("No data dimensions have been specified")
        elif self._var_meta is None:
            raise ValueError("No variable metadata has been entered")

        # Create a new NetCDF dataset in memory.
        output_file = Dataset(filepath, 'w', format)

        # Create dimensions within the dataset.
        for dim in self._dimensions:
            dim_name = dim[0]
            dim_type = dim[1]
            dim_size = dim[2]

            output_file.createDimension(dim_name, dim_size)
            output_file.createVariable(dim_name, dim_type, (dim_name,))

        var_name = self._var_meta[0]
        var_type = self._var_meta[1]

        # Load the main variable data into the dataset, using all dimensions.
        all_dims = tuple([dim[0] for dim in self._dimensions])
        one_var = output_file.createVariable(var_name, var_type, all_dims)
        one_var[:] = self._data

        # Finally, write the file to disk.
        output_file.close()
