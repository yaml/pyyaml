
NAME = 'PyYAML3000'
VERSION = '0.1'
DESCRIPTION = "The next generation YAML parser for Python"
AUTHOR = "Kirill Simonov"
AUTHOR_EMAIL = 'xi@resolvent.net'
LICENSE = "MIT"

from distutils.core import setup

setup(
    name=NAME,
    version=VERSION,
    description=DESCRIPTION,
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    license=LICENSE,

    package_dir={'': 'lib'},
    packages=['yaml'],
)

