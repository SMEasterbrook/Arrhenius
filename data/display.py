from os import path
from typing import List, Tuple

from data.resources import OUTPUT_REL_PATH
from data.reader import NetCDFReader
from data.writer import NetCDFWriter
from data.grid import LatLongGrid, GridDimensions,\
    extract_multidimensional_grid_variable

from core.output_config import global_output_center, ReportDatatype, Debug,\
    DATASET_VARS, IMAGES

from pathlib import Path
from mpl_toolkits.basemap import Basemap

import matplotlib
matplotlib.use("QT5Agg")
import matplotlib.pyplot as plt
import numpy as np


OUTPUT_FULL_PATH = path.join(Path('.').absolute(), OUTPUT_REL_PATH)

# Keys in the dictionary below.
VAR_TYPE = "Type"

VAR_ATTRS = "Attrs"
VAR_UNITS = "Units"
VAR_DESCRIPTION = "Desc"

# Data describing each variable in the dataset.
VARIABLE_METADATA = {
    ReportDatatype.REPORT_TEMP.value: {
        VAR_TYPE: np.float32,
        VAR_ATTRS: {
            VAR_UNITS: "Degrees Celsius",
            VAR_DESCRIPTION: "Final temperature of the grid cell that is"
                             "centered at the associated latitude and"
                             "longitude coordinates"
        }
    },
    ReportDatatype.REPORT_TEMP_CHANGE.value: {
        VAR_TYPE: np.float32,
        VAR_ATTRS: {
            VAR_UNITS: "Degrees Celsius",
            VAR_DESCRIPTION: "Temperature change observed due to CO2 change"
                             "for the grid cell that is centered at the"
                             "associated latitude and longitude coordinates"
        }
    },
    ReportDatatype.REPORT_HUMIDITY.value: {
        VAR_TYPE: np.float32,
        VAR_ATTRS: {
            VAR_UNITS: "Percent Saturation",
            VAR_DESCRIPTION: "Final relative humidity of the grid cell"
                             "centered at the associated latitude and"
                             "longitude coordinates"
        }
    },
    ReportDatatype.REPORT_ALBEDO.value: {
        VAR_TYPE: np.float32,
        VAR_ATTRS: {
            VAR_UNITS: "Decimal Absorption",
            VAR_DESCRIPTION: "Percent of incoming solar energy absorbed"
                             "by the Earth's surface within the grid cell"
                             "centered at the associated latitude and"
                             "longitude coordinates"
        }
    },
}


class ModelImageRenderer:
    """
    A converter between gridded climate data and image visualizations of the
    data. Displays data in the form of nested lists or arrays as an overlay
    on a world map projection.
    """
    def __init__(self: 'ModelImageRenderer',
                 data: np.ndarray) -> None:
        """
        Instantiate a new ModelImageReader.

        Data to display is provided through the data parameter. This parameter
        may either by an array, or an array-like structure such as a nested
        list. the There must be three dimensions to the data: time first,
        followed by latitude and longitude.

        :param data:
            An array-like structure of numeric values, representing temperature
            over a globe
        """
        self._data = data
        self._grid = GridDimensions((len(data), len(data[0])), "count")

        # Some parameters for the visualization are also left as attributes.
        self._continent_linewidth = 0.5
        self._lat_long_linewidth = 0.1

    def save_image(self: 'ModelImageRenderer',
                   out_path: str,
                   min_max_grades: Tuple[float, float] = (-8, 8)) -> None:
        """
        Produces a .PNG formatted image file containing the gridded data
        overlaid on a map projection.

        The map is displayed in equirectangular projection, labelled with
        lines of latitude and longitude at the intersection between
        neighboring grid cells. The grid cells are filled in with a colour
        denoting the magnitude of the temperature at that cell.

        The optional min_max_grades parameter specifies the lower bound and
        the upper bound of the range of values for which different colours
        are assigned. Any grid cell with a temperature value below the first
        element of min_max_grades will be assigned the same colour. The same
        applies to any cell with a temperature greater than min_max_grades[1].
        The default boundaries are -60 and 40.

        The image is saved at the specified absolute or relative filepath.

        :param out_path:
            The location where the image file is created
        :param min_max_grades:
            A tuple containing the boundary values for the colorbar shown in
            the image file
        """
        if min_max_grades is not None and len(min_max_grades) != 2:
            raise ValueError("Color grade boundaries must be given in a tuple"
                             "of length 2 (is length {})"
                             .format(len(min_max_grades)))
        # Create an empty world map in equirectangular projection.
        map = Basemap(llcrnrlat=-90, llcrnrlon=-180,
                      urcrnrlat=90, urcrnrlon=180)
        map.drawcoastlines(linewidth=self._continent_linewidth)

        # Construct a grid from the horizontal and vertical sizes of the cells.
        grid_by_width = self._grid.dims_by_width()

        lat_val = -90.0
        lats = []
        while lat_val <= 90:
            lats.append(lat_val)
            lat_val += grid_by_width[0]

        lon_val = -180.0
        lons = []
        while lon_val <= 180:
            lons.append(lon_val)
            lon_val += grid_by_width[1]

        map.drawparallels(lats, linewidth=self._lat_long_linewidth)
        map.drawmeridians(lons, linewidth=self._lat_long_linewidth)
        x, y = map(lons, lats)

        # Overlap the gridded data on top of the map, and display a colour
        # legend with the appropriate boundaries.
        img_bin = map.pcolormesh(x, y, self._data, cmap=plt.cm.get_cmap("jet"))

        map.colorbar(img_bin)
        plt.clim(min_max_grades[0], min_max_grades[1])

        fig = plt.gcf()
        fig.canvas.draw()
        pixels = fig.canvas.tostring_rgb()
        img = np.fromstring(pixels, dtype=np.uint8, sep='')
        img = img.reshape(fig.canvas.get_width_height()[::-1] + (3,))
        img = img[118:-113, 80:-30, :]

        alphas = np.ones(img.shape[:2], dtype=np.uint8) * 255
        alphas[:, -65:-57] = 0
        alphas[:9, :-43] = 0
        alphas[-8:, :-43] = 0

        for i in range(img.shape[0]):
            for j in range(img.shape[1] - 43, img.shape[1]):
                pixel = tuple(img[i, j, :])
                # if sum(pixel) == 765:
                if sum(pixel) < 450 and j >= img.shape[1] - 33:
                    img[i, j, :] = [147, 149, 152]
                elif j >= img.shape[1] - 33 or i < 9 or i > img.shape[0] - 9:
                    alphas[i, j] = 0

        img = np.dstack((img, alphas))
        plt.imsave(fname=out_path, arr=img)
        plt.close()


def write_image_type(data: np.ndarray,
                     output_path: str,
                     data_type: str,
                     run_id: str,
                     scale: Tuple[float, float] = (-8, 8)) -> None:
    """
    Write out a category of output, given by the parameter data, to a
    directory with the name given by output_path. One image file will
    be produced for every index in the highest-level dimension in the
    data.

    The third ard fourth parameters specify the name of the variable
    being represented by this set of images, and the name of the model
    run respectively. EAch image's name will begin with run_id followed
    by an underscore followed by data_type. These will be followed by a
    number indicating the order in which the images were written.

    :param data:
        A single-variable grid derived from Arrhenius model output
    :param output_path:
        The directory where image files will be stored
    :param data_type:
        The name of the variable on which the data is based
    :param run_id:
        A unique name for the current model run
    :param scale:
        The lower and upper limits to the colorbar on each image
    """
    Path(output_path).mkdir(exist_ok=True)
    output_center = global_output_center()
    output_center.submit_output(Debug.PRINT_NOTICES,
                                "Preparing to write {} images"
                                .format(data_type))

    img_base_name = "_".join([run_id, data_type])
    file_ext = '.png'

    annual_avg = np.array([np.mean(data, axis=0)])
    data = np.concatenate([annual_avg, data], axis=0)

    # Write an image file for each time segment.
    for i in range(len(data)):
        img_name = "_".join([img_base_name, str(i) + file_ext])
        img_path = path.join(output_path, img_name)

        # Produce and save the image.
        output_center.submit_output(Debug.PRINT_NOTICES,
                                    "\tSaving image file {}...".format(i))
        g = ModelImageRenderer(data[i])
        g.save_image(img_path, scale)


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
                 data: List['LatLongGrid']) -> None:
        """
        Instantiate a new ModelOutput object.

        Model data is provided through the data parameter, through a list of
        grid objects. Each grid in the list represents a segment of time, such
        as a month or a season. All grids must have the same dimensions.

        :param data:
            A list of latitude-longitude grids of data
        """
        # Create output directory if it does not already exist.
        parent_out_dir = Path(OUTPUT_FULL_PATH)
        parent_out_dir.mkdir(exist_ok=True)

        self._data = data
        self._grid = data[0].dimensions()
        self._dataset = NetCDFWriter()

    def write_dataset(self: 'ModelOutput',
                      data: List['LatLongGrid'],
                      dir_path: str,
                      dataset_name: str) -> None:
        """
        Produce a NetCDF dataset, with the name given by dataset_name.nc,
        containing the variables in the data parameter that the output
        controller allows. The dataset will be written to the specified
        path in the file system.

        The dataset contains all the dimensions that are used in the data
        (e.g. time, latitude, longitude) as well as variables including
        final temperature, temperature change, humidity, etc. according
        to which of the ReportDatatype output types are enabled in the
        current output controller.

        :param data:
            Output from an Arrhenius model run
        :param dir_path:
            The directory where the dataset will be written
        :param dataset_name:
            The name of the dataset
        """
        # Write the data out to a NetCDF file in the output directory.
        grid_by_count = self._grid.dims_by_count()
        output_path = path.join(dir_path, dataset_name)

        global_output_center().submit_output(Debug.PRINT_NOTICES,
                                             "Writing NetCDF dataset...")
        self._dataset.global_attribute("description", "Output for an"
                                                      "Arrhenius model run.")\
            .dimension('time', np.int32, len(data), (0, len(data)))\
            .dimension('latitude', np.int32, grid_by_count[0], (-90, 90)) \
            .dimension('longitude', np.int32, grid_by_count[1], (-180, 180)) \

        for output_type in ReportDatatype:
            variable_data =\
                extract_multidimensional_grid_variable(data,
                                                       output_type.value)
            global_output_center().submit_output(output_type, variable_data,
                                                 output_type.value)

        self._dataset.write(output_path)

    def write_dataset_variable(self: 'ModelOutput',
                               data: np.ndarray,
                               data_type: str) -> None:
        """
        Prepare to write data into a variable by the name of data_type
        in this instance's NetCDF dataset file. Apply this variable's
        dimensions and type, along with several attributes.

        :param data:
            A single-variable grid taken from Arrhenius model output
        :param data_type:
            The name of the variable as it will appear in the dataset
        """
        dims_map = [
            [],
            ['latitude'],
            ['latitude', 'longitude'],
            ['time', 'latitude', 'longitude'],
            ['time', 'level', 'latitude', 'longitude']
        ]

        global_output_center().submit_output(Debug.PRINT_NOTICES,
                                             "Writing {} to dataset"
                                             .format(data_type))
        variable_type = VARIABLE_METADATA[data_type][VAR_TYPE]
        self._dataset.variable(data_type, variable_type, dims_map[data.ndim])

        for attr, val in VARIABLE_METADATA[data_type][VAR_ATTRS].items():
            self._dataset.variable_attribute(data_type, attr, val)

        self._dataset.data(data_type, data)

    def write_images(self: 'ModelOutput',
                     data: List['LatLongGrid'],
                     output_path: str,
                     run_id: str = "",
                     scale: Tuple[float, float] = (-8, 8)) -> None:
        """
        Produce a series of maps displaying some of the results of an
        Arrhenius model run according to what variable the output controller
        allows. Images are stored in a directory given by output_path.

        One image will be produced per time segment per variable for which
        output is allowed by the output controller, based on which
        ReportDatatype output types are enabled. The optional argument
        img_base_name specifies a prefix that will be added to each of the
        image files to identify which model run they belong to.

        :param data:
            The output from an Arrhenius model run
        :param output_path:
            The directory where image files will be stored
        :param run_id:
            A prefix that will start off the names of all the image files
        :param scale:
            The lower and upper limits to the colorbar on each image
        """
        output_controller = global_output_center()

        # Attempt to output images for each variable output type.
        for output_type in ReportDatatype:
            variable_name = output_type.value
            variable = extract_multidimensional_grid_variable(data,
                                                              variable_name)
            img_type_path = path.join(output_path, variable_name)

            output_controller.submit_output(output_type, variable,
                                            img_type_path,
                                            variable_name,
                                            run_id,
                                            scale)

    def write_output(self: 'ModelOutput',
                     run_title: str,
                     scale: Tuple[float, float] = (-8, 8)) -> None:
        """
        Produce NetCDF data files and image files from the provided data, and
        a directory with the name dir_name to hold them.

        One image file is created per time segment in the data. In the
        case of Arrhenius' model, this is one per season. Only one NetCDF data
        file is produced, in which all time segments are present.

        :param run_title:
            A unique name for the output directory, associated with the model
            run's unique configuration
        :param scale:
            The lower and upper limits to the colorbar on each image
        """
        # Create a directory for this model output if none exists already.
        out_dir_path = path.join(OUTPUT_FULL_PATH, run_title)
        out_dir = Path(out_dir_path)
        out_dir.mkdir(exist_ok=True)

        output_controller = global_output_center()
        output_controller.submit_collection_output((DATASET_VARS,),
                                                   self._data,
                                                   out_dir_path,
                                                   run_title + ".nc")
        output_controller.submit_collection_output((IMAGES,),
                                                   self._data,
                                                   out_dir_path,
                                                   run_title,
                                                   scale)


def save_from_dataset(dataset_parent: str,
                      run_id: str,
                      var_name: str,
                      time_seg: int,
                      scale: Tuple[float, float] = (-8, 8)) -> bool:
    """
    Produce a set of image outputs based on a dataset, written by a
    previous run of the Arrhenius model. This dataset is stored in the
    directory given by the path dataset_parent, and is named run_id.
    run_id need not include the .nc file extension.

    The images produced are under the variable var_name in the dataset,
    and only in the time unit given by time_seg. If time_seg is 0, then
    one image will be produced containing averages over the datapoints
    in all time units.

    The colourbar boundaries on any of these images are given by the
    scale parameter.

    Returns True iff a new image was produced by this call, i.e. iff it
    did not exist prior to the call.

    :param dataset_parent:
        A path to the directory containing the dataset
    :param run_id:
        The name of the dataset, as well as of the output image files
    :param var_name:
        The variable from the dataset that will be used to generate the images
    :param time_seg:
        An integer specifying which time unit to use data from
    :param scale:
        The lower and upper limits to the colorbar on each image
    :return:
        True iff a new image file was created
    """
    # Locate or create a directory to contain image files.
    parent_path = path.join(dataset_parent, var_name)
    Path(parent_path).mkdir(exist_ok=True)

    # Detect if the desired image file already exists.
    file_name = "_".join([run_id, var_name, str(time_seg)])
    img_path = path.join(parent_path, file_name)

    if not Path(img_path).is_file():
        # Locate the dataset and read the desired variable from it.
        dataset_path = path.join(dataset_parent, run_id + ".nc")
        reader = NetCDFReader(dataset_path)
        data = reader.collect_untimed_data(var_name)

        # Extract only the requested parts of the data.
        if time_seg == 0:
            selected_time_data = data.mean(axis=0)
        else:
            selected_time_data = data[time_seg - 1]

        # Write the new image file.
        img_writer = ModelImageRenderer(selected_time_data)
        img_writer.save_image(img_path, scale)
        reader.close()

        created = True
    else:
        created = False

    return created


def write_model_output(data: List['LatLongGrid'],
                       run_title: str,
                       scale: Tuple[float, float] = (-8, 8)) -> None:
    """
    Write the results of a model run (data) to disk, in the form of a
    NetCDF dataset and a series of image files arranged into a directory
    with the name given by output_title.

    :param data:
        The output from an Arrhenius model run
    :param run_title:
            A unique name for the output directory, associated with the model
            run's unique configuration
    :param scale:
        The lower and upper limits to the colorbar on each image
    """
    writer = ModelOutput(data)
    controller = global_output_center()

    # Upload collection handlers for dataset and image file collections.
    controller.register_collection(DATASET_VARS, handler=writer.write_dataset)
    controller.register_collection(IMAGES, handler=writer.write_images)

    # Change several output type handlers within each collection.
    for output_type in ReportDatatype:
        controller.change_handler_if_enabled(output_type,
                                             (DATASET_VARS,),
                                             writer.write_dataset_variable)
        controller.change_handler_if_enabled(output_type,
                                             (IMAGES,),
                                             write_image_type)

    writer.write_output(run_title, scale)
