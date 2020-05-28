#!/bin/bash

set -eux

./packaging/build/libyaml.sh

mkdir -p wheelhouse
rm -vf wheelhouse/*.whl

# PyYAML supports Python 2.7, 3.5-3.8
for PYBIN in /opt/python/*/bin; do
    "${PYBIN}/python" -m pip install -U Cython auditwheel wheel setuptools pip
    USE_CYTHON=1 "${PYBIN}/python" -m pip wheel --verbose --no-deps -w wheelhouse .
done

for whl in wheelhouse/*.whl; do
    auditwheel repair "$whl" --plat "$PLAT" -w wheelhouse/
    rm -f "$whl"
done

ls -1 wheelhouse/
