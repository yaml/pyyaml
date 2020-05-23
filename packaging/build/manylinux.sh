#!/bin/bash

set -eux

pushd /opt
LIBYAML_VERSION='0.2.4'
git config --global advice.detachedHead false
git clone -q \
    --branch "$LIBYAML_VERSION" \
    https://github.com/yaml/libyaml.git libyaml
pushd libyaml
./bootstrap
./configure
make
make install
ldconfig

pushd /io
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
