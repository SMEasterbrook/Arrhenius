from pathlib import Path
from os import path, environ


MAIN_PATH_VAR = "ARRHENIUS_MAIN_PATH"

MAIN_PATH = environ.get(MAIN_PATH_VAR) or Path("..").absolute()
DATASET_PATH = path.join(MAIN_PATH, 'data', 'models/')
OUTPUT_REL_PATH = path.join(MAIN_PATH, 'website', 'output/')

DATASETS = {
    'arrhenius': "arrhenius_data.nc",
    'temperature': {
        'berkeley': 'Land_And_Ocean_LatLong1.nc'
    },
    'albedo': None,
    'carbon': None,
    'water': {
        'NCEP/NCAR': 'shum.mon.mean.nc'
    }
}
