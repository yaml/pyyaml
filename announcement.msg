From: Kirill Simonov <xi@resolvent.net>
To: python-list@python.org, python-announce@python.org, yaml-core@lists.sourceforge.net
Subject: [ANN] PyYAML-3.10: YAML parser and emitter for Python

========================
 Announcing PyYAML-3.10
========================

A new bug fix release of PyYAML is now available:

    http://pyyaml.org/wiki/PyYAML


Changes
=======

* Do not try to build LibYAML bindings on platforms other than CPython;
  this fixed installation under Jython (Thank to olt(at)bogosoft(dot)com).
* Clear cyclic references in the parser and the emitter
  (Thank to kristjan(at)ccpgames(dot)com).
* LibYAML bindings are rebuilt with the latest version of Cython.
* Dropped support for Python 2.3 and 2.4; currently supported versions
  are 2.5 to 3.2.


Resources
=========

PyYAML homepage: http://pyyaml.org/wiki/PyYAML
PyYAML documentation: http://pyyaml.org/wiki/PyYAMLDocumentation

TAR.GZ package: http://pyyaml.org/download/pyyaml/PyYAML-3.10.tar.gz
ZIP package: http://pyyaml.org/download/pyyaml/PyYAML-3.10.zip
Windows installers:
    http://pyyaml.org/download/pyyaml/PyYAML-3.10.win32-py2.5.exe
    http://pyyaml.org/download/pyyaml/PyYAML-3.10.win32-py2.6.exe
    http://pyyaml.org/download/pyyaml/PyYAML-3.10.win32-py3.0.exe
    http://pyyaml.org/download/pyyaml/PyYAML-3.10.win32-py3.1.exe
    http://pyyaml.org/download/pyyaml/PyYAML-3.10.win32-py3.2.exe

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

