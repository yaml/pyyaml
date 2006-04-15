
__all__ = ['BaseLoader', 'SafeLoader', 'Loader']

from reader import *
from scanner import *
from parser import *
from composer import *
from constructor import *
from detector import *

class BaseLoader(Reader, Scanner, Parser,
        BaseComposer, BaseConstructor, BaseDetector):

    def __init__(self, stream):
        Reader.__init__(self, stream)
        Scanner.__init__(self)
        Parser.__init__(self)
        BaseComposer.__init__(self)
        BaseConstructor.__init__(self)
        BaseDetector.__init__(self)

class SafeLoader(Reader, Scanner, Parser, Composer, SafeConstructor, Detector):

    def __init__(self, stream):
        Reader.__init__(self, stream)
        Scanner.__init__(self)
        Parser.__init__(self)
        Composer.__init__(self)
        SafeConstructor.__init__(self)
        Detector.__init__(self)

class Loader(Reader, Scanner, Parser, Composer, Constructor, Detector):

    def __init__(self, stream):
        Reader.__init__(self, stream)
        Scanner.__init__(self)
        Parser.__init__(self)
        Composer.__init__(self)
        Constructor.__init__(self)
        Detector.__init__(self)

