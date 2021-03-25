

# You can set these variables from the command line.
# SPHINXBUILD   = python -msphinx
# SPHINXPROJ    = SpinalCordToolbox

# Put it first so that "make" without argument is like "make help".
# help:
# 	TODO

# .PHONY: help Makefile

install:
	conda init zsh
	zsh -i install/install_plugin.sh
	zsh -i installer/install_pipx.sh
	zsh -i installer/install_shimming_toolbox.sh

run:
	conda init zsh
	zsh -i run.sh
