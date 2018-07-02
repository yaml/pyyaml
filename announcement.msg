From: Ingy döt Net <ingy@ingy.net>
To: python-list@python.org, python-announce@python.org, yaml-core@lists.sourceforge.net
Subject: [ANN] PyYAML-3.13: YAML parser and emitter for Python

========================
 Announcing PyYAML-3.13
========================

A new bug fix release of PyYAML is now available:

    http://pyyaml.org/wiki/PyYAML

*** Important Note From Maintainers ***

This is the first PyYAML release by the new maintainers. It was made critical
because PyYAML-3.12 did not work with the recent Python 3.7 release.

A more ambitious 4.1 release was attempted last week and needed to be retracted
for many reasons. We apologize any pain caused by the 4.1 removal, but we
remain confident that it was the best decision.

There are over 60 pull requests in PyYAML and LibYAML that will be represented
in the upcoming 4.2 release and we are working hard to get those to you as soon
as the release is ready (but no sooner :).

We are are excited that the PyYAML project is moving forward again.

-- The PyYAML Maintenance Team



Changes
=======

* Rebuilt with the latest Cython to support the new Python 3.7 release.
* No functionality is different from PyYAML 3.12 in this release.


Resources
=========

PyYAML IRC Channel: #pyyaml on irc.freenode.net
YAML IRC Channel: #yaml-dev on irc.freenode.net
LibYAML IRC Channel: #libyaml on irc.freenode.net

PyYAML homepage: http://pyyaml.org/wiki/PyYAML
PyYAML documentation: http://pyyaml.org/wiki/PyYAMLDocumentation
Source and binary installers: https://pypi.python.org/pypi/PyYAML/3.13

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
files to object serialization and persistance.


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

Copyright (c) 2017-2018 Ingy döt Net <ingy@ingy.net>
Copyright (c) 2006-2016 Kirill Simonov <xi@resolvent.net>

The PyYAML module was written by Kirill Simonov <xi@resolvent.net>.
It is currently maintained by the YAML and Python communities.

PyYAML is released under the MIT license.
See the file LICENSE for more details.
