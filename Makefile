
.PHONY: build dist

PYTHON=/usr/bin/python3
TEST=
PARAMETERS=

build:
	${PYTHON} setup.py build ${PARAMETERS}

buildext:
	${PYTHON} setup.py --with-libyaml build ${PARAMETERS}

force:
	${PYTHON} setup.py build -f ${PARAMETERS}

forceext:
	${PYTHON} setup.py --with-libyaml build -f ${PARAMETERS}

install:
	${PYTHON} setup.py install ${PARAMETERS}

installext:
	${PYTHON} setup.py --with-libyaml install ${PARAMETERS}

test: build
	PYYAML_FORCE_LIBYAML=0 ${PYTHON} -I -m pytest

testext: buildext
	PYYAML_FORCE_LIBYAML=1 ${PYTHON} -I -m pytest

testall:
	${PYTHON} -m pytest

dist:
	@# No longer uploading a zip file to pypi
	@# ${PYTHON} setup.py --with-libyaml sdist --formats=zip,gztar
	${PYTHON} setup.py --with-libyaml sdist --formats=gztar

clean:
	${PYTHON} setup.py --with-libyaml clean -a
	rm -fr \
	    dist/ \
	    lib/PyYAML.egg-info/ \
	    lib/yaml/__pycache__/ \
	    tests/__pycache__/ \
	    tests/legacy_tests/__pycache__/ \
	    yaml/_yaml.c
