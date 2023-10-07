
from dataclasses import dataclass, InitVar, field
from enum import Enum
from typing import Any, Collection, Mapping, Sequence


class Tag(Enum):
    """The default tags"""
    # failsafe
    MAPPING = 'tag:yaml.org,2002:map'
    SEQUENCE = 'tag:yaml.org,2002:seq'
    STRING = 'tag:yaml.org,2002:str'
    # jsonschema
    NULL = 'tag:yaml.org,2002:null'

@dataclass(repr=False, frozen=True)
class Node:
    value: Any
    tag: Any
    start_mark: Any | None = None
    end_mark: Any | None = None

    def __repr__(self):
        return 'Node(tag=%r, value=%r)' % (self.tag, self.value)

@dataclass(repr=False, frozen=True)
class ScalarNode(Node):
    tag: str = Tag.STRING.value
    style: Any | None = None

    id = 'scalar'

    def __repr__(self):
        return 'ScalarNode(tag=%r, value=%r)' % (self.tag, self.value)

@dataclass(repr=False, frozen=True)
class StringNode(ScalarNode):
    value: str = ""
    style: Any | None = None

    id = 'scalar'

@dataclass(repr=False, frozen=True)
class CollectionNode(Node):
    value: Collection[Any]
    flow_style: Any | None = None

@dataclass(repr=False, frozen=True)
class SequenceNode(CollectionNode):
    value: Sequence[Any] = field(default_factory=tuple)
    tag: InitVar[str] = Tag.SEQUENCE.value

    def __post_init__(self, *args):
        assert type(self.value) == tuple

    id = 'sequence'

    def __repr__(self):
        return 'SequenceNode(tag=%r, value=%r)' % (self.tag, list(self.value))

    # def __hash__(self):
    #     return hash((super(), list(self.value)))

@dataclass(repr=False, frozen=True)
class MappingNode(CollectionNode):
    value: Mapping[Any, Any] = field(default_factory=dict)
    tag: InitVar[str] = Tag.MAPPING.value

    id = 'mapping'

    def __repr__(self):
        return "MappingNode(tag=%r, value=%r)" % (self.tag, self.value)

@dataclass(repr=False, frozen=True)
class NullNode(ScalarNode):
    value: InitVar[str] = 'null'
    tag: InitVar[str] = Tag.NULL.value
