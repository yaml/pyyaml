
import unittest, os

from yaml.tokens import *
from yaml.events import *

class TestAppliance(unittest.TestCase):

    DATA = 'tests/data'

    all_tests = {}
    for filename in os.listdir(DATA):
        if os.path.isfile(os.path.join(DATA, filename)):
            root, ext = os.path.splitext(filename)
            all_tests.setdefault(root, []).append(ext)

    def add_tests(cls, method_name, *extensions):
        for test in cls.all_tests:
            available_extensions = cls.all_tests[test]
            for ext in extensions:
                if ext not in available_extensions:
                    break
            else:
                filenames = [os.path.join(cls.DATA, test+ext) for ext in extensions]
                def test_method(self, test=test, filenames=filenames):
                    getattr(self, '_'+method_name)(test, *filenames)
                test = test.replace('-', '_')
                try:
                    test_method.__name__ = '%s_%s' % (method_name, test)
                except TypeError:
                    import new
                    test_method = new.function(test_method.func_code, test_method.func_globals,
                            '%s_%s' % (method_name, test), test_method.func_defaults,
                            test_method.func_closure)
                setattr(cls, test_method.__name__, test_method)
    add_tests = classmethod(add_tests)

class Error(Exception):
    pass

class CanonicalScanner:

    def __init__(self, data):
        self.data = unicode(data, 'utf-8')+u'\0'
        self.index = 0

    def scan(self):
        #print self.data[self.index:]
        tokens = []
        tokens.append(StreamStartToken(None, None))
        while True:
            self.find_token()
            ch = self.data[self.index]
            if ch == u'\0':
                tokens.append(StreamEndToken(None, None))
                break
            elif ch == u'%':
                tokens.append(self.scan_directive())
            elif ch == u'-' and self.data[self.index:self.index+3] == u'---':
                self.index += 3
                tokens.append(DocumentStartToken(None, None))
            elif ch == u'[':
                self.index += 1
                tokens.append(FlowSequenceStartToken(None, None))
            elif ch == u'{':
                self.index += 1
                tokens.append(FlowMappingStartToken(None, None))
            elif ch == u']':
                self.index += 1
                tokens.append(FlowSequenceEndToken(None, None))
            elif ch == u'}':
                self.index += 1
                tokens.append(FlowMappingEndToken(None, None))
            elif ch == u'?':
                self.index += 1
                tokens.append(KeyToken(None, None))
            elif ch == u':':
                self.index += 1
                tokens.append(ValueToken(None, None))
            elif ch == u',':
                self.index += 1
                tokens.append(FlowEntryToken(None, None))
            elif ch == u'*' or ch == u'&':
                tokens.append(self.scan_alias())
            elif ch == u'!':
                tokens.append(self.scan_tag())
            elif ch == u'"':
                tokens.append(self.scan_scalar())
            else:
                raise Error("invalid token")
        return tokens

    DIRECTIVE = u'%YAML 1.1'

    def scan_directive(self):
        if self.data[self.index:self.index+len(self.DIRECTIVE)] == self.DIRECTIVE and \
                self.data[self.index+len(self.DIRECTIVE)] in u' \n\0':
            self.index += len(self.DIRECTIVE)
            return DirectiveToken('YAML', (1, 1), None, None)

    def scan_alias(self):
        if self.data[self.index] == u'*':
            TokenClass = AliasToken
        else:
            TokenClass = AnchorToken
        self.index += 1
        start = self.index
        while self.data[self.index] not in u', \n\0':
            self.index += 1
        value = self.data[start:self.index]
        return TokenClass(value, None, None)

    def scan_tag(self):
        self.index += 1
        start = self.index
        while self.data[self.index] not in u' \n\0':
            self.index += 1
        value = self.data[start:self.index]
        if value[0] == u'!':
            value = 'tag:yaml.org,2002:'+value[1:]
        elif value[0] == u'<' and value[-1] == u'>':
            value = value[1:-1]
        else:
            value = u'!'+value
        return TagToken(value, None, None)

    QUOTE_CODES = {
        'x': 2,
        'u': 4,
        'U': 8,
    }

    QUOTE_REPLACES = {
        u'\\': u'\\',
        u'\"': u'\"',
        u' ': u' ',
        u'a': u'\x07',
        u'b': u'\x08',
        u'e': u'\x1B',
        u'f': u'\x0C',
        u'n': u'\x0A',
        u'r': u'\x0D',
        u't': u'\x09',
        u'v': u'\x0B',
        u'N': u'\u0085',
        u'L': u'\u2028',
        u'P': u'\u2029',
        u'_': u'_',
        u'0': u'\x00',

    }

    def scan_scalar(self):
        self.index += 1
        chunks = []
        start = self.index
        ignore_spaces = False
        while self.data[self.index] != u'"':
            if self.data[self.index] == u'\\':
                ignore_spaces = False
                chunks.append(self.data[start:self.index])
                self.index += 1
                ch = self.data[self.index]
                self.index += 1
                if ch == u'\n':
                    ignore_spaces = True
                elif ch in self.QUOTE_CODES:
                    length = self.QUOTE_CODES[ch]
                    code = int(self.data[self.index:self.index+length], 16)
                    chunks.append(unichr(code))
                    self.index += length
                else:
                    chunks.append(self.QUOTE_REPLACES[ch])
                start = self.index
            elif self.data[self.index] == u'\n':
                chunks.append(self.data[start:self.index])
                chunks.append(u' ')
                self.index += 1
                start = self.index
                ignore_spaces = True
            elif ignore_spaces and self.data[self.index] == u' ':
                self.index += 1
                start = self.index
            else:
                ignore_spaces = False
                self.index += 1
        chunks.append(self.data[start:self.index])
        self.index += 1
        return ScalarToken(u''.join(chunks), False, None, None)

    def find_token(self):
        found = False
        while not found:
            while self.data[self.index] in u' \t':
                self.index += 1
            if self.data[self.index] == u'#':
                while self.data[self.index] != u'\n':
                    self.index += 1
            if self.data[self.index] == u'\n':
                self.index += 1
            else:
                found = True

class CanonicalParser:

    def __init__(self, data):
        self.scanner = CanonicalScanner(data)
        self.events = []

    # stream: STREAM-START document* STREAM-END
    def parse_stream(self):
        self.consume_token(StreamStartToken)
        self.events.append(StreamStartEvent(None, None))
        while not self.test_token(StreamEndToken):
            if self.test_token(DirectiveToken, DocumentStartToken):
                self.parse_document()
            else:
                raise Error("document is expected, got "+repr(self.tokens[self.index]))
        self.consume_token(StreamEndToken)
        self.events.append(StreamEndEvent(None, None))

    # document: DIRECTIVE? DOCUMENT-START node
    def parse_document(self):
        node = None
        if self.test_token(DirectiveToken):
            self.consume_token(DirectiveToken)
        self.consume_token(DocumentStartToken)
        self.events.append(DocumentStartEvent(None, None))
        self.parse_node()
        self.events.append(DocumentEndEvent(None, None))

    # node: ALIAS | ANCHOR? TAG? (SCALAR|sequence|mapping)
    def parse_node(self):
        if self.test_token(AliasToken):
            self.events.append(AliasEvent(self.get_value(), None, None))
        else:
            anchor = None
            if self.test_token(AnchorToken):
                anchor = self.get_value()
            tag = u'!'
            if self.test_token(TagToken):
                tag = self.get_value()
            if self.test_token(ScalarToken):
                self.events.append(ScalarEvent(anchor, tag, self.get_value(), None, None))
            elif self.test_token(FlowSequenceStartToken):
                self.events.append(SequenceStartEvent(anchor, tag, None, None))
                self.parse_sequence()
            elif self.test_token(FlowMappingStartToken):
                self.events.append(MappingStartEvent(anchor, tag, None, None))
                self.parse_mapping()
            else:
                raise Error("SCALAR, '[', or '{' is expected, got "+repr(self.tokens[self.index]))

    # sequence: SEQUENCE-START (node (ENTRY node)*)? ENTRY? SEQUENCE-END
    def parse_sequence(self):
        self.consume_token(FlowSequenceStartToken)
        if not self.test_token(FlowSequenceEndToken):
            self.parse_node()
            while not self.test_token(FlowSequenceEndToken):
                self.consume_token(FlowEntryToken)
                if not self.test_token(FlowSequenceEndToken):
                    self.parse_node()
        self.consume_token(FlowSequenceEndToken)
        self.events.append(SequenceEndEvent(None, None))

    # mapping: MAPPING-START (map_entry (ENTRY map_entry)*)? ENTRY? MAPPING-END
    def parse_mapping(self):
        self.consume_token(FlowMappingStartToken)
        if not self.test_token(FlowMappingEndToken):
            self.parse_map_entry()
            while not self.test_token(FlowMappingEndToken):
                self.consume_token(FlowEntryToken)
                if not self.test_token(FlowMappingEndToken):
                    self.parse_map_entry()
        self.consume_token(FlowMappingEndToken)
        self.events.append(MappingEndEvent(None, None))

    # map_entry: KEY node VALUE node
    def parse_map_entry(self):
        self.consume_token(KeyToken)
        self.parse_node()
        self.consume_token(ValueToken)
        self.parse_node()

    def test_token(self, *choices):
        for choice in choices:
            if isinstance(self.tokens[self.index], choice):
                return True
        return False

    def consume_token(self, cls):
        if not isinstance(self.tokens[self.index], cls):
            raise Error("unexpected token "+repr(self.tokens[self.index]))
        self.index += 1

    def get_value(self):
        value = self.tokens[self.index].value
        self.index += 1
        return value

    def parse(self):
        self.tokens = self.scanner.scan()
        self.index = 0
        self.parse_stream()
        return self.events

    def get(self):
        return self.events.pop(0)

    def check(self, *choices):
        for choice in choices:
            if isinstance(self.events[0], choice):
                return True
        return False

    def peek(self):
        return self.events[0]

