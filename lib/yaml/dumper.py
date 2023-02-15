
__all__ = ['BaseDumper', 'SafeDumper', 'Dumper', 'CommonDumper', 'FastestBaseDumper']

from . import tagset

from .config import DumperConfigMixin
from .emitter import *
from .serializer import *
from .representer import *
from .resolver import *

try:
    from .cyaml import CDumper as FastestBaseDumper
except ImportError as ie:
    FastestBaseDumper = None


class BaseDumper(Emitter, Serializer, BaseRepresenter, BaseResolver, DumperConfigMixin):

    def __init__(self, stream,
            default_style=None, default_flow_style=False,
            canonical=None, indent=None, width=None,
            allow_unicode=None, line_break=None,
            encoding=None, explicit_start=None, explicit_end=None,
            version=None, tags=None, sort_keys=True):
        Emitter.__init__(self, stream, canonical=canonical,
                indent=indent, width=width,
                allow_unicode=allow_unicode, line_break=line_break)
        Serializer.__init__(self, encoding=encoding,
                explicit_start=explicit_start, explicit_end=explicit_end,
                version=version, tags=tags)
        Representer.__init__(self, default_style=default_style,
                default_flow_style=default_flow_style, sort_keys=sort_keys)
        Resolver.__init__(self)


if not FastestBaseDumper:
    # fall back to pure-Python if CBaseDumper is unavailable
    FastestBaseDumper = BaseDumper

# FIXME: reimplement all these as config calls, eg:
# SafeDumper = FastestBaseDumper.config(type_name='SafeDumper', tagset=tagset.yaml11)



class SafeDumper(Emitter, Serializer, SafeRepresenter, Resolver, DumperConfigMixin):

    def __init__(self, stream,
            default_style=None, default_flow_style=False,
            canonical=None, indent=None, width=None,
            allow_unicode=None, line_break=None,
            encoding=None, explicit_start=None, explicit_end=None,
            version=None, tags=None, sort_keys=True):
        Emitter.__init__(self, stream, canonical=canonical,
                indent=indent, width=width,
                allow_unicode=allow_unicode, line_break=line_break)
        Serializer.__init__(self, encoding=encoding,
                explicit_start=explicit_start, explicit_end=explicit_end,
                version=version, tags=tags)
        SafeRepresenter.__init__(self, default_style=default_style,
                default_flow_style=default_flow_style, sort_keys=sort_keys)
        Resolver.__init__(self)

class CommonDumper(Emitter, Serializer, CommonRepresenter, BaseResolver, DumperConfigMixin):

    def __init__(self, stream,
            default_style=None, default_flow_style=False,
            canonical=None, indent=None, width=None,
            allow_unicode=None, line_break=None,
            encoding=None, explicit_start=None, explicit_end=None,
            version=None, tags=None, sort_keys=True):
        Emitter.__init__(self, stream, canonical=canonical,
                indent=indent, width=width,
                allow_unicode=allow_unicode, line_break=line_break)
        Serializer.__init__(self, encoding=encoding,
                explicit_start=explicit_start, explicit_end=explicit_end,
                version=version, tags=tags)
        CommonRepresenter.__init__(self, default_style=default_style,
                default_flow_style=default_flow_style, sort_keys=sort_keys)
        BaseResolver.__init__(self)

    @classmethod
    def init_tags(cls, tagset: tagset.TagSet):
        cls.init_representers(tagset.representers)
        cls.init_resolvers(tagset.resolvers)


class Dumper(Emitter, Serializer, Representer, Resolver, DumperConfigMixin):

    def __init__(self, stream,
            default_style=None, default_flow_style=False,
            canonical=None, indent=None, width=None,
            allow_unicode=None, line_break=None,
            encoding=None, explicit_start=None, explicit_end=None,
            version=None, tags=None, sort_keys=True):
        Emitter.__init__(self, stream, canonical=canonical,
                indent=indent, width=width,
                allow_unicode=allow_unicode, line_break=line_break)
        Serializer.__init__(self, encoding=encoding,
                explicit_start=explicit_start, explicit_end=explicit_end,
                version=version, tags=tags)
        Representer.__init__(self, default_style=default_style,
                default_flow_style=default_flow_style, sort_keys=sort_keys)
        Resolver.__init__(self)


_12_CoreDumper = CommonDumper.config(type_name='_12_CoreDumper', tagset=tagset.core)
_12_JSONDumper = CommonDumper.config(type_name='_12_JSONDumper', tagset=tagset.json)


