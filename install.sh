
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
