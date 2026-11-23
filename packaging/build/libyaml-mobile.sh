#!/bin/bash
#
# Cross-compile a static libyaml for an iOS or Android target. This is run by
# cibuildwheel as the `before-build` step for iOS and Android builds (see
# [tool.cibuildwheel] in pyproject.toml).
#
# libyaml is installed into build/deps/<os>_<arch>/prefix, and
# build/deps/current is pointed at the most recently built target, so that the
# extension build can find the headers and library at a fixed location.
#
# Only a static library is built: on iOS, extension modules can't depend on
# other dynamic libraries, and on Android it avoids needing auditwheel to vendor
# a shared library.

set -eux

# A libyaml release version; a release tarball is used, not a git ref,
# so that autoreconf isn't needed for a build.
LIBYAML_REF=${LIBYAML_REF:-0.2.6}
LIBYAML_REPO=${LIBYAML_REPO:-https://github.com/yaml/libyaml}
LIBYAML_URL=${LIBYAML_URL:-${LIBYAML_REPO}/releases/download/${LIBYAML_REF}/yaml-${LIBYAML_REF}.tar.gz}

# CIBUILDWHEEL_BUILD_IDENTIFIER is {python}-{os}_{arch}, e.g.
# cp313-ios_arm64_iphonesimulator or cp313-android_arm64_v8a.
CIBW_OS_ARCH=${CIBUILDWHEEL_BUILD_IDENTIFIER#*-}
CIBW_OS=${CIBW_OS_ARCH%%_*}
CIBW_ARCH=${CIBW_OS_ARCH#*_}

# Paths are relative to the project root, regardless of the current directory.
PROJECT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
BUILD_DEPS=$PROJECT_DIR/build/deps
WORKDIR=$BUILD_DEPS/$CIBW_OS_ARCH
BUILD_PREFIX=$WORKDIR/prefix

mkdir -p "$WORKDIR"
ln -sfn "$CIBW_OS_ARCH" "$BUILD_DEPS/current"

# before-build runs once per Python version; libyaml only needs to be built
# once per target.
STAMP=$WORKDIR/libyaml-$LIBYAML_REF.stamp
if [ -e "$STAMP" ]; then
    echo "libyaml $LIBYAML_REF already built for $CIBW_OS_ARCH"
    exit 0
fi

case "$CIBW_OS" in
    ios)
        PLAT=${CIBW_ARCH%_*}        # arm64 | x86_64
        IOS_SDK=${CIBW_ARCH##*_}    # iphoneos | iphonesimulator
        if [ "$PLAT" = "arm64" ]; then
            GNU_ARCH=aarch64
        else
            GNU_ARCH=x86_64
        fi
        IOS_SDK_PATH=$(xcrun --sdk "$IOS_SDK" --show-sdk-path)
        IOS_HOST_TRIPLE=$PLAT-apple-ios${IPHONEOS_DEPLOYMENT_TARGET}
        if [ "$IOS_SDK" = "iphonesimulator" ]; then
            IOS_HOST_TRIPLE=$IOS_HOST_TRIPLE-simulator
        fi

        export CC=$(xcrun --find --sdk "$IOS_SDK" clang)
        export AR=$(xcrun --find --sdk "$IOS_SDK" ar)
        export RANLIB=$(xcrun --find --sdk "$IOS_SDK" ranlib)
        export CFLAGS="-target $IOS_HOST_TRIPLE --sysroot=$IOS_SDK_PATH -mios-version-min=$IPHONEOS_DEPLOYMENT_TARGET -O2"
        export LDFLAGS="$CFLAGS"
        # autotools doesn't know about *-apple-ios-simulator; the -target in
        # CFLAGS selects the simulator.
        HOST=$GNU_ARCH-apple-ios
        BUILD=$(uname -m | sed 's/arm64/aarch64/')-apple-darwin
        ;;
    android)
        # cibuildwheel has already set CC, CFLAGS, LDFLAGS etc. for the target.
        case "$CIBW_ARCH" in
            arm64_v8a) HOST=aarch64-linux-android ;;
            x86_64) HOST=x86_64-linux-android ;;
            *) echo "Unsupported Android arch: $CIBW_ARCH"; exit 1 ;;
        esac
        BUILD=
        ;;
    *)
        echo "Unsupported platform: $CIBW_OS"
        exit 1
        ;;
esac
unset LIBRARY_PATH

# Fetch the libyaml release tarball.
echo "::group::fetch libyaml ${LIBYAML_REF}"
SRC_DIR=$WORKDIR/yaml-$LIBYAML_REF
rm -rf "$SRC_DIR"
curl --fail --location --silent --show-error --retry 3 "$LIBYAML_URL" | tar -xz -C "$WORKDIR"
echo "::endgroup::"

echo "::group::configure libyaml"
pushd "$SRC_DIR"
./configure \
    --host="$HOST" \
    ${BUILD:+--build="$BUILD"} \
    --prefix="$BUILD_PREFIX" \
    --disable-dependency-tracking \
    --with-pic \
    --enable-static \
    --disable-shared
echo "::endgroup::"

echo "::group::build libyaml"
# Only build and install the library and headers; the test programs can't be
# run when cross-compiling.
make -C include install
make -C src install
popd

# Make sure nothing dynamic could be picked up by the linker.
find "$BUILD_PREFIX" \( -name '*.dylib' -o -name '*.so' -o -name '*.so.*' -o -name '*.la' \) -delete
touch "$STAMP"
echo "::endgroup::"
