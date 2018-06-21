from netCDF4 import Dataset
from typing import List, Union
from numpy import ndarray


DIM_TYPE_KEY = 'type'
DIM_SIZE_KEY = 'size'

VAR_TYPE_KEY = 'type'
VAR_DIMS_KEY = 'dims'
VAR_ATTR_KEY = 'attrs'


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

        self._global_attrs = {}

    def global_attribute(self: 'NetCDFWriter',
                         attr_name: str,
                         attr_val: str) -> 'NetCDFWriter':
        """
        Register a global attribute to be added to the NetCDF output file.
        For example, the attribute 'description' may refer to the string
        'A dataset containing 10x20 degree gridded temperature and humidity
        data used in Arrhenius' 1895 climate model.'

        Preconditions:
            attr_name != ''

        :param attr_name:
            The name of the new global attribute
        :param attr_val:
            The value of the new global attribute
        :return:
            This NetCDFWriter instance
        """
        # Integrity checks for attribute name.
        if attr_name is None:
            raise ValueError("Attrribute name must not be None")
        elif type(attr_name) != str:
            raise TypeError("Attribute name must be of type str"
                            " (is {})".format(type(attr_name)))
        elif attr_name == '':
            raise ValueError("Attribute name must be a non-empty string")

        # Integrity checks for attribute value.
        if attr_val is None:
            raise ValueError("Attribute value must not be None")
        elif type(attr_val) != str:
            raise TypeError("Attribute value must be of type str"
                            " (is {})".format(type(attr_val)))

        self._global_attrs[attr_name] = attr_val
        return self

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

        Preconditions:
            var_name != ''
            each element of var_dims must be registered as a dimension

        :param var_name:
            The name of the new variable
        :param var_type:
            The type of the new variable
        :param var_dims:
            The list of dimensions associated with the new variable, in
            order of appearance in the variable's data array
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
            VAR_DIMS_KEY: var_dims,
            VAR_ATTR_KEY: {}
        }

        return self

    def variable_attribute(self: 'NetCDFWriter',
                           var_name: str,
                           attr_name: str,
                           attr_val: str) -> 'NetCDFWriter':
        """
        Register an attribute to be added to the NetCDF output file, associated
        with the variable var_name.
        For example, the attribute 'units' for variable latitude may refer to
        the string 'Degrees north of the equator.'

        Preconditions:
            var_name must be registered as a variable
            attr_name != ''

        :param var_name:
            The name of the variable to which the attribute will be associated
        :param attr_name:
            The name of the new attribute
        :param attr_val:
            The value of the new attribute
        :return:
            This NetCDFWriter instance
        """
        # Integrity checks for variable name.
        if var_name is None:
            raise ValueError("Variable name must not be None")
        elif type(var_name) != str:
            raise TypeError("Variable name must be of type str"
                            " (is {})".format(type(var_name)))
        elif var_name not in self._variables:
            raise ValueError("Variable {} not registered".format(var_name))

        # Integrity checks for attribute name.
        if attr_name is None:
            raise ValueError("Attrribute name must not be None")
        elif type(attr_name) != str:
            raise TypeError("Attribute name must be of type str"
                            " (is {})".format(type(attr_name)))
        elif attr_name == '':
            raise ValueError("Attribute name must be a non-empty string")

        # Integrity checks for attribute value.
        if attr_val is None:
            raise ValueError("Attribute value must not be None")
        elif type(attr_val) != str:
            raise TypeError("Attribute value must be of type str"
                            " (is {})".format(type(attr_val)))

        self._variables[var_name][VAR_ATTR_KEY][attr_name] = attr_val
        return self

    def data(self: 'NetCDFWriter',
             var_name: str,
             data: ndarray) -> 'NetCDFWriter':
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
        elif type(data) != ndarray:
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
        Use the dimensions, variables, variable data, and attributes to write a
        NetCDF file with the specified format. This file is placed in the
        output directory specified in the resources.py file.

        Throws an error if not all the required pieces (dimensions, data,
        variables) have been entered. These pieces are not reset after the
        function exits, and so it can be called successively with different
        file name arguments without having to reload data.

        :param filepath:
            An absolute or relative path to the NetCDF file to be produced
        :param format:
            The file format for the NetCDF file (defaults to NetCDF4)
        """
        if len(self._data) == 0:
            raise ValueError("No data has been submitted to be written")
        elif len(self._dimensions) == 0:
            raise ValueError("No data dimensions have been registered")
        elif len(self._variables) == 0:
            raise ValueError("No variables have been registered")

        for variable in self._variables:
            if variable not in self._data:
                raise LookupError("No data has been submitted for variable"
                                  "{}".format(variable))

        # Create a new NetCDF dataset in memory.
        output_dataset = Dataset(filepath, 'w', format)

        # Load global attributes.
        for attr_name, attr_val in self._global_attrs.items():
            setattr(output_dataset, attr_name, attr_val)

        # Create dimensions within the dataset.
        for dim_name in self._dimensions:
            dim_type = self._dimensions[dim_name][DIM_TYPE_KEY]
            dim_size = self._dimensions[dim_name][DIM_SIZE_KEY]

            output_dataset.createDimension(dim_name, dim_size)
            output_dataset.createVariable(dim_name, dim_type, (dim_name,))

        for var_name in self._variables:
            var_type = self._variables[var_name][VAR_TYPE_KEY]
            var_dims = tuple(self._variables[var_name][VAR_DIMS_KEY])
            var_attrs = self._variables[var_name][VAR_ATTR_KEY]

            # Load the main variable data into the dataset, using
            # all dimensions.
            var = output_dataset.createVariable(var_name, var_type, var_dims)

            # Load variable attributes.
            for attr_name, attr_val in var_attrs.items():
                setattr(var, attr_name, attr_val)

            var[:] = self._data[var_name]

        # Finally, write the file to disk.
        output_dataset.close()
