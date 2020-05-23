#!/bin/bash

set -eux

yum install -y libyaml libyaml-devel

cd /io
# TODO: might want to modify make clean / setup.py clean
mkdir -p wheelhouse
rm -vf wheelhouse/*.whl

for PYBIN in /opt/python/*/bin; do
    "${PYBIN}/python" -m pip install -U Cython auditwheel wheel setuptools pip
    "${PYBIN}/python" -m pip wheel \
        --verbose \
        --no-deps \
        --global-option '--with-libyaml' \
        --global-option "build_ext" \
        -w wheelhouse .
done

for whl in wheelhouse/*.whl; do
    "${PYBIN}/python" -m auditwheel repair "$whl" --plat "$PLAT" -w wheelhouse/
    rm -f "$whl"
done

ls -1 wheelhouse/
