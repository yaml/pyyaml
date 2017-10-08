# PyYAML

## The next generation YAML parser and emitter for Python

[![Build Status](https://travis-ci.org/yaml/pyyaml.svg?branch=master)](https://travis-ci.org/yaml/pyyaml)

To install, type:

```bash
python setup.py install
```

By default, the setup.py script checks whether LibYAML is installed
and if so, builds and installs LibYAML bindings.  To skip the check
and force installation of LibYAML bindings, use the option `--with-libyaml`:
`python setup.py --with-libyaml install`.  To disable the check and
skip building and installing LibYAML bindings, use `--without-libyaml`:
`python setup.py --without-libyaml install`.

When LibYAML bindings are installed, you may use fast LibYAML-based
parser and emitter as follows:

```python
>>> yaml.load(stream, Loader=yaml.CLoader)
>>> yaml.dump(data, Dumper=yaml.CDumper)
```
PyYAML includes a comprehensive test suite.  To run the tests, type:
```bash
python setup.py test
```

For more information, check the PyYAML homepage:
http://pyyaml.org/wiki/PyYAML.

For PyYAML tutorial and reference, see:
http://pyyaml.org/wiki/PyYAMLDocumentation.

Post your questions and opinions to the YAML-Core mailing list:
http://lists.sourceforge.net/lists/listinfo/yaml-core.

Submit bug reports and feature requests to the PyYAML bug tracker:
https://github.com/yaml/pyyaml/issues.

PyYAML is written by Kirill Simonov <xi@resolvent.net>.  It is released
under the MIT license. See the file LICENSE for more details.
