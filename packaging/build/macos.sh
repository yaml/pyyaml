#!/bin/bash

set -eux

brew update -y
brew upgrade gettext || brew install gettext
brew upgrade automake || brew install automake
python -V
pip install -U setuptools wheel pip Cython delocate
python setup.py bdist_wheel
delocate-listdeps dist/*.whl
delocate-wheel -v dist/*.whl
ls -1 dist/
