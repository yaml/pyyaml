import re
import typing as t

from dataclasses import dataclass
# FIXME: disentangle various class inits so we can define these all together
from .constructor import _core_constructors, _json_constructors, _yaml11_constructors
from .representer import _representers  # FIXME make consistent
from .resolver import _core_resolvers, _json_resolvers, _yaml11_resolvers

# FIXME: restructure these as dataclasses for each type that are individually accessible to make it easier to build up a custom tag set with well-known types

# FIXME: add Python tags here as well

@dataclass
class TagSet:
    name: str
    constructors: dict[str, t.Callable]  # FIXME: implement constructor dataclass?
    representers: dict[str, t.Callable]  # FIXME: implement representer dataclass?
    resolvers: list[list]  # FIXME: implement ImplicitResolver dataclass
    # FIXME: add support for multi/implicit constructors, representers, resolvers, etc?


yaml11 = TagSet(name='yaml11',
                constructors=_yaml11_constructors,
                representers=_representers['yaml11'],
                resolvers=_yaml11_resolvers)

core = TagSet(name='core',
              constructors=_core_constructors,
              representers=_representers['core'],
              resolvers=_core_resolvers)

json = TagSet(name='json',
              constructors=_json_constructors,
              representers=_representers['json'],
              resolvers=_json_resolvers)

