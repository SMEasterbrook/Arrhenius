from data.reader import NetCDFReader, TimeboundNetCDFReader
from data.resources import DATASET_PATH, DATASETS

from numpy import ndarray


class ArrheniusDataReader(NetCDFReader):
    """
    A NetCDF dataset reader designed to read from the Arrhenius Project's
    dataset for Arrhenius' original gridded temperature and humidity data.
    The dataset only contains values for one year (1895), so its data is
    all considered two-dimensional, without any time dimension involved.
    For this reason, temperature and humidity data can be retrieved from
    the dataset using the collect_untimed_data method.
    """
    def __init__(self: 'ArrheniusDataReader',
                 format: str = "NETCDF4") -> None:
        file_name = DATASET_PATH + DATASETS['arrhenius']
        super(ArrheniusDataReader, self).__init__(file_name, format)


class BerkeleyEarthTemperatureReader(TimeboundNetCDFReader):
    """
    A NetCDF dataset reader designed to read from the Berkeley Earth surface
    temperature dataset.
    """

    def __init__(self: 'BerkeleyEarthTemperatureReader',
                 format: str = "NETCDF4") -> None:
        file_name = DATASET_PATH + DATASETS['temperature']['berkeley']
        super(BerkeleyEarthTemperatureReader, self).__init__(file_name, format)

    def collect_timed_data(self: 'BerkeleyEarthTemperatureReader',
                           datapoint: str,
                           year: int) -> ndarray:
        # Lazy-open the dataset if it is not open already.
        self._open_dataset()

        data = self._dataset()
        var = data.variables[datapoint]

        # Translate the year into an index in the dataset.
        year_delta = year - 1850
        start_ind = year_delta * 12
        # Slice the dataset across the selected range of years.
        return var[start_ind:start_ind + 12, :, :]


class NCEPReader(TimeboundNetCDFReader):
    """
    A NetCDF dataset reader specialized for reading from the NCEP/NCAR
    Reanalysis I dataset.
    """

    def __init__(self: 'NCEPReader',
                 data_type: str,
                 format: str = "NETCDF4") -> None:
        file_name = DATASET_PATH + DATASETS[data_type]['NCEP/NCAR']
        super(NCEPReader, self).__init__(file_name, format)

    def collect_timed_data(self: 'NCEPReader',
                           datapoint: str,
                           year: int) -> ndarray:
        self._open_dataset()

        data = self._dataset()
        var = data.variables[datapoint]

        # Translate the year into an index in the dataset.
        year_delta = year - 1948
        start_ind = year_delta * 12
        # Slice the dataset across the selected range of years.
        return var[start_ind:start_ind + 12, 0, :, :]

    def collect_layer_data(self: 'NCEPReader',
                             datapoint: str,
                             layer_num: int) -> ndarray:
        """
        Collect the data for the specified datapoint for a single layer
        across the whole time of the dataset.

        :param datapoint:
            The name of the variable requested from the dataset
        :param layer_num:
            The layer in the dataset to choose, with 1 being the lowest
            in altitude and 8 being the highest
        :return:
            An array of the relative humidity values across the 1900's
        """
        self._open_dataset()

        data = self._dataset()
        var = data.variables[datapoint]

        return var[:, layer_num, :, :]

    def collect_timed_layered_data(self: 'NCEPReader',
                                 datapoint: str,
                                 year: int) -> ndarray:
        self._open_dataset()

        data = self._dataset()
        var = data.variables[datapoint]

        # Translate the year into an index in the dataset.
        year_delta = year - 1948
        start_ind = year_delta * 12

        return var[start_ind:start_ind + 12, :, :, :]

    def pressure(self: 'NCEPReader') -> ndarray:
        return self.collect_untimed_data("level")

    def latitude(self: 'NCEPReader') -> ndarray:
        return self.collect_untimed_data("lat")

    def longitude(self: 'NCEPReader') -> ndarray:
        return self.collect_untimed_data("lon")
