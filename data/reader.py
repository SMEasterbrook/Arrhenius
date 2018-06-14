from netCDF4 import Dataset
from datetime import datetime


class TimeboundNetCDFReader:
    """
    A dataset reader for NetCDF files. Provides read-only access to existing
    NetCDF data. Tailored for datasets that have a notion of time, with
    methods of accepting data from only certain years.
    """
    def __init__(self, file_name, format="NETCDF4"):
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

    def _open_dataset(self):
        """ Ensure the data reader's NetCDF dataset has been opened. """
        if self._data is None:
            self._data = Dataset(self._file, self._file_mode,
                                 self._file_format)

    def _dataset(self):
        return self._data

    def read_newest(self, datapoint):
        """
        Retrieve the data under the heading specified by var, limited to the
        current year. Only applies to datasets that have a time value for
        every datapoint.

        :param datapoint:
            The heading of the data desired from the dataset
        :return:
            The requested data, taken only for the past year
        """
        today = datetime.now()
        this_year = int(today.year)
        data_now = self.collect_timed_data(datapoint, this_year - 1)

        return data_now

    def collect_timed_data(self, datapoint, years):
        """
        Returns the data under the specified header, taken from the selected
        range of years.

        Subclasses must provide a data-set specific override of this method,
        since different datasets may have different structures.

        :param datapoint:
            The heading of the required data
        :param years:
            The range of years from which to collect data
        :return:
            The requested data, limited to that from the selected years
        """
        raise NotImplementedError

    def collect_untimed_data(self, datapoint):
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
        return var

    def latitude(self):
        """
        Returns the NetCDF data file's latitude variable values.

        :return: The dataset's latitude variable
        """
        raise NotImplementedError

    def longitude(self):
        """
        Returns the NetCDF data file's longitude variable values.

        :return: The dataset's longitude variable
        """
        raise NotImplementedError
