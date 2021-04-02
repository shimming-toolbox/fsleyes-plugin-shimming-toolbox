#!/usr/bin/env bash

set -e

VENV_ID=1267b18e73341ad94da34474
VENV=pst_venv_$VENV_ID

yes | conda activate $VENV

cd ..
curl -L https://github.com/shimming-toolbox/shimming-toolbox/archive/refs/tags/v0.1-beta.tar.gz > shimming-toolbox-0.1-beta.tar.gz
gunzip -c shimming-toolbox-0.1-beta.tar.gz | tar xopf -
cd shimming-toolbox-0.1-beta
pipx install . --force
