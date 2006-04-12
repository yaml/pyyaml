
__all__ = ['Serializer', 'SerializerError']

from error import YAMLError
from events import *
from nodes import *

class SerializerError(YAMLError):
    pass

class Serializer:

    ANCHOR_TEMPLATE = u'id%03d'

    def __init__(self, emitter, encoding=None, line_break=None, canonical=None,
            indent=None, width=None, allow_unicode=None):
        self.emitter = emitter
        self.serialized_nodes = {}
        self.anchors = {}
        self.last_anchor_id = 0
        self.closed = None
        self.open(encoding, line_break, canonical, indent, width, allow_unicode)

    def open(self, encoding=None, line_break=None, canonical=None,
            indent=None, width=None, allow_unicode=None):
        if self.closed is None:
            self.emitter.emit(StreamStartEvent(encoding=encoding,
                line_break=line_break, canonical=canonical,
                indent=indent, width=width, allow_unicode=allow_unicode))
            self.closed = False
        elif self.closed:
            raise SerializerError("serializer is closed")
        else:
            raise SerializerError("serializer is already opened")

    def close(self):
        if self.closed is None:
            raise SerializerError("serializer is not opened")
        elif not self.closed:
            self.emitter.emit(StreamEndEvent())
            self.closed = True

    def __del__(self):
        self.close()

    def serialize(self, node, explicit_start=None, explicit_end=None,
            version=None, tags=None):
        if self.closed is None:
            raise SerializerError("serializer is not opened")
        elif self.closed:
            raise SerializerError("serializer is closed")
        self.emitter.emit(DocumentStartEvent(explicit=explicit_start,
            version=version, tags=tags))
        self.anchor_node(node)
        self.serialize_node(node)
        self.emitter.emit(DocumentEndEvent(explicit=explicit_end))
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
            self.emitter.emit(AliasEvent(alias))
        else:
            self.serialized_nodes[node] = True
            if isinstance(node, ScalarNode):
                self.emitter.emit(ScalarEvent(alias, node.tag, node.value,
                    implicit=node.implicit, style=node.style))
            elif isinstance(node, SequenceNode):
                self.emitter.emit(SequenceStartEvent(alias, node.tag,
                    flow_style=node.flow_style))
                for item in node.value:
                    self.serialize_node(item)
                self.emitter.emit(SequenceEndEvent())
            elif isinstance(node, MappingNode):
                self.emitter.emit(MappingStartEvent(alias, node.tag,
                    flow_style=node.flow_style))
                for key in node.value:
                    self.serialize_node(key)
                    self.serialize_node(node.value[key])
                self.emitter.emit(MappingEndEvent())

