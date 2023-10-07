
from dataclasses import dataclass, InitVar
from typing import Any


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
    style: Any | None = None

    id = 'scalar'

    def __repr__(self):
        return 'ScalarNode(tag=%r, value=%r)' % (self.tag, self.value)

@dataclass(repr=False)
class CollectionNode(Node):
    flow_style: Any | None = None

@dataclass(repr=False)
class SequenceNode(CollectionNode):
    tag: InitVar[str] = 'tag:yaml.org,2002:seq'

    id = 'sequence'

    def __repr__(self):
        return 'SequenceNode(tag=%r, value=%r)' % (self.tag, self.value)

@dataclass(repr=False)
class MappingNode(CollectionNode):
    tag: InitVar[str] = 'tag:yaml.org,2002:map'

    id = 'mapping'

    def __repr__(self):
        return 'MappingNode(tag=%r, value=%r)' % (self.tag, self.value)

@dataclass(repr=False)
class NullNode(ScalarNode):
    value: InitVar[str] = 'null'
    tag: InitVar[str] = 'tag:yaml.org,2002:null'
