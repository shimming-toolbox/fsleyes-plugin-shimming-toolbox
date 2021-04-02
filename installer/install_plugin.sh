#!/usr/bin/env bash

set -e

VENV_ID=1267b18e73341ad94da34474
VENV=pst_venv_$VENV_ID

# conda activate base
yes | conda create --name $VENV
yes | conda activate $VENV
yes | conda install -c conda-forge fsleyes
yes | conda install -c conda-forge wxpython=4.0.7
cd ..
python3 -m pip install ./fsleyes-plugin-shimming-toolbox
