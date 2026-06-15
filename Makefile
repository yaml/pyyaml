R := https://github.com/makeplus/makes
C := b0edc13d2045c1a06a92752ea4bfb48cbb59cc4b
M := $(or $(MAKES_REPO_DIR),.cache/makes)
$(shell [ -d '$M' ] || git clone -q $R '$M')
$(shell cd '$M' && [ "$$(git rev-parse HEAD)" = '$C' ] || \
  { git fetch -q origin && git checkout -q '$C'; })

include $M/init.mk

export UV_CACHE_DIR = $(LOCAL-CACHE)/uv
PYTHON-VENV-SETUP = uv pip install Cython pytest setuptools wheel
include $M/python.mk
include $M/clean.mk
include $M/shell.mk

PYTHON-DEPS = $(PYTHON) $(PYTHON-VENV)
PYTEST-PYTHON = \
import sys; \
sys.path.insert(0, 'build/lib'); \
import pytest; \
raise SystemExit(pytest.main())

PYTEST-LIBYAML = \
import pathlib, sys; \
sys.path.insert(0, next(str(p) for p in pathlib.Path('build').glob('lib.*'))); \
import pytest; \
raise SystemExit(pytest.main())

TEST=
PARAMETERS=

LIBYAML-REPO ?= https://github.com/yaml/libyaml
LIBYAML-REF ?= 0.2.5
LIBYAML-DIR := $(LOCAL-CACHE)/libyaml-$(LIBYAML-REF)
LIBYAML-BUILD := $(LIBYAML-DIR)/src/.libs/libyaml.$(SO)
LIBYAML-INCLUDE := $(LIBYAML-DIR)/include
LIBYAML-LIB := $(LIBYAML-DIR)/src/.libs
LIBYAML-ENV := \
  CFLAGS="-I$(LIBYAML-INCLUDE) $${CFLAGS:-}" \
  LDFLAGS="-L$(LIBYAML-LIB) $${LDFLAGS:-}" \
  LD_LIBRARY_PATH="$(LIBYAML-LIB):$${LD_LIBRARY_PATH:-}"

MAKES-CLEAN := \
  lib/PyYAML.egg-info/ \
  lib/yaml/__pycache__/ \
  tests/__pycache__/ \
  tests/legacy_tests/__pycache__/ \
  .pytest_cache/ \
  yaml/_yaml.c \
  build/ \
  dist \


build: $(PYTHON-DEPS)
	python setup.py build $(PARAMETERS)

build-python: $(PYTHON-DEPS)
	PYYAML_FORCE_LIBYAML=0 python setup.py --without-libyaml build $(PARAMETERS)

buildext: $(PYTHON-DEPS) $(LIBYAML-BUILD)
	$(LIBYAML-ENV) python setup.py --with-libyaml build $(PARAMETERS)

force: $(PYTHON-DEPS)
	python setup.py build -f $(PARAMETERS)

forceext: $(PYTHON-DEPS) $(LIBYAML-BUILD)
	$(LIBYAML-ENV) python setup.py --with-libyaml build -f $(PARAMETERS)

install: $(PYTHON-DEPS)
	python setup.py install $(PARAMETERS)

installext: $(PYTHON-DEPS) $(LIBYAML-BUILD)
	$(LIBYAML-ENV) python setup.py --with-libyaml install $(PARAMETERS)

test: test-python test-libyaml

test-python: build-python
	PYYAML_FORCE_LIBYAML=0 python -I -c "$(PYTEST-PYTHON)"

test-libyaml: buildext
	$(LIBYAML-ENV) PYYAML_FORCE_LIBYAML=1 python -I -c "$(PYTEST-LIBYAML)"

$(LIBYAML-BUILD):
	rm -fr $(LIBYAML-DIR)
	git clone --branch $(LIBYAML-REF) $(LIBYAML-REPO) $(LIBYAML-DIR)
	cd $(LIBYAML-DIR) && git reset --hard $(LIBYAML-REF)
	cd $(LIBYAML-DIR) && ./bootstrap
	cd $(LIBYAML-DIR) && ./configure --disable-dependency-tracking --with-pic --enable-shared=yes
	$(MAKE) -C $(LIBYAML-DIR)

dist: $(PYTHON-DEPS)
	@# No longer uploading a zip file to pypi
	@# python setup.py --with-libyaml sdist --formats=zip,gztar
	python setup.py --with-libyaml sdist --formats=gztar

.PHONY: build dist
