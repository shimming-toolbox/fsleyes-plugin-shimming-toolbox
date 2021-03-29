#!/usr/bin/env zsh

set -e

VENV_ID=1267b18e73341ad94da34474
VENV=pst_venv_$VENV_ID

yes | conda activate $VENV
python3 -m pip install --user pipx
python3 -m pipx ensurepath

echo "Package pipx successfully installed. To use pipx, restart your shell."
