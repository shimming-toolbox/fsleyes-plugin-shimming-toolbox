
# Put it first so that "make" without argument is like "make help".
help:
	@egrep -h '\s##\s' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m  %-30s\033[0m %s\n", $$1, $$2}'

# .PHONY: help Makefile

install: ## Run 'make install' to install the plugin
	conda init zsh
	zsh -i installer/install_plugin.sh
	zsh -i installer/install_pipx.sh
	zsh -i installer/install_shimming_toolbox.sh

run: ## To open fsleyes with the plugin, run 'make run'
	conda init zsh
	zsh -i run.sh
