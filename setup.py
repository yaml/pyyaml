
NAME = 'PyYAML3000'
VERSION = '0.1'
DESCRIPTION = "YAML parser (and emitter)"
AUTHOR = "Kirill Simonov"
AUTHOR_EMAIL = 'xi@resolvent.net'
LICENSE = "BSD"

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

