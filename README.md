# The Arrhenius Project

This project is a programmatic reconstruction of Svante Arrhenius' 1896 climate model, widely regarded as the first global climate model in history. The reconstruction attempts to be as true as possible to the original model, using the same equations and the same data. At the same time, the reconstructed model allows several modes for exploration of properties of the model, such as extension to a multi-layered atmosphere system, and use of alternative datasets.

This project could be used to test the performance of the Arrhenius model, explore its sources of error and how it performs when more expensive computations are applied than were feasible at the time of the original model.

## Outputs

A variety of outputs can be produced by the model, defaulting to a NetCDF dataset and a set of image files plotting temperature change through the model run on a world map. The dataset currently contains only temperature change data from the model run.



## Running the Model

The model run is controlled by a set of configuration options, usually specified by a JSON file that is parsed and loaded into an ArrheniusConfig object. Default options are available via functions:

```
import core.configuration as cnf
config = cnf.default_config()
```

Custom JSON can be specified by configuration by reading the JSON file and passing its contents to a separate function:

```
json_file = open(path_to_file, "rb")
json_config = json_file.read()
config = cnf.from_json_string(json_config)
```

These configuration objects and an OutputConfig instance must be passed to a ModelRun object constructor to initialize the run and its options. Calling the run_model method of the object will compute model results.

```
import core.output_config as out_cnf
from runner import ModelRun

out_config = out_cnf.default_output_config()
runner = ModelRun(config, out_config)
results = runner.run_model()
```

A variety of methods are available to change both the model configuration and the output configuration after their objects are initialized. An example is given in the main function inside runner.py.

## Installation

To run the project, clone this repository or download it as a zipfile. For installing dependencies, use of the Anaconda package manager is recommended. A script is provided with the project that installs all dependencies using Anaconda:

```
./install.sh
```

Users of other package managers may install the same packages as in the file, except using a package manager other than Anaconda. The installation script does not install Lowtran, an atmospheric data API that is the core of several modes of the model. There are several ways to install Lowtran, such as through pip:

```
pip install lowtran
```

Alternatively, the source code can be downloaded and compiled separately. A Fortran compiler such as gfortran is required. The following command can be used to compile the code from inside the src directory in the lowtran project:

```
f2py -m lowtran7 -c lowtran7.f
```

When Lowtran is successfully installed and compiled, the Arrhenius Project should be ready to run.
