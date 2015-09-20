
__all__ = ['CBaseLoader', 'CSafeLoader', 'CUnsafeLoader', 'CLoader',
        'CBaseDumper', 'CSafeDumper', 'CUnsafeDumper', 'CDumper']

from _yaml import CParser, CEmitter

from .constructor import *
from .representer import *
from .resolver import *
from .serializer import *

from .deprecated import warn_if_instantiated

class CBaseLoader(CParser, BaseConstructor, BaseResolver):

    def __init__(self, stream):
        CParser.__init__(self, stream)
        BaseConstructor.__init__(self)
        BaseResolver.__init__(self)

class CSafeLoader(CParser, SafeConstructor, Resolver):

    def __init__(self, stream):
        CParser.__init__(self, stream)
        SafeConstructor.__init__(self)
        Resolver.__init__(self)

class CUnsafeLoader(CParser, Constructor, Resolver):

    def __init__(self, stream):
        CParser.__init__(self, stream)
        Constructor.__init__(self)
        Resolver.__init__(self)

class CLoader(CUnsafeLoader):

    def __init__(self, stream):
        warn_if_instantiated('CLoader')
        CUnsafeLoader.__init__(self, stream)

class CBaseDumper(CEmitter, BaseRepresenter, BaseResolver):

    def __init__(self, stream,
            default_style=None, default_flow_style=None,
            canonical=None, indent=None, width=None,
            allow_unicode=None, line_break=None,
            encoding=None, explicit_start=None, explicit_end=None,
            version=None, tags=None):
        CEmitter.__init__(self, stream, canonical=canonical,
                indent=indent, width=width, encoding=encoding,
                allow_unicode=allow_unicode, line_break=line_break,
                explicit_start=explicit_start, explicit_end=explicit_end,
                version=version, tags=tags)
        Representer.__init__(self, default_style=default_style,
                default_flow_style=default_flow_style)
        Resolver.__init__(self)

class CSafeDumper(CEmitter, SafeRepresenter, Resolver):

    def __init__(self, stream,
            default_style=None, default_flow_style=None,
            canonical=None, indent=None, width=None,
            allow_unicode=None, line_break=None,
            encoding=None, explicit_start=None, explicit_end=None,
            version=None, tags=None):
        CEmitter.__init__(self, stream, canonical=canonical,
                indent=indent, width=width, encoding=encoding,
                allow_unicode=allow_unicode, line_break=line_break,
                explicit_start=explicit_start, explicit_end=explicit_end,
                version=version, tags=tags)
        SafeRepresenter.__init__(self, default_style=default_style,
                default_flow_style=default_flow_style)
        Resolver.__init__(self)

class CUnsafeDumper(CEmitter, Serializer, Representer, Resolver):

    def __init__(self, stream,
            default_style=None, default_flow_style=None,
            canonical=None, indent=None, width=None,
            allow_unicode=None, line_break=None,
            encoding=None, explicit_start=None, explicit_end=None,
            version=None, tags=None):
        CEmitter.__init__(self, stream, canonical=canonical,
                indent=indent, width=width, encoding=encoding,
                allow_unicode=allow_unicode, line_break=line_break,
                explicit_start=explicit_start, explicit_end=explicit_end,
                version=version, tags=tags)
        Representer.__init__(self, default_style=default_style,
                default_flow_style=default_flow_style)
        Resolver.__init__(self)

class CDumper(CUnsafeDumper):

    def __init__(self, stream,
            default_style=None, default_flow_style=None,
            canonical=None, indent=None, width=None,
            allow_unicode=None, line_break=None,
            encoding=None, explicit_start=None, explicit_end=None,
            version=None, tags=None):
        warn_if_instantiated('CDumper')
        CUnsafeDumper.__init__(self, stream, default_style=default_style,
            default_flow_style=default_flow_style,
            canonical=canonical, indent=indent, width=width,
            allow_unicode=allow_unicode, line_break=line_break,
            encoding=encoding, explicit_start=explicit_start,
            explicit_end=explicit_end, version=version, tags=tags)
