
__all__ = ['BaseLoader', 'SafeLoader', 'UnsafeLoader', 'Loader']

from reader import *
from scanner import *
from parser import *
from composer import *
from constructor import *
from resolver import *

from deprecation import warn_if_instantiated

class BaseLoader(Reader, Scanner, Parser, Composer, BaseConstructor, BaseResolver):

    def __init__(self, stream):
        Reader.__init__(self, stream)
        Scanner.__init__(self)
        Parser.__init__(self)
        Composer.__init__(self)
        BaseConstructor.__init__(self)
        BaseResolver.__init__(self)

class SafeLoader(Reader, Scanner, Parser, Composer, SafeConstructor, Resolver):

    def __init__(self, stream):
        Reader.__init__(self, stream)
        Scanner.__init__(self)
        Parser.__init__(self)
        Composer.__init__(self)
        SafeConstructor.__init__(self)
        Resolver.__init__(self)

class UnsafeLoader(Reader, Scanner, Parser, Composer, Constructor, Resolver):

    def __init__(self, stream):
        Reader.__init__(self, stream)
        Scanner.__init__(self)
        Parser.__init__(self)
        Composer.__init__(self)
        Constructor.__init__(self)
        Resolver.__init__(self)

class Loader(UnsafeLoader):

    def __init__(self, stream):
        warn_if_instantiated('Loader')
        UnsafeLoader.__init__(self, stream)
