
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
        self.indents = []
        self.indent = None
        self.flow_level = 0
        self.key_context = False
        self.space = True
        self.line = True
        self.allow_inline_collection = False
        self.allow_indentless_sequence = False
        self.simple_key = False
        self.event_queue = []

    def emit(self, event):
        if self.event_queue:
            self.event_queue.append(event)
            event = self.event_queue.pop(0)
        self.state(event)

    def push_back(self, event):
        self.event_queue.insert(0, event)

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
            self.allow_inline_collection = False
            self.allow_indentless_sequence = False
        elif isinstance(event, StreamEndEvent):
            self.writer.flush()
            self.state = self.expect_nothing
        else:
            raise EmitterError("expected DocumentStartEvent, but got %s" % event.__class__.__name__)

    def expect_document_end(self, event):
        if isinstance(event, DocumentEndEvent):
            self.write_document_end()
            self.state = self.expect_document_start
            self.allow_inline_collection = False
            self.allow_indentless_sequence = False
        else:
            raiseEmitterError("expected DocumentEndEvent, but got %s" % event.__class__.__name__)

    def expect_root_node(self, event):
        self.expect_node(event)

    def expect_node(self, event):
        empty = None
        if isinstance(event, (SequenceEvent, MappingEvent)):
            if not self.event_queue:
                return self.push_back(event)
            empty = isinstance(self.event_queue[0], CollectionEndEvent)
        if isinstance(event, AliasEvent):
            self.expect_alias(event)
        elif isinstance(event, (ScalarEvent, SequenceEvent, MappingEvent)):
            if event.anchor:
                self.write_anchor("&", event.anchor)
                self.allow_inline_collection = False
            if event.tag not in [None, u'!']:
                self.write_tag(event.tag)
                self.allow_inline_collection = False
            if isinstance(event, ScalarEvent):
                self.expect_scalar(event)
            elif isinstance(event, SequenceEvent):
                self.expect_sequence(event, empty)
            elif isinstance(event, MappingEvent):
                self.expect_mapping(event, empty)
        else:
            raise EmitterError("Expected NodeEvent, but got %s" % event.__class__.__name__)

    def expect_alias(self, event):
        self.write_anchor("*", event.anchor)
        self.state = self.states.pop()

    def expect_scalar(self, event):
        self.indents.append(self.indent)
        if self.indent is None:
            self.indent = 2
        else:
            self.indent += 2
        self.write_scalar(event.value, event.implicit, event.style)
        self.indent = self.indents.pop()
        self.state = self.states.pop()
        self.allow_inline_collection = False
        self.allow_indentless_sequence = False

    def expect_sequence(self, event, empty):
        if self.flow_level or event.flow or empty:
            self.write_indicator("[", need_space=True, provide_space=True)
            self.flow_level += 1
            self.indents.append(self.indent)
            if self.indent is None:
                self.indent = 2
            else:
                self.indent += 2
            self.state = self.expect_first_flow_sequence_item
        else:
            self.indents.append(self.indent)
            if self.indent is None:
                self.indent = 0
            else:
                self.indent += 2
            self.state = self.expect_first_block_sequence_item

    def expect_mapping(self, event, empty):
        if self.flow_level or event.flow or empty:
            self.write_indicator("{", need_space=True, provide_space=True)
            self.flow_level += 1
            self.indents.append(self.indent)
            if self.indent is None:
                self.indent = 2
            else:
                self.indent += 2
            self.state = self.expect_first_flow_mapping_key
        else:
            self.indents.append(self.indent)
            if self.indent is None:
                self.indent = 0
            else:
                self.indent += 2
            self.state = self.expect_first_block_mapping_key

    def expect_first_flow_sequence_item(self, event):
        if isinstance(event, CollectionEndEvent):
            self.indent = self.indents.pop()
            self.write_indicator("]", provide_space=True)
            self.flow_level -= 1
            self.state = self.states.pop()
        else:
            self.write_indent()
            self.states.append(self.expect_flow_sequence_item)
            self.state = self.expect_node
            self.expect_node(event)

    def expect_flow_sequence_item(self, event):
        if isinstance(event, CollectionEndEvent):
            self.write_indicator(",")
            self.indent = self.indents.pop()
            self.write_indent()
            self.write_indicator("]")
            self.flow_level -= 1
            self.state = self.states.pop()
        else:
            self.write_indicator(",")
            self.write_indent()
            self.states.append(self.expect_flow_sequence_item)
            self.state = self.expect_node
            self.expect_node(event)

    def expect_first_block_sequence_item(self, event):
        assert not isinstance(event, CollectionEndEvent)
        if not self.allow_inline_collection:
            if self.allow_indentless_sequence:
                self.indent = self.indents.pop()
                self.indents.append(self.indent)
            self.write_indent()
        self.write_indicator("-", need_space=True)
        self.allow_indentless_sequence = False
        self.allow_inline_collection = True
        self.states.append(self.expect_block_sequence_item)
        self.state = self.expect_node
        self.expect_node(event)

    def expect_block_sequence_item(self, event):
        if isinstance(event, CollectionEndEvent):
            self.indent = self.indents.pop()
            self.state = self.states.pop()
        else:
            self.write_indent()
            self.write_indicator("-", need_space=True)
            self.allow_indentless_sequence = False
            self.allow_inline_collection = True
            self.states.append(self.expect_block_sequence_item)
            self.state = self.expect_node
            self.expect_node(event)

    def expect_first_flow_mapping_key(self, event):
        if isinstance(event, CollectionEndEvent):
            self.indent = self.indents.pop()
            self.write_indicator("}")
            self.flow_level -= 1
            self.state = self.states.pop()
        else:
            self.write_indent()
            if self.is_simple(event):
                self.simple_key = True
            else:
                self.write_indicator("?", need_space=True)
            self.states.append(self.expect_flow_mapping_value)
            self.state = self.expect_node
            self.expect_node(event)

    def expect_flow_mapping_key(self, event):
        if isinstance(event, CollectionEndEvent):
            self.indent = self.indents.pop()
            self.write_indent()
            self.write_indicator("}")
            self.flow_level -= 1
            self.state = self.states.pop()
        else:
            self.write_indicator(",")
            self.write_indent()
            if self.is_simple(event):
                self.simple_key = True
            else:
                self.write_indicator("?", need_space=True)
            self.states.append(self.expect_flow_mapping_value)
            self.state = self.expect_node
            self.expect_node(event)

    def expect_flow_mapping_value(self, event):
        if self.simple_key:
            self.write_indicator(":", need_space=False)
            self.simple_key = False
        else:
            self.write_indent()
            self.write_indicator(":", need_space=True)
        self.states.append(self.expect_flow_mapping_key)
        self.state = self.expect_node
        self.expect_node(event)

    def expect_first_block_mapping_key(self, event):
        assert not isinstance(event, CollectionEndEvent)
        simple = self.is_simple(event)
        if simple is None:
            return self.push_back(event)
        if not self.allow_inline_collection:
            self.write_indent()
        if self.is_simple(event):
            self.allow_indentless_sequence = True
            self.allow_inline_collection = False
            self.simple_key = True
        else:
            self.write_indicator("?", need_space=True)
            self.allow_indentless_sequence = True
            self.allow_inline_collection = True
        self.states.append(self.expect_block_mapping_value)
        self.state = self.expect_node
        self.expect_node(event)

    def expect_block_mapping_key(self, event):
        if isinstance(event, CollectionEndEvent):
            self.indent = self.indents.pop()
            self.state = self.states.pop()
        else:
            self.write_indent()
            if self.is_simple(event):
                self.allow_indentless_sequence = True
                self.allow_inline_collection = False
                self.simple_key = True
            else:
                self.write_indicator("?", need_space=True)
                self.allow_indentless_sequence = True
                self.allow_inline_collection = True
            self.states.append(self.expect_block_mapping_value)
            self.state = self.expect_node
            self.expect_node(event)

    def expect_block_mapping_value(self, event):
        if self.simple_key:
            self.write_indicator(":", need_space=False)
            self.allow_indentless_sequence = True
            self.allow_inline_collection = False
            self.simple_key = False
        else:
            self.write_indent()
            self.write_indicator(":", need_space=True)
            self.allow_indentless_sequence = True
            self.allow_inline_collection = True
        self.states.append(self.expect_block_mapping_key)
        self.state = self.expect_node
        self.expect_node(event)

    def expect_nothing(self, event):
        raise EmitterError("expected nothing, but got %s" % event.__class__.__name__)

    def write_document_start(self):
        self.writer.write("%YAML 1.1")
        self.write_line_break()
        self.writer.write("---")
        self.space = False
        self.line = False

    def write_document_end(self):
        if not self.line:
            self.write_line_break()
        self.writer.write("...")
        self.write_line_break()

    def write_line_break(self):
        self.writer.write('\n')
        self.space = True
        self.line = True

    def write_anchor(self, indicator, name):
        if not self.space:
            self.writer.write(" ")
        self.writer.write("%s%s" % (indicator, name))
        self.space = False
        self.line = False

    def write_tag(self, tag):
        if not self.space:
            self.writer.write(" ")
        if tag.startswith("tag:yaml.org,2002:"):
            self.writer.write("!!%s" % tag[len("tag.yaml.org,2002:"):])
        else:
            self.writer.write("!<%s>" % tag)
        self.space = False
        self.line = False

    def is_simple(self, event):
        if not isinstance(event, ScalarEvent):
            return False
        if '\n' in event.value or len(event.value) > 128:
            return False
        if event.style and event.style in '|>':
            return False
        return True

    def write_scalar(self, value, implicit, style):
        if implicit:
            if not self.space:
                self.writer.write(" ")
            self.writer.write(value.encode('utf-8'))
            self.space = False
            self.line = False
        elif style in ['>', '|'] and not self.flow_level and not self.simple_key:
            if not self.space:
                self.writer.write(" ")
            self.writer.write("|-")
            self.write_line_break()
            self.write_indent()
            self.writer.write(value.encode('utf-8'))
            self.write_line_break()
        else:
            if not self.space:
                self.writer.write(" ")
            self.writer.write("\"%s\"" % value.encode('utf-8'))
            self.space = False
            self.line = False

    def write_indicator(self, indicator, need_space=False, provide_space=False):
        if need_space and not self.space:
            self.writer.write(" ")
        self.writer.write(indicator)
        self.space = provide_space
        self.line = False

    def write_indent(self):
        if not self.line:
            self.write_line_break()
        if self.indent:
            self.writer.write(" "*self.indent)
            self.line = False
        self.space = True

