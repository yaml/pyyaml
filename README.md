# PyYAML

A full-featured YAML processing framework for Python.

The documentation is available on the
[PyYAML website](https://pyyaml.org/wiki/PyYAMLDocumentation)
or in the form of
[GitHub flavoured markdown](https://github.com/yaml/pyyaml#readme).


## Installation

### Default

```bash
pip install pyyaml
```

### From Source

```bash
pip install git+https://github.com/yaml/pyyaml.git@master
```

or checkout the repository, or extract the `.tar.gz` and navigate inside and run:

```bash
python setup.py install
```

### with LibYAML

By default, the `setup.py` script checks whether LibYAML is installed and if
so, builds and installs LibYAML bindings.

#### Why LibYAML?

When LibYAML bindings are installed, you may use fast C-based parser and
emitter as follows:

```python
yaml.load(stream, Loader=yaml.CLoader)
yaml.dump(data, Dumper=yaml.CDumper)
```

#### Force installation **with** LibYAML `--with-libyaml`

```bash
python setup.py --with-libyaml install
```

#### Force installation **without** LibYAML `--without-libyaml`

```bash
python setup.py --without-libyaml install
```

## Testing

PyYAML includes a comprehensive test suite.
To run the tests:

```bash
python setup.py test
```

## Loadings and Dumping 

### `safe_load` and `safe_dump`

Your default and safest choice for YAML streams.

### `load` and `dump`

WARNING: CVE reference, etc. from wiki page.

Can load Python objects:

### The `Loader` options

e.g. `SafeLoader` etc ...

## The yaml package
### The keyword arguments

<!-- 
A lot of the keyword arguments are shared. 
Need a sensible way to just list all of them and their types/meaning.
Then need to have the function signatures like below, 
ideally world we won't use `...`, 
use **kwargs and have a comment for full signature, e.g.:
"refer to the dump() signature for the full list of available kwargs"?

```python
load(stream, Loader=Loader)
load_all(stream, Loader=Loader)

safe_load(stream)
safe_load_all(stream)

dump(data, stream=None, Dumper=Dumper,
    default_style=None,
    default_flow_style=None,
    encoding='utf-8', # encoding=None (Python 3)
    explicit_start=None,
    explicit_end=None,
    version=None,
    tags=None,
    canonical=None,
    indent=None,
    width=None,
    allow_unicode=None,
    line_break=None)
dump_all(data, stream=None, Dumper=Dumper, ...)

safe_dump(data, stream=None, ...)
safe_dump_all(data, stream=None, ...)
```
-->
Mention that these are the keyword arguments of the `Dumper` class and subclasses.
- `documents` - the python object to serialise
- `stream` - where to output
  - IOObject - anything with a `.write()`, will be written to
  - `None` - returns a string.
- `Dumper` - `Type[Dumper]` class/subclass of `Dumper`
...
- `default_flow_style` - `Optional[bool]`
  - `True` - what true does
  - `False` - what false does
  - `None` - what None does


Mention that these are the keyword arguments of the `Loader` class and subclasses.
- `stream`

<!--
Old Documentation TOC
- [PyYAML Documentation](#pyyaml-documentation)
  * [Installation](#installation)
  * [Frequently Asked Questions](#frequently-asked-questions)
    + [Dictionaries without nested collections are not dumped correctly](#dictionaries-without-nested-collections-are-not-dumped-correctly)
  * [Python 3 support](#python-3-support)
  * [Tutorial](#tutorial)
    + [Loading YAML](#loading-yaml)
    + [Dumping YAML](#dumping-yaml)
    + [Constructors, representers, resolvers](#constructors--representers--resolvers)
  * [YAML syntax](#yaml-syntax)
    + [Documents](#documents)
    + [Block sequences](#block-sequences)
    + [Block mappings](#block-mappings)
    + [Flow collections](#flow-collections)
    + [Scalars](#scalars)
    + [Aliases](#aliases)
    + [Tags](#tags)
  * [YAML tags and Python types](#yaml-tags-and-python-types)
    + [String conversion (Python 2 only)](#string-conversion--python-2-only-)
    + [String conversion (Python 3 only)](#string-conversion--python-3-only-)
    + [Names and modules](#names-and-modules)
    + [Objects](#objects)
  * [Reference](#reference)
    + [The yaml package](#the-yaml-package)
    + [Mark](#mark)
    + [YAMLError](#yamlerror)
    + [Tokens](#tokens)
    + [Events](#events)
    + [Nodes](#nodes)
    + [Loader](#loader)
    + [Dumper](#dumper)
    + [YAMLObject](#yamlobject)
  * [Deviations from the specification](#deviations-from-the-specification)
 -->

## Constructors, representers, resolvers
## YAML syntax

### Documents
### Block sequences
### Block mappings
### Flow collections
### Scalars
### Aliases

## YAML tags and Python types

### String conversion (Python 2 only)
### String conversion (Python 3 only)
### Names and modules
### Objects

## Deviations from the specification


## Reference

### The yaml package
### Mark
### YAMLError
### Tokens
### Events
### Nodes
### Loader
### Dumper
### YAMLObject

## Frequently Asked Questions (FAQs)

### YAML Specification Suppport

1.2 vs 1.1 and what pyyaml versions support what


### Dictionaries without nested collections are not dumped correctly

_Why does_

```python
import yaml
document = """
  a: 1
  b:
    c: 3
    d: 4
"""
print yaml.dump(yaml.load(document))
```

_give_

```
a: 1
b: {c: 3, d: 4}
```

_(see #18, #24)?_

It's a correct output despite the fact that the style of the nested mapping is
different.

By default, PyYAML chooses the style of a collection depending on whether it
has nested collections.
If a collection has nested collections, it will be assigned the block style.
Otherwise it will have the flow style.

If you want collections to be always serialized in the block style, set the
parameter `default_flow_style` of `dump()` to `False`.
For instance,

```python
>>> print yaml.dump(yaml.load(document), default_flow_style=False)
a: 1
b:
  c: 3
  d: 4
```


## Python 3 support

Starting from the *3.08* release, PyYAML and LibYAML bindings provide a
complete support for Python 3.
Python 2 support was dropped in the *6.0* release.
This is a short outline of differences in PyYAML API between Python 2 and
Python 3 versions.


_In Python 2:_

* `str` objects are converted into `!!str`, `!!python/str`
  or `!binary` nodes depending on whether the object is an ASCII, UTF-8
  or binary string.
* `unicode` objects are converted into `!!python/unicode` or
  `!!str` nodes depending on whether the object is an ASCII string or not.
* `yaml.dump(data)` produces the document as a UTF-8 encoded `str` object.
* `yaml.dump(data, encoding=('utf-8'|'utf-16-be'|'utf-16-le'))` produces
  a `str` object in the specified encoding.
* `yaml.dump(data, encoding=None)` produces a `unicode` object.


_In Python 3:_

* `str` objects are converted to `!!str` nodes.
* `bytes` objects are converted to `!!binary` nodes.
* For compatibility reasons, `!!python/str` and `!python/unicode` tags are
  still supported and the corresponding nodes are converted to `str` objects.
* `yaml.dump(data)` produces the document as a `str` object.
* `yaml.dump(data, encoding=('utf-8'|'utf-16-be'|'utf-16-le'))` produces
  a `bytes` object in the specified encoding.



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
