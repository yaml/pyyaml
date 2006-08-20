From: Kirill Simonov <xi@gamma.dn.ua>
To: python-list@python.org, python-announce@python.org, yaml-core@lists.sourceforge.net
Subject: [ANN] PyYAML-3.04: YAML parser and emitter for Python

========================
 Announcing PyYAML-3.04
========================

A new release of PyYAML, featuring LibYAML bindings and support for recursive
structures, is now available:

    http://pyyaml.org/wiki/PyYAML


Changes
=======

* Include experimental LibYAML bindings.
* Fully support recursive structures.
* Fix a number of bugs and annoyances
  (see http://pyyaml.org/wiki/PyYAML#History for more details).


Resources
=========

PyYAML homepage: http://pyyaml.org/wiki/PyYAML
PyYAML documentation: http://pyyaml.org/wiki/PyYAMLDocumentation

TAR.GZ package: http://pyyaml.org/download/pyyaml/PyYAML-3.04.tar.gz
ZIP package: http://pyyaml.org/download/pyyaml/PyYAML-3.04.zip
Windows installer:
    http://pyyaml.org/download/pyyaml/PyYAML-3.04.win32-py2.3.exe
    http://pyyaml.org/download/pyyaml/PyYAML-3.04.win32-py2.4.exe

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
>>> print yaml.load("""
... &A {
...     direct self reference: *A,
...     indirect self references: [*A, *A, *A]
... }
... """)
{'direct self reference': {...},
'indirect self references': [{...}, {...}, {...}]}


Copyright
=========

The PyYAML module is written by Kirill Simonov <xi@resolvent.net>.

PyYAML is released under the MIT license.

This release is developed with the support of the Google Summer of Code
program under the mentorship of Clark Evans.

