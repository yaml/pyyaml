#!/bin/bash

set -eux

# We need to build this here rather than as a CI step
# so that it's easily available in the container itself
./packaging/build/libyaml.sh

mkdir -p wheelhouse
rm -vf wheelhouse/*.whl

# PyYAML supports Python 2.7, 3.5-3.8
for tag in $PYTHON_TAGS; do
  PYBIN="/opt/python/${tag}/bin"
  "${PYBIN}/python" -m pip install -U wheel setuptools pip Cython auditwheel
  "${PYBIN}/python" -m pip wheel \
    --verbose \
    --no-deps \
    --global-option '--with-libyaml' \
    --global-option "build_ext" \
    -w wheelhouse .
done

for whl in wheelhouse/*.whl; do
  auditwheel repair "$whl" --plat "$PLAT" -w wheelhouse/
  rm -f "$whl"
done

mkdir dist
mv wheelhouse/*.whl dist/
ls -1 dist/
