
NAME = 'PyYAML'
VERSION = '3.0'
DESCRIPTION = "YAML parser and emitter for Python"
LONG_DESCRIPTION = """\
YAML is a data serialization format designed for human readability and
interaction with scripting languages.  PyYAML is a YAML parser and emitter
for Python.

PyYAML features a complete YAML 1.1 parser, Unicode support, event-based parser
and emitter (like SAX), API for serializing and deserializing Python objects
(like DOM or pickle).  PyYAML supports all tags from the YAML types repository
and allows you to extend it easily.

PyYAML is applicable for a broad range of tasks from configuration files to
object persistance."""
AUTHOR = "Kirill Simonov"
AUTHOR_EMAIL = 'xi@resolvent.net'
LICENSE = "MIT"
PLATFORMS = "Any"
URL = "http://pyyaml.org/wiki/PyYAML"
DOWNLOAD_URL = "http://pyyaml.org/download/pyyaml/%s-%s.tar.gz" % (NAME, VERSION)
CLASSIFIERS = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python",
    "Topic :: Software Development :: Libraries :: Python Modules",
    "Topic :: Text Processing :: Markup",
]


from distutils.core import setup

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

    package_dir={'': 'lib'},
    packages=['yaml'],
)

