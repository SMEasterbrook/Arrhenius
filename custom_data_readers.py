from dataset_reader import TimeboundNetCDFReader
from resources import DATASET_PATH, DATASETS


class BerkeleyEarthTemperatureReader(TimeboundNetCDFReader):
    """
    A NetCDF dataset reader designed to read from the Berkeley Earth surface
    temperature dataset.
    """

    def __init__(self, file_name, format="NETCDF4"):
        super(BerkeleyEarthTemperatureReader, self).__init__(file_name, format)

    def collect_data(self, datapoint, year):
        # Lazy-open the dataset if it is not open already.
        self._open_dataset()

        data = self._dataset()
        var = data.variables[datapoint]

        # Translate the year into an index in the dataset.
        year_delta = year - 1850
        start_ind = year_delta * 12
        # Slice the dataset across the selected range of years.
        data = var[start_ind:start_ind + 12, :, :]
        return data

    def _adjust_values(self, data):
        dataset = self._dataset()
        clmt = dataset.variables['climatology']

        for i in range(0, 12):
            # Store arrays locally to avoid repeatedly indexing dataset.
            data_by_month = data[i]
            clmt_by_month = clmt[i]

            for j in range(0, 180):
                data_by_lat = data_by_month[j]
                clmt_by_lat = clmt_by_month[j]

                for k in range(0, 360):
                    # Only one array index required per addition instead
                    # of three gives significant performance increases.
                    data_by_lat[k] += clmt_by_lat[k]


if __name__ == '__main__':
    file = DATASET_PATH + DATASETS['temperature']
    reader = BerkeleyEarthTemperatureReader(file)

    temp_data = reader.read_newest('temperature')
    # Print values from temp_data to check correctness, etc.
