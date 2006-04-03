
# Emitter expects events obeying the following grammar:
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

    DEFAULT_TAG_PREFIXES = {
        u'!' : u'!',
        u'tag:yaml.org,2002:' : u'!!',
    }

    def __init__(self, writer):

        # The writer should have the methods `write` and possibly `flush`.
        self.writer = writer

        # Encoding is provided by STREAM-START.
        self.encoding = None

        # Emitter is a state machine with a stack of states to handle nested
        # structures.
        self.states = []
        self.state = self.expect_stream_start

        # Current event and the event queue.
        self.events = []
        self.event = None

        # The current indentation level and the stack of previous indents.
        self.indents = []
        self.indent = None

        # Flow level.
        self.flow_level = 0

        # Contexts.
        self.root_context = False
        self.sequence_context = False
        self.mapping_context = False
        self.simple_key_context = False

        # Characteristics of the last emitted character:
        #  - current position.
        #  - is it a line break?
        #  - is it a whitespace?
        #  - is it an indention character
        #    (indentation space, '-', '?', or ':')?
        self.line = 0
        self.column = 0
        self.whitespace = True
        self.indention = True

        # Formatting details.
        self.canonical = False
        self.best_line_break = u'\n'
        self.best_indent = 2
        self.best_width = 80
        self.tag_prefixes = None

        # Scalar analysis.
        self.analysis = None

    def emit(self, event):
        if self.events:
            self.events.append(event)
            event = self.events.pop(0)
        self.event = event
        if self.need_more_events():
            self.event.insert(0, event)
            return
        self.state()
        self.event = None

    # In some cases, we wait for a few next events before emitting.

    def need_more_events(self):
        if isinstance(self.event, DocumentStartEvent):
            return self.need_events(1)
        elif isinstance(self.event, SequenceStartEvent):
            return self.need_events(2)
        elif isinstance(self.event, MappingStartEvent):
            return self.need_events(3)
        else:
            return False

    def need_events(self, count):
        level = 0
        for event in self.events:
            if isinstance(event, (DocumentStart, CollectionStart)):
                level += 1
            elif isinstance(event, (DocumentEnd, CollectionEnd)):
                level -= 1
            elif isinstance(event, StreamEnd):
                level = -1
            if level < 0:
                return False
        return (len(self.events) < count)

    def increase_indent(self, flow=False, indentless=False):
        self.indents.append(self.indent)
        if self.indent is None:
            if flow:
                self.indent = self.best_indent
            else:
                self.indent = 0
        elif not indentless:
            self.indent += self.best_indent

    # States.

    # Stream handlers.

    def expect_stream_start(self):
        if isinstance(self.event, StreamStartEvent):
            self.encoding = event.encoding
            self.canonical = event.canonical
            if self.event.indent and self.event.indent > 1:
                self.best_indent = self.event.indent
            if self.event.width and self.event.width > self.best_indent:
                self.best_width = self.event.width
            if self.event.line_break in [u'\r', u'\n', u'\r\n']:
                self.best_line_break = self.event.line_break
            self.write_stream_start()
            self.state = self.expect_first_document_start
        else:
            raise EmitterError("expected StreamStartEvent, but got %s"
                    % self.event)

    def expect_nothing(self):
        raise EmitterError("expected nothing, but got %s" % self.event)

    # Document handlers.

    def expect_first_document_start(self):
        return self.expect_document_start(first=True)

    def expect_document_start(self, first=False):
        if isinstance(self.event, DocumentStartEvent):
            if self.event.version:
                self.write_version_directive(self.event.version)
            self.tag_prefixes = self.DEFAULT_TAG_PREFIXES.copy()
            if self.event.tags:
                for handle in self.event.tags:
                    prefix = self.event.tags[handle]
                    self.tag_prefixes[prefix] = handle
                    self.write_tag_directive(handle, prefix)
            implicit = (first and self.event.implicit and not self.canonical
                    and not self.event.version and not self.event.tags
                    and not self.check_next_empty_scalar())
            if not implicit:
                self.write_indent()
                self.write_indicator(u'---', True)
                if self.canonical:
                    self.write_indent()
            self.state = self.expect_document_root
        elif isinstance(self.event, StreamEndEvent):
            self.write_stream_end()
            self.state = self.expect_nothing
        else:
            raise EmitterError("expected DocumentStartEvent, but got %s"
                    % self.event)

    def expect_document_end(self):
        if isinstance(self.event, DocumentEndEvent):
            self.write_indent()
            if not event.implicit:
                self.write_indicator(u'...', True)
                self.write_indent()
            self.state = self.expect_document_start
        else:
            raise EmitterError("expected DocumentEndEvent, but got %s"
                    % self.event)

    def expect_document_root(self):
        self.expect_node(root=True)

    # Node handlers.

    def expect_node(self, root=False, sequence=False, mapping=False,
            simple_key=False):
        self.root_context = root
        self.sequence_context = sequence
        self.mapping_context = mapping
        self.simple_key_context = simple_key
        if isinstance(self.event, AliasEvent):
            self.expect_alias()
        elif isinstance(event, (ScalarEvent, CollectionEvent)):
            self.process_anchor()
            self.process_tag()
            if isinstance(self.event, ScalarEvent):
                self.expect_scalar()
            elif isinstance(self.event, SequenceEvent):
                if self.flow_level or self.canonical or self.event.flow_style   \
                        or self.check_empty_sequence():
                    self.expect_flow_sequence()
                else:
                    self.expect_block_sequence()
            elif isinstance(self.event, MappingEvent):
                if self.flow_level or self.canonical or self.event.flow_style   \
                        or self.check_empty_mapping():
                    self.expect_flow_mapping()
                else:
                    self.expect_block_mapping()
        else:
            raise EmitterError("expected NodeEvent, but got %s" % self.event)

    def expect_alias(self):
        self.write_anchor(u'*', self.event.anchor)
        self.state = self.states.pop()

    def expect_scalar(self):
        self.increase_indent(flow=True)
        self.process_scalar()
        self.indent = self.indents.pop()
        self.state = self.states.pop()

    # Flow sequence handlers.

    def expect_flow_sequence(self):
        self.write_indicator(u'[', True, whitespace=True)
        self.flow_level += 1
        self.increase_indent(flow=True)
        self.state = self.expect_first_flow_sequence_item

    def expect_first_flow_sequence_item(self):
        if isinstance(self.event, SequenceEndEvent):
            self.indent = self.indents.pop()
            self.flow_level -= 1
            self.write_indicator(u']', False)
            self.state = self.states.pop()
        else:
            if self.canonical or self.column > self.best_width:
                self.write_indent()
            self.states.append(self.expect_flow_sequence_item)
            self.expect_node(sequence=True)

    def expect_flow_sequence_item(self):
        if isinstance(self.event, SequenceEndEvent):
            self.indent = self.indents.pop()
            self.flow_level -= 1
            if self.canonical:
                self.write_indicator(u',', False)
                self.write_indent()
            self.write_indicator(u']', False)
            self.state = self.states.pop()
        else:
            self.write_indicator(u',', False)
            if self.canonical or self.column > self.best_width:
                self.write_indent()
            self.states.append(self.expect_flow_sequence_item)
            self.expect_node(sequence=True)

    # Flow mapping handlers.

    def expect_flow_mapping(self):
        self.write_indicator(u'{', True, whitespace=True)
        self.flow_level += 1
        self.increase_indent(flow=True)
        self.state = self.expect_first_flow_mapping_key

    def expect_first_flow_mapping_key(self):
        if isinstance(self.event, MappingEndEvent):
            self.indent = self.indents.pop()
            self.flow_level -= 1
            self.write_indicator(u'}', False)
            self.state = self.states.pop()
        else:
            if self.canonical or self.column > self.best_width:
                self.write_indent()
            if not self.canonical and self.check_simple_key():
                self.states.append(self.expect_flow_mapping_simple_value)
                self.expect_node(mapping=True, simple_key=True)
            else:
                self.write_indicator(u'?', True)
                self.states.append(self.expect_flow_mapping_value)
                self.expect_node(mapping=True)

    def expect_flow_mapping_key(self):
        if isinstance(self.event, MappingEndEvent):
            self.indent = self.indents.pop()
            self.flow_level -= 1
            if self.canonical:
                self.write_indicator(u',', False)
                self.write_indent()
            self.write_indicator(u'}', False)
            self.state = self.states.pop()
        else:
            self.write_indicator(u',', False)
            if self.canonical or self.column > self.best_width:
                self.write_indent()
            if not self.canonical and self.check_simple_key():
                self.states.append(self.expect_flow_mapping_simple_value)
                self.expect_node(mapping=True, simple_key=True)
            else:
                self.write_indicator(u'?', True)
                self.states.append(self.expect_flow_mapping_value)
                self.expect_node(mapping=True)

    def expect_flow_mapping_simple_value(self):
        self.write_indicator(u':', False)
        self.states.append(self.expect_flow_mapping_key)
        self.expect_node(mapping=True)

    def expect_flow_mapping_value(self):
        if self.canonical or self.column > self.best_width:
            self.write_indent()
        self.write_indicator(u':', True)
        self.states.append(self.expect_flow_mapping_key)
        self.expect_node(mapping=True)

    # Block sequence handlers.

    def expect_block_sequence(self):
        indentless = (self.mapping_context and not self.indention)
        self.increase_indent(flow=False, indentless=indentless)
        self.state = self.expect_first_block_sequence_item

    def expect_first_block_sequence_item(self):
        return self.expect_block_sequence_item(first=True)

    def expect_block_sequence_item(self, first=False):
        if not first and isinstance(self.event, SequenceEndEvent):
            self.indent = self.indents.pop()
            self.state = self.states.pop()
        else:
            self.write_indent()
            self.write_indicator(u'-', True, indention=True)
            self.states.append(self.expect_block_sequence_item)
            self.expect_node(sequence=True)

    # Block mapping handlers.

    def expect_block_mapping(self):
        self.increase_indent(flow=False)
        self.state = self.expect_first_block_mapping_key

    def expect_first_block_mapping_key(self):
        return self.expect_block_mapping_key(first=True)

    def expect_block_mapping_key(self, first=False):
        if not first and isinstance(self.event, SequenceEndEvent):
            self.indent = self.indents.pop()
            self.state = self.states.pop()
        else:
            self.write_indent()
            if self.check_simple_key():
                self.states.append(self.expect_block_mapping_simple_value)
                self.expect_node(mapping=True, simple_key=True)
            else:
                self.write_indicator(u'?', True, indention=True)
                self.states.append(self.expect_block_mapping_value)
                self.expect_node(mapping=True)

    def expect_block_mapping_simple_value(self):
        self.write_indicator(u':', False)
        self.states.append(self.expect_block_mapping_key)
        self.expect_node(mapping=True)

    def expect_block_mapping_value(self):
        self.write_indent()
        self.write_indicator(u':', True, indention=True)
        self.states.append(self.expect_block_mapping_key)
        self.expect_node(mapping=True)

    # Writers.

    def write_stream_start(self):
        # Write BOM if needed.
        if self.encoding and self.encoding.startswith('utf-16'):
            self.writer.write(u'\xFF\xFE'.encode(self.encoding))

    def write_stream_end(self):
        if hasattr(self.writer, 'flush'):
            self.writer.flush()

    def write_indicator(self, indicator, need_whitespace,
            whitespace=False, indention=False):
        if self.whitespace:
            data = indicator
        else:
            data = u' '+indicator
        self.writespace = whitespace
        self.indention = self.indention and indention
        self.column += len(data)
        if self.encoding:
            data = data.encode(self.encoding)
        self.writer.write(data)

    def write_indent(self):
        indent = self.indent or 0
        if not self.indention or self.column > indent:
            self.write_line_break()
        if self.column < indent:
            data = u' '*(indent-self.column)
            self.column = indent
            if self.encoding:
                data = data.encode(self.encoding)
            self.writer.write(data)

    def write_line_break(self):
        data = self.best_line_break
        self.whitespace = True
        self.indention = True
        self.line += 1
        self.column = 0
        if self.encoding:
            data = data.encode(self.encoding)
        self.writer.write(data)

