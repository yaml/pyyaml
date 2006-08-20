
.PHONY: default build buildext force forceext install installext test testext dist clean

PYTHON=/usr/bin/python
TEST=
PARAMETERS=

build:
	${PYTHON} setup.py build ${PARAMETERS}

buildext:
	${PYTHON} setup_with_libyaml.py build ${PARAMETERS}

force:
	${PYTHON} setup.py build -f ${PARAMETERS}

forceext:
	${PYTHON} setup_with_libyaml.py build -f ${PARAMETERS}

install: build
	${PYTHON} setup.py install ${PARAMETERS}

installext: buildext
	${PYTHON} setup_with_libyaml.py install ${PARAMETERS}

test: build
	${PYTHON} tests/test_build.py ${TEST}

testext: buildext
	${PYTHON} tests/test_build_ext.py ${TEST}

dist:
	${PYTHON} setup.py sdist --formats=zip,gztar

windist:
	${PYTHON} setup.py bdist_wininst

clean:
	${PYTHON} setup.py clean -a
