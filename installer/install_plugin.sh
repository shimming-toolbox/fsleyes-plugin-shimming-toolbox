#!/usr/bin/env bash

set -e

VENV_ID=1267b18e73341ad94da34474
VENV=pst_venv_$VENV_ID
ST_DIR=$HOME/shimming_toolbox
PYTHON_DIR=python

# conda activate base
source $ST_DIR/$PYTHON_DIR/etc/profile.d/conda.sh
# set +u
conda activate $VENV
# set -u
yes | conda install -c conda-forge fsleyes
yes | conda install -c conda-forge wxpython=4.0.7
echo "Installing fsleyes-plugin-shimming-toolbox"
python -m pip install .
