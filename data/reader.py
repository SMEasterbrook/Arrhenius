from netCDF4 import Dataset
from datetime import datetime
from numpy import ndarray


class NetCDFReader:
    """
    A dataset reader for NetCDF files. Provides read-only access to existing
    NetCDF data.
    """
    def __init__(self: 'NetCDFReader',
                 file_name: str,
                 format: str = "NETCDF4") -> None:
        """
        Create a TimeboundNetCDFReader to access data in a NetCDF file.

        The file is lazy-loaded upon the first call to the read method.

        :param file_name:
            The NetCDF file in which the desired dataset is contained
        :param format:
            The file format for the NetCDF file (defaults to NetCDF4)
        """
        self._file = file_name
        self._file_mode = "r"
        self._file_format = format
        self._data = None

    def _open_dataset(self: 'NetCDFReader') -> None:
        """ Ensure the data reader's NetCDF dataset has been opened. """
        if self._data is None:
            self._data = Dataset(self._file, self._file_mode,
                                 self._file_format)

    def _dataset(self: 'NetCDFReader') -> Dataset:
        """ Returns the reader's underlying Dataset object. """
        return self._data

    def collect_untimed_data(self: 'NetCDFReader',
                             datapoint: str) -> ndarray:
        """
        Returns the data under the specified header, which is not associated
        with a time field.

        Subclasses must provide a data-set specific override of this method,
        since different datasets may have different structures.

        :param datapoint:
            The heading of the required data
        :return:
            The data under the requested header
        """
        self._open_dataset()

        data = self._dataset()
        var = data.variables[datapoint]
        return var[:]

    def latitude(self: 'NetCDFReader') -> ndarray:
        """
        Returns the NetCDF data file's latitude variable values.

        :return: The dataset's latitude variable
        """
        return self.collect_untimed_data("latitude")

    def longitude(self: 'NetCDFReader') -> ndarray:
        """
        Returns the NetCDF data file's longitude variable values.

        :return: The dataset's longitude variable
        """
        return self.collect_untimed_data("longitude")


class TimeboundNetCDFReader(NetCDFReader):
    """
    A dataset reader for NetCDF files, tailored for datasets that have a
    notion of time. In addition to regular data access methods from the
    NetCDFReader superclass, provides additional methods of accessing
    data from only certain years.
    """

    def read_newest(self: 'TimeboundNetCDFReader',
                    datapoint: str) -> ndarray:
        """
        Retrieve the data under the variable specified by var, limited to the
        current year. Only applies to datasets that have a time value for
        at least the requested datapoint.

        :param datapoint:
            The name of the variable requested from the dataset
        :return:
            The requested data, taken only for the most reent year
        """
        today = datetime.now()
        this_year = int(today.year)
        data_now = self.collect_timed_data(datapoint, this_year - 1)

        return data_now

    def collect_timed_data(self: 'TimeboundNetCDFReader',
                           datapoint: str,
                           year: int) -> ndarray:
        """
        Returns the data under the specified header, taken from the selected
        year.

        Subclasses must provide a data-set specific override of this method,
        since different datasets may have different structures.

        :param datapoint:
            The name of the variable requested from the dataset
        :param year:
            The year from which to collect data
        :return:
            The requested data, limited to that from the selected years
        """
        raise NotImplementedError
