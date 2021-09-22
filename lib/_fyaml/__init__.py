# This is a stub package designed to roughly emulate the _yaml
# extension module, which previously existed as a standalone module
# and has been moved into the `yaml` package namespace.
# It does not perfectly mimic its old counterpart, but should get
# close enough for anyone who's relying on it even when they shouldn't.
import yaml

# in some circumstances, the yaml module we imoprted may be from a different version, so we need
# to tread carefully when poking at it here (it may not have the attributes we expect)
if not getattr(yaml, '__with_libfyaml__', False):
    from sys import version_info

    exc = ModuleNotFoundError if version_info >= (3, 6) else ImportError
    raise exc("No module named '_fyaml'")
else:
    from yaml._fyaml import *
    import warnings
    warnings.warn(
        ' To use the libfyaml-based parser and emitter, import from `yaml`:'
        ' `from yaml import FLoader as Loader, FDumper as Dumper`.',
        DeprecationWarning
    )
    del warnings
    # Don't `del yaml` here because yaml is actually an existing
    # namespace member of _yaml.

__name__ = '_fyaml'
# If the module is top-level (i.e. not a part of any specific package)
# then the attribute should be set to ''.
# https://docs.python.org/3.8/library/types.html
__package__ = ''