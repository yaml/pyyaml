
# Production rules:
# stream            ::= implicit_document? explicit_document* END
# explicit_document ::= DIRECTIVE* DOCUMENT-START block_node? DOCUMENT-END?
# implicit_document ::= block_node DOCUMENT-END?
# block_node    ::= ALIAS | properties? block_content
# flow_node     ::= ALIAS | properties? flow_content
# properties    ::= TAG ANCHOR? | ANCHOR TAG?
# block_content     ::= block_collection | flow_collection | SCALAR
# flow_content      ::= flow_collection | SCALAR
# block_collection  ::= block_sequence | block_mapping
# block_sequence    ::= BLOCK-SEQUENCE-START (ENTRY block_node?)* BLOCK-END
# block_mapping     ::= BLOCK-MAPPING_START ((KEY block_node_or_indentless_sequence?)? (VALUE block_node_or_indentless_sequence?)?)* BLOCK-END
# block_node_or_indentless_sequence ::= ALIAS | properties? (block_content | indentless_block_sequence)
# indentless_block_sequence         ::= (ENTRY block_node?)+
# flow_collection   ::= flow_sequence | flow_mapping
# flow_sequence     ::= FLOW-SEQUENCE-START (flow_sequence_entry ENTRY)* flow_sequence_entry? FLOW-SEQUENCE-END
# flow_mapping      ::= FLOW-MAPPING-START flow_mapping_entry ENTRY)* flow_mapping_entry? FLOW-MAPPING-END
# flow_sequence_entry   ::= flow_node | KEY flow_node (VALUE flow_node?)?
# flow_mapping_entry    ::= flow_node | KEY flow_node (VALUE flow_node?)?

# FIRST(rule) sets:
# stream: {}
# explicit_document: { DIRECTIVE DOCUMENT-START }
# implicit_document: block_node
# block_node: { ALIAS TAG ANCHOR SCALAR BLOCK-SEQUENCE-START BLOCK-MAPPING-START FLOW-SEQUENCE-START FLOW-MAPPING-START }
# flow_node: { ALIAS ANCHOR TAG SCALAR FLOW-SEQUENCE-START FLOW-MAPPING-START }
# block_content: { BLOCK-SEQUENCE-START BLOCK-MAPPING-START FLOW-SEQUENCE-START FLOW-MAPPING-START SCALAR }
# flow_content: { FLOW-SEQUENCE-START FLOW-MAPPING-START SCALAR }
# block_collection: { BLOCK-SEQUENCE-START BLOCK-MAPPING-START }
# flow_collection: { FLOW-SEQUENCE-START FLOW-MAPPING-START }
# block_sequence: { BLOCK-SEQUENCE-START }
# block_mapping: { BLOCK-MAPPING-START }
# block_node_or_indentless_sequence: { ALIAS ANCHOR TAG SCALAR BLOCK-SEQUENCE-START BLOCK-MAPPING-START FLOW-SEQUENCE-START FLOW-MAPPING-START ENTRY }
# indentless_sequence: { ENTRY }
# flow_collection: { FLOW-SEQUENCE-START FLOW-MAPPING-START }
# flow_sequence: { FLOW-SEQUENCE-START }
# flow_mapping: { FLOW-MAPPING-START }
# flow_sequence_entry: { ALIAS ANCHOR TAG SCALAR FLOW-SEQUENCE-START FLOW-MAPPING-START KEY }
# flow_mapping_entry: { ALIAS ANCHOR TAG SCALAR FLOW-SEQUENCE-START FLOW-MAPPING-START KEY }

from error import YAMLError
from tokens import *

class ParserError(YAMLError):
    pass

class Node:
    def __repr__(self):
        args = []
        for attribute in ['anchor', 'tag', 'value']:
            if hasattr(self, attribute):
                args.append(repr(getattr(self, attribute)))
        return "%s(%s)" % (self.__class__.__name__, ', '.join(args))

class AliasNode(Node):
    def __init__(self, anchor):
        self.anchor = anchor

class ScalarNode(Node):
    def __init__(self, anchor, tag, value):
        self.anchor = anchor
        self.tag = tag
        self.value = value

class SequenceNode(Node):
    def __init__(self, anchor, tag, value):
        self.anchor = anchor
        self.tag = tag
        self.value = value

class MappingNode(Node):
    def __init__(self, anchor, tag, value):
        self.anchor = anchor
        self.tag = tag
        self.value = value

class Parser:

    def __init__(self, scanner):
        self.scanner = scanner

    def is_token(self, *choices):
        token = self.scanner.peek_token()
        for choice in choices:
            if isinstance(token, choices):
                return True
        return False

    def get_token(self):
        return self.scanner.get_token()

    def parse(self):
        return self.parse_stream()

    def parse_stream(self):
        documents = []
        if not self.is_token(DirectiveToken, DocumentStartToken, EndToken):
            documents.append(self.parse_block_node())
        while not self.is_token(EndToken):
            while self.is_token(DirectiveToken):
                self.get_token()
            if not self.is_token(DocumentStartToken):
                self.fail('DOCUMENT-START is expected')
            self.get_token()
            if self.is_token(DirectiveToken,
                    DocumentStartToken, DocumentEndToken, EndToken):
                documents.append(None)
            else:
                documents.append(self.parse_block_node())
            while self.is_token(DocumentEndToken):
                self.get_token()
        if not self.is_token(EndToken):
            self.fail("END is expected")
        return documents

    def parse_block_node(self):
        return self.parse_node(block=True)

    def parse_flow_node(self):
        return self.parse_node()

    def parse_block_node_or_indentless_sequence(self):
        return self.parse_node(block=True, indentless_sequence=True)

    def parse_node(self, block=False, indentless_sequence=False):
        if self.is_token(AliasToken):
            token = self.get_token()
            return AliasNode(token.value)
        anchor = None
        tag = None
        if self.is_token(AnchorToken):
            anchor = self.get_token().value
            if self.is_token(TagToken):
                tag = self.get_token().value
        elif self.is_token(TagToken):
            tag = self.get_token().value
            if self.is_token(AnchorToken):
                anchor = self.get_token().value
        if indentless_sequence and self.is_token(EntryToken):
            NodeClass = SequenceNode
            value = self.parse_indentless_sequence()
        else:
            if self.is_token(ScalarToken):
                NodeClass = ScalarNode
            elif self.is_token(BlockSequenceStartToken, FlowSequenceStartToken):
                NodeClass = SequenceNode
            elif self.is_token(BlockMappingStartToken, FlowMappingStartToken):
                NodeClass = MappingNode
            if block:
                value = self.parse_block_content()
            else:
                value = self.parse_flow_content()
        return NodeClass(anchor, tag, value)

    def parse_block_content(self):
        if self.is_token(ScalarToken):
            return self.get_token().value
        elif self.is_token(BlockSequenceStartToken):
            return self.parse_block_sequence()
        elif self.is_token(BlockMappingStartToken):
            return self.parse_block_mapping()
        elif self.is_token(FlowSequenceStartToken):
            return self.parse_flow_sequence()
        elif self.is_token(FlowMappingStartToken):
            return self.parse_flow_mapping()
        else:
            self.fail('block content is expected')

    def parse_flow_content(self):
        if self.is_token(ScalarToken):
            return self.get_token().value
        elif self.is_token(FlowSequenceStartToken):
            return self.parse_flow_sequence()
        elif self.is_token(FlowMappingStartToken):
            return self.parse_flow_mapping()
        else:
            self.fail('flow content is expected')

    def parse_block_sequence(self):
        sequence = []
        if not self.is_token(BlockSequenceStartToken):
            self.fail('BLOCK-SEQUENCE-START is expected')
        self.get_token()
        while self.is_token(EntryToken):
            self.get_token()
            if not self.is_token(EntryToken, BlockEndToken):
                sequence.append(self.parse_block_node())
            else:
                sequence.append(None)
        if not self.is_token(BlockEndToken):
            self.fail('BLOCK-END is expected')
        self.get_token()
        return sequence

    def parse_indentless_sequence(self):
        sequence = []
        while self.is_token(EntryToken):
            self.get_token()
            if not self.is_token(EntryToken):
                sequence.append(self.parse_block_node())
            else:
                sequence.append(None)
        return sequence

    def parse_block_mapping(self):
        mapping = []
        if not self.is_token(BlockMappingStartToken):
            self.fail('BLOCK-MAPPING-START is expected')
        self.get_token()
        while self.is_token(KeyToken, ValueToken):
            key = None
            value = None
            if self.is_token(KeyToken):
                self.get_token()
                if not self.is_token(KeyToken, ValueToken, BlockEndToken):
                    key = self.parse_block_node_or_indentless_sequence()
            if self.is_token(ValueToken):
                self.get_token()
                if not self.is_token(KeyToken, ValueToken, BlockEndToken):
                    value = self.parse_block_node_or_indentless_sequence()
            mapping.append((key, value))
        if not self.is_token(BlockEndToken):
            self.fail('BLOCK-END is expected')
        self.get_token()
        return mapping

    def parse_flow_sequence(self):
        sequence = []
        if not self.is_token(FlowSequenceStartToken):
            self.fail('FLOW-SEQUENCE-START is expected')
        self.get_token()
        while not self.is_token(FlowSequenceEndToken):
            if self.is_token(KeyToken):
                self.get_token()
                key = None
                value = None
                if not self.is_token(ValueToken):
                    key = self.parse_flow_node()
                if self.is_token(ValueToken):
                    self.get_token()
                    if not self.is_token(EntryToken, FlowSequenceEndToken):
                        value = self.parse_flow_node()
                node = MappingNode(None, None, [(key, value)])
                sequence.append(node)
            else:
                sequence.append(self.parse_flow_node())
            if not self.is_token(EntryToken, FlowSequenceEndToken):
                self.fail("ENTRY or FLOW-SEQUENCE-END are expected")
            if self.is_token(EntryToken):
                self.get_token()
        if not self.is_token(FlowSequenceEndToken):
            self.fail('FLOW-SEQUENCE-END is expected')
        self.get_token()
        return sequence

    def parse_flow_mapping(self):
        mapping = []
        if not self.is_token(FlowMappingStartToken):
            self.fail('FLOW-MAPPING-START is expected')
        self.get_token()
        while not self.is_token(FlowMappingEndToken):
            if self.is_token(KeyToken):
                self.get_token()
                key = None
                value = None
                if not self.is_token(ValueToken):
                    key = self.parse_flow_node()
                if self.is_token(ValueToken):
                    self.get_token()
                    if not self.is_token(EntryToken, FlowMappingEndToken):
                        value = self.parse_flow_node()
                mapping.append((key, value))
            else:
                mapping.append((self.parse_flow_node(), None))
            if not self.is_token(EntryToken, FlowMappingEndToken):
                self.fail("ENTRY or FLOW-MAPPING-END are expected")
            if self.is_token(EntryToken):
                self.get_token()
        if not self.is_token(FlowMappingEndToken):
            self.fail('FLOW-MAPPING-END is expected')
        self.get_token()
        return mapping

    def fail(self, message):
        marker = self.scanner.peek_token().start_marker
        raise Error(message+':\n'+marker.get_snippet())

