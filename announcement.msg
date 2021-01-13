From: Matt Davis <mrd@redhat.com>
To: python-list@python.org, python-announce@python.org, yaml-core@lists.sourceforge.net
Subject: [ANN] PyYAML-5.4b1: Linux and Mac users, please test!

=========================
Announcing PyYAML-5.4b1
=========================

A beta release of PyYAML is now available:
https://github.com/yaml/pyyaml/releases/tag/5.4b1

This release contains a security fix for CVE-2020-14343. It removes the
python/module, python/object, and python/object/new tags from the FullLoader.
YAML that uses these tags must be loaded by UnsafeLoader, or a custom loader
that has explicitly enabled them.

This beta release also adds Python wheels for manylinux1 (x86_64) and
MacOS (x86_64) with the libyaml extension included (built on libyaml 0.2.5).
We believe these wheels to be stable, but please take the opportunity to test
against your local Linux and MacOS environments, and file any issues at
https://github.com/yaml/pyyaml/issues.

PyYAML 5.4 will be the last release to support Python 2.7.


Changes
=======

* https://github.com/yaml/pyyaml/pull/407 -- build modernization, remove distutils, fix metadata, build wheels, CI to GHA
* https://github.com/yaml/pyyaml/pull/472 -- fix for CVE-2020-14343, moves arbitrary python tags to UnsafeLoader
* https://github.com/yaml/pyyaml/pull/441 -- fix memory leak in implicit resolver setup
* https://github.com/yaml/pyyaml/pull/392 -- fix py2 copy support for timezone objects
* https://github.com/yaml/pyyaml/pull/378 -- fix compatibility with Jython


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
* Matt Davis

and many thanks to all who have contribributed!
See: https://github.com/yaml/pyyaml/pulls


Copyright
=========

Copyright (c) 2017-2020 Ingy döt Net <ingy@ingy.net>
Copyright (c) 2006-2016 Kirill Simonov <xi@resolvent.net>

The PyYAML module was written by Kirill Simonov <xi@resolvent.net>.
It is currently maintained by the YAML and Python communities.

PyYAML is released under the MIT license.
See the file LICENSE for more details.
