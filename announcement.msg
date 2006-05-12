From: Kirill Simonov <xi@gamma.dn.ua>
To: python-list@python.org, python-announce@python.org, yaml-core@lists.sourceforge.net
Subject: PyYAML-3.01: Initial Release

PyYAML: YAML parser and emitter for Python
==========================================

YAML is a data serialization format designed for human readability and
interaction with scripting languages.  PyYAML is a YAML parser and
emitter for Python.

PyYAML features a complete YAML 1.1 parser, Unicode support, pickle
support, capable extension API, and sensible error messages.  PyYAML
supports standard YAML tags and provides Python-specific tags that allow
to represent an arbitrary Python object.

PyYAML is applicable for a broad range of tasks from complex
configuration files to object serialization and persistance.

You may download PyYAML from http://pyyaml.org/wiki/PyYAML.


Example
=======

>>> import yaml

>>> yaml.load("""
... name: PyYAML
... version: 3.01
... description: YAML parser and emitter for Python
... homepage: http://pyyaml.org/wiki/PyYAML
... keywords: [YAML, serialization, configuration, persistance, pickle]
... """)
{'keywords': ['YAML', 'serialization', 'configuration', 'persistance',
'pickle'], 'version': 3.01, 'homepage': 'http://pyyaml.org/wiki/PyYAML',
'description': 'YAML parser and emitter for Python', 'name': 'PyYAML'}

>>> print yaml.dump(_)
homepage: http://pyyaml.org/wiki/PyYAML
version: 3.01
name: PyYAML
keywords: [YAML, serialization, configuration, persistance, pickle]
description: YAML parser and emitter for Python


Links
=====

PyYAML homepage: http://pyyaml.org/wiki/PyYAML
PyYAML documentation: http://pyyaml.org/wiki/PyYAMLDocumentation

TAR.GZ package: http://pyyaml.org/download/pyyaml/PyYAML-3.01.tar.gz
ZIP package: http://pyyaml.org/download/pyyaml/PyYAML-3.01.zip
Windows installer: http://pyyaml.org/download/pyyaml/PyYAML-3.01.win32.exe

PyYAML SVN repository: http://svn.pyyaml.org/pyyaml
Submit a bug report: http://pyyaml.org/newticket?component=pyyaml

YAML homepage: http://yaml.org/
YAML-core mailing list: http://lists.sourceforge.net/lists/listinfo/yaml-core


Changes
=======

* Initial release.  The version number reflects the codename of the
  project (PyYAML 3000) and differenciates it from the abandoned PyYaml
  module.


Copyright
=========

The PyYAML module is written by Kirill Simonov <xi@resolvent.net>.

PyYAML is released under the MIT license.

