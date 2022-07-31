__all__ = ["BaseLoader", "FullLoader", "SafeLoader", "Loader", "UnsafeLoader"]

from abc import ABC, abstractproperty
from typing import Type
from .reader import *
from .scanner import *
from .parser import *
from .composer import *
from .constructor import *
from .resolver import *
from .types import _Stream


class LoaderABC(
    ABC,
    Parser,
    Composer,
    BaseConstructor,
    BaseResolver,
    Scanner,  # TODO: Why get_token is used?, mypy complains without this, replaces Reader
):
    @abstractproperty
    def _constructor(self) -> Type[BaseConstructor]:
        """Constructor"""

    @abstractproperty
    def _resolver(self) -> Type[BaseResolver]:
        """Resolver"""

    def __init__(self, stream: _Stream):
        Reader.__init__(self, stream)
        Scanner.__init__(self)  # TODO: why mypy wants Scanner for tokens
        Parser.__init__(self)
        Composer.__init__(self)
        self._constructor.__init__(self)
        self._resolver.__init__(self)


class BaseLoader(LoaderABC):

    _constructor = BaseConstructor
    _resolver = BaseResolver


class FullLoader(LoaderABC):

    _constructor = FullConstructor
    _resolver = Resolver


class SafeLoader(LoaderABC):
    _constructor = SafeConstructor
    _resolver = Resolver


class Loader(LoaderABC):

    _constructor = Constructor
    _resolver = Resolver


# UnsafeLoader is the same as Loader (which is and was always unsafe on
# untrusted input). Use of either Loader or UnsafeLoader should be rare, since
# FullLoad should be able to load almost all YAML safely. Loader is left intact
# to ensure backwards compatibility.
class UnsafeLoader(LoaderABC):

    _constructor = Constructor
    _resolver = Resolver
