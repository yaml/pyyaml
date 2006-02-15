
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

class Parser:

    def parse(self, source, data):
        scanner = Scanner()
        self.tokens = scanner.scan(source, data)
        self.tokens.append('END')
        documents = self.parse_stream()
        if len(documents) == 1:
            return documents[0]
        return documents

    def parse_stream(self):
        documents = []
        if self.tokens[0] not in ['DIRECTIVE', 'DOCUMENT_START', 'END']:
            documents.append(self.parse_block_node())
        while self.tokens[0] != 'END':
            while self.tokens[0] == 'DIRECTIVE':
                self.tokens.pop(0)
            if self.tokens[0] != 'DOCUMENT_START':
                self.error('DOCUMENT_START is expected')
            self.tokens.pop(0)
            if self.tokens[0] in ['DIRECTIVE', 'DOCUMENT_START', 'DOCUMENT_END', 'END']:
                documents.append(None)
            else:
                documents.append(self.parse_block_node())
            while self.tokens[0] == 'DOCUMENT_END':
                self.tokens.pop(0)
        if self.tokens[0] != 'END':
            self.error("END is expected")
        return tuple(documents)

    def parse_block_node(self):
        if self.tokens[0] == 'ALIAS':
            self.tokens.pop(0)
            return '*'
        if self.tokens[0] == 'TAG':
            self.tokens.pop(0)
            if self.tokens[0] == 'ANCHOR':
                self.tokens.pop(0)
        elif self.tokens[0] == 'ANCHOR':
            self.tokens.pop(0)
            if self.tokens[0] == 'TAG':
                self.tokens.pop(0)
        return self.parse_block_content()

    def parse_flow_node(self):
        if self.tokens[0] == 'ALIAS':
            self.tokens.pop(0)
            return '*'
        if self.tokens[0] == 'TAG':
            self.tokens.pop(0)
            if self.tokens[0] == 'ANCHOR':
                self.tokens.pop(0)
        elif self.tokens[0] == 'ANCHOR':
            self.tokens.pop(0)
            if self.tokens[0] == 'TAG':
                self.tokens.pop(0)
        return self.parse_flow_content()

    def parse_block_node_or_indentless_sequence(self):
        if self.tokens[0] == 'ALIAS':
            self.tokens.pop(0)
            return '*'
        if self.tokens[0] == 'TAG':
            self.tokens.pop(0)
            if self.tokens[0] == 'ANCHOR':
                self.tokens.pop(0)
        elif self.tokens[0] == 'ANCHOR':
            self.tokens.pop(0)
            if self.tokens[0] == 'TAG':
                self.tokens.pop(0)
        if self.tokens[0] == 'ENTRY':
            return self.parse_indentless_sequence(self)
        return self.parse_block_content()

    def parse_block_content(self):
        if self.tokens[0] == 'SCALAR':
            self.tokens.pop(0)
            return True
        elif self.tokens[0] == 'BLOCK_SEQ_START':
            return self.parse_block_sequence()
        elif self.tokens[0] == 'BLOCK_MAP_START':
            return self.parse_block_mapping()
        elif self.tokens[0] == 'FLOW_SEQ_START':
            return self.parse_flow_sequence()
        elif self.tokens[0] == 'FLOW_MAP_START':
            return self.parse_flow_mapping()
        else:
            self.error('block content is expected')

    def parse_flow_content(self):
        if self.tokens[0] == 'SCALAR':
            self.tokens.pop(0)
            return True
        elif self.tokens[0] == 'FLOW_SEQ_START':
            return self.parse_flow_sequence()
        elif self.tokens[0] == 'FLOW_MAP_START':
            return self.parse_flow_mapping()
        else:
            self.error('flow content is expected')

    def parse_block_sequence(self):
        sequence = []
        if self.tokens[0] != 'BLOCK_SEQ_START':
            self.error('BLOCK_SEQ_START is expected')
        self.tokens.pop(0)
        while self.tokens[0] == 'ENTRY':
            self.tokens.pop(0)
            if self.tokens[0] not in ['ENTRY', 'BLOCK_END']:
                sequence.append(self.parse_block_node())
            else:
                sequence.append(None)
        if self.tokens[0] != 'BLOCK_END':
            self.error('BLOCK_END is expected')
        self.tokens.pop(0)
        return sequence

    def parse_indentless_sequence(self):
        sequence = []
        while self.tokens[0] == 'ENTRY':
            self.tokens.pop(0)
            if self.tokens[0] not in ['ENTRY']:
                sequence.append(self.parse_block_node())
            else:
                sequence.append(None)
        return sequence

    def parse_block_mapping(self):
        mapping = []
        if self.tokens[0] != 'BLOCK_MAP_START':
            self.error('BLOCK_MAP_START is expected')
        self.tokens.pop(0)
        while self.tokens[0] in ['KEY', 'VALUE']:
            key = None
            value = None
            if self.tokens[0] == 'KEY':
                self.tokens.pop(0)
                if self.tokens[0] not in ['KEY', 'VALUE', 'BLOCK_END']:
                    key = self.parse_block_node_or_indentless_sequence()
            if self.tokens[0] == 'VALUE':
                self.tokens.pop(0)
                if self.tokens[0] not in ['KEY', 'VALUE', 'BLOCK_END']:
                    value = self.parse_block_node_or_indentless_sequence()
            mapping.append((key, value))
        if self.tokens[0] != 'BLOCK_END':
            self.error('BLOCK_END is expected')
        self.tokens.pop(0)
        return mapping

    def parse_flow_sequence(self):
        sequence = []
        if self.tokens[0] != 'FLOW_SEQ_START':
            self.error('FLOW_SEQ_START is expected')
        self.tokens.pop(0)
        while self.tokens[0] != 'FLOW_SEQ_END':
            if self.tokens[0] == 'KEY':
                self.tokens.pop(0)
                key = None
                value = None
                if self.tokens[0] != 'VALUE':
                    key = self.parse_flow_node()
                if self.tokens[0] == 'VALUE':
                    self.tokens.pop(0)
                    if self.tokens[0] not in ['ENTRY', 'FLOW_SEQ_END']:
                        value = self.parse_flow_node()
                sequence.append([(key, value)])
            else:
                sequence.append(self.parse_flow_node())
            if self.tokens[0] not in ['ENTRY', 'FLOW_SEQ_END']:
                self.error("ENTRY or FLOW_SEQ_END is expected")
            if self.tokens[0] == 'ENTRY':
                self.tokens.pop(0)
        if self.tokens[0] != 'FLOW_SEQ_END':
            self.error('FLOW_SEQ_END is expected')
        self.tokens.pop(0)
        return sequence

    def parse_flow_mapping(self):
        mapping = []
        if self.tokens[0] != 'FLOW_MAP_START':
            self.error('FLOW_MAP_START is expected')
        self.tokens.pop(0)
        while self.tokens[0] != 'FLOW_MAP_END':
            if self.tokens[0] == 'KEY':
                self.tokens.pop(0)
                key = None
                value = None
                if self.tokens[0] != 'VALUE':
                    key = self.parse_flow_node()
                if self.tokens[0] == 'VALUE':
                    self.tokens.pop(0)
                    if self.tokens[0] not in ['ENTRY', 'FLOW_MAP_END']:
                        value = self.parse_flow_node()
                mapping.append((key, value))
            else:
                mapping.append((self.parse_flow_node(), None))
            if self.tokens[0] not in ['ENTRY', 'FLOW_MAP_END']:
                self.error("ENTRY or FLOW_MAP_END is expected")
            if self.tokens[0] == 'ENTRY':
                self.tokens.pop(0)
        if self.tokens[0] != 'FLOW_MAP_END':
            self.error('FLOW_MAP_END is expected')
        self.tokens.pop(0)
        return mapping

    def error(self, message):
        raise Error(message+': '+str(self.tokens))


