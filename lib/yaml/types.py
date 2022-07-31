from typing import IO, Any, Type, Union
from .loader import BaseLoader, FullLoader, SafeLoader, Loader, UnsafeLoader
from .dumper import BaseDumper, SafeDumper, Dumper

_Stream = Union[bytes, IO[bytes], str, IO[str]]

# FIXME: the functions really return str if encoding is None, otherwise bytes. Waiting for python/mypy#5621
_Yaml = Any

_Loader = Union[
    BaseLoader,
    FullLoader,
    SafeLoader,
    Loader,
    UnsafeLoader,
]

_Dumper = Union[
    BaseDumper,
    SafeDumper,
    Dumper,
]

_Tag = str
