
__all__ = ['BaseLoader', 'FullLoader', 'SafeLoader', 'Loader', 'UnsafeLoader']

from .reader import *
from .scanner import *
from .parser import *
from .composer import *
from .constructor import *
from .resolver import *

class BaseLoader(Reader, Scanner, Parser, Composer, BaseConstructor, BaseResolver):

    def _base_init(self, stream):
        self._yaml_instance = True

        Reader.__init__(self, stream)
        Scanner.__init__(self)
        Parser.__init__(self)
        Composer.__init__(self)

    def __init__(self, stream=None):
        self._base_init(stream)
        BaseConstructor.__init__(self)
        BaseResolver.__init__(self)

    def load(self, stream):
        self._load_init(stream)

        try:
            return self.get_single_data()
        finally:
            self.dispose()
            self.stream = None

    def _load_init(self, stream):
        if hasattr(self, 'stream') and self.stream is None:
            if stream is None:
                raise TypeError("load() requires stream=...")
            self._base_init(stream)

class FullLoader(BaseLoader, Reader, Scanner, Parser, Composer, FullConstructor, Resolver):

    def __init__(self, stream=None):
        self._base_init(stream)
        FullConstructor.__init__(self)
        Resolver.__init__(self)

class SafeLoader(BaseLoader, Reader, Scanner, Parser, Composer, SafeConstructor, Resolver):

    def __init__(self, stream=None):
        self._base_init(stream)
        SafeConstructor.__init__(self)
        Resolver.__init__(self)

class Loader(BaseLoader, Reader, Scanner, Parser, Composer, Constructor, Resolver):

    def __init__(self, stream=None):
        self._base_init(stream)
        Constructor.__init__(self)
        Resolver.__init__(self)

# UnsafeLoader is the same as Loader (which is and was always unsafe on
# untrusted input). Use of either Loader or UnsafeLoader should be rare, since
# FullLoad should be able to load almost all YAML safely. Loader is left intact
# to ensure backwards compatibility.
class UnsafeLoader(BaseLoader, Reader, Scanner, Parser, Composer, Constructor, Resolver):

    def __init__(self, stream=None):
        self._base_init(stream)
        Constructor.__init__(self)
        Resolver.__init__(self)
