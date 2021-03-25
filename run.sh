#!/usr/bin/env zsh

set -e

VENV_ID=1267b18e73341ad94da34474
VENV=pst_venv_$VENV_ID

conda activate $VENV
fsleyes &
