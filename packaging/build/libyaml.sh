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
sudo make install
sudo ldconfig
popd && popd
rm -rvf "$TD"
