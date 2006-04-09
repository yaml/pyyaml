
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

class ScalarAnalysis:
    def __init__(self, scalar, empty, multiline,
            allow_flow_plain, allow_block_plain,
            allow_single_quoted, allow_double_quoted, allow_block):
        self.scalar = scalar
        self.empty = empty
        self.multiline = multiline
        self.allow_flow_plain = allow_flow_plain
        self.allow_block_plain = allow_block_plain
        self.allow_single_quoted = allow_single_quoted
        self.allow_double_quoted = allow_double_quoted
        self.allow_block = allow_block

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

        # Analyses cache.
        self.anchor_text = None
        self.tag_text = None
        self.scalar_analysis = None
        self.scalar_style = None

    def emit(self, event):
        self.events.append(event)
        while not self.need_more_events():
            self.event = self.events.pop(0)
            self.state()
            self.event = None

    # In some cases, we wait for a few next events before emitting.

    def need_more_events(self):
        if not self.events:
            return True
        event = self.events[0]
        if isinstance(event, DocumentStartEvent):
            return self.need_events(1)
        elif isinstance(event, SequenceStartEvent):
            return self.need_events(2)
        elif isinstance(event, MappingStartEvent):
            return self.need_events(3)
        else:
            return False

    def need_events(self, count):
        level = 0
        for event in self.events[1:]:
            if isinstance(event, (DocumentStartEvent, CollectionStartEvent)):
                level += 1
            elif isinstance(event, (DocumentEndEvent, CollectionEndEvent)):
                level -= 1
            elif isinstance(event, StreamEndEvent):
                level = -1
            if level < 0:
                return False
        return (len(self.events) < count+1)

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
            self.encoding = self.event.encoding
            self.canonical = self.event.canonical
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
                version_text = self.analyze_version(self.event.version)
                self.write_version_directive(version_text)
            self.tag_prefixes = self.DEFAULT_TAG_PREFIXES.copy()
            if self.event.tags:
                handles = self.event.tags.keys()
                handles.sort()
                for handle in handles:
                    prefix = self.event.tags[handle]
                    self.tag_prefixes[prefix] = handle
                    handle_text = self.analyze_tag_handle(handle)
                    prefix_text = self.analyze_tag_prefix(prefix)
                    self.write_tag_directive(handle_text, prefix_text)
            implicit = (first and not self.event.explicit and not self.canonical
                    and not self.event.version and not self.event.tags
                    and not self.check_empty_document())
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
            if self.event.explicit:
                self.write_indicator(u'...', True)
                self.write_indent()
            self.state = self.expect_document_start
        else:
            raise EmitterError("expected DocumentEndEvent, but got %s"
                    % self.event)

    def expect_document_root(self):
        self.states.append(self.expect_document_end)
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
        elif isinstance(self.event, (ScalarEvent, CollectionStartEvent)):
            self.process_anchor(u'&')
            self.process_tag()
            if isinstance(self.event, ScalarEvent):
                self.expect_scalar()
            elif isinstance(self.event, SequenceStartEvent):
                if self.flow_level or self.canonical or self.event.flow_style   \
                        or self.check_empty_sequence():
                    self.expect_flow_sequence()
                else:
                    self.expect_block_sequence()
            elif isinstance(self.event, MappingStartEvent):
                if self.flow_level or self.canonical or self.event.flow_style   \
                        or self.check_empty_mapping():
                    self.expect_flow_mapping()
                else:
                    self.expect_block_mapping()
        else:
            raise EmitterError("expected NodeEvent, but got %s" % self.event)

    def expect_alias(self):
        if self.event.anchor is None:
            raise EmitterError("anchor is not specified for alias")
        self.process_anchor(u'*')
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
        if not first and isinstance(self.event, MappingEndEvent):
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

    # Checkers.

    def check_empty_sequence(self):
        return (isinstance(self.event, SequenceStartEvent) and self.events
                and isinstance(self.events[0], SequenceEndEvent))

    def check_empty_mapping(self):
        return (isinstance(self.event, MappingStartEvent) and self.events
                and isinstance(self.events[0], MappingEndEvent))

    def check_empty_document(self):
        if not isinstance(self.event, DocumentStartEvent) or not self.events:
            return False
        event = self.events[0]
        return (isinstance(event, ScalarEvent) and event.anchor is None
                and event.tag is None and event.implicit and event.value == u'')

    def check_simple_key(self):
        length = 0
        if isinstance(self.event, NodeEvent) and self.event.anchor is not None:
            if self.anchor_text is None:
                self.anchor_text = self.analyze_anchor(self.event.anchor)
            length += len(self.anchor_text)
        if isinstance(self.event, (ScalarEvent, CollectionStartEvent))  \
                and self.event.tag is not None:
            if self.tag_text is None:
                self.tag_text = self.analyze_tag(self.event.tag)
            length += len(self.tag_text)
        if isinstance(self.event, ScalarEvent):
            if self.scalar_analysis is None:
                self.scalar_analysis = self.analyze_scalar(self.event.value)
            length += len(self.scalar_analysis.scalar)
        return (length < 128 and (isinstance(self.event, AliasEvent)
            or (isinstance(self.event, ScalarEvent) and not self.scalar_analysis.multiline)
            or self.check_empty_sequence() or self.check_empty_mapping()))

    # Anchor, Tag, and Scalar processors.

    def process_anchor(self, indicator):
        if self.event.anchor is None:
            return
        if self.anchor_text is None:
            self.anchor_text = self.analyze_anchor(self.event.anchor)
        if self.anchor_text:
            self.write_indicator(indicator+self.anchor_text, True)
        self.anchor_text = None

    def process_tag(self):
        if self.event.tag is None:
            return
        if isinstance(self.event, ScalarEvent) and self.best_scalar_style() == '':
            return
        if self.tag_text is None:
            self.tag_text = self.analyze_tag(self.event.tag)
        if self.tag_text:
            self.write_indicator(self.tag_text, True)
        self.tag_text = None

    def best_scalar_style(self):
        if self.scalar_analysis is None:
            self.scalar_analysis = self.analyze_scalar(self.event.value)
        if self.canonical:
            return '"'
        if (self.event.implicit and not self.event.style
                and ((self.flow_level and self.scalar_analysis.allow_flow_plain)
                    or (not self.flow_level and self.scalar_analysis.allow_block_plain))
                and (len(self.scalar_analysis.scalar) > 0
                    or (not self.flow_level and not self.simple_key_context))):
            return ''
        elif self.event.style == '\'' and self.scalar_analysis.allow_single_quoted:
            return '\''
        elif self.event.style in ['|', '>'] and not self.flow_level and self.scalar_analysis.allow_block:
            return self.event.style
        else:
            return '"'
        return style

    def process_scalar(self):
        if self.scalar_analysis is None:
            self.scalar_analysis = self.analyze_scalar(self.event.value)
        style = self.best_scalar_style()
        if self.scalar_analysis.multiline and not self.simple_key_context   \
                and style not in ['|', '>']:
            self.write_indent()
        if style == '"':
            self.write_double_quoted(self.scalar_analysis.scalar,
                    split=(not self.simple_key_context))
        elif style == '\'':
            self.write_single_quoted(self.scalar_analysis.scalar,
                    split=(not self.simple_key_context))
        elif style == '>':
            self.write_folded(self.scalar_analysis.scalar)
        elif style == '|':
            self.write_literal(self.scalar_analysis.scalar)
        else:
            self.write_plain(self.scalar_analysis.scalar,
                    split=(not self.simple_key_context))
        self.scalar_analysis = None

    # Analyzers.

    def analyze_version(self, version):
        major, minor = version
        if major != 1:
            raise EmitterError("unsupported YAML version: %d.%d" % (major, minor))
        return u'%d.%d' % (major, minor)

    def analyze_tag_handle(self, handle):
        if not handle:
            raise EmitterError("tag handle must not be empty")
        if handle[0] != u'!' or handle[-1] != u'!':
            raise EmitterError("tag handle must start and end with '!': %r"
                    % (handle.encode('utf-8')))
        for ch in handle[1:-1]:
            if not (u'0' <= ch <= u'9' or u'A' <= ch <= 'Z' or u'a' <= ch <= 'z'    \
                    or ch in u'-_'):
                raise EmitterError("invalid character %r in the tag handle: %r"
                        % (ch.encode('utf-8'), handle.encode('utf-8')))
        return handle

    def analyze_tag_prefix(self, prefix):
        if not prefix:
            raise EmitterError("tag prefix must not be empty")
        chunks = []
        start = end = 0
        if prefix[0] == u'!':
            end = 1
        while end < len(prefix):
            ch = prefix[end]
            if u'0' <= ch <= u'9' or u'A' <= ch <= 'Z' or u'a' <= ch <= 'z'  \
                    or ch in u'-;/?!:@&=+$,_.~*\'()[]':
                end += 1
            else:
                if start < end:
                    chunks.append(prefix[start:end])
                start = end = end+1
                data = ch.encode('utf-8')
                for ch in data:
                    chunks.append(u'%%%02X' % ord(ch))
        if start < end:
            chunks.append(prefix[start:end])
        return u''.join(chunks)

    def analyze_tag(self, tag):
        if not tag:
            raise EmitterError("tag must not be empty")
        handle = None
        suffix = tag
        for prefix in self.tag_prefixes:
            if tag.startswith(prefix)   \
                    and (prefix == u'!' or len(prefix) < len(tag)):
                handle = self.tag_prefixes[prefix]
                suffix = tag[len(prefix):]
        chunks = []
        start = end = 0
        while end < len(suffix):
            ch = suffix[end]
            if u'0' <= ch <= u'9' or u'A' <= ch <= 'Z' or u'a' <= ch <= 'z'  \
                    or ch in u'-;/?:@&=+$,_.~*\'()[]'   \
                    or (ch == u'!' and handle != u'!'):
                end += 1
            else:
                if start < end:
                    chunks.append(suffix[start:end])
                start = end = end+1
                data = ch.encode('utf-8')
                for ch in data:
                    chunks.append(u'%%%02X' % ord(ch))
        if start < end:
            chunks.append(suffix[start:end])
        suffix_text = u''.join(chunks)
        if handle:
            return u'%s%s' % (handle, suffix_text)
        else:
            return u'!<%s>' % suffix_text

    def analyze_anchor(self, anchor):
        if not anchor:
            raise EmitterError("anchor must not be empty")
        for ch in anchor:
            if not (u'0' <= ch <= u'9' or u'A' <= ch <= 'Z' or u'a' <= ch <= 'z'    \
                    or ch in u'-_'):
                raise EmitterError("invalid character %r in the anchor: %r"
                        % (ch.encode('utf-8'), text.encode('utf-8')))
        return anchor

    def analyze_scalar(self, scalar):   # It begs for refactoring.
        if not scalar:
            return ScalarAnalysis(scalar=scalar, empty=True, multiline=False,
                    allow_flow_plain=False, allow_block_plain=True,
                    allow_single_quoted=True, allow_double_quoted=True,
                    allow_block=False)
        contains_block_indicator = False
        contains_flow_indicator = False
        contains_line_breaks = False
        contains_unicode_characters = False
        contains_special_characters = False
        contains_inline_spaces = False          # non-space space+ non-space
        contains_inline_breaks = False          # non-space break+ non-space
        contains_leading_spaces = False         # ^ space+ (non-space | $)
        contains_leading_breaks = False         # ^ break+ (non-space | $)
        contains_trailing_spaces = False        # non-space space+ $
        contains_trailing_breaks = False        # non-space break+ $
        contains_inline_breaks_spaces = False   # non-space break+ space+ non-space
        contains_mixed_breaks_spaces = False    # anything else
        if scalar.startswith(u'---') or scalar.startswith(u'...'):
            contains_block_indicator = True
            contains_flow_indicator = True
        first = True
        last = (len(scalar) == 1)
        preceeded_by_space = False
        followed_by_space = (len(scalar) > 1 and
                scalar[1] in u'\0 \t\r\n\x85\u2028\u2029')
        spaces = breaks = mixed = leading = False
        index = 0
        while index < len(scalar):
            ch = scalar[index]
            if first:
                if ch in u'#,[]{}#&*!|>\'\"%@`': 
                    contains_flow_indicator = True
                    contains_block_indicator = True
                if ch in u'?:':
                    contains_flow_indicator = True
                    if followed_by_space or last:
                        contains_block_indicator = True
                if ch == u'-' and followed_by_space or last:
                    contains_flow_indicator = True
                    contains_block_indicator = True
            else:
                if ch in u',?[]{}':
                    contains_flow_indicator = True
                if ch == u':':
                    contains_flow_indicator = True
                    if followed_by_space or last:
                        contains_block_indicator = True
                if ch == u'#' and preceeded_by_space:
                    contains_flow_indicator = True
                    contains_block_indicator = True
            if ch in u'\n\x85\u2028\u2029':
                contains_line_breaks = True
            if not (ch == u'\n' or u'\x20' <= ch <= u'\x7E'):
                if ch < u'\x80':
                    contains_special_characters = True
                else:
                    contains_special_characters = True
                    # TODO: We need an option to allow unescaped unicode
                    # characters.
                    contains_unicode_characters = True
            if ch == u' ':
                if not spaces and not breaks:
                    leading = first
                spaces = True
            elif ch in u'\n\x85\u2028\u2029':
                if not spaces and not breaks:
                    leading = first
                breaks = True
                if spaces:
                    mixed = True
            if ch not in u' \n\x85\u2028\u2029':
                if leading:
                    if spaces and breaks:
                        contains_mixed_breaks_spaces = True
                    elif spaces:
                        contains_leading_spaces = True
                    elif breaks:
                        contains_leading_breaks = True
                else:
                    if mixed:
                        contains_mixed_break_spaces = True
                    elif spaces and breaks:
                        contains_inline_breaks_spaces = True
                    elif spaces:
                        contains_inline_spaces = True
                    elif breaks:
                        contains_inline_breaks = True
                spaces = breaks = mixed = leading = False
            elif last:
                if spaces and breaks:
                    contains_mixed_break_spaces = True
                elif spaces:
                    if leading:
                        contains_leading_spaces = True
                    else:
                        contains_trailing_spaces = True
                elif breaks:
                    if leading:
                        contains_leading_breaks = True
                    else:
                        contains_trailing_breaks = True
            index += 1
            first = False
            last = (index+1 == len(scalar))
            preceeded_by_space = (ch in u'\0 \t\r\n\x85\u2028\u2029')
            followed_by_space = (index+1 < len(scalar) and
                    scalar[index+1] in u'\0 \t\r\n\x85\u2028\u2029')
        allow_flow_plain = not (contains_flow_indicator or contains_special_characters
            or contains_leading_spaces or contains_leading_breaks
            or contains_trailing_spaces or contains_trailing_breaks
            or contains_inline_breaks_spaces or contains_mixed_breaks_spaces)
        allow_block_plain = not (contains_block_indicator or contains_special_characters
            or contains_leading_spaces or contains_leading_breaks
            or contains_trailing_spaces or contains_trailing_breaks
            or contains_inline_breaks_spaces or contains_mixed_breaks_spaces)
        allow_single_quoted = not (contains_special_characters
            or contains_inline_breaks_spaces or contains_mixed_breaks_spaces)
        allow_double_quoted = True
        allow_block = not (contains_special_characters
            or contains_leading_spaces or contains_leading_breaks
            or contains_trailing_spaces or contains_mixed_breaks_spaces)
        return ScalarAnalysis(scalar=scalar, empty=False, multiline=contains_line_breaks,
                allow_flow_plain=allow_flow_plain, allow_block_plain=allow_block_plain,
                allow_single_quoted=allow_single_quoted, allow_double_quoted=allow_double_quoted,
                allow_block=allow_block)

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
        if self.whitespace or not need_whitespace:
            data = indicator
        else:
            data = u' '+indicator
        self.whitespace = whitespace
        self.indention = self.indention and indention
        self.column += len(data)
        if self.encoding:
            data = data.encode(self.encoding)
        self.writer.write(data)

    def write_indent(self):
        indent = self.indent or 0
        if not self.indention or self.column > indent   \
                or (self.column == indent and not self.whitespace):
            self.write_line_break()
        if self.column < indent:
            self.whitespace = True
            data = u' '*(indent-self.column)
            self.column = indent
            if self.encoding:
                data = data.encode(self.encoding)
            self.writer.write(data)

    def write_line_break(self, data=None):
        if data is None:
            data = self.best_line_break
        self.whitespace = True
        self.indention = True
        self.line += 1
        self.column = 0
        if self.encoding:
            data = data.encode(self.encoding)
        self.writer.write(data)

    def write_version_directive(self, version_text):
        data = u'%%YAML %s' % version_text
        if self.encoding:
            data = data.encode(self.encoding)
        self.writer.write(data)
        self.write_line_break()

    def write_tag_directive(self, handle_text, prefix_text):
        data = u'%%TAG %s %s' % (handle_text, prefix_text)
        if self.encoding:
            data = data.encode(self.encoding)
        self.writer.write(data)
        self.write_line_break()

    # Scalar writers.

    def write_single_quoted(self, text, split=True):
        self.write_indicator(u'\'', True)
        spaces = False
        breaks = False
        start = end = 0
        while end <= len(text):
            ch = None
            if end < len(text):
                ch = text[end]
            if spaces:
                if ch is None or ch != u' ':
                    if start+1 == end and self.column > self.best_width and split   \
                            and start != 0 and end != len(text):
                        self.write_indent()
                    else:
                        data = text[start:end]
                        self.column += len(data)
                        if self.encoding:
                            data = data.encode(self.encoding)
                        self.writer.write(data)
                    start = end
            elif breaks:
                if ch is None or ch not in u'\n\x85\u2028\u2029':
                    if text[start] == u'\n':
                        self.write_line_break()
                    for br in text[start:end]:
                        if br == u'\n':
                            self.write_line_break()
                        else:
                            self.write_line_break(br)
                    self.write_indent()
                    start = end
            else:
                if ch is None or ch in u' \n\x85\u2028\u2029' or ch == u'\'':
                    if start < end:
                        data = text[start:end]
                        self.column += len(data)
                        if self.encoding:
                            data = data.encode(self.encoding)
                        self.writer.write(data)
                        start = end
                    if ch == u'\'':
                        data = u'\'\''
                        self.column += 2
                        if self.encoding:
                            data = data.encode(self.encoding)
                        self.writer.write(data)
                        start = end + 1
            if ch is not None:
                spaces = (ch == u' ')
                breaks = (ch in u'\n\x85\u2028\u2029')
            end += 1
        self.write_indicator(u'\'', False)

    ESCAPE_REPLACEMENTS = {
        u'\0':      u'0',
        u'\x07':    u'a',
        u'\x08':    u'b',
        u'\x09':    u't',
        u'\x0A':    u'n',
        u'\x0B':    u'v',
        u'\x0C':    u'f',
        u'\x0D':    u'r',
        u'\x1B':    u'e',
        u'\"':      u'\"',
        u'\\':      u'\\',
        u'\x85':    u'N',
        u'\xA0':    u'_',
        u'\u2028':  u'L',
        u'\u2029':  u'P',
    }

    def write_double_quoted(self, text, split=True):
        self.write_indicator(u'"', True)
        start = end = 0
        while end <= len(text):
            ch = None
            if end < len(text):
                ch = text[end]
            if ch is None or not (u'\x20' <= ch <= u'\x7E') or ch in u'"\\':
                if start < end:
                    data = text[start:end]
                    self.column += len(data)
                    if self.encoding:
                        data = data.encode(self.encoding)
                    self.writer.write(data)
                    start = end
                if ch is not None:
                    if ch in self.ESCAPE_REPLACEMENTS:
                        data = u'\\'+self.ESCAPE_REPLACEMENTS[ch]
                    elif ch <= u'\xFF':
                        data = u'\\x%02X' % ord(ch)
                    elif ch <= u'\uFFFF':
                        data = u'\\u%04X' % ord(ch)
                    else:
                        data = u'\\U%08X' % ord(ch)
                    self.column += len(data)
                    if self.encoding:
                        data = data.encode(self.encoding)
                    self.writer.write(data)
                    start = end+1
            if 0 < end < len(text)-1 and (ch == u' ' or start >= end)   \
                    and self.column+(end-start) > self.best_width and split:
                data = text[start:end]+u'\\'
                if start < end:
                    start = end
                self.column += len(data)
                if self.encoding:
                    data = data.encode(self.encoding)
                self.writer.write(data)
                self.write_indent()
                self.whitespace = False
                self.indention = False
                if ch == u' ':
                    data = u'\\'
                    self.column += len(data)
                    if self.encoding:
                        data = data.encode(self.encoding)
                    self.writer.write(data)
            end += 1
        self.write_indicator(u'"', False)

    def determine_chomp(self, text):
        tail = text[-2:]
        while len(tail) < 2:
            tail = u' '+tail
        if tail[-1] in u'\n\x85\u2028\u2029':
            if tail[-2] in u'\n\x85\u2028\u2029':
                return u'+'
            else:
                return u''
        else:
            return u'-'

    def write_folded(self, text):
        chomp = self.determine_chomp(text)
        self.write_indicator(u'>'+chomp, True)
        self.write_indent()
        leading_space = False
        spaces = False
        breaks = False
        start = end = 0
        while end <= len(text):
            ch = None
            if end < len(text):
                ch = text[end]
            if breaks:
                if ch is None or ch not in u'\n\x85\u2028\u2029':
                    if not leading_space and ch is not None and ch != u' '  \
                            and text[start] == u'\n':
                        self.write_line_break()
                    leading_space = (ch == u' ')
                    for br in text[start:end]:
                        if br == u'\n':
                            self.write_line_break()
                        else:
                            self.write_line_break(br)
                    if ch is not None:
                        self.write_indent()
                    start = end
            elif spaces:
                if ch != u' ':
                    if start+1 == end and self.column > self.best_width:
                        self.write_indent()
                    else:
                        data = text[start:end]
                        self.column += len(data)
                        if self.encoding:
                            data = data.encode(self.encoding)
                        self.writer.write(data)
                    start = end
            else:
                if ch is None or ch in u' \n\x85\u2028\u2029':
                    data = text[start:end]
                    if self.encoding:
                        data = data.encode(self.encoding)
                    self.writer.write(data)
                    if ch is None:
                        self.write_line_break()
                    start = end
            if ch is not None:
                breaks = (ch in u'\n\x85\u2028\u2029')
                spaces = (ch == u' ')
            end += 1

    def write_literal(self, text):
        chomp = self.determine_chomp(text)
        self.write_indicator(u'|'+chomp, True)
        self.write_indent()
        breaks = False
        start = end = 0
        while end <= len(text):
            ch = None
            if end < len(text):
                ch = text[end]
            if breaks:
                if ch is None or ch not in u'\n\x85\u2028\u2029':
                    for br in text[start:end]:
                        if br == u'\n':
                            self.write_line_break()
                        else:
                            self.write_line_break(br)
                    if ch is not None:
                        self.write_indent()
                    start = end
            else:
                if ch is None or ch in u'\n\x85\u2028\u2029':
                    data = text[start:end]
                    if self.encoding:
                        data = data.encode(self.encoding)
                    self.writer.write(data)
                    if ch is None:
                        self.write_line_break()
                    start = end
            if ch is not None:
                breaks = (ch in u'\n\x85\u2028\u2029')
            end += 1

    def write_plain(self, text, split=True):
        if not text:
            return
        if not self.whitespace:
            data = u' '
            self.column += len(data)
            if self.encoding:
                data = data.encode(self.encoding)
            self.writer.write(data)
        self.writespace = False
        self.indention = False
        spaces = False
        breaks = False
        start = end = 0
        while end <= len(text):
            ch = None
            if end < len(text):
                ch = text[end]
            if spaces:
                if ch != u' ':
                    if start+1 == end and self.column > self.best_width and split:
                        self.write_indent()
                        self.writespace = False
                        self.indention = False
                    else:
                        data = text[start:end]
                        self.column += len(data)
                        if self.encoding:
                            data = data.encode(self.encoding)
                        self.writer.write(data)
                    start = end
            elif breaks:
                if ch not in u'\n\x85\u2028\u2029':
                    if text[start] == u'\n':
                        self.write_line_break()
                    for br in text[start:end]:
                        if br == u'\n':
                            self.write_line_break()
                        else:
                            self.write_line_break(br)
                    self.write_indent()
                    self.whitespace = False
                    self.indention = False
                    start = end
            else:
                if ch is None or ch in u' \n\x85\u2028\u2029':
                    data = text[start:end]
                    self.column += len(data)
                    if self.encoding:
                        data = data.encode(self.encoding)
                    self.writer.write(data)
                    start = end
            if ch is not None:
                spaces = (ch == u' ')
                breaks = (ch in u'\n\x85\u2028\u2029')
            end += 1

