From: Tina Müller <post@tinita.de>
To: python-list@python.org, python-announce@python.org, yaml-core@lists.sourceforge.net
Subject: [ANN] PyYAML-5.2: YAML parser and emitter for Python

=======================
Announcing PyYAML-5.2
=======================

A new release of PyYAML is now available:
https://pypi.org/project/PyYAML/

This fixes some incompatibilities introduced in version 5.1 and also removes
another possibility of loading arbitrary code.

Changes
=======

* Repair incompatibilities introduced with 5.1. The default Loader was changed,
  but several methods like add_constructor still used the old default
  https://github.com/yaml/pyyaml/pull/279 -- A more flexible fix for custom tag constructors
  https://github.com/yaml/pyyaml/pull/287 -- Change default loader for yaml.add_constructor
  https://github.com/yaml/pyyaml/pull/305 -- Change default loader for add_implicit_resolver, add_path_resolver
* Make FullLoader safer by removing python/object/apply from the default FullLoader
  https://github.com/yaml/pyyaml/pull/347 -- Move constructor for object/apply to UnsafeConstructor
* Fix bug introduced in 5.1 where quoting went wrong on systems with sys.maxunicode <= 0xffff
  https://github.com/yaml/pyyaml/pull/276 -- Fix logic for quoting special characters
* Other PRs:
  https://github.com/yaml/pyyaml/pull/280 -- Update CHANGES for 5.1

Resources
=========

PyYAML IRC Channel: #pyyaml on irc.freenode.net
PyYAML homepage: https://github.com/yaml/pyyaml
PyYAML documentation: http://pyyaml.org/wiki/PyYAMLDocumentation
Source and binary installers: https://pypi.org/project/PyYAML/
GitHub repository: https://github.com/yaml/pyyaml/
Bug tracking: https://github.com/yaml/pyyaml/issues

YAML homepage: http://yaml.org/
YAML-core mailing list: http://lists.sourceforge.net/lists/listinfo/yaml-core


About PyYAML
============

YAML is a data serialization format designed for human readability and
interaction with scripting languages. PyYAML is a YAML parser and emitter for
Python.

PyYAML features a complete YAML 1.1 parser, Unicode support, pickle support,
capable extension API, and sensible error messages. PyYAML supports standard
YAML tags and provides Python-specific tags that allow to represent an
arbitrary Python object.

PyYAML is applicable for a broad range of tasks from complex configuration
files to object serialization and persistence.


Example
=======

>>> import yaml

>>> yaml.full_load("""
... name: PyYAML
... description: YAML parser and emitter for Python
... homepage: https://github.com/yaml/pyyaml
... keywords: [YAML, serialization, configuration, persistence, pickle]
... """)
{'keywords': ['YAML', 'serialization', 'configuration', 'persistence',
'pickle'], 'homepage': 'https://github.com/yaml/pyyaml', 'description':
'YAML parser and emitter for Python', 'name': 'PyYAML'}

>>> print(yaml.dump(_))
name: PyYAML
homepage: https://github.com/yaml/pyyaml
description: YAML parser and emitter for Python
keywords: [YAML, serialization, configuration, persistence, pickle]


Maintainers
===========

The following people are currently responsible for maintaining PyYAML:

* Ingy döt Net
* Tina Mueller
* Matt Davis

and many thanks to all who have contribributed!
See: https://github.com/yaml/pyyaml/pulls


Copyright
=========

Copyright (c) 2017-2019 Ingy döt Net <ingy@ingy.net>
Copyright (c) 2006-2016 Kirill Simonov <xi@resolvent.net>

The PyYAML module was written by Kirill Simonov <xi@resolvent.net>.
It is currently maintained by the YAML and Python communities.

PyYAML is released under the MIT license.
See the file LICENSE for more details.
