import os
from typing import List, Tuple, Union

from resources import OUTPUT_REL_PATH

from pathlib import Path
from mpl_toolkits.basemap import Basemap
import matplotlib.pyplot as plt


OUTPUT_FULL_PATH = os.path.join(Path('.').absolute(), OUTPUT_REL_PATH)


class ModelImageRenderer:
    """
    A converter between gridded climate data and image visualizations of the
    data. Displays data in the form of nested lists or arrays as an overlay
    on a world map projection.
    """
    def __init__(self: 'ModelImageRenderer',
                 data: List[Union[List, float]],
                 grid: Tuple[int] = (1, 1)) -> None:
        """
        Instantiate a new ModelImageReader.

        Data to display is provided through the data parameter. This parameter
        may either by an array, or an array-like structure such as a nested
        list. the There must be three dimensions to the data: time first,
        followed by latitude and longitude.

        The time dimension can be any size (including 1), but the latitude and
        longitude dimensions must match the numbers given in the second grid
        parameter.

        The grid must be a tuple of two numbers which represent the width of
        each grid cell in degrees latitude and longitude, respectively.

        :param data:
            An array-like structure of numeric values, representing temperature
            over a globe
        :param grid:
            The latitude and longitude widths of a cell in the data's grid
        """
        self._data = data
        self._grid = grid

        # Some parameters for the visualization are also left as attributes.
        self._linewidth = 0.5

    def save_image(self: 'ModelImageRenderer',
                   out_path: str) -> None:
        """
        Produces a .PNG formatted image file containing the gridded data
        overlaid on a map projection.

        The map is displayed in equirectangular projection, without any lines
        of latitude or longitude shown. Instead, each grid cell is filled in
        on the inside with a colour unique to the value within that cell.

        The image is saved at the specified absolute or relative filepath.

        :param out_path:
            The location where the image file is created
        """
        # Create an empty world map in equirectangular projection.
        map = Basemap(llcrnrlat=-90, llcrnrlon=-180,
                      urcrnrlat=90, urcrnrlon=180)
        map.drawcoastlines(linewidth=self._linewidth)

        # Construct a grid from the horizontal and vertical sizes of the cells.
        lats = list(range(-90, 91, self._grid[0]))
        lons = list(range(-180, 181, self._grid[1]))
        x, y = map(lons, lats)

        # Overlap the gridded data on top of the map.
        img = map.pcolormesh(x, y, self._data)
        map.colorbar(img)
        # Save the image and clear added components from memory
        plt.savefig(out_path)
        plt.close()


class ModelOutput:
    """
    A general-purpose center for all forms of output. Responsible for
    organization of program output into folders.

    The output of a program is defined as the temperature data produced by
    a run of the model. This data may be saved in the form of a data file
    (such as a NetCDF file) and/or as image representations, and/or in other
    data formats.

    All of these output types are produced side-by-side, and stored in their
    own directory to keep data separate from different model runs.
    """

    def __init__(self: 'ModelOutput',
                 title: str,
                 data: List[Union[List, float]],
                 data_grid: Tuple[int]) -> None:
        """
        Instantiate a new ModelOutput object.

        Model data is provided through the data parameter, which must be an
        array or array-like structure (such as a nested list) of the right
        dimensions. The first dimension is time, and can contain any number
        of elements; the second and third dimensions are latitude and
        longitude, respectively. The number of elements in these dimensions
        must be able to be multiplied by the corresponding grid cell width
        in the grid to gve 180 degrees latitude and 360 degrees longitude.

        The grid must be a tuple of two numbers which represent the width of
        each grid cell in degrees latitude and longitude, respectively.

        Finally, the title parameter gives the name of the directory that
        will store output files. This directory will be located within a
        directory called 'output' within the program's running directory.
        Output files will also be named after this title, with possible
        deviations, for example to denote between different seasons amongst
        a set of output files that each represents a season.

        :param title:
            The base name of the output files, and of the directory that will
            store them
        :param data:
            An array-like structure of numeric values, representing temperature
            over a globe
        :param data_grid:
            The latitude and longitude widths of a cell in the data's grid
        """
        # Create output directory if it does not already exist.
        parent_out_dir = Path(OUTPUT_FULL_PATH)
        parent_out_dir.mkdir(exist_ok=True)

        self._title = title
        self._data = data
        self._grid = data_grid

