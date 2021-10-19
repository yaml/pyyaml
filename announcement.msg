From: Ingy döt Net <ingy@ingy.net>
To: python-list@python.org, python-announce@python.org, yaml-core@lists.sourceforge.net
Subject: [ANN] PyYAML-6.0 Released

=====================
Announcing PyYAML-6.0
=====================

A new release of PyYAML is now available:
https://github.com/yaml/pyyaml/releases/tag/6.0

The previously-deprecated default loader selection in `yaml.load()` has
been removed; `Loader` is now a required argument.

Support for Python 2.7 and 3.5 has been dropped, and support for Python 3.10
added. It now includes libyaml 0.2.5 extension wheels for MacOS M1
(Apple Silicon/arm64), Linux s390x and Linux aarch64.

Numerous other bugfixes and code cleanups are included in this release.


Changes
=======

* https://github.com/yaml/pyyaml/pull/327 -- Change README format to Markdown
* https://github.com/yaml/pyyaml/pull/483 -- Add a test for YAML 1.1 types
* https://github.com/yaml/pyyaml/pull/497 -- fix float resolver to ignore `.` and `._`
* https://github.com/yaml/pyyaml/pull/550 -- drop Python 2.7
* https://github.com/yaml/pyyaml/pull/553 -- Fix spelling of “hexadecimal”
* https://github.com/yaml/pyyaml/pull/556 -- fix representation of Enum subclasses
* https://github.com/yaml/pyyaml/pull/557 -- fix libyaml extension compiler warnings
* https://github.com/yaml/pyyaml/pull/560 -- fix ResourceWarning on leaked file descriptors
* https://github.com/yaml/pyyaml/pull/561 -- always require `Loader` arg to `yaml.load()`
* https://github.com/yaml/pyyaml/pull/564 -- remove remaining direct distutils usage


Resources
=========

PyYAML Matrix: https://matrix.to/#/#pyyaml:yaml.io
PyYAML IRC Channel: #pyyaml on irc.libera.chat
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

```
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
```

Maintainers
===========

The following people are currently responsible for maintaining PyYAML:

* Ingy döt Net
* Matt Davis

and many thanks to all who have contributed!
See: https://github.com/yaml/pyyaml/pulls


Copyright
=========

Copyright (c) 2017-2021 Ingy döt Net <ingy@ingy.net>
Copyright (c) 2006-2016 Kirill Simonov <xi@resolvent.net>

The PyYAML module was written by Kirill Simonov <xi@resolvent.net>.
It is currently maintained by the YAML and Python communities.

PyYAML is released under the MIT license.
See the file LICENSE for more details.
