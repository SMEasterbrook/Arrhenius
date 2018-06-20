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

    def dimension(self: 'NetCDFWriter',
                  dim_name: str,
                  dim_type: type,
                  dim_size: Union[int, None]) -> 'NetCDFWriter':
        """
        Adds a new variable dimension to the end of the current list
        of dimensions.

        Preconditions:
            dim_name != ''
            dim_size > 0

        :param dim_name:
            The name of the new dimension
        :param dim_type:
            The type of the new dimension's values
        :param dim_size:
            The number of entries in the dimension, or None if the dimension
            is to have unlimited size
        :return:
            This NetCDFWriter instance
        """
        # Integrity checks for dimension name.
        if dim_name is None:
            raise ValueError("Dimension name must not be None")
        elif type(dim_name) != str:
            raise TypeError("Dimension name must be of type str"
                            " (is {})".format(type(dim_name)))
        elif dim_name == '':
            raise ValueError("Dimension name must be a non-empty string")

        # Integrity checks for dimension type.
        if dim_type is None:
            raise ValueError("Dimension type must not be None")
        elif type(dim_type) != type:
            raise TypeError("Dimension type must be of type type"
                            " (is {})".format(type(dim_type)))

        # Integrity checks for dimension size.
        if dim_size is not None:
            if type(dim_size) != int:
                raise TypeError("Dimension size must be of type int or None"
                                " (is {})".format(type(dim_size)))
            elif dim_size <= 0:
                raise ValueError("Dimension size must be greater than 0"
                                 "(is {})".format(dim_size))

        self._dimensions[dim_name] = {
            DIM_TYPE_KEY: dim_type,
            DIM_SIZE_KEY: dim_size
        }

        return self

    def variable(self: 'NetCDFWriter',
                 var_name: str,
                 var_type: type,
                 var_dims: List[str]) -> 'NetCDFWriter':
        """
        Add a new variable to be written, or replace any existing variable with
        the same name.

        The last argument specifies all the dimensions associated with this new
        variable. Each dimension must have already been registered in this
        Writer or else a ValueError will be raised.

        Dimensions in the list should be in the same order as they appear in
        the variable's actual data. For example, if the first dimension in a
        variable's data array is time, then 'time' should be the first element
        in the dimensions list. It will be written to the file as such.

        :param var_name:
            The name of the new variable
        :param var_type:
            The type of the new variable
        :param var_dims:
            The list of dimensions associated with the new variable, in order of
            appearance in the variable's data array
        :return:
            This NetCDFWriter instance
        """
        # Integrity checks for variable name.
        if var_name is None:
            raise ValueError("Variable name must not be None")
        elif type(var_name) != str:
            raise TypeError("Variable name must be of type str"
                            " (is {})".format(type(var_name)))
        elif var_name == '':
            raise ValueError("Variable name must be non-empty")

        # Integrity checks for variable type.
        if var_type is None:
            raise ValueError("Variable type must not be None")
        elif type(var_type) != type:
            raise TypeError("Variable type must be of type type"
                            " (is {})".format(type(var_type)))

        # Integrity checks for variable dimensions.
        if var_dims is None:
            # None is considered as a way of specifying empty dimensions.
            var_dims = []
        if type(var_dims) != list:
            raise TypeError("Variable dimensions must be of type list"
                            " (is {})".format(type(var_dims)))

        # Integrity checks for each dimension listed for the variable.
        for i in range(len(var_dims)):
            dim = var_dims[i]
            if type(dim) != str:
                raise TypeError("All variable dimensions must be type str"
                                " (index {} is {})".format(i, type(dim)))
            elif dim not in self._dimensions:
                raise ValueError("All variable dimensions must be registered"
                                 " as data dimensions ({} is not)".format(dim))

        self._variables[var_name] = {
            VAR_TYPE_KEY: var_type,
            VAR_DIMS_KEY: var_dims
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
