
# Events should obey the following grammar:
# stream ::= STREAM-START document* STREAM-END
# document ::= DOCUMENT-START node DOCUMENT-END
# node ::= SCALAR | sequence | mapping
# sequence ::= SEQUENCE-START node* SEQUENCE-END
# mapping ::= MAPPING-START (node node)* MAPPING-END

__all__ = ['Emitter', 'EmitterError']

from error import YAMLError
from events import *

class EmitterError(YAMLError):
    pass

class Emitter:

    def __init__(self, writer):
        self.writer = writer
        self.states = []
        self.state = self.expect_stream_start
        self.levels = []
        self.level = 0
        self.soft_space = False

    def emit(self, event):
        self.state(event)

    def expect_stream_start(self, event):
        if isinstance(event, StreamStartEvent):
            self.state = self.expect_document_start
        else:
            raise EmitterError("expected StreamStartEvent, but got %s" % event.__class__.__name__)

    def expect_document_start(self, event):
        if isinstance(event, DocumentStartEvent):
            self.write_document_start()
            self.states.append(self.expect_document_end)
            self.state = self.expect_root_node
        elif isinstance(event, StreamEndEvent):
            self.writer.flush()
            self.state = self.expect_nothing
        else:
            raise EmitterError("expected DocumentStartEvent, but got %s" % event.__class__.__name__)

    def expect_document_end(self, event):
        if isinstance(event, DocumentEndEvent):
            self.write_document_end()
            self.state = self.expect_document_start
        else:
            raiseEmitterError("expected DocumentEndEvent, but got %s" % event.__class__.__name__)

    def expect_root_node(self, event):
        self.expect_node(event)

    def expect_node(self, event):
        if isinstance(event, AliasEvent):
            self.write_anchor("*", event.anchor)
            self.state = self.states.pop()
        elif isinstance(event, NodeEvent):
            if event.anchor:
                self.write_anchor("&", event.anchor)
            if event.tag:
                self.write_tag(event.tag)
            if isinstance(event, ScalarEvent):
                self.write_scalar(event.value)
                self.state = self.states.pop()
            elif isinstance(event, SequenceEvent):
                self.write_collection_start("[")
                self.level += 1
                self.state = self.expect_first_sequence_item
            elif isinstance(event, MappingEvent):
                self.write_collection_start("{")
                self.level += 1
                self.state = self.expect_first_mapping_key
        else:
            raise EmitterError("Expected NodeEvent, but got %s" % event.__class__.__name__)

    def expect_first_sequence_item(self, event):
        if isinstance(event, CollectionEndEvent):
            self.write_collection_end("]")
            self.state = self.states.pop()
        else:
            self.write_indent()
            self.states.append(self.expect_sequence_item)
            self.expect_node(event)

    def expect_sequence_item(self, event):
        if isinstance(event, CollectionEndEvent):
            self.level -= 1
            self.write_indent()
            self.write_collection_end("]")
            self.state = self.states.pop()
        else:
            self.write_indicator(",")
            self.write_indent()
            self.states.append(self.expect_sequence_item)
            self.expect_node(event)
        
    def expect_first_mapping_key(self, event):
        if isinstance(event, CollectionEndEvent):
            self.write_collection_end("}")
            self.state = self.states.pop()
        else:
            self.write_indent()
            self.write_indicator("?")
            self.states.append(self.expect_mapping_value)
            self.expect_node(event)

    def expect_mapping_key(self, event):
        if isinstance(event, CollectionEndEvent):
            self.level -= 1
            self.write_indent()
            self.write_collection_end("}")
            self.state = self.states.pop()
        else:
            self.write_indicator(",")
            self.write_indent()
            self.write_indicator("?")
            self.states.append(self.expect_mapping_value)
            self.expect_node(event)

    def expect_mapping_value(self, event):
        self.write_indent()
        self.write_indicator(":")
        self.states.append(self.expect_mapping_key)
        self.expect_node(event)

    def expect_nothing(self, event):
        raise EmitterError("expected nothing, but got %s" % event.__class__.__name__)

    def write_document_start(self):
        self.writer.write("%YAML 1.1\n")
        self.writer.write("---")
        self.soft_space = True

    def write_document_end(self):
        self.writer.write("\n...\n")
        self.soft_space = False

    def write_collection_start(self, indicator):
        if self.soft_space:
            self.writer.write(" ")
        self.writer.write(indicator)
        self.soft_space = False

    def write_collection_end(self, indicator):
        self.writer.write(indicator)
        self.soft_space = True

    def write_anchor(self, indicator, name):
        if self.soft_space:
            self.writer.write(" ")
        self.writer.write("%s%s" % (indicator, name))
        self.soft_space = True

    def write_tag(self, tag):
        if self.soft_space:
            self.writer.write(" ")
        if tag.startswith("tag:yaml.org,2002:"):
            self.writer.write("!!%s" % tag[len("tag.yaml.org,2002:"):])
        else:
            self.writer.write("!<%s>" % tag)
        self.soft_space = True

    def write_scalar(self, value):
        if self.soft_space:
            self.writer.write(" ")
        self.writer.write("\"%s\"" % value.encode('utf-8'))
        self.soft_space = True

    def write_indicator(self, indicator):
        self.writer.write(indicator)
        self.soft_space = True

    def write_indent(self):
        self.writer.write("\n"+" "*(self.level*4))
        self.soft_space = False

