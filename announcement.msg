From: Kirill Simonov <xi@gamma.dn.ua>
To: python-list@python.org, python-announce@python.org, yaml-core@lists.sourceforge.net, python-porting@python.org
Subject: [ANN] PyYAML-3.08: Now with Python 3 support

========================
 Announcing PyYAML-3.08
========================

A new release of PyYAML is now available:

    http://pyyaml.org/wiki/PyYAML

This release features a complete support for Python 3.  For
compatibility notes between Python 2 and Python 3 versions,
please see

    http://pyyaml.org/wiki/PyYAMLDocumentation#Python3support


Changes
=======

* Python 3 support (Thank to Erick Tryzelaar).
* Use Cython instead of Pyrex to build LibYAML bindings.  Note
  that the source package is distributed with a pre-generated
  '_yaml.c' file so you don't need Cython installed to build
  LibYAML bindings.
* Refactored support for unicode and byte input/output streams.


Resources
=========

PyYAML homepage: http://pyyaml.org/wiki/PyYAML
PyYAML documentation: http://pyyaml.org/wiki/PyYAMLDocumentation

TAR.GZ package: http://pyyaml.org/download/pyyaml/PyYAML-3.08.tar.gz
ZIP package: http://pyyaml.org/download/pyyaml/PyYAML-3.08.zip
Windows installers:
    http://pyyaml.org/download/pyyaml/PyYAML-3.08.win32-py2.3.exe
    http://pyyaml.org/download/pyyaml/PyYAML-3.08.win32-py2.4.exe
    http://pyyaml.org/download/pyyaml/PyYAML-3.08.win32-py2.5.exe
    http://pyyaml.org/download/pyyaml/PyYAML-3.08.win32-py2.6.exe
    http://pyyaml.org/download/pyyaml/PyYAML-3.08.win32-py3.0.exe

PyYAML SVN repository: http://svn.pyyaml.org/pyyaml
Submit a bug report: http://pyyaml.org/newticket?component=pyyaml

YAML homepage: http://yaml.org/
YAML-core mailing list: http://lists.sourceforge.net/lists/listinfo/yaml-core


About PyYAML
============

YAML is a data serialization format designed for human readability and
interaction with scripting languages.  PyYAML is a YAML parser and
emitter for Python.

PyYAML features a complete YAML 1.1 parser, Unicode support, pickle
support, capable extension API, and sensible error messages.  PyYAML
supports standard YAML tags and provides Python-specific tags that allow
to represent an arbitrary Python object.

PyYAML is applicable for a broad range of tasks from complex
configuration files to object serialization and persistance.


Example
=======

>>> import yaml

>>> yaml.load("""
... name: PyYAML
... description: YAML parser and emitter for Python
... homepage: http://pyyaml.org/wiki/PyYAML
... keywords: [YAML, serialization, configuration, persistance, pickle]
... """)
{'keywords': ['YAML', 'serialization', 'configuration', 'persistance',
'pickle'], 'homepage': 'http://pyyaml.org/wiki/PyYAML', 'description':
'YAML parser and emitter for Python', 'name': 'PyYAML'}

>>> print yaml.dump(_)
name: PyYAML
homepage: http://pyyaml.org/wiki/PyYAML
description: YAML parser and emitter for Python
keywords: [YAML, serialization, configuration, persistance, pickle]


Copyright
=========

The PyYAML module is written by Kirill Simonov <xi@resolvent.net>.

PyYAML is released under the MIT license.

