from pathlib import Path
from os import path


DATASET_PATH = path.join(Path("..").absolute(), 'data', 'models/')
OUTPUT_REL_PATH = path.join(Path("..").absolute(), 'data', 'output/')

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
