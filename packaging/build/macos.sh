#!/bin/bash

set -eux

./packaging/build/libyaml.sh

brew update
brew upgrade pyenv
eval "$(pyenv init -)"
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
pyenv --version
# If the Python version isn't found (e.g. it's not available in
# share/python-build, then at least list what's available)
pyenv install -s "$PYENV_VERSION" || (pyenv install --list && exit 1)
pyenv local "$PYENV_VERSION"
python -V
pip install -U Cython wheel setuptools delocate
python setup.py bdist_wheel
delocate-listdeps dist/*.whl
delocate-wheel -v dist/*.whl
ls -1 dist/
