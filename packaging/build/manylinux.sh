#!/bin/bash

set -eux

PYBIN="/opt/python/${PYTHON_TAG}/bin/python"

# modern tools don't allow us to pass eg, --with-libyaml, so we force it via env
export PYYAML_FORCE_CYTHON=1
export PYYAML_FORCE_LIBYAML=1

# we're using a private build of libyaml, so set paths to favor that instead of whatever's laying around
export C_INCLUDE_PATH=libyaml/include:${C_INCLUDE_PATH:-}
export LIBRARY_PATH=libyaml/src/.libs:${LIBRARY_PATH:-}
export LD_LIBRARY_PATH=libyaml/src/.libs:${LD_LIBRARY_PATH:-}

# install deps
echo "::group::installing build deps"
# FIXME: installing Cython here won't be necessary once we fix tests, since the build is PEP517 and declares its own deps
"${PYBIN}" -m pip install build==0.1.0 Cython
echo "::endgroup::"

if [[ ${PYYAML_RUN_TESTS:-1} -eq 1 ]]; then
  echo "::group::running test suite"
  # FIXME: split tests out for easier direct execution w/o Makefile
  # run full test suite
  make testall PYTHON="${PYBIN}"
  echo "::endgroup::"
else
  echo "skipping test suite..."
fi


if [[ ${PYYAML_BUILD_WHEELS:-0} -eq 1 ]]; then
  echo "::group::building wheels"
  "${PYBIN}" -m build -w -o tempwheel .
  echo "::endgroup::"

  echo "::group::validating wheels"

  for whl in tempwheel/*.whl; do
    auditwheel repair --plat "${AW_PLAT}" "$whl" -w dist/
  done

  # ensure exactly one finished artifact
  shopt -s nullglob
  DISTFILES=(dist/*.whl)
  if [[ ${#DISTFILES[@]} -ne 1 ]]; then
    echo -e "unexpected dist content:\n\n$(ls)"
    exit 1
  fi

  "${PYBIN}" -m pip install dist/*.whl

  "${PYBIN}" packaging/build/smoketest.py

  ls -1 dist/

  echo "::endgroup::"

else
  echo "skipping wheel build..."
fi
