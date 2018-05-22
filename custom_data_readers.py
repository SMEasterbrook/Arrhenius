from dataset_reader import TimeboundNetCDFReader
from resources import DATASET_PATH, DATASETS


class BerkeleyEarthTemperatureReader(TimeboundNetCDFReader):
    """
    A NetCDF dataset reader designed to read from the Berkeley Earth surface
    temperature dataset.
    """

    def __init__(self, file_name, format="NETCDF4"):
        super(BerkeleyEarthTemperatureReader, self).__init__(file_name, format)

    def collect_timed_data(self, datapoint, year):
        # Lazy-open the dataset if it is not open already.
        self._open_dataset()

        data = self._dataset()
        var = data.variables[datapoint]

        # Translate the year into an index in the dataset.
        year_delta = year - 1850
        start_ind = year_delta * 12
        # Slice the dataset across the selected range of years.
        return var[start_ind:start_ind + 12, :, :]

    def collect_untimed_data(self, datapoint):
        self._open_dataset()

        data = self._dataset()
        var = data.variables[datapoint]
        return var