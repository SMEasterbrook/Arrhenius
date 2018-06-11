from netCDF4 import Dataset
from .resources import OUTPUT_PATH


class NetCDFWriter:
    """
    A general NetCDF data writer, capable of writing various formats
    of NetCDF files one variable at a time.
    """

    def __init__(self, dimensions=None, data=None):
        """
        Create a new NetCDFWriter instance.

        :param dimensions:
            A starting set of variable dimensions to use
        :param data:
            A starting dataset to write
        """
        self._dimensions = [] if dimensions is None else dimensions
        self._data = data
        self._var_meta = None

    def dimensions(self, dims):
        """
        Load in a new set of variable dimensions for the next write.

        Variable dimensions must be in the form of a list of tuples, where
        each tuple contains a str followed by a type followed by an int.

        The first element of each tuple, the str, represents the name of
        the dimension (e.g. latitude, time). The type element is the type
        that will be stored (e.g. numpy.int32). The third int type is the
        size of the dimension, or the expected number of elements. Leave as
        None for an unlimited size dimension.

        These variable dimensions will be used as dimensions in the NetCDF
        file upon writing. They must occur in the same order as the
        corresponding nested list within the data list structure; that is,
        if latitude is first in the list of dimensions, the outermost list
        in the data list must represent latitude.

        :param dims:
            The new list of variable dimensions
        :return:
            This NetCDFWriter instance
        """
        if dims is None:
            raise ValueError("dimensions cannot be None")
        elif type(dims) != list:
            raise TypeError("dimensions must be of type list")
        elif len(dims) == 0:
            raise ValueError("dimensions must contain at least one element")

        self._dimensions = []
        for dimension in dims:
            self.add_dimension(dimension)

        return self

    def add_dimension(self, dim):
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

        The nth dimension added will correspond to the nth nested layer of
        lists within the data list.

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
        elif dim in self._dimensions:
            raise ValueError("Dimension {} already present".format(dim[0]))

        self._dimensions.append(dim)
        return self

    def data(self, data):
        """
        Submit a set of data that can be written to a NetCDF file.

        Only a single point of data can be loaded at once, which means that
        if multiple variables must be added to the file, they must be added
        separately, possibly with new variable dimensions and metadata.

        The data must be in the form of a multilevel nested list, where all
        the lists at a certain level have the same length. Intuitively, the
        lists must be arranged like an n-dimensional array.

        The nth layer of nested lists is interpreted according to the nth
        variable dimension that was loaded. Therefore, the types and sizes
        must match up. This is evaluated upon calling for the write to take
        place, and so no warnings are given if dimensions and data do not
        match.

        :param data:
            A new variable worth of data to add into the NetCDF file
        :return:
            This NetCDFWriter instance
        """
        if data is None:
            raise ValueError("data cannot be None")
        elif type(data) != list:
            raise TypeError("data must be of type list")

        self._data = data
        return self

    def variable_meta(self, var_meta):
        """
        Load a new set of metadata for the variable to be written.

        This metadata must be in the form of a tuple containing two elements.
        The first element, a str, is the name of the variable. The second, a
        type, is the type (e.g. numpy.int32) with which the data will be
        written.

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

        self._var_meta = var_meta
        return self

    def write(self, file_name, format='NETCDF4'):
        """
        Use the dimensions, variable data, and variable metadata to write a
        NetCDF file with the specified format. This file is placed in the
        output directory specified in the resources.py file.

        Throws an error if not all the required pieces (dimensions, data,
        metadata) have been entered. These pieces are not reset after the
        function exits, and so it can be called successively with different
        file name arguments without having to reload data.

        :param file_name:
            The name of the NetCDF file to be produced
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
        file_path = OUTPUT_PATH + file_name + '.nc'
        output_file = Dataset(file_path, 'w', format)

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
