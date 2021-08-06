#!/usr/bin/env bash

set -e

VENV_ID=1267b18e73341ad94da34474
VENV=pst_venv_$VENV_ID
ST_DIR=$HOME/shimming_toolbox
PYTHON_DIR=python
BIN_DIR=bin

# Print with color
# @input1: {info, code, error}: type of text
# rest of inputs: text to print
function print() {
  type=$1; shift
  case "$type" in
  # Display useful info (green)
  info)
    echo -e "\n\033[0;32m${*}\033[0m\n"
    ;;
  # To interact with user (no carriage return) (light green)
  question)
    echo -e -n "\n\033[0;92m${*}\033[0m"
    ;;
  # To display code that is being run in the Terminal (blue)
  code)
    echo -e "\n\033[0;34m${*}\033[0m\n"
    ;;
  # Warning message (yellow)
  warning)
    echo -e "\n\033[0;93m${*}\033[0m\n"
    ;;
  # Error message (red)
  error)
    echo -e "\n\033[0;31m${*}\033[0m\n"
    ;;
  esac
}

# Elegant exit with colored message
function die() {
  print error "$1"
  exit 1
}

# Run a command and display it in color. Exit if error.
# @input: string: command to run
function run() {
  ( # this subshell means the 'die' only kills this function and not the whole script;
    # the caller can decide what to do instead (but with set -e that usually means terminating the whole script)
    print code "$@"
    if ! "$@" ; then
      die "ERROR: Command failed."
    fi
  )
}


# Gets the shell rc file path based on the default shell.
# @output: THE_RC and RC_FILE_PATH vars are modified
function get_shell_rc_path() {
  if [[ "$SHELL" == *"bash"* ]]; then
    THE_RC="bash"
    RC_FILE_PATH="$HOME/.bashrc"
  elif [[ "$SHELL" == *"/sh"* ]]; then
    THE_RC="bash"
    RC_FILE_PATH="$HOME/.bashrc"
  elif [[ "$SHELL" == *"zsh"* ]]; then
    THE_RC="bash"
    RC_FILE_PATH="$HOME/.zshrc"
  elif [[ "$SHELL" == *"csh"* ]]; then
    THE_RC="csh"
    RC_FILE_PATH="$HOME/.cshrc"
  else
    find ~/.* -maxdepth 0 -type f
    die "ERROR: Shell was not recognized: $SHELL"
  fi
}

# Define sh files
get_shell_rc_path

# Update PATH variables based on Shell type
DISPLAY_UPDATE_PATH="export PATH=\"$ST_DIR/$BIN_DIR:\$PATH\""

# Installation text to insert in shell config file
function edit_shellrc() {
  # Write text common to all shells
  if ! grep -Fq "FSLEYES_PLUGIN_SHIMMING_TOOLBOX (installed on" $RC_FILE_PATH; then
      (
        echo
        echo ""
        echo "# FSLEYES_PLUGIN_SHIMMING_TOOLBOX (installed on $(date +%Y-%m-%d\ %H:%M:%S))"
        echo "$DISPLAY_UPDATE_PATH"
        echo "export ST_DIR=$ST_DIR"
        echo "alias shimming-toolbox='$ST_DIR/$BIN_DIR/shimming-toolbox.sh'"
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

# Install fsleyes
print info "Installing fsleyes"
yes | conda install -c conda-forge fsleyes=0.34.2

# Downgrade wxpython version due to bugs
print info "Downgrading wxpython to 4.0.7"
yes | conda install -c conda-forge wxpython=4.0.7

# Install fsleyes-plugin-shimming-toolbox
print info "Installing fsleyes-plugin-shimming-toolbox"
python -m pip install .

# Create launchers
print info "Creating launcher for fsleyes-plugin-shimming-toolbox..."
mkdir -p $ST_DIR/$BIN_DIR
# echo $ST_DIR/python/envs/$VENV/bin/*st_*
chmod +x shimming-toolbox.sh
cp shimming-toolbox.sh $ST_DIR/$BIN_DIR/ # || die "Problem creating launchers!"

# Activate the launchers
export PATH=$ST_DIR/$BIN_DIR:$PATH

edit_shellrc

print info "Open a new Terminal window to load environment variables, or run: source $RC_FILE_PATH"
