__all__ = ["BaseDumper", "SafeDumper", "Dumper"]

from abc import ABC, abstractproperty
from typing import Literal, Optional, Type, Union
from .emitter import *
from .serializer import *
from .representer import *
from .resolver import *

from .types import _Stream


class DumperABC(ABC, Emitter, Serializer, BaseResolver, BaseRepresenter):
    def __init__(
        self,
        stream: _Stream,
        default_style=None,
        default_flow_style: Optional[bool] = False,
        canonical: bool = None,
        indent: int = None,
        width: int = None,
        allow_unicode: bool = None,
        line_break: Union[Literal["\r"], Literal["\n"], Literal["\r\n"], None] = None,
        encoding: str = None,
        explicit_start=None,
        explicit_end=None,
        version=None,
        tags=None,
        sort_keys=True,
    ) -> None:
        Emitter.__init__(
            self,
            stream,
            canonical=canonical,
            indent=indent,
            width=width,
            allow_unicode=allow_unicode,
            line_break=line_break,
        )
        Serializer.__init__(
            self,
            encoding=encoding,
            explicit_start=explicit_start,
            explicit_end=explicit_end,
            version=version,
            tags=tags,
        )
        self._representer.__init__(
            self,
            default_style=default_style,
            default_flow_style=default_flow_style,
            sort_keys=sort_keys,
        )
        self._resolver.__init__(self)

    @abstractproperty
    def _resolver(self) -> Type[BaseResolver]:
        """Resolver Class to use"""

    @abstractproperty
    def _representer(self) -> Type[BaseRepresenter]:
        """Representer Class to use"""


class BaseDumper(DumperABC):

    _resolver = BaseResolver
    _representer = BaseRepresenter


class SafeDumper(DumperABC):

    _resolver = Resolver
    _representer = SafeRepresenter


class Dumper(DumperABC):

    _resolver = Resolver
    _representer = Representer
