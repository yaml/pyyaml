#!/bin/bash

set -eux

python -V
pip install -U setuptools wheel pip Cython delocate
python setup.py bdist_wheel
delocate-listdeps dist/*.whl
delocate-wheel -v dist/*.whl
ls -1 dist/
