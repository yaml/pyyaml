From: Ingy döt Net <ingy@ingy.net>
To: python-list@python.org, python-announce@python.org, yaml-core@lists.sourceforge.net
Subject: [ANN] PyYAML-5.1: YAML parser and emitter for Python

=======================
 Announcing PyYAML-5.1
=======================

A new MAJOR RELEASE of PyYAML is now available:
https://pypi.org/project/PyYAML/

This is the first major release of PyYAML under the new maintenance team.

Among the many changes listed below, this release specifically addresses the
arbitrary code execution issue raised by:

    https://nvd.nist.gov/vuln/detail/CVE-2017-18342

(See https://github.com/yaml/pyyaml/wiki/PyYAML-yaml.load(input)-Deprecation
for complete details).

The PyYAML project is now maintained by the YAML and Python communities.
Planning happens on the #yaml-dev, #pyyaml and #libyaml IRC channels on
irc.freenode.net.


Changes
=======

* https://github.com/yaml/pyyaml/pull/35  -- Some modernization of the test running
* https://github.com/yaml/pyyaml/pull/42  -- Install tox in a virtualenv
* https://github.com/yaml/pyyaml/pull/45  -- Allow colon in a plain scalar in a flow context
* https://github.com/yaml/pyyaml/pull/48  -- Fix typos
* https://github.com/yaml/pyyaml/pull/55  -- Improve RepresenterError creation
* https://github.com/yaml/pyyaml/pull/59  -- Resolves #57, update readme issues link
* https://github.com/yaml/pyyaml/pull/60  -- Document and test Python 3.6 support
* https://github.com/yaml/pyyaml/pull/61  -- Use Travis CI built in pip cache support
* https://github.com/yaml/pyyaml/pull/62  -- Remove tox workaround for Travis CI
* https://github.com/yaml/pyyaml/pull/63  -- Adding support to Unicode characters over codepoint 0xffff
* https://github.com/yaml/pyyaml/pull/65  -- Support unicode literals over codepoint 0xffff
* https://github.com/yaml/pyyaml/pull/75  -- add 3.12 changelog
* https://github.com/yaml/pyyaml/pull/76  -- Fallback to Pure Python if Compilation fails
* https://github.com/yaml/pyyaml/pull/84  -- Drop unsupported Python 3.3
* https://github.com/yaml/pyyaml/pull/102 -- Include license file in the generated wheel package
* https://github.com/yaml/pyyaml/pull/105 -- Removed Python 2.6 & 3.3 support
* https://github.com/yaml/pyyaml/pull/111 -- Remove commented out Psyco code
* https://github.com/yaml/pyyaml/pull/129 -- Remove call to `ord` in lib3 emitter code
* https://github.com/yaml/pyyaml/pull/143 -- Allow to turn off sorting keys in Dumper
* https://github.com/yaml/pyyaml/pull/149 -- Test on Python 3.7-dev
* https://github.com/yaml/pyyaml/pull/158 -- Support escaped slash in double quotes "\/"
* https://github.com/yaml/pyyaml/pull/181 -- Import Hashable from collections.abc
* https://github.com/yaml/pyyaml/pull/256 -- Make default_flow_style=False
* https://github.com/yaml/pyyaml/pull/257 -- Deprecate yaml.load and add FullLoader and UnsafeLoader classes
* https://github.com/yaml/pyyaml/pull/263 -- Windows Appveyor build


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
