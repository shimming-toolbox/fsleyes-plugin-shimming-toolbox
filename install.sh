#!/usr/bin/env zsh

VENV_ID=1267b18e73341ad94da34474
VENV=pst_venv_$VENV_ID

conda activate base
yes | conda create --name $VENV
yes | conda activate $VENV
yes | conda install -c conda-forge fsleyes
yes | conda install -c conda-forge wxpython=4.0.7
cd ..
python3 -m pip install ./fsleyes-plugin-shimming-toolbox
python3 -m pip install --user pipx
curl -L https://github.com/shimming-toolbox/shimming-toolbox/archive/refs/tags/v0.1-beta.tar.gz > shimming-toolbox-0.1-beta.tar.gz
gunzip -c shimming-toolbox-0.1-beta.tar.gz | tar xopf -
cd shimming-toolbox-0.1-beta
pipx install . --force
