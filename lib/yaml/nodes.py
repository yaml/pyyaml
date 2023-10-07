
from dataclasses import dataclass, InitVar
from enum import Enum
from typing import Any


class Tag(Enum):
    """The default tags"""
    # failsafe
    MAPPING = 'tag:yaml.org,2002:map'
    SEQUENCE = 'tag:yaml.org,2002:seq'
    SCALAR = 'tag:yaml.org,2002:str'
    # jsonschema
    NULL = 'tag:yaml.org,2002:null'

@dataclass(repr=False)
class Node:
    value: Any
    tag: Any
    start_mark: Any | None = None
    end_mark: Any | None = None

    def __repr__(self):
        return 'Node(tag=%r, value=%r)' % (self.tag, self.value)

@dataclass(repr=False)
class ScalarNode(Node):
    tag: str = Tag.SCALAR
    style: Any | None = None

    id = 'scalar'

    def __repr__(self):
        return 'ScalarNode(tag=%r, value=%r)' % (self.tag, self.value)

@dataclass(repr=False)
class CollectionNode(Node):
    flow_style: Any | None = None

@dataclass(repr=False)
class SequenceNode(CollectionNode):
    tag: InitVar[str] = Tag.SEQUENCE.value

    id = 'sequence'

    def __repr__(self):
        return 'SequenceNode(tag=%r, value=%r)' % (self.tag, self.value)

@dataclass(repr=False)
class MappingNode(CollectionNode):
    tag: InitVar[str] = Tag.MAPPING.value

    id = 'mapping'

    def __repr__(self):
        return 'MappingNode(tag=%r, value=%r)' % (self.tag, self.value)

@dataclass(repr=False)
class NullNode(ScalarNode):
    value: InitVar[str] = 'null'
    tag: InitVar[str] = Tag.NULL.value
