#!/bin/bash

set -eux

./packaging/build/libyaml.sh

brew update
brew upgrade pyenv
eval "$(pyenv init -)"
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
pyenv --version
pyenv install -s "$PYENV_VERSION"
pyenv local "$PYENV_VERSION"
python -V
pip install -U Cython wheel setuptools delocate
python setup.py bdist_wheel
delocate-listdeps dist/*.whl
delocate-wheel -v dist/*.whl
ls -1 dist/
