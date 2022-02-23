#!/usr/bin/env bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
source $SCRIPT_DIR/utils.sh

set -e

ST_DIR=$HOME/shimming-toolbox

cd $ST_DIR

print info "Downloading Shimming-Toolbox"

ST_VERSION=12d8dba96c7b80d61c7250ca4e1d50f49b80e240

curl -L "https://github.com/shimming-toolbox/shimming-toolbox/archive/${ST_VERSION}.zip" > "shimming-toolbox-${ST_VERSION}.zip"

# Froze a commit, we can select a release later
# gunzip -c "shimming-toolbox-${ST_VERSION}.tar.gz" | tar xopf -
# unzip for now, when we use releases we can use the tar and gunzip
unzip -o "shimming-toolbox-${ST_VERSION}.zip"
cd "shimming-toolbox-${ST_VERSION}"
make install CLEAN=false

# Copy coil config file in shimming toolbox directory
cp "${ST_DIR}/shimming-toolbox-${ST_VERSION}/config/coil_config.json" "${ST_DIR}/coil_config.json"

print info "To launch the plugin, load the environment variables then run: shimming-toolbox"
