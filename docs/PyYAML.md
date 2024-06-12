# PyYAML

PyYAML is a YAML parser and emitter for Python.

## Overview

[YAML](http://yaml.org/) is a data serialization format designed for human
readability and interaction with scripting languages.

[PyYAML](http://pyyaml.org/wiki/PyYAML) is a YAML parser and emitter for
the Python programming language.

PyYAML features

* a *complete* [YAML 1.1](http://yaml.org/spec/1.1/) parser.
  In particular, PyYAML can parse all examples from the specification.
  The parsing algorithm is simple enough to be a reference for YAML parser implementors.
* Unicode support including UTF-8/UTF-16 input/output and *\u* escape sequences.
* low-level event-based parser and emitter API (like SAX).
* high-level API for serializing and deserializing native Python objects (like DOM or pickle).
* support for all types from the [YAML types repository](http://yaml.org/type/index.html).
  A simple extension API is provided.
* both pure-Python and fast [LibYAML](./LibYAML)-based parsers and emitters.
* relatively sensible error messages.

## Requirements

PyYAML requires Python 2.7 or Python 3.4+.

## Download and Installation

The current stable release of PyYAML: *5.1*.

Download links:

* *TAR.GZ package*: <http://pyyaml.org/download/pyyaml/PyYAML-5.1.tar.gz>
<!-- * *ZIP package*: <http://pyyaml.org/download/pyyaml/PyYAML-5.1.zip> -->
* *Windows installers (32-bit)*:
    * <http://pyyaml.org/download/pyyaml/PyYAML-5.1-cp27-cp27m-win32.whl> (for Python 2.7)
    * <http://pyyaml.org/download/pyyaml/PyYAML-5.1-cp34-cp34m-win32.whl> (for Python 3.4)
    * <http://pyyaml.org/download/pyyaml/PyYAML-5.1-cp35-cp35m-win32.whl> (for Python 3.5)
    * <http://pyyaml.org/download/pyyaml/PyYAML-5.1-cp36-cp36m-win32.whl> (for Python 3.6)
    * <http://pyyaml.org/download/pyyaml/PyYAML-5.1-cp37-cp37m-win32.whl> (for Python 3.7)
* *Windows installers (64-bit)*:
    * <http://pyyaml.org/download/pyyaml/PyYAML-5.1-cp27-cp27m-win_amd64.whl> (for Python 2.7)
    * <http://pyyaml.org/download/pyyaml/PyYAML-5.1-cp34-cp34m-win_amd64.whl> (for Python 3.4)
    * <http://pyyaml.org/download/pyyaml/PyYAML-5.1-cp35-cp35m-win_amd64.whl> (for Python 3.5)
    * <http://pyyaml.org/download/pyyaml/PyYAML-5.1-cp36-cp36m-win_amd64.whl> (for Python 3.6)
    * <http://pyyaml.org/download/pyyaml/PyYAML-5.1-cp37-cp37m-win_amd64.whl> (for Python 3.7)

Unpack the archive and install the package by executing

    $ python setup.py install

If you want to use [LibYAML](./LibYAML) bindings, you need to download and install [LibYAML](./LibYAML).
Then you may install the bindings by executing

    $ python setup.py --with-libyaml install

The source distribution includes a comprehensive test suite.  To run the tests, type

    $ python setup.py test

## Documentation

_Quick example (see documentation for loading multiple documents):_

``` {.python}
>>> import yaml

>>> print yaml.load("""
... name: Vorlin Laruknuzum
... sex: Male
... class: Priest
... title: Acolyte
... hp: [32, 71]
... sp: [1, 13]
... gold: 423
... inventory:
... - a Holy Book of Prayers (Words of Wisdom)
... - an Azure Potion of Cure Light Wounds
... - a Silver Wand of Wonder
... """)

{'name': 'Vorlin Laruknuzum', 'gold': 423, 'title': 'Acolyte', 'hp': [32, 71],
'sp': [1, 13], 'sex': 'Male', 'inventory': ['a Holy Book of Prayers (Words of Wisdom)',
'an Azure Potion of Cure Light Wounds', 'a Siver Wand of Wonder'], 'class': 'Priest'}

>>> print yaml.dump({'name': "The Cloak 'Colluin'", 'depth': 5, 'rarity': 45,
... 'weight': 10, 'cost': 50000, 'flags': ['INT', 'WIS', 'SPEED', 'STEALTH']})

name: The Cloak 'Colluin'
rarity: 45
flags: [INT, WIS, SPEED, STEALTH]
weight: 10
cost: 50000
depth: 5
```

For more details, please check [PyYAML Documentation](./PyYAMLDocumentation).


## History

*5.1 (2019-03-13)*

* Incompatible changes:
* #257 -- Deprecate yaml.load and add FullLoader and UnsafeLoader classes
* #256 -- Make default_flow_style=False
* Features:
* #158 -- Support escaped slash in double quotes "\/"
* #45 -- Allow colon in a plain scalar in a flow context
* #63 -- Adding support to Unicode characters over codepoint 0xffff
* #254 -- Allow to turn off sorting keys in Dumper
* Bugfixes:
* #129 -- Remove call to `ord` in lib3 emitter code
* Other:
* #35 -- Some modernization of the test running
* #42 -- Install tox in a virtualenv
* #48 -- Fix typos
* #55 -- Improve RepresenterError creation
* #59 -- Resolves #57, update readme issues link
* #60 -- Document and test Python 3.6 support
* #61 -- Use Travis CI built in pip cache support
* #62 -- Remove tox workaround for Travis CI
* #75 -- add 3.12 changelog
* #76 -- Fallback to Pure Python if Compilation fails
* #84 -- Drop unsupported Python 3.3
* #102 -- Include license file in the generated wheel package
* #105 -- Removed Python 2.6 & 3.3 support
* #111 -- Remove commented out Psyco code
* #149 -- Test on Python 3.7-dev
* #175 -- Updated link to pypi in release announcement
* #181 -- Import Hashable from collections.abc
* #194 -- Reverting https://github.com/yaml/pyyaml/pull/74
* #195 -- Build libyaml on travis
* #196 -- Force cython when building sdist
* #261 -- Skip certain unicode tests when maxunicode not > 0xffff
* #263 -- Windows Appveyor build

*3.13 (2018-07-05)*

* Rebuild wheels using latest Cython for Python 3.7 support.

*3.12 (2016-08-28)*

* Wheel packages for Windows binaries.
* Adding an implicit resolver to a derived loader should not affect
  the base loader (fixes issue #57).
* Uniform representation for OrderedDict across different versions
  of Python (fixes issue #61).
* Fixed comparison to None warning (closes issue #64).

*3.11 (2014-03-26)*

* Source and binary distributions are rebuilt against the latest versions
  of Cython and LibYAML.

*3.10 (2011-05-30)*

 * Do not try to build LibYAML bindings on platforms other than CPython;
   this fixed installation under Jython (Thank to olt(at)bogosoft(dot)com).
 * Clear cyclic references in the parser and the emitter
   (Thank to kristjan(at)ccpgames(dot)com).
 * LibYAML bindings are rebuilt with the latest version of Cython.
 * Dropped support for Python 2.3 and 2.4; currently supported versions
   are 2.5 to 3.2.

*3.09 (2009-08-31)*

 * Fixed use of uninitialized memory when emitting anchors with
   LibYAML bindings (Thank to cegner(at)yahoo-inc(dot)com).
 * Fixed emitting incorrect BOM characters for UTF-16 (Thank to
   Valentin Nechayev)
 * Fixed the emitter for folded scalars not respecting the preferred
   line width (Thank to Ingy).
 * Fixed a subtle ordering issue with emitting `%TAG` directives
   (Thank to Andrey Somov).
 * Fixed performance regression with LibYAML bindings.

*3.08 (2008-12-31)*

 * Python 3 support (Thank to Erick Tryzelaar).
 * Use Cython instead of Pyrex to build LibYAML bindings.
 * Refactored support for unicode and byte input/output streams.

*3.07 (2008-12-29)*

 * The emitter learned to use an optional indentation indicator
   for block scalar; thus scalars with leading whitespaces
   could now be represented in a literal or folded style.
 * The test suite is now included in the source distribution.
   To run the tests, type `python setup.py test`.
 *  Refactored the test suite: dropped `unittest` in favor of
   a custom test appliance.
 * Fixed the path resolver in `CDumper`.
 * Forced an explicit document end indicator when there is
   a possibility of parsing ambiguity.
 * More `setup.py` improvements: the package should be usable
   when any combination of `setuptools`, `Pyrex` and `LibYAML`
   is installed.
 * Windows binary packages are built against LibYAML-0.1.2.
 * Minor typos and corrections.  Thank to Ingy dot Net
   and Andrey Somov.

*3.06 (2008-10-03)*

 * setup.py checks whether [LibYAML](./LibYAML) is installed and if so, builds
   and installs [LibYAML](./LibYAML) bindings.  To force or disable installation
   of [LibYAML](./LibYAML) bindings, use `--with-libyaml` or `--without-libyaml`
   respectively (partially fixes #34).
 * Building [LibYAML](./LibYAML) bindings no longer requires Pyrex installed (fixed #33).
 * `yaml.load()` raises an exception if the input stream contains
   more than one YAML document (fixed #54).
 * Fixed exceptions produced by [LibYAML](./LibYAML) bindings (fixed #50).
 * Fixed a dot `'.'` character being recognized as `!!float` (fixed #62).
 * Fixed Python 2.3 compatibility issue in constructing `!!timestamp` values.
 * Windows binary packages are built against the [LibYAML](./LibYAML) stable branch.
 * Added attributes `yaml.__version__` and  `yaml.__with_libyaml__` (fixed #85).

*3.05 (2007-05-13)*

 * Allow for immutable subclasses of YAMLObject. Fixed #53.
 * Make the encoding of the unicode->str conversion explicit; fixed #52.
 * Fixed a problem when the `DOCUMENT-END` event is not emitted until the beginning
   of the next document is available. Fixed #51. Thanks edward(at)sweetbytes.net
   for the bug report. 
 * Improve output of float values. Fixed #49. 
 * Fix the bug when the path in `add_path_resolver` contains boolean values.
   Fixed #43 (thanks to jstroud(at)mbi.ucla.edu for reporting and pointing to the cause).
 * Use the types module instead of constructing type objects by hand. Fixed #41.
   Thanks to v.haisman(at)sh.cvut.cz for the patch.
 * Fix loss of microsecond precision in datetime.datetime constructor (fix #30).
   Thanks to edemaine(at)mit.edu for the bug report and the patch.
 * Fixed loading an empty YAML stream.

*3.04 (2006-08-20)*

 * Include experimental [LibYAML](./LibYAML) bindings.
 * Fully support recursive structures (close #5).
 * Sort dictionary keys (close #23). Mapping node values are now represented as lists of pairs
   instead of dictionaries. Do not check for duplicate mapping keys as it didn't work correctly anyway.
 * Fix invalid output of single-quoted scalars in cases when a single
   quote is not escaped when preceeded by whitespaces or line breaks
   (close #17).
 * To make porting easier, rewrite Parser not using generators.
 * Fix handling of unexpected block mapping values, like 
   {{{
   : foo
   }}}
 * Fix a bug in `Representer.represent_object`: `copy_reg.dispatch_table`
   was not correctly handled.
 * Fix a bug when a block scalar is incorrectly emitted in the simple key context.
 * Hold references to the objects being represented (close #22).
 * Make Representer not try to guess `!!pairs` when a list is represented.
 * Fix timestamp constructing and representing (close #25).
 * Fix the 'N' plain scalar being incorrectly recognized as ``!!bool`` (close #26).

*3.03 (2006-06-19)*

 * Fix Python 2.5 compatibility issues.
 * Fix numerous bugs in the float handling.
 * Fix scanning some ill-formed documents.
 * Other minor fixes.

*3.02 (2006-05-15)*

 * Fix win32 installer.  Apparently bdist_wininst does not work well under
   Linux.
 * Fix a bug in add_path_resolver.
 * Add the yaml-highlight example.  Try to run on a color terminal:
   `python yaml_hl.py <any_document.yaml`.

*3.01 (2006-05-07)*

 * Initial release.  The version number reflects the codename of the
   project (PyYAML 3000) and differenciates it from the abandoned
   PyYaml module.

## Author and Copyright

Copyright (c) 2017-2019 Ingy döt Net
Copyright (c) 2006-2016 Kirill Simonov

The PyYAML module was written by [Kirill Simonov](mailto:xi@resolvent.net).
It is now maintained by the YAML community.

PyYAML is released under the MIT license.
