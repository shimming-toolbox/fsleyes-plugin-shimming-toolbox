#!/usr/bin/env bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
source $SCRIPT_DIR/utils.sh

set -e

ST_DIR=$HOME/shimming-toolbox

cd $ST_DIR

print info "Downloading Shimming-Toolbox"

curl -L https://github.com/shimming-toolbox/shimming-toolbox/archive/refs/heads/master.zip > shimming-toolbox-master.tar.gz
#gunzip -c shimming-toolbox-master.tar.gz | tar xopf -
#unzip for now
unzip -o shimming-toolbox-master.tar.gz
cd shimming-toolbox-master
make install

print info "To launch the plugin, load the environment variables then run: shimming-toolbox"
