from __future__ import annotations

import typing as t

from functools import partialmethod
from .tagset import TagSet

T = t.TypeVar('T')


class LoaderConfigMixin:
    @classmethod
    # FIXME: fix tagset type to use DataClasses, at least externally?
    def config(cls: type[T], type_name: str | None = None, tagset: TagSet | ... = ..., **kwargs) -> type[T]:
        if not type_name:
            # FIXME: hash the inputs for a dynamic type name and cache it?
            type_name = f'abcd_from_{cls.__name__}'

        new_type = t.cast(cls, type(type_name, (cls, ), {}))

        # FIXME: add support for arbitrary kwargs passthru ala dumper?

        if tagset is not ...:
            # FIXME: provide a base class hook/method for this reset
            new_type.yaml_implicit_resolvers = {}
            new_type.init_resolvers(tagset.resolvers)
            new_type.yaml_constructors = {}
            new_type.init_constructors(tagset.constructors)

        return new_type


class DumperConfigMixin:
    @classmethod
    def config(cls: type[T], type_name: str | None = None,
               tagset: TagSet | ... = ...,
               # FIXME: make some of the more obscure style things "nicer" (eg enums?) or just pass through existing values?
               default_style: str | ... = ..., default_flow_style: bool | ... = ...,
               # FIXME: properly type-annotate the rest of these
               canonical=..., indent=..., width=...,
               allow_unicode=..., line_break=...,
               encoding=..., explicit_start=..., explicit_end=...,
               version=..., tags=..., sort_keys=...,
               **kwargs) -> type[T]:

        if not type_name:
            # FIXME: hash the inputs for a dynamic type name and cache it?
            type_name = f'abcd_from_{cls.__name__}'

        # preserve wrapped config defaults for values where we didn't get a default
        # FIXME: share this code with the one in __init__.dump_all (and implement on others)
        dumper_init_kwargs = dict(
            default_style=default_style,
            default_flow_style=default_flow_style,
            canonical=canonical, indent=indent, width=width,
            allow_unicode=allow_unicode, line_break=line_break,
            encoding=encoding, version=version, tags=tags,
            explicit_start=explicit_start, explicit_end=explicit_end, sort_keys=sort_keys, **kwargs)

        dumper_init_kwargs = {k: v for k, v in dumper_init_kwargs.items() if v is not ...}

        patched_init = partialmethod(cls.__init__,
                                     **dumper_init_kwargs)

        new_type = t.cast(cls, type(type_name, (cls, ), {'__init__': patched_init}))

        # FIXME: support all the dynamic dispatch types (multi*, etc)
        if tagset is not ...:
            # FIXME: provide a base class hook/method for this reset
            new_type.yaml_implicit_resolvers = {}
            new_type.init_resolvers(tagset.resolvers)
            new_type.yaml_representers = {}
            new_type.init_representers(tagset.representers)

        return new_type
