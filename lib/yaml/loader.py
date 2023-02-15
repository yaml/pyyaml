from __future__ import annotations

__all__ = ['BaseLoader', 'FullLoader', 'SafeLoader', 'Loader', 'UnsafeLoader', 'FastestBaseLoader']

from .config import LoaderConfigMixin
from .reader import *
from .scanner import *
from .parser import *
from .composer import *
from .constructor import *
from .resolver import *
from . import tagset

# FIXME: defer setup to fix circular import
try:
    from .cyaml import CBaseLoader as FastestBaseLoader
except ImportError as ie:
    FastestBaseLoader = None


class BaseLoader(Reader, Scanner, Parser, Composer, BaseConstructor, BaseResolver, LoaderConfigMixin):
    def __init__(self, stream):
        Reader.__init__(self, stream)
        Scanner.__init__(self)
        Parser.__init__(self)
        Composer.__init__(self)
        BaseConstructor.__init__(self)
        BaseResolver.__init__(self)

    @classmethod
    def init_tags(cls, tagset: tagset.TagSet):
        cls.init_constructors(tagset.constructors)
        cls.init_resolvers(tagset.resolvers)


if not FastestBaseLoader:
    # fall back to pure Python if CBaseLoader is unavailable
    FastestBaseLoader = BaseLoader


# FIXME: once we fully implement the config stuff, these can all be collapsed to a config call, eg:
# FullLoader = FastestBaseLoader.config(type_name='FullLoader', tagset=tagset.yaml11 | tagset.python_full)
# SafeLoader = FastestBaseLoader.config(type_name='SafeLoader', tagset=tagset.yaml11)
# UnsafeLoader = FastestBaseLoader.config(type_name='UnsafeLoader', tagset=tagset.yaml11 | tagset.python_unsafe)
# this pattern will also allow a much easier path for users to bolt on default behavior to any old loader

class FullLoader(Reader, Scanner, Parser, Composer, FullConstructor, Resolver, LoaderConfigMixin):

    def __init__(self, stream):
        Reader.__init__(self, stream)
        Scanner.__init__(self)
        Parser.__init__(self)
        Composer.__init__(self)
        FullConstructor.__init__(self)
        Resolver.__init__(self)

class SafeLoader(Reader, Scanner, Parser, Composer, SafeConstructor, Resolver, LoaderConfigMixin):

    def __init__(self, stream):
        Reader.__init__(self, stream)
        Scanner.__init__(self)
        Parser.__init__(self)
        Composer.__init__(self)
        SafeConstructor.__init__(self)
        Resolver.__init__(self)

class Loader(Reader, Scanner, Parser, Composer, Constructor, Resolver, LoaderConfigMixin):

    def __init__(self, stream):
        Reader.__init__(self, stream)
        Scanner.__init__(self)
        Parser.__init__(self)
        Composer.__init__(self)
        Constructor.__init__(self)
        Resolver.__init__(self)

# UnsafeLoader is the same as Loader (which is and was always unsafe on
# untrusted input). Use of either Loader or UnsafeLoader should be rare, since
# FullLoad should be able to load almost all YAML safely. Loader is left intact
# to ensure backwards compatibility.
class UnsafeLoader(Reader, Scanner, Parser, Composer, Constructor, Resolver, LoaderConfigMixin):

    def __init__(self, stream):
        Reader.__init__(self, stream)
        Scanner.__init__(self)
        Parser.__init__(self)
        Composer.__init__(self)
        Constructor.__init__(self)
        Resolver.__init__(self)


_12_CoreLoader = BaseLoader.config(type_name='_12_CoreLoader', tagset=tagset.core)
_12_JSONLoader = BaseLoader.config(type_name='_12_JSONLoader', tagset=tagset.json)

