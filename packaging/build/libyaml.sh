#!/bin/bash

set -eux

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
# Avoid error where we may be root but not have sudo itself available
if [[ "$UID" != 0 ]]; then
    if [[ ! -x "$(command -v sudo)" ]]; then
        echo "Error: lacking sudo as non-root user" >&2
        exit 1
    fi
    sudo make install
    sudo ldconfig
else
    make install
    ldconfig
fi
popd && popd
rm -rvf "$TD"
