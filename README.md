# PyYAML
The next generation YAML parser and emitter for Python.

## Install
```shell script
python setup.py install
```

By default, the `setup.py` script checks whether LibYAML is installed and if so, builds and installs LibYAML bindings.
* Skip the check and force installation of LibYAML bindings:
    ```shell script
    python setup.py --with-libyaml install
    ```
* Disable the check and skip building and installing LibYAML bindings:
    ```shell script
    python setup.py --without-libyaml install
    ```

## Usage
When LibYAML bindings are installed, you may use fast LibYAML-based parser and emitter as follows:

```python
data = yaml.load(stream, Loader=yaml.CLoader)
yaml.dump(data, Dumper=yaml.CDumper)
```

If you don't trust the input stream, you should use:

```
data = yaml.safe_load(stream)
```

## Tests
PyYAML includes a comprehensive test suite.  To run the tests, type `python setup.py test`.

## Additional information
* Homepage: <https://github.com/yaml/pyyaml>
* Tutorial and reference: <http://pyyaml.org/wiki/PyYAMLDocumentation>
* Discuss PyYAML with the maintainers: `#pyyaml` in  <irc://irc.freenode.net>
* YAML-Core mailing list: <http://lists.sourceforge.net/lists/listinfo/yaml-core>
* Bugs and feature requests: <https://github.com/yaml/pyyaml/issues>

The PyYAML module was written by Kirill Simonov `<xi@resolvent.net>`.
It is currently maintained by the YAML and Python communities.

PyYAML is released under the MIT license. See the file [LICENSE](LICENSE) for more details.
