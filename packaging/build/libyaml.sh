#!/bin/bash

set -eux

# build the requested version of libyaml locally
echo "::group::fetch libyaml ${LIBYAML_REF}"
git config --global advice.detachedHead false
git clone --branch "$LIBYAML_REF" "$LIBYAML_REPO" libyaml
pushd libyaml
git reset --hard "$LIBYAML_REF"
echo "::endgroup::"

# ensure the prove testing tool is available
echo "::group::ensure build/test prerequisites"
if ! command -v prove; then
  if grep -m 1 alpine /etc/os-release; then
    apk add perl-utils
  elif grep -m 1 "Rocky Linux" /etc/os-release; then
    dnf install -y perl-Test-Harness
  else
    echo "prove (perl) testing tool unavailable"
    exit 1
  fi
fi

# hack to fix up locally musl1.2 libtool macros
if grep -m 1 alpine /etc/os-release; then
  if ! grep -E 'AC_CONFIG_MACRO_DIRS\(\[m4])' configure.ac; then
    echo 'AC_CONFIG_MACRO_DIRS([m4])' >> configure.ac
    ACLOCAL_PATH=/usr/local/share/libtool/ libtoolize
  fi
fi
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
