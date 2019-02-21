# shellcheck shell=bash

main() (
  set -eu -o pipefail
  set -x

  check-env

  func=$1; shift
  type "$func" &>/dev/null || {
    echo 'Invalid travis.sh function'
    return 1
  }

  "$func" "$@"
)

travis:install() {
  python -m pip.__main__ install cython tox

  git clone --branch="$LIBYAML_VERSION" \
    https://github.com/yaml/libyaml.git \
    /tmp/libyaml

  # build libyaml
  (
    cd /tmp/libyaml
    ./bootstrap
    ./configure
    make
    make test-all
    sudo make install
  )
}

travis:before_install:osx() {
  brew install zlib readline
  brew install https://raw.githubusercontent.com/Homebrew/homebrew-core/master/Formula/pyenv.rb ||
    brew upgrade pyenv

  eval "$(pyenv init -)"

  local version_re=${TRAVIS_PYTHON_VERSION//./\\.}
  if [[ $TRAVIS_PYTHON_VERSION != *dev* ]]; then
    TRAVIS_PYTHON_VERSION=$(
      pyenv install --list |
        grep -E "\s\s$version_re" |
        grep -vE 'dev|rc' |
        tail -n 1 |
        tr -d '[:space:]'
    )
    export TRAVIS_PYTHON_VERSION
  fi

  pyenv install --skip-existing --keep --verbose "$TRAVIS_PYTHON_VERSION" | \
  tee pyenv-install.log | tail -n 50

  pyenv shell "$TRAVIS_PYTHON_VERSION"
  python --version
}

check-env() {
  if \
    [[ -z $BASH_VERSION ]] ||
    [[ $0 == "${BASH_SOURCE[0]}" ]] ||
    [[ $SHELL != /bin/bash ]]
  then
    echo 'Unexpected travis-ci environment'
    return 1
  fi
}

main "$@"
