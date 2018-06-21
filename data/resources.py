<<<<<<< HEAD
from pathlib import Path
from os import path


DATASET_PATH = path.join(Path("..").absolute(), 'data', 'models/')
OUTPUT_REL_PATH = path.join(Path("..").absolute(), 'data', 'output/')
=======
DATASET_PATH = 'models/'
OUTPUT_PATH = 'output/'
>>>>>>> master

DATASETS = {
    'temperature': {
        'berkeley': 'Land_And_Ocean_LatLong1.nc'
    },
    'albedo': None,
    'carbon': None,
    'water': None
}
