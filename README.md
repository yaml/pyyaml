PyYAML
======

The next generation YAML parser and emitter for Python.

A full-featured YAML processing framework for Python

[![PyYAML CI](https://github.com/yaml/pyyaml/actions/workflows/ci.yaml/badge.svg)](https://github.com/yaml/pyyaml/actions/workflows/ci.yaml)
[![PyPI version](https://badge.fury.io/py/PyYAML.svg)](https://badge.fury.io/py/PyYAML)

YAML is a data serialization format designed for human readability
and interaction with scripting languages.  PyYAML is a YAML parser
and emitter for Python.

PyYAML features a complete YAML 1.1 parser, Unicode support, pickle
support, capable extension API, and sensible error messages.  PyYAML
supports standard YAML tags and provides Python-specific tags that
allow to represent an arbitrary Python object.

PyYAML is applicable for a broad range of tasks from complex
configuration files to object serialization and persistence.

## Installation

To install, type following:

```shell
# recommended
pip install PyYAML
# or
python setup.py install
```

By default, the `setup.py` script checks whether LibYAML is installed and if
so, builds and installs LibYAML bindings.
To skip the check and force installation of LibYAML bindings, use the option
`--with-libyaml`: `python setup.py --with-libyaml install`.
To disable the check and skip building and installing LibYAML bindings, use
`--without-libyaml`:

```shell
# recommended
python -m pip install pyyaml --global-option=--without-libyaml
# or
python setup.py --without-libyaml install
# Ref: https://pip.pypa.io/en/stable/cli/pip_install/#per-requirement-overrides
```

When LibYAML bindings are installed, you may use fast LibYAML-based parser and
emitter as follows:

```python
    >>> yaml.load(stream, Loader=yaml.CLoader)
    >>> yaml.dump(data, Dumper=yaml.CDumper)
```

If you don't trust the input YAML stream, you should use:

```python
    >>> yaml.safe_load(stream)
```

## Testing

PyYAML includes a comprehensive test suite.
To run the tests, type `python setup.py test`.

## Further Information

* For more information, check the
  [PyYAML homepage](https://github.com/yaml/pyyaml).

* [PyYAML tutorial and reference](http://pyyaml.org/wiki/PyYAMLDocumentation).

* Discuss PyYAML with the maintainers on
  Matrix at https://matrix.to/#/#pyyaml:yaml.io or
  IRC #pyyaml irc.libera.chat

* Submit bug reports and feature requests to the
  [PyYAML bug tracker](https://github.com/yaml/pyyaml/issues).

## License

The PyYAML module was written by Kirill Simonov <xi@resolvent.net>.
It is currently maintained by the YAML and Python communities.

PyYAML is released under the MIT license.

See the file LICENSE for more details.
