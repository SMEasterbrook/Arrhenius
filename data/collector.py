

class ClimateDataCollector:
    """
    Assembles various types of data, including surface temperature, albedo,
    and atmospheric absorbption coefficients, and ensures that data formatting
    is consistent between data types.

    Designed for flexibility in data sources, and allows for sources to be
    swapped out during execution. This may be used to try out different dataset
    files to test performance, or to input stub or mock data providers to help
    test functionality.
    """

    def __init__(self):
        self._temp_source = None
        self._albedo_source = None
        self._absorbance_source = None
        self._grid_data = None
        self._absorbance_data = None

    def use_temperature_source(self, temp_src):
        """
        Load a new temperature provider function, used as an access point to
        temperature data. Returns the collector object, so that repeated
        builder method calls can be continued.

        Calling this function voids any previously cached grid data, including
        albedo values.

        :param temp_src:
            A new temperature provider function
        :return:
            This ClimateDataCollector
        """
        self._temp_source = temp_src
        self._grid_data = None
        return self

    def use_albedo_source(self, albedo_src):
        """
        Load a new albedo provider function, used as an access point to
        surface albedo data. Returns the collector object, so that repeated
        builder method calls can be continued.

        Calling this function voids any previously cached grid data, including
        temperature values.

        :param albedo_src:
            A new albedo provider function
        :return:
            This ClimateDataCollector
        """
        self._albedo_source = albedo_src
        self._grid_data = None
        return self

    def use_absorbance_source(self, absorbance_src):
        """
        Load a new absorbance provider function, used as an access point to
        atmospheric heat absorbance data. Returns the collector object, so
        that repeated builder method calls can be continued.

        Calling this function voids any previously cached absorbance data.

        :param absorbance_src:
            A new absorbance provider function
        :return:
            This ClimateDataCollector
        """
        self._absorbance_source = absorbance_src
        self._absorbance_data = None
        return self

    def get_gridded_data(self):
        """
        Combines and returns all 2-dimensional gridded surface data, including
        surface temperature and surface albedo.

        Data is returned in a 2-dimensional array of dictionaries, where each
        dictionary acts like a JSON object. The temperature field in the dict
        refers to an array of 12 monthly temperature values, with index 0
        being January and index 11 being December. The albedo field refers to
        the grid cell's surface albedo.

        Raises an exception if not all of the required data providers have
        been loaded through builder methods.

        :return:
            An array of 1-degree gridded surface data
        """
        if self._grid_data is not None:
            return self._grid_data
        elif self._temp_source is None:
            raise PermissionError("No temperature provider function selected")
        elif self._albedo_source is None:
            raise PermissionError("No albedo provider function selected")

        temp_data = self._temp_source()
        albedo_data = self._albedo_source()
        self._grid_data = []

        # Start building a 2-D nested list structure for output, row by row.
        for i in range(180):
            # Holding row lists in memory prevents excess list lookups.
            albedo_row = albedo_data[i]
            # Start creating a new list column for entry into the output list.
            longitude_row = []

            for j in range(360):
                albedo = albedo_row[j]
                temp = temp_data[:, i, j]

                # Create JSON-like grid cell dictionary with gridded data.
                grid_cell_obj = {
                    'temperature': temp,
                    'albedo': albedo
                }

                # Add new objects into the 2-D nested lists.
                longitude_row.append(grid_cell_obj)
            self._grid_data.append(longitude_row)

        return self._grid_data

    def get_absorbance_data(self):
        """
        Builds and returns atmospheric absorbance data.

        This data may be in the form of a float, if the collector is using
        a simple absorbance provider function; otherwise, it may also return
        a 2-D grid with an absorbance value for different areas of the
        atmosphere. It should be possible to predict which type will be
        returned, given which absorbance provider function is in use.

        Raises an exception if not all of the required data providers have
        been loaded through builder methods.

        :return:
            Global or gridded atmospheric heat absorbance data
        """
        if self._absorbance_data is not None:
            return self._absorbance_data
        elif self._absorbance_source is None:
            raise PermissionError("No absorbance provider function selected")

        self._absorbance_data = self._absorbance_source()
        return self._absorbance_data
