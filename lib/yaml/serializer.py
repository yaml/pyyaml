
__all__ = ['Serializer', 'SerializerError']

from error import YAMLError
from events import *
from nodes import *

class SerializerError(YAMLError):
    pass

class Serializer:

    ANCHOR_TEMPLATE = u'id%03d'

    def __init__(self, encoding=None,
            explicit_start=None, explicit_end=None, version=None, tags=None):
        self.use_encoding = encoding
        self.use_explicit_start = explicit_start
        self.use_explicit_end = explicit_end
        self.use_version = version
        self.use_tags = tags
        self.serialized_nodes = {}
        self.anchors = {}
        self.last_anchor_id = 0
        self.closed = None

    def open(self):
        if self.closed is None:
            self.emit(StreamStartEvent(encoding=self.use_encoding))
            self.closed = False
        elif self.closed:
            raise SerializerError("serializer is closed")
        else:
            raise SerializerError("serializer is already opened")

    def close(self):
        if self.closed is None:
            raise SerializerError("serializer is not opened")
        elif not self.closed:
            self.emit(StreamEndEvent())
            self.closed = True

    #def __del__(self):
    #    self.close()

    def serialize(self, node):
        if self.closed is None:
            raise SerializerError("serializer is not opened")
        elif self.closed:
            raise SerializerError("serializer is closed")
        self.emit(DocumentStartEvent(explicit=self.use_explicit_start,
            version=self.use_version, tags=self.use_tags))
        self.anchor_node(node)
        self.serialize_node(node)
        self.emit(DocumentEndEvent(explicit=self.use_explicit_end))
        self.serialized_nodes = {}
        self.anchors = {}
        self.last_alias_id = 0

    def anchor_node(self, node):
        if node in self.anchors:
            if self.anchors[node] is None:
                self.anchors[node] = self.generate_anchor(node)
        else:
            self.anchors[node] = None
            if isinstance(node, SequenceNode):
                for item in node.value:
                    self.anchor_node(item)
            elif isinstance(node, MappingNode):
                for key in node.value:
                    self.anchor_node(key)
                    self.anchor_node(node.value[key])

    def generate_anchor(self, node):
        self.last_anchor_id += 1
        return self.ANCHOR_TEMPLATE % self.last_anchor_id

    def serialize_node(self, node):
        alias = self.anchors[node]
        if node in self.serialized_nodes:
            self.emit(AliasEvent(alias))
        else:
            self.serialized_nodes[node] = True
            if isinstance(node, ScalarNode):
                detected_tag = self.detect(node.value)
                implicit = (node.tag == self.detect(node.value)
                        or (node.tag == self.DEFAULT_SCALAR_TAG
                            and detected_tag is None))
                self.emit(ScalarEvent(alias, node.tag, implicit, node.value,
                    style=node.style))
            elif isinstance(node, SequenceNode):
                # TODO:
                # 1) Check the current path in the Resolver.
                # 2) Add the implicit flag to the SequenceStartEvent and
                # MappingStartEvent.
                tag = node.tag
                if tag == self.DEFAULT_SEQUENCE_TAG and not self.canonical:
                    tag = None
                self.emit(SequenceStartEvent(alias, tag,
                    flow_style=node.flow_style))
                for item in node.value:
                    self.serialize_node(item)
                self.emit(SequenceEndEvent())
            elif isinstance(node, MappingNode):
                tag = node.tag
                if tag == self.DEFAULT_MAPPING_TAG and not self.canonical:
                    tag = None
                self.emit(MappingStartEvent(alias, tag,
                    flow_style=node.flow_style))
                if hasattr(node.value, 'keys'):
                    for key in node.value.keys():
                        self.serialize_node(key)
                        self.serialize_node(node.value[key])
                else:
                    for key, value in node.value:
                        self.serialize_node(key)
                        self.serialize_node(value)
                self.emit(MappingEndEvent())

