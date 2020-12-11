#!/bin/bash

set -eux

# build the requested version of libyaml locally
echo "::group::fetch libyaml ${LIBYAML_REF}"
git config --global advice.detachedHead false
git clone --branch "$LIBYAML_REF" "$LIBYAML_REPO" libyaml
pushd libyaml
git reset --hard "$LIBYAML_REF"
echo "::endgroup::"

echo "::group::autoconf libyaml w/ static only"
./bootstrap
# build only a static library- reduces our reliance on auditwheel/delocate magic
./configure --disable-dependency-tracking --with-pic --enable-shared=no
echo "::endgroup::"

echo "::group::build libyaml"
make
echo "::endgroup::"

echo "::group::test built libyaml"
make test-all
echo "::endgroup::"
popd
