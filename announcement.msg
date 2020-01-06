From: Tina Müller <post@tinita.de>
To: python-list@python.org, python-announce@python.org, yaml-core@lists.sourceforge.net
Subject: [ANN] PyYAML-5.3: YAML parser and emitter for Python

=======================
Announcing PyYAML-5.3
=======================

A new release of PyYAML is now available:
https://pypi.org/project/PyYAML/

This release contains some bugfixes (handling of slots, enable unicode for
maxunicode < 0xffff, enable large files), enhancements (create timezone
aware datetimes) and some other small enhancements.

Changes
=======

* https://github.com/yaml/pyyaml/pull/290 -- Use `is` instead of equality for comparing with `None`
* https://github.com/yaml/pyyaml/pull/270 -- fix typos and stylistic nit
* https://github.com/yaml/pyyaml/pull/309 -- Fix up small typo
* https://github.com/yaml/pyyaml/pull/161 -- Fix handling of __slots__
* https://github.com/yaml/pyyaml/pull/358 -- Allow calling add_multi_constructor with None
* https://github.com/yaml/pyyaml/pull/285 -- Add use of safe_load() function in README
* https://github.com/yaml/pyyaml/pull/351 -- Fix reader for Unicode code points over 0xFFFF
* https://github.com/yaml/pyyaml/pull/360 -- Enable certain unicode tests when maxunicode not > 0xffff
* https://github.com/yaml/pyyaml/pull/359 -- Use full_load in yaml-highlight example
* https://github.com/yaml/pyyaml/pull/244 -- Document that PyYAML is implemented with Cython
* https://github.com/yaml/pyyaml/pull/329 -- Fix for Python 3.10
* https://github.com/yaml/pyyaml/pull/310 -- increase size of index, line, and column fields
* https://github.com/yaml/pyyaml/pull/260 -- remove some unused imports
* https://github.com/yaml/pyyaml/pull/163 -- Create timezone-aware datetimes when parsed as such
* https://github.com/yaml/pyyaml/pull/363 -- Add tests for timezone


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
