
__all__ = ['BaseLoader', 'FullLoader', 'SafeLoader', 'UnsafeLoader']

from .reader import *
from .scanner import *
from .parser import *
from .composer import *
from .constructor import *
from .resolver import *
import warnings

class BaseLoader(Reader, Scanner, Parser, Composer, BaseConstructor, BaseResolver):

    def __init__(self, stream):
        Reader.__init__(self, stream)
        Scanner.__init__(self)
        Parser.__init__(self)
        Composer.__init__(self)
        BaseConstructor.__init__(self)
        BaseResolver.__init__(self)

class FullLoader(Reader, Scanner, Parser, Composer, FullConstructor, Resolver):

    def __init__(self, stream):
        Reader.__init__(self, stream)
        Scanner.__init__(self)
        Parser.__init__(self)
        Composer.__init__(self)
        FullConstructor.__init__(self)
        Resolver.__init__(self)

class SafeLoader(Reader, Scanner, Parser, Composer, SafeConstructor, Resolver):

    def __init__(self, stream):
        Reader.__init__(self, stream)
        Scanner.__init__(self)
        Parser.__init__(self)
        Composer.__init__(self)
        SafeConstructor.__init__(self)
        Resolver.__init__(self)

# UnsafeLoader is unsafe on untrusted input. Use should be rare, since
# FullLoader should be able to load almost all YAML safely.
class UnsafeLoader(Reader, Scanner, Parser, Composer, Constructor, Resolver):

    def __init__(self, stream):
        warnings.warn(
            "UnsafeLoader is unsafe and can execute arbitrary code when loading untrusted YAML data. "
            "Use SafeLoader or FullLoader instead.",
            RuntimeWarning, stacklevel=2
        )
        Reader.__init__(self, stream)
        Scanner.__init__(self)
        Parser.__init__(self)
        Composer.__init__(self)
        Constructor.__init__(self)
        Resolver.__init__(self)
