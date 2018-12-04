
# Create a new environment for the project, given as the first argument.
if [ $# -gt 0 ]
then
    conda create -n $1
    source activate $1
fi

# Install dependencies.
# Note: Some project dependencies are implicit, as they are installed
#       alongside one of the following packages.
conda install -c conda-forge pyresample netCDF4 basemap jsonschema frozendict

# Install project packages.
pip install -e .

# Write environment variables that are used by the project.
export PYTHONHASHSEED=0
export ARRHENIUS_MAIN_PATH=`pwd`

# Download data files from remote sources
wget -nc -P data/models http://berkeleyearth.lbl.gov/auto/Global/Gridded/Land_and_Ocean_LatLong1.nc
wget -nc -P data/models ftp://ftp.cdc.noaa.gov/Datasets/ncep.reanalysis.derived/pressure/air.mon.mean.nc
wget -nc -P data/models ftp://ftp.cdc.noaa.gov/Datasets/ncep.reanalysis.derived/pressure/rhum.mon.mean.nc