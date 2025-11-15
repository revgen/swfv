#-----------------------------------------------------------------------------
##Usage: make <command>
##Commands:
#-----------------------------------------------------------------------------

default: help
APP_NAME=swfv
PYTHON_ORIGIN := $(shell which python3 || which python)
VENV=.venv
PYTHON=$(VENV)/bin/python
OS = $(shell uname -s)

.PHONY: init help build lint clean

version=$(shell grep "^version" pyproject.toml | cut -d"=" -f2 | sed 's/[ "]*//g')
ifeq ($(CLEAN_ALL),true)
dir_to_cleanup = ./dist ./build $(VENV)
else
dir_to_cleanup = ./dist ./build 
endif

ifeq ($(OS),Darwin)
stat_args = -f "%N, %z bytes, %Sm"
else
stat_args = -f "%n, %s bytes, %y"
endif

#-----------------------------------------------------------------------------
init:           ## Prepeare development environemnt
	@make clean >/dev/null
	@echo "Initialize environemnt in $(PWD)..."
	@$(PYTHON_ORIGIN) -m venv $(VENV)
	@echo "Virtual environent $(VENV) was created. Install dependencies..."
	@$(PYTHON) -m pip install uv ruff
	@echo "Environment initialization complete"

lint:           ## Check source code
	@$(VENV)/bin/ruff check ./src/

build:          ## Build project
	@echo "Build $(APP_NAME) v$(version) in $(PWD)..."
	@#------------------------------------------------------------
	@echo "Update version in the code..."
	@cp -f ./src/swfv/config.py ./src/swfv/config.py.tmp
	@sed 's/^__version__ = "[\.0-9]*"/__version__ = "'"$(version)"'"/' ./src/swfv/config.py.tmp > ./src/swfv/config.py
	@rm -f ./src/swfv/config.py.tmp
	@grep "__version__" ./src/swfv/config.py | grep -v "APP"
	@#------------------------------------------------------------
	@$(VENV)/bin/uv pip install ./
	@printf "Build complete: "
	@$(PYTHON) -c "import $(APP_NAME); print($(APP_NAME).__version__)"

test:           ## Check code style
	@echo "Run tests"
	@$(PYTHON) -c "import $(APP_NAME); $(APP_NAME).main(['--version'])"

pack:           ## Create a distribution package
	@make build
	@echo "Create a distribution package..."
	@rm -rf ./dist
	@$(VENV)/bin/uv build --wheel
	@echo "Create is successfull:"
	@stat $(stat_args) ./dist/*.whl | sed "s/^/* /g"

clean:          ## Cleanup project directory
	@echo "Cleanup in $(PWD)..."
	@printf "Directory size before cleanup: " && du -sh ${PWD} | cut -f1
	@echo "Deleting $(dir_to_cleanup)..."
	@rm -rvf $(dir_to_cleanup)
	@echo "Deleting python temp files..."
	@find ./src -type d -name "__pycache__" -print -exec rm -vfr "{}" \; 2>/dev/null || true
	@find ./src -type d -name "*.egg-info" -print -exec rm -vfr "{}" \; 2>/dev/null || true
	@find ./src -type f -name "*.pyc" -print -exec rm -vfr "{}" \; 2>/dev/null || true
	@echo "Cleanup is done."
	@printf "Directory size: " && du -sh ${PWD} | cut -f1

clean-all:
	@CLEAN_ALL=true make clean

help:           ## Show this help.
	@fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | sed -e 's/\\$$//' | sed -e 's/##//' | sed -e 's/##//'
