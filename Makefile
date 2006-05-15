
.PHONY: default build force install test dist clean

PYTHON=/usr/bin/python
TEST=
PARAMETERS=

build:
	${PYTHON} setup.py build ${PARAMETERS}

force:
	${PYTHON} setup.py build -f ${PARAMETERS}

install: build
	${PYTHON} setup.py install ${PARAMETERS}

test: build
	${PYTHON} tests/test_build.py ${TEST}

dist: build
	${PYTHON} setup.py sdist --formats=zip,gztar

windist: build
	${PYTHON} setup.py bdist_wininst

clean:
	${PYTHON} setup.py clean -a

