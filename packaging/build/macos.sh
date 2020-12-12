#!/bin/bash

set -eux

# doesn't really matter which Python we use, so long as it can run cibuildwheels, and we're consistent within the
# build, since cibuildwheel is internally managing looping over all the Pythons for us.
export PYBIN=/usr/bin/python3

${PYBIN} -V
${PYBIN} -m pip install -U --user cibuildwheel
# run cibuildwheel; we can skip CIBW_ENVIRONMENT since the Mac version will directly inherit the envvars we set to
# force Cython and --with-libyaml. cibuildwheel will install Cython before each version is built. We expect that
# the calling environment will set CIBW_SKIP or CIBW_BUILD to control which Pythons we build for. (eg, CIBW_SKIP='pp* cp27* cp35*')

# we're using a private build of libyaml, so set paths to favor that instead of whatever's laying around
export C_INCLUDE_PATH=$(cd libyaml/include; pwd):${C_INCLUDE_PATH:-}
export LIBRARY_PATH=$(cd libyaml/src/.libs; pwd):${LIBRARY_PATH:-}
export LD_LIBRARY_PATH=$(cd libyaml/src/.libs; pwd):${LD_LIBRARY_PATH:-}

export PYYAML_FORCE_CYTHON=1
export PYYAML_FORCE_LIBYAML=1

if [[ ${PYYAML_RUN_TESTS:-1} -eq 1 ]]; then
  # tweak CIBW behavior to run our tests for us
  export CIBW_BEFORE_BUILD='pip install Cython && make testall PYTHON=python'
else
  echo "skipping test suite..."
fi

export CIBW_TEST_COMMAND='python {project}/packaging/build/smoketest.py'

${PYBIN} -m cibuildwheel --platform macos .

mkdir -p dist
mv wheelhouse/* dist/

# ensure exactly one artifact
shopt -s nullglob
DISTFILES=(dist/*.whl)
if [[ ${#DISTFILES[@]} -ne 1 ]]; then
  echo -e "unexpected dist content:\n\n$(ls)"
  exit 1
fi
