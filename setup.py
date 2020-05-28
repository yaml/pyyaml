import os
import sys

from setuptools import setup, Extension

with_libyaml = '--with-libyaml' in sys.argv
with_cython = 'sdist' in sys.argv or os.environ.get('USE_CYTHON')
cython_available = False
try:
    from Cython.Build import cythonize
    cython_available = True
except ImportError:
    if with_cython:
        raise

NAME = 'PyYAML'
VERSION = '5.3.1'
DESCRIPTION = "YAML parser and emitter for Python"
LONG_DESCRIPTION = """\
YAML is a data serialization format designed for human readability
and interaction with scripting languages.  PyYAML is a YAML parser
and emitter for Python.

PyYAML features a complete YAML 1.1 parser, Unicode support, pickle
support, capable extension API, and sensible error messages.  PyYAML
supports standard YAML tags and provides Python-specific tags that
allow to represent an arbitrary Python object.

PyYAML is applicable for a broad range of tasks from complex
configuration files to object serialization and persistence."""
AUTHOR = "Kirill Simonov"
AUTHOR_EMAIL = 'xi@resolvent.net'
LICENSE = "MIT"
PLATFORMS = "Any"
URL = "https://github.com/yaml/pyyaml"
DOWNLOAD_URL = "https://pypi.org/project/PyYAML/"
CLASSIFIERS = [
    "Development Status :: 5 - Production/Stable",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Cython",
    "Programming Language :: Python",
    "Programming Language :: Python :: 2",
    "Programming Language :: Python :: 2.7",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.5",
    "Programming Language :: Python :: 3.6",
    "Programming Language :: Python :: 3.7",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: Implementation :: CPython",
    "Programming Language :: Python :: Implementation :: PyPy",
    "Topic :: Software Development :: Libraries :: Python Modules",
    "Topic :: Text Processing :: Markup",
]

source = 'yaml/_yaml.%s' % 'pyx' if with_cython else 'c'
if not os.path.isfile(source):
    msg = "Attempting to build %s but cythonized file does not exist" % source
    raise RuntimeError(msg)

extension = Extension(
    'yaml._yaml',
    sources=[source],
    libraries=['yaml'],
)

if __name__ == '__main__':
    setup(
        name=NAME,
        version=VERSION,
        description=DESCRIPTION,
        long_description=LONG_DESCRIPTION,
        author=AUTHOR,
        author_email=AUTHOR_EMAIL,
        license=LICENSE,
        platforms=PLATFORMS,
        url=URL,
        download_url=DOWNLOAD_URL,
        classifiers=CLASSIFIERS,
        package_dir={'': {2: 'lib', 3: 'lib3'}[sys.version_info[0]]},
        packages=['yaml'],
        python_requires='>=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*',
        ext_modules=(cythonize(extension) if with_cython else [extension]),
    )
