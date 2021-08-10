#!/usr/bin/env bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
source $SCRIPT_DIR/utils.sh

set -e

VENV_ID=1267b18e73341ad94da34474
VENV=pst_venv_$VENV_ID
ST_DIR=$HOME/shimming_toolbox
PYTHON_DIR=python
BIN_DIR=bin


# Define sh files
get_shell_rc_path

# Update PATH variables based on Shell type
DISPLAY_UPDATE_PATH="export PATH=\"$ST_DIR/$BIN_DIR:\$PATH\""

# Installation text to insert in shell config file
function edit_shellrc() {
  # Write text common to all shells
  if ! grep -Fq "SHIMMINGTOOLBOX (installed on" $RC_FILE_PATH; then
      (
        echo
        echo ""
        echo "# SHIMMINGTOOLBOX (installed on $(date +%Y-%m-%d\ %H:%M:%S))"
        echo "$DISPLAY_UPDATE_PATH"
        echo "export ST_DIR=$ST_DIR"
        echo ""
      ) >> "$RC_FILE_PATH"
      else
          echo "$RC_FILE_PATH file already updated from previous install, continuing to next step."
  fi
}

source $ST_DIR/$PYTHON_DIR/etc/profile.d/conda.sh
# set +u
conda activate $VENV
# set -u

cd $ST_DIR
curl -L https://github.com/shimming-toolbox/shimming-toolbox/archive/refs/tags/v0.1-beta.tar.gz > shimming-toolbox-0.1-beta.tar.gz
gunzip -c shimming-toolbox-0.1-beta.tar.gz | tar xopf -
cd shimming-toolbox-0.1-beta
cp config/dcm2bids.json $ST_DIR/dcm2bids.json
python -m pip install .

# Create launchers for Python scripts
echo "Creating launchers for Python scripts..."
mkdir -p $ST_DIR/$BIN_DIR
echo $ST_DIR/python/envs/$VENV/bin/*st_*
for file in $ST_DIR/python/envs/$VENV/bin/*st_*; do
  cp "$file" $ST_DIR/$BIN_DIR/ # || die "Problem creating launchers!"
done

# Activate the launchers
export PATH=$ST_DIR/$BIN_DIR:$PATH

edit_shellrc

echo "Open a new Terminal window to load environment variables, or run: source $RC_FILE_PATH"
