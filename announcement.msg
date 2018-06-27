From: Ingy döt Net <ingy@ingy.net>
To: python-list@python.org, python-announce@python.org, yaml-core@lists.sourceforge.net
Subject: [ANN] PyYAML-4.1: YAML parser and emitter for Python

=======================
 Announcing PyYAML-4.1
=======================

A new MAJOR RELEASE of PyYAML is now available:
https://pypi.org/project/PyYAML/

This is the first release of PyYAML under a new maintenance team. In August
2016, maintenance of PyYAML and LibYAML was turned over from the original
author, Kirill Simonov, to Ian Cordasco and Ingy döt Net.

The canonical source repo moved:

    from: https://bitbucket.org/xi/pyyaml/
    to:   https://github.com/yaml/pyyaml

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
* https://github.com/yaml/pyyaml/pull/74  -- Make pyyaml safe by default.
* https://github.com/yaml/pyyaml/pull/75  -- add 3.12 changelog
* https://github.com/yaml/pyyaml/pull/76  -- Fallback to Pure Python if Compilation fails
* https://github.com/yaml/pyyaml/pull/84  -- Drop unsupported Python 3.3
* https://github.com/yaml/pyyaml/pull/111 -- Remove commented out Psyco code
* https://github.com/yaml/pyyaml/pull/149 -- Test on Python 3.7-dev
* https://github.com/yaml/pyyaml/pull/158 -- Support escaped slash in double quotes "\/"


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

>>> yaml.load("""
... name: PyYAML
... description: YAML parser and emitter for Python
... homepage: https://github.com/yaml/pyyaml
... keywords: [YAML, serialization, configuration, persistence, pickle]
... """)
{'keywords': ['YAML', 'serialization', 'configuration', 'persistence',
'pickle'], 'homepage': 'https://github.com/yaml/pyyaml', 'description':
'YAML parser and emitter for Python', 'name': 'PyYAML'}

>>> print yaml.dump(_)
name: PyYAML
homepage: https://github.com/yaml/pyyaml
description: YAML parser and emitter for Python
keywords: [YAML, serialization, configuration, persistence, pickle]


Maintainers
===========

The following people are responsible for maintaining PyYAML:

* Ingy döt Net
* Ian Cordasco
* Tina Mueller
* Alex Gaynor
* Donald Stufft
* Matt Davis

and many thanks to all who have contribributed!
See: https://github.com/yaml/pyyaml/pulls


Copyright
=========

Copyright (c) 2017-2018 Ingy döt Net <ingy@ingy.net>
Copyright (c) 2006-2016 Kirill Simonov <xi@resolvent.net>

The PyYAML module was written by Kirill Simonov <xi@resolvent.net>.
It is currently maintained by the YAML and Python communities.

PyYAML is released under the MIT license.
See the file LICENSE for more details.
