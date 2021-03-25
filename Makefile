

# You can set these variables from the command line.
# SPHINXBUILD   = python -msphinx
# SPHINXPROJ    = SpinalCordToolbox

# Put it first so that "make" without argument is like "make help".
# help:
# 	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

# .PHONY: help Makefile

install:
	conda init zsh
	zsh -i install.sh

run:
	conda init zsh
	zsh -i run.sh
