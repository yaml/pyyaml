
# YAML can be parsed by an LL(1) parser!
#
# We use the following production rules:
# stream            ::= implicit_document? explicit_document* STREAM-END
# explicit_document ::= DIRECTIVE* DOCUMENT-START block_node? DOCUMENT-END?
# implicit_document ::= block_node DOCUMENT-END?
# block_node    ::= ALIAS | properties? block_content
# flow_node     ::= ALIAS | properties? flow_content
# properties    ::= TAG ANCHOR? | ANCHOR TAG?
# block_content     ::= block_collection | flow_collection | SCALAR
# flow_content      ::= flow_collection | SCALAR
# block_collection  ::= block_sequence | block_mapping
# block_sequence    ::= BLOCK-SEQUENCE-START (BLOCK-ENTRY block_node?)* BLOCK-END
# block_mapping     ::= BLOCK-MAPPING_START ((KEY block_node_or_indentless_sequence?)? (VALUE block_node_or_indentless_sequence?)?)* BLOCK-END
# block_node_or_indentless_sequence ::= ALIAS | properties? (block_content | indentless_block_sequence)
# indentless_block_sequence         ::= (BLOCK-ENTRY block_node?)+
# flow_collection   ::= flow_sequence | flow_mapping
# flow_sequence     ::= FLOW-SEQUENCE-START (flow_sequence_entry FLOW-ENTRY)* flow_sequence_entry? FLOW-SEQUENCE-END
# flow_mapping      ::= FLOW-MAPPING-START (flow_mapping_entry FLOW-ENTRY)* flow_mapping_entry? FLOW-MAPPING-END
# flow_sequence_entry   ::= flow_node | KEY flow_node? (VALUE flow_node?)?
# flow_mapping_entry    ::= flow_node | KEY flow_node? (VALUE flow_node?)?

# TODO: support for BOM within a stream.
# stream ::= (BOM? implicit_document)? (BOM? explicit_document)* STREAM-END

# Note that there is a slight deviation from the specification. We require a
# non-empty node content if ANCHOR or TAG is specified. This disallow such
# documents as
#
#   key:    !!str   # empty value
#
# This is done to prevent ambiguity in parsing tags and aliases:
#
#   {   !!perl/YAML::Parser:    value }
#
# What is it? Should it be interpreted as
#   {   ? !<tag:yaml.org,2002:perl/YAML::Parser> '' : value }
# or
#   {   ? !<tag:yaml.org,2002:perl/YAML::Parser:> value : '' }
# Since we disallow non-empty node content, tags are always followed by spaces
# or line breaks.

# FIRST sets:
# stream: FIRST(block_node) + { DIRECTIVE DOCUMENT-START }
# explicit_document: { DIRECTIVE DOCUMENT-START }
# implicit_document: FIRST(block_node)
# block_node: { ALIAS TAG ANCHOR SCALAR BLOCK-SEQUENCE-START BLOCK-MAPPING-START FLOW-SEQUENCE-START FLOW-MAPPING-START }
# flow_node: { ALIAS ANCHOR TAG SCALAR FLOW-SEQUENCE-START FLOW-MAPPING-START }
# block_content: { BLOCK-SEQUENCE-START BLOCK-MAPPING-START FLOW-SEQUENCE-START FLOW-MAPPING-START SCALAR }
# flow_content: { FLOW-SEQUENCE-START FLOW-MAPPING-START SCALAR }
# block_collection: { BLOCK-SEQUENCE-START BLOCK-MAPPING-START }
# flow_collection: { FLOW-SEQUENCE-START FLOW-MAPPING-START }
# block_sequence: { BLOCK-SEQUENCE-START }
# block_mapping: { BLOCK-MAPPING-START }
# block_node_or_indentless_sequence: { ALIAS ANCHOR TAG SCALAR BLOCK-SEQUENCE-START BLOCK-MAPPING-START FLOW-SEQUENCE-START FLOW-MAPPING-START BLOCK-ENTRY }
# indentless_sequence: { ENTRY }
# flow_collection: { FLOW-SEQUENCE-START FLOW-MAPPING-START }
# flow_sequence: { FLOW-SEQUENCE-START }
# flow_mapping: { FLOW-MAPPING-START }
# flow_sequence_entry: { ALIAS ANCHOR TAG SCALAR FLOW-SEQUENCE-START FLOW-MAPPING-START KEY }
# flow_mapping_entry: { ALIAS ANCHOR TAG SCALAR FLOW-SEQUENCE-START FLOW-MAPPING-START KEY }

from error import MarkedYAMLError
from tokens import *
from events import *

class ParserError(MarkedYAMLError):
    pass

class Parser:
    # Since writing an LL(1) parser is a straightforward task, we do not give
    # many comments here.
    # Note that we use Python generators. If you rewrite the parser in another
    # language, you may replace all 'yield'-s with event handler calls.

    DEFAULT_TAGS = {
        u'!':   u'!',
        u'!!':  u'tag:yaml.org,2002:',
    }

    def __init__(self, scanner):
        self.scanner = scanner
        self.current_event = None
        self.yaml_version = None
        self.tag_handles = {}
        self.event_generator = self.parse_stream()

    def check(self, *choices):
        # Check the type of the next event.
        if self.current_event is None:
            try:
                self.current_event = self.event_generator.next()
            except StopIteration:
                pass
        if self.current_event is not None:
            for choice in choices:
                if isinstance(self.current_event, choice):
                    return True
        return False

    def peek(self):
        # Get the next event.
        if self.current_event is None:
            try:
                self.current_event = self.event_generator.next()
            except StopIteration:
                pass
        return self.current_event

    def get(self):
        # Get the next event.
        if self.current_event is None:
            try:
                self.current_event = self.event_generator.next()
            except StopIteration:
                pass
        value = self.current_event
        self.current_event = None
        return value

    def __iter__(self):
        # Iterator protocol.
        return self.event_generator

    def parse_stream(self):
        # implicit_document? explicit_document* STREAM-END

        # Parse implicit document.
        if not self.scanner.check(DirectiveToken, DocumentStartToken,
                StreamEndToken):
            self.tag_handles = self.DEFAULT_TAGS
            for event in self.parse_block_node():
                yield event

        # Parse explicit documents.
        while not self.scanner.check(StreamEndToken):
            self.process_directives()
            if not self.scanner.check(DocumentStartToken):
                raise ParserError(None, None,
                        "expected '<document start>', but found %r"
                        % self.scanner.peek().id,
                        self.scanner.peek().start_marker)
            token = self.scanner.get()
            if self.scanner.check(DirectiveToken,
                    DocumentStartToken, DocumentEndToken, StreamEndToken):
                yield self.process_empty_scalar(token.end_marker)
            else:
                for event in self.parse_block_node():
                    yield event
            while self.scanner.check(DocumentEndToken):
                self.scanner.get()

        # Parse end of stream.
        token = self.scanner.get()
        yield StreamEndEvent(token.start_marker, token.end_marker)

    def process_directives(self):
        # DIRECTIVE*
        self.yaml_version = None
        self.tag_handles = {}
        while self.scanner.check(DirectiveToken):
            token = self.scanner.get()
            if token.name == u'YAML':
                if self.yaml_version is not None:
                    raise ParserError(None, None,
                            "found duplicate YAML directive", token.start_marker)
                major, minor = token.value
                if major != 1:
                    raise ParserError(None, None,
                            "found incompatible YAML document (version 1.* is required)",
                            token.start_marker)
                self.yaml_version = token.value
            elif token.name == u'TAG':
                handle, prefix = token.value
                if handle in self.tag_handles:
                    raise ParserError(None, None,
                            "duplicate tag handle %r" % handle.encode('utf-8'),
                            token.start_marker)
                self.tag_handles[handle] = prefix
        for key in self.DEFAULT_TAGS:
            if key not in self.tag_handles:
                self.tag_handles[key] = self.DEFAULT_TAGS[key]

    def parse_block_node(self):
        return self.parse_node(block=True)

    def parse_flow_node(self):
        return self.parse_node()

    def parse_block_node_or_indentless_sequence(self):
        return self.parse_node(block=True, indentless_sequence=True)

    def parse_node(self, block=False, indentless_sequence=False):
        # block_node    ::= ALIAS | properties? block_content
        # flow_node     ::= ALIAS | properties? flow_content
        # properties    ::= TAG ANCHOR? | ANCHOR TAG?
        # block_content     ::= block_collection | flow_collection | SCALAR
        # flow_content      ::= flow_collection | SCALAR
        # block_collection  ::= block_sequence | block_mapping
        # block_node_or_indentless_sequence ::= ALIAS | properties?
        #                                       (block_content | indentless_block_sequence)
        if self.scanner.check(AliasToken):
            token = self.scanner.get()
            yield AliasEvent(token.value, token.start_marker, token.end_marker)
        else:
            anchor = None
            tag = None
            start_marker = end_marker = tag_marker = None
            if self.scanner.check(AnchorToken):
                token = self.scanner.get()
                start_marker = end_marker = token.start_marker
                anchor = token.value
                if self.scanner.check(TagToken):
                    token = self.scanner.get()
                    end_marker = tag_marker = token.start_marker
                    tag = token.value
            elif self.scanner.check(TagToken):
                token = self.scanner.get()
                start_marker = end_marker = tag_marker = token.start_marker
                tag = token.value
                if self.scanner.check(AnchorToken):
                    token = self.scanner.get()
                    end_marker = token.start_marker
                    anchor = token.value
            if tag is not None:
                handle, suffix = tag
                if handle is not None:
                    if handle not in self.tag_handles:
                        raise ParserError("while parsing a node", start_marker,
                                "found undefined tag handle %r" % handle.encode('utf-8'),
                                tag_marker)
                    tag = self.tag_handles[handle]+suffix
                else:
                    tag = suffix
            if tag is None:
                if not (self.scanner.check(ScalarToken) and
                        self.scanner.peek().plain):
                    tag = u'!'
            if start_marker is None:
                start_marker = self.scanner.peek().start_marker
            event = None
            collection_events = None
            if indentless_sequence and self.scanner.check(BlockEntryToken):
                end_marker = self.scanner.peek().end_marker
                event = SequenceEvent(anchor, tag, start_marker, end_marker)
                collection_events = self.parse_indentless_sequence()
            else:
                if self.scanner.check(ScalarToken):
                    token = self.scanner.get()
                    end_marker = token.end_marker
                    event = ScalarEvent(anchor, tag, token.value,
                            start_marker, end_marker)
                elif self.scanner.check(FlowSequenceStartToken):
                    end_marker = self.scanner.peek().end_marker
                    event = SequenceEvent(anchor, tag, start_marker, end_marker)
                    collection_events = self.parse_flow_sequence()
                elif self.scanner.check(FlowMappingStartToken):
                    end_marker = self.scanner.peek().end_marker
                    event = MappingEvent(anchor, tag, start_marker, end_marker)
                    collection_events = self.parse_flow_mapping()
                elif block and self.scanner.check(BlockSequenceStartToken):
                    end_marker = self.scanner.peek().start_marker
                    event = SequenceEvent(anchor, tag, start_marker, end_marker)
                    collection_events = self.parse_block_sequence()
                elif block and self.scanner.check(BlockMappingStartToken):
                    end_marker = self.scanner.peek().start_marker
                    event = MappingEvent(anchor, tag, start_marker, end_marker)
                    collection_events = self.parse_block_mapping()
                else:
                    if block:
                        node = 'block'
                    else:
                        node = 'flow'
                    token = self.scanner.peek()
                    raise ParserError("while scanning a %s node" % node, start_marker,
                            "expected the node content, but found %r" % token.id,
                            token.start_marker)
            yield event
            if collection_events is not None:
                for event in collection_events:
                    yield event

    def parse_block_sequence(self):
        # BLOCK-SEQUENCE-START (BLOCK-ENTRY block_node?)* BLOCK-END
        token = self.scanner.get()
        start_marker = token.start_marker
        while self.scanner.check(BlockEntryToken):
            token = self.scanner.get()
            if not self.scanner.check(BlockEntryToken, BlockEndToken):
                for event in self.parse_block_node():
                    yield event
            else:
                yield self.process_empty_scalar(token.end_marker)
        if not self.scanner.check(BlockEndToken):
            token = self.scanner.peek()
            raise ParserError("while scanning a block collection", start_marker,
                    "expected <block end>, but found %r" % token.id, token.start_marker)
        token = self.scanner.get()
        yield CollectionEndEvent(token.start_marker, token.end_marker)

    def parse_indentless_sequence(self):
        # (BLOCK-ENTRY block_node?)+
        while self.scanner.check(BlockEntryToken):
            token = self.scanner.get()
            if not self.scanner.check(BlockEntryToken,
                    KeyToken, ValueToken, BlockEndToken):
                for event in self.parse_block_node():
                    yield event
            else:
                yield self.process_empty_scalar(token.end_marker)
        token = self.scanner.peek()
        yield CollectionEndEvent(token.start_marker, token.start_marker)

    def parse_block_mapping(self):
        # BLOCK-MAPPING_START
        #   ((KEY block_node_or_indentless_sequence?)?
        #   (VALUE block_node_or_indentless_sequence?)?)*
        # BLOCK-END
        token = self.scanner.get()
        start_marker = token.start_marker
        while self.scanner.check(KeyToken, ValueToken):
            if self.scanner.check(KeyToken):
                token = self.scanner.get()
                if not self.scanner.check(KeyToken, ValueToken, BlockEndToken):
                    for event in self.parse_block_node_or_indentless_sequence():
                        yield event
                else:
                    yield self.process_empty_scalar(token.end_marker)
            if self.scanner.check(ValueToken):
                token = self.scanner.get()
                if not self.scanner.check(KeyToken, ValueToken, BlockEndToken):
                    for event in self.parse_block_node_or_indentless_sequence():
                        yield event
                else:
                    yield self.process_empty_scalar(token.end_marker)
            else:
                token = self.scanner.peek()
                yield self.process_empty_scalar(token.start_marker)
        if not self.scanner.check(BlockEndToken):
            token = self.scanner.peek()
            raise ParserError("while scanning a block mapping", start_marker,
                    "expected <block end>, but found %r" % token.id, token.start_marker)
        token = self.scanner.get()
        yield CollectionEndEvent(token.start_marker, token.end_marker)

    def parse_flow_sequence(self):
        # flow_sequence     ::= FLOW-SEQUENCE-START
        #                       (flow_sequence_entry FLOW-ENTRY)*
        #                       flow_sequence_entry?
        #                       FLOW-SEQUENCE-END
        # flow_sequence_entry   ::= flow_node | KEY flow_node? (VALUE flow_node?)?
        #
        # Note that while production rules for both flow_sequence_entry and
        # flow_mapping_entry are equal, their interpretations are different.
        # For `flow_sequence_entry`, the part `KEY flow_node? (VALUE flow_node?)?`
        # generate an inline mapping (set syntax).
        token = self.scanner.get()
        start_marker = token.start_marker
        while not self.scanner.check(FlowSequenceEndToken):
            if self.scanner.check(KeyToken):
                token = self.scanner.get()
                yield MappingEvent(None, u'!',
                        token.start_marker, token.end_marker)
                if not self.scanner.check(ValueToken,
                        FlowEntryToken, FlowSequenceEndToken):
                    for event in self.parse_flow_node():
                        yield event
                else:
                    yield self.process_empty_scalar(token.end_marker)
                if self.scanner.check(ValueToken):
                    token = self.scanner.get()
                    if not self.scanner.check(FlowEntryToken, FlowSequenceEndToken):
                        for event in self.parse_flow_node():
                            yield event
                    else:
                        yield self.process_empty_scalar(token.end_marker)
                else:
                    token = self.scanner.peek()
                    yield self.process_empty_scalar(token.start_marker)
                token = self.scanner.peek()
                yield CollectionEndEvent(token.start_marker, token.start_marker)
            else:
                for event in self.parse_flow_node():
                    yield event
            if not self.scanner.check(FlowEntryToken, FlowSequenceEndToken):
                token = self.scanner.peek()
                raise ParserError("while scanning a flow sequence", start_marker,
                        "expected ',' or ']', but got %r" % token.id, token.start_marker)
            if self.scanner.check(FlowEntryToken):
                self.scanner.get()
        token = self.scanner.get()
        yield CollectionEndEvent(token.start_marker, token.end_marker)

    def parse_flow_mapping(self):
        # flow_mapping      ::= FLOW-MAPPING-START
        #                       (flow_mapping_entry FLOW-ENTRY)*
        #                       flow_mapping_entry?
        #                       FLOW-MAPPING-END
        # flow_mapping_entry    ::= flow_node | KEY flow_node? (VALUE flow_node?)?
        token = self.scanner.get()
        start_marker = token.start_marker
        while not self.scanner.check(FlowMappingEndToken):
            if self.scanner.check(KeyToken):
                token = self.scanner.get()
                if not self.scanner.check(ValueToken,
                        FlowEntryToken, FlowMappingEndToken):
                    for event in self.parse_flow_node():
                        yield event
                else:
                    yield self.process_empty_scalar(token.end_marker)
                if self.scanner.check(ValueToken):
                    token = self.scanner.get()
                    if not self.scanner.check(FlowEntryToken, FlowMappingEndToken):
                        for event in self.parse_flow_node():
                            yield event
                    else:
                        yield self.process_empty_scalar(token.end_marker)
                else:
                    token = self.scanner.peek()
                    yield self.process_empty_scalar(token.start_marker)
            else:
                for event in self.parse_flow_node():
                    yield event
                yield self.process_empty_scalar(self.scanner.peek().start_marker)
            if not self.scanner.check(FlowEntryToken, FlowMappingEndToken):
                token = self.scanner.peek()
                raise ParserError("while scanning a flow mapping", start_marker,
                        "expected ',' or '}', but got %r" % token.id, token.start_marker)
            if self.scanner.check(FlowEntryToken):
                self.scanner.get()
        if not self.scanner.check(FlowMappingEndToken):
            token = self.scanner.peek()
            raise ParserError("while scanning a flow mapping", start_marker,
                    "expected '}', but found %r" % token.id, token.start_marker)
        token = self.scanner.get()
        yield CollectionEndEvent(token.start_marker, token.end_marker)

    def process_empty_scalar(self, marker):
        return ScalarEvent(None, None, u'', marker, marker)

