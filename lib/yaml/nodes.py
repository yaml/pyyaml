from typing import Any, List, Tuple

from .error import Mark


class Node(object):
    id: str

    def __init__(
        self,
        tag: str,
        value: Any,
        start_mark: Mark,
        end_mark: Mark,
    ):
        self.tag = tag
        self.value = value
        self.start_mark = start_mark
        self.end_mark = end_mark

    def __repr__(self):
        value = self.value
        # if isinstance(value, list):
        #    if len(value) == 0:
        #        value = '<empty>'
        #    elif len(value) == 1:
        #        value = '<1 item>'
        #    else:
        #        value = '<%d items>' % len(value)
        # else:
        #    if len(value) > 75:
        #        value = repr(value[:70]+u' ... ')
        #    else:
        #        value = repr(value)
        value = repr(value)
        return "%s(tag=%r, value=%s)" % (self.__class__.__name__, self.tag, value)


class ScalarNode(Node):
    id = "scalar"

    def __init__(
        self,
        tag: str,
        value: str,
        start_mark: Mark = None,
        end_mark: Mark = None,
        style=None,
    ):
        self.tag = tag
        self.value = value
        self.start_mark = start_mark
        self.end_mark = end_mark
        self.style = style


class CollectionNode(Node):
    def __init__(
        self,
        tag: str,
        value: Any,
        start_mark: Mark = None,
        end_mark: Mark = None,
        flow_style=None,
    ):
        self.tag = tag
        self.value = value
        self.start_mark = start_mark
        self.end_mark = end_mark
        self.flow_style = flow_style


class SequenceNode(CollectionNode):
    id = "sequence"
    value: List[Node]


class MappingNode(CollectionNode):
    id = "mapping"
    value: List[Tuple[Node, Node]]
