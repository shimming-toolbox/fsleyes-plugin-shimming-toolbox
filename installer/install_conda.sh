#!/usr/bin/env bash

set -e

if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    apt-get install -y curl
    CONDA_INSTALLER=Miniconda3-latest-Linux-x86_64.sh
elif [[ "$OSTYPE" == "darwin"* ]]; then
    CONDA_INSTALLER=Miniconda3-latest-MacOSX-x86_64.sh
elif [[ "$OSTYPE" == "cygwin" ]]; then
    # POSIX compatibility layer and Linux environment emulation for Windows
    echo "Invalid operating system"
    exit 1
elif [[ "$OSTYPE" == "msys" ]]; then
    # Lightweight shell and GNU utilities compiled for Windows (part of MinGW)
    echo "Invalid operating system"
    exit 1
elif [[ "$OSTYPE" == "win32" ]]; then
    echo "Invalid operating system"
    exit 1
elif [[ "$OSTYPE" == "freebsd"* ]]; then
    echo "Invalid operating system"
    exit 1
else
    echo "Invalid operating system"
    exit 1
fi

CONDA_INSTALLER_URL=https://repo.anaconda.com/miniconda/$CONDA_INSTALLER

installConda() {
    mkdir tmp
    cd tmp
    curl -O $CONDA_INSTALLER_URL
    bash $CONDA_INSTALLER -b -p $HOME/miniconda3
    export PATH=$HOME/miniconda3/bin:$PATH
    source $HOME/miniconda3/bin/activate
}

conda list || installConda
