from data.reader import NetCDFReader, TimeboundNetCDFReader
from data.resources import DATASET_PATH, DATASETS


class ArrheniusDataReader(NetCDFReader):
    """
    A NetCDF dataset reader designed to read from the Arrhenius Project's
    dataset for Arrhenius' original gridded temperature and humidity data.

    The dataset only contains values for one year (1895), so its data is
    all considered two-dimensional, without any time dimension involved.
    For this reason, temperature and humidity data can be retrieved from
    the dataset using the collect_untimed_data method.
    """
    def __init__(self, format="NETCDF4"):
        file_name = DATASET_PATH + DATASETS['arrhenius']
        super(ArrheniusDataReader, self).__init__(file_name, format)


class BerkeleyEarthTemperatureReader(TimeboundNetCDFReader):
    """
    A NetCDF dataset reader designed to read from the Berkeley Earth surface
    temperature dataset.
    """

    def __init__(self, format="NETCDF4"):
        file_name = DATASET_PATH + DATASETS['temperature']['berkeley']
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


class NCEPHumidityReader(TimeboundNetCDFReader):
    """
    A NetCDF dataset reader specialized for reading from the NCEP/NCAR
    Reanalysis I dataset.
    """

    def __init__(self, format="NETCDF4"):
        file_name = DATASET_PATH + DATASETS['water']['NCEP/NCAR']
        super(NCEPHumidityReader, self).__init__(file_name, format)

    def collect_timed_data(self, datapoint, year):
        self._open_dataset()

        data = self._dataset()
        var = data.variables[datapoint]

        # Translate the year into an index in the dataset.
        year_delta = year - 1948
        start_ind = year_delta * 12
        # Slice the dataset across the selected range of years.
        return var[start_ind:start_ind + 12, 0, :, :]

    def latitude(self):
        return self.collect_untimed_data("lat")

    def longitude(self):
        return self.collect_untimed_data("lon")
