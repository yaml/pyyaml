From: Kirill Simonov <xi@gamma.dn.ua>
To: python-list@python.org, python-announce@python.org, yaml-core@lists.sourceforge.net
Subject: [ANN] PyYAML-3.05: YAML parser and emitter for Python

========================
 Announcing PyYAML-3.05
========================

A new bug fix release of PyYAML is now available:

    http://pyyaml.org/wiki/PyYAML


Changes
=======

* Windows binary packages were built with LibYAML trunk.
* Fixed a bug that prevent processing a live stream of YAML documents in timely
  manner (Thanks edward(at)sweetbytes(dot)net).
* Fixed a bug when the path in add_path_resolver contains boolean values
  (Thanks jstroud(at)mbi(dot)ucla(dot)edu).
* Fixed loss of microsecond precision in timestamps
  (Thanks edemaine(at)mit(dot)edu).
* Fixed loading an empty YAML stream.
* A number of smaller fixes and improvements
  (see http://pyyaml.org/wiki/PyYAML#History for more details).


Resources
=========

PyYAML homepage: http://pyyaml.org/wiki/PyYAML
PyYAML documentation: http://pyyaml.org/wiki/PyYAMLDocumentation

TAR.GZ package: http://pyyaml.org/download/pyyaml/PyYAML-3.05.tar.gz
ZIP package: http://pyyaml.org/download/pyyaml/PyYAML-3.05.zip
Windows installer:
    http://pyyaml.org/download/pyyaml/PyYAML-3.05.win32-py2.3.exe
    http://pyyaml.org/download/pyyaml/PyYAML-3.05.win32-py2.4.exe
    http://pyyaml.org/download/pyyaml/PyYAML-3.05.win32-py2.5.exe

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

