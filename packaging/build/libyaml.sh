#!/bin/bash

set -eux

if [[ "$UID" != 0 ]]; then
    echo "Must be root" >&2
    exit 1
fi
. ./LIBYAML_VERSION
TD="$(mktemp -d)"
pushd "$TD" || exit 1
git clone https://github.com/yaml/libyaml.git
pushd libyaml
git config --global advice.detachedHead false
git reset --hard "$LIBYAML_VERSION"
./bootstrap
./configure
make
make test-all
make install
ldconfig
popd && popd
rm -rvf "$TD"
