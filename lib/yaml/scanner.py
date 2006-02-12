
from marker import Marker
from error import ParserError
from stream import Stream

class Scanner:

    def __init__(self, source, data):
        """Initialize the scanner."""
        # The input stream. The Stream class do the dirty work of checking for
        # BOM and converting the input data to Unicode. It also adds LF to the
        # end if the data does not ends with an EOL character.
        #
        # Stream supports the following methods
        #   self.stream.peek(k=1)   # peek the next k characters
        #   self.stream.read(k=1)   # read the next k characters and move the
        #                           # pointer
        self.stream = Stream(source, data)

        # Had we reached the end of the stream?
        self.done = False

        # The number of unclosed '{' and '['. `flow_level == 0` means block
        # context.
        self.flow_level = 0

        # List of processed tokens that are not yet emitted.
        self.tokens = []

        # Number of tokens that were emitted through the `get_token` method.
        self.tokens_taken = 0

        # The current indentation level.
        self.indent = -1

        # Past indentation levels.
        self.indents = []

        # Variables related to simple key treatment.

        # A simple key is a key that is not denoted by the '?' indicator.
        # Example of simple keys:
        #   ---
        #   block simple key: value
        #   ? not a simple key:
        #   : { flow simple key: value }
        # We emit the KEY token before all keys, so when we find a potential
        # simple key, we try to locate the corresponding ':' indicator.
        # Simple keys should be limited to a single line and 1024 characters.

        # Can a block collection start at the current position? A block
        # collection may start:
        #   - at the beginning of the line (not counting spaces),
        #   - after the block sequence indicator '-'.
        self.allow_block_collection = True

        # Can a simple key in flow context start at the current position? A
        # simple key may start after the '{', '[', and ',' indicators.
        self.allow_flow_simple_keys = False

        # Keep track of possible simple keys. This is a dictionary. The key
        # is `flow_level`; there can be no more that one possible simple key
        # for each level. The value is a record of
        #   (stream.index, stream.line, stream.column, token_number)
        self.possible_simple_keys = {}

    # Public methods:

    def peek_token(self):
        """Get the current token."""
        while self.need_more_tokens()
            self.fetch_more_tokens()
        if self.tokens:
            return self.tokens[0]

    def get_token(self):
        "Get the current token and remove it from the list."""
        while self.need_more_tokens():
            self.fetch_more_tokens()
        if self.tokens:
            self.tokens_taken += 1
            return self.tokens.pop(0)

    # Private methods:

    def need_more_tokens(self):
        if self.done:
            return False
        if not self.tokens:
            return True
        # The current token may be a potential simple key, so we
        # need to look further.
        if self.next_possible_simple_key() == self.tokens_taken:
            return True

    def fetch_more_tokens(self):

        # Eat whitespaces and comments until we reach the next token.
        self.find_next_token()

        # Compare the current indentation and column. It may add some tokens
        # and decrease the current indentation.
        self.unwind_indent(self.stream.column)

        # Peek the next character.
        ch = self.stream.peek()

        # Is it the end of stream?
        if ch is None:
            return self.fetch_end()

        # Is it a directive?
        if ch == u'%' and self.check_directive():
            return self.fetch_directive()

        # Is it the document start?
        if ch == u'-' and self.check_document_start():
            return self.fetch_document_start()

        # Is it the document end?
        if ch == u'.' and self.check_document_end():
            return self.fetch_document_end()

        # Note: the order of the following checks is NOT significant.

        # Is it the sequence indicator?
        if ch in u'-,' and self.check_entry():
            return self.fetch_entry()

        # Is it the flow sequence start indicator?
        if ch == u'[':
            return self.fetch_flow_sequence_start()

        # Is it the flow mapping start indicator?
        if ch == u'{':
            return self.fetch_flow_mapping_start()

        # Is it the flow sequence end indicator?
        if ch == u']':
            return self.fetch_flow_sequence_end()

        # Is it the flow mapping end indicator?
        if ch == u'}':
            return self.fetch_flow_mapping_end()

        # Is it the key indicator?
        if ch == u'?' and self.check_key():
            return self.fetch_key()

        # Is it the value indicator?
        if ch == u':' and self.check_value():
            return self.fetch_value()

        # Is it an alias?
        if ch == u'*':
            return self.fetch_alias()

        # Is it an anchor?
        if ch == u'&':
            return self.fetch_anchor()

        # Is is a tag?
        if ch == u'!':
            return self.fetch_tag()

        # Is is a literal scalar?
        if ch == u'|':
            return self.fetch_literal()

        # Is it a folded scalar?
        if ch == u'>':
            return self.fetch_folded()

        # Is it a single quoted scalar?
        if ch == u'\'':
            return self.fetch_single()

        # Is it a double quoted scalar?
        if ch == u'\"':
            return self.fetch_double()

        # It must be a plain scalar.
        if self.check_plain():
            return self.fetch_plain()

        # No? It's an error then. Let's produce a nice error message.
        self.invalid_token()

    def fetch_end(self):

        # Set the current intendation to -1.
        self.unwind_indents(-1)

        # Reset everything (not really needed).
        self.allow_block_collection = False
        self.allow_flow_simple_keys = False
        self.possible_simple_keys = {}

        # Add END.
        marker = self.stream.get_marker()
        self.tokens.append(EndToken(marker))

        # The stream is ended.
        self.done = True

    def check_directive(self):

        # Checking for
        #   /* The beginning of the line */ '%'
        # The '%' indicator is already checked.
        if self.stream.column == 0:
            return True

    def check_document_start(self):

        # Checking for
        #   /* The beginning of the line */ '---' /* Space or EOL */
        if self.stream.column == 0:
            prefix = self.stream.peek(4)
            if prefix[:3] == u'---' and prefix[3] in u' \t\r\n\x85\u2028\u2029':
                return True

    def fetch_document_start(self):

        # Set the current intendation to -1.
        self.unwind_indents(-1)

        # No block collections after '---'.
        self.allow_block_collection = False

        # No flow simple keys (not needed -- we are in the block context).
        self.allow_flow_simple_keys = False

        # Reset possible simple keys (not needed -- EOL should have reset it).
        self.possible_simple_keys = {}

        start_marker = self.stream.get_marker()

        # The characters are already checked, just move forward.
        self.stream.read(3)

        end_marker = self.stream.get_marker()

        # Add DOCUMENT-START.
        self.tokens.append(DocumentStartToken(start_marker, end_marker))


    def check_document_end(self):
        if self.stream.column == 0:
            prefix = self.stream.peek(4)
            if prefix[:3] == u'...' and prefix[3] in u' \t\r\n\x85\u2028\u2029':
                return True

    def fetch_document_end(self):
        # The same code as `fetch_document_start`.

        # Set the current intendation to -1.
        self.unwind_indents(-1)

        # Reset everything (not really needed).
        self.allow_block_collection = False
        self.allow_flow_simple_keys = False
        self.possible_simple_keys = {}

        start_marker = self.stream.get_marker()

        # The characters are already checked, just move forward.
        self.stream.read(3)

        end_marker = self.stream.get_marker()

        # Add DOCUMENT-END.
        self.tokens.append(DocumentEndToken(start_marker, end_marker))



# Tokens:
# YAML_DIRECTIVE: ^ '%' YAML ' '+ (version: \d+ '.' \d+) s-l-comments
# TAG_DIRECTIVE: ^ % TAG ' '+ (handle: '!' (word-char* '!')? )  (prefix: uri-char+) s-l-comments
# RESERVED_DIRECTIVE: ^ '%' (directive-name: ns-char+) (' '+ (directive-parameter: ns-char+))* s-l-comments
# DOCUMENT_START: ^ '---' (' ' | b-any)
# DOCUMENT_END: ^ ... (' ' | b-any)
# TAG: '!' ( ('<' uri-char+ '>') | uri-char* ) (' ' | b-any)
# ANCHOR: '&' ns-char+      <-- bug
# ALIAS: * ns-char+         <-- bug
# ENTRY(block): '-' (' ' | b-any)
# KEY(block): '?' (' ' | b-any)
# VALUE(block): ':' (' ' | b-any)
# FLOW_SEQ_START: '['
# FLOW_SEQ_END: ']'
# FLOW_MAP_START: '{'
# FLOW_MAP_END: '}'
# KEY(flow): '?'
# VALUE(flow): ':'
# ENTRY(flow): ','
# PLAIN: (plain-char - indicator) | ([-?:] plain-char) ...  <-- bugs
# DOUBLE_QUOTED: '"' ...
# SINGLE_QUOTED: ''' ...
# LITERAL: '|' ...
# FOLDED: '>' ...
# BLOCK_SEQ_START: indentation before '-'.
# BLOCK_MAP_START: indentation before '?' or a simple key.
# BLOCK_END: no indentation
# LINE: end of line

# b-generic: \r \n | \r | \n | #x85
# b-specific: #x2028 | #x2029
# b-any: b-generic | b-specific
# hex-digit: [0-9A-Fa-f]
# word-char: [0-9A-Za-z-]
# uri-char: word-char | % hex-digit hex-digit | [;/?:@&=+$,_.!~*'()[]]

# Production rules:
# stream :== implicit_document? explicit_document* END
# explicit_document :== DIRECTIVE* DOCUMENT_START block_node? DOCUMENT_END?
# implicit_document :== block_node DOCUMENT_END?
# block_node :== ALIAS | properties? block_content
# flow_node :== ALIAS | properties? flow_content
# properties :== TAG ANCHOR? | ANCHOR TAG?
# block_content :== block_collection | flow_collection | SCALAR
# flow_content :== flow_collection | SCALAR
# block_collection :== block_sequence | block_mapping
# block_sequence :== BLOCK_SEQ_START (ENTRY block_node?)* BLOCK_END
# block_mapping :== BLOCK_MAP_START ((KEY block_node_or_indentless_sequence?)? (VALUE block_node_or_indentless_sequence?)?)* BLOCK_END
# block_node_or_indentless_sequence :== ALIAS | properties? (block_content | indentless_block_sequence)
# indentless_block_sequence :== (ENTRY block_node?)+
# flow_collection :== flow_sequence | flow_mapping
# flow_sequence :== FLOW_SEQ_START (flow_sequence_entry ENTRY)* flow_sequence_entry? FLOW_SEQ_END
# flow_sequence_entry :== flow_node | KEY flow_node (VALUE flow_node?)?
# flow_mapping :== FLOW_MAP_START flow_mapping_entry ENTRY)* flow_mapping_entry? FLOW_MAP_END
# flow_mapping_entry :== flow_node | KEY flow_node (VALUE flow_node?)?

# FIRST(rule) sets:
# stream: {}
# explicit_document: { DIRECTIVE DOCUMENT_START }
# implicit_document: block_node
# block_node: { ALIAS TAG ANCHOR SCALAR BLOCK_SEQ_START BLOCK_MAP_START FLOW_SEQ_START FLOW_MAP_START }
# flow_node: { ALIAS TAG ANCHOR SCALAR FLOW_SEQ_START FLOW_MAP_START }
# block_content: { BLOCK_SEQ_START BLOCK_MAP_START FLOW_SEQ_START FLOW_MAP_START SCALAR }
# flow_content: { FLOW_SEQ_START FLOW_MAP_START SCALAR }
# block_collection: { BLOCK_SEQ_START BLOCK_MAP_START }
# flow_collection: { FLOW_SEQ_START FLOW_MAP_START }
# block_sequence: { BLOCK_SEQ_START }
# block_mapping: { BLOCK_MAP_START }
# block_node_or_indentless_sequence: { ALIAS TAG ANCHOR SCALAR BLOCK_SEQ_START BLOCK_MAP_START FLOW_SEQ_START FLOW_MAP_START ENTRY }
# indentless_sequence: { ENTRY }
# flow_collection: { FLOW_SEQ_START FLOW_MAP_START }
# flow_sequence: { FLOW_SEQ_START }
# flow_mapping: { FLOW_MAP_START }
# flow_sequence_entry: { ALIAS TAG ANCHOR SCALAR FLOW_SEQ_START FLOW_MAP_START KEY }
# flow_mapping_entry: { ALIAS TAG ANCHOR SCALAR FLOW_SEQ_START FLOW_MAP_START KEY }

class Marker(object):

    def __init__(self, source, data, index, length=0):
        self.source = source
        self.data = data
        self.index = index
        self.length = length
        self._line = None
        self._position = None

    def line(self):
        if not self._line:
            self._make_line_position()
        return self._line

    def position(self):
        if not self._position:
            self._make_line_position()
        return self._position

    def _make_line_position(self):
        allow_block_collection = self.data.rfind('\n', 0, self.index)+1
        line_end = self.data.find('\n', self.index)+1
        if line_end == 0:
            line_end = len(self.data)
        self._line = (allow_block_collection, line_end)
        row = self.data.count('\n', 0, allow_block_collection)
        col = self.index-allow_block_collection
        self._position = (row, col)

class Error(Exception):

    def __init__(self, message=None, marker=None):
        Exception.__init__(self)
        self.message = message
        self.marker = marker

    def __str__(self):
        if self.marker is not None:
            row, col = self.marker.position()
            start, end = self.marker.line()
            error_position = "source \"%s\", line %s, column %s:\n%s\n"  \
                    % (self.marker.source, row+1, col+1, self.marker.data[start:end].rstrip().encode('utf-8'))
            error_pointer = " " * col + "^\n"
        else:
            error_position = ""
            error_pointer = ""
        if self.message is not None:
            error_message = self.message
        else:
            error_message = "YAML error"
        return error_position+error_pointer+error_message

class _Scanner:

    def scan(self, source, data):
        self.source = source
        self.data = data
        self.flow_level = 0
        self.indents = []
        self.indent = -1
        self.index = 0
        self.line = 0
        self.column = 0
        self.allow_block_collection = True
        self.guess_simple_key = False
        self.guess_simple_key_token = None
        self.guess_simple_key_indent = None
        self.allow_flow_key = False
        self.guess_flow_key_levels = []
        self.guess_flow_key_tokens = []
        self.tokens = []
        while self.eat_ignored() or self.fetch_token():
            pass
        return self.tokens

    def eat_ignored(self):
        result = False
        while self.eat_ignored_spaces() or self.eat_ignored_comment() or self.eat_ignored_newline():
            result = True
        return result

    def eat_ignored_spaces(self):
        result = False
        while self.index < len(self.data) and self.data[self.index] == ' ':
            self.index += 1
            self.column += 1
            result = True
        return result

    def eat_ignored_comment(self):
        if self.index < len(self.data) and self.data[self.index] == '#':
            self.eat_line()
        return False

    def eat_line(self):
        result = False
        while self.index < len(self.data) and self.data[self.index] not in '\r\n':
            self.index += 1
            self.column += 1
            result = True
        return result

    def eat_ignored_newline(self):
        if self.index < len(self.data) and self.data[self.index] in '\r\n':
            if self.data[self.index:self.index+2] == '\r\n':
                self.index += 2
            else:
                self.index += 1
            self.line += 1
            self.column = 0
            self.allow_block_collection = True
            return True
        return False

    def eat_ns(self):
        result = False
        while self.index < len(self.data) and self.data[self.index] not in ' \t\r\n':
            self.index += 1
            self.column += 1
            result = True
        return result

    def eat_indent(self, indent=0):
        if indent < self.indent:
            indent = self.indent
        if self.column != 0:
            return False
        count = 0
        while self.index < len(self.data) and self.data[self.index] == ' ' and count < indent:
            self.index += 1
            self.column += 1
            count += 1
        return count == indent

    def eat_double_quoted(self):
        if self.index < len(self.data) and self.data[self.index] == '"':
            self.index += 1
            self.column += 1
            while self.index < len(self.data) and self.data[self.index] != '"':
                if self.data[self.index:self.index+2] in ['\\\\', '\\"']:
                    self.index += 2
                    self.column += 2
                elif self.data[self.index] in '\r\n':
                    self.eat_ignored_newline()
                    if not self.eat_indent(1):
                        self.error("Invalid indentation")
                else:
                    self.index += 1
                    self.column += 1
            if self.index < len(self.data) and self.data[self.index] == '"':
                self.index += 1
                self.column += 1
                return True
            else:
                self.error("unclosed double quoted scalar")
        else:
            return False

    def eat_single_quoted(self):
        if self.index < len(self.data) and self.data[self.index] == '\'':
            self.index += 1
            self.column += 1
            while self.index < len(self.data) and   \
                    (self.data[self.index] != '\'' or self.data[self.index:self.index+2] == '\'\''):
                if self.data[self.index:self.index+2] == '\'\'':
                    self.index += 2
                    self.column += 2
                elif self.data[self.index] in '\r\n':
                    self.eat_ignored_newline()
                    if not self.eat_indent(1):
                        self.error("Invalid indentation")
                else:
                    self.index += 1
                    self.column += 1
            if self.index < len(self.data) and self.data[self.index] == '\'':
                self.index += 1
                self.column += 1
                return True
            else:
                self.error("unclosed single quoted scalar")
        else:
            return False

    def eat_folded(self):
        self.eat_block_scalar()

    def eat_literal(self):
        self.eat_block_scalar()

    def eat_block_scalar(self):
        if self.index < len(self.data) and self.data[self.index] in '>|':
            self.eat_line()
            if not self.eat_ignored_newline():
                return True
            indent = self.indent+1
            if indent < 1:
                indent = 1
            while (self.eat_indent(indent) and ((self.eat_line() and self.eat_ignored_newline()) or (self.eat_ignored_newline()))) or  \
                    (self.eat_ignored_comment() and self.eat_ignored_newline()) or  \
                    self.eat_ignored_newline():
                pass
            return True
        return False

    def eat_block_plain(self):
        return self.eat_plain(block=True)

    def eat_flow_plain(self):
        return self.eat_plain(block=False)

    def eat_plain(self, block):
        indent = self.indent+1
        if indent < 1:
            indent = 1
        if self.index < len(self.data):
            if self.data[self.index] not in ' \t\r\n-?:,[]{}#&*!|>\'"%@`' or    \
                    (block and self.data[self.index] == '-' and self.data[self.index:self.index+2] not in ['-', '- ', '-\r', '-\n']) or \
                    (block and self.data[self.index] == '?' and self.data[self.index:self.index+2] not in ['?', '? ', '?\r', '?\n']) or \
                    (block and self.data[self.index] == ':' and self.data[self.index:self.index+2] not in [':', ': ', ':\r', ':\n']):
                if block and self.allow_block_collection:
                    self.guessing_simple_key()
                if self.flow_level and self.allow_flow_key:
                    self.guess_flow_key_levels.append(self.flow_level)
                    self.guess_flow_key_tokens.append(len(self.tokens))
                self.allow_flow_key = False
                self.index += 1
                self.column += 1
                space = False
                while True:
                    self.eat_ignored_spaces()
                    while self.index < len(self.data) and (
                            self.data[self.index] not in '\r\n?:,[]{}#' or
                            (not space and self.data[self.index] == '#') or
                            (block and self.data[self.index] in '?,[]{}') or
                            (block and self.data[self.index] == ':' and self.data[self.index:self.index+2] not in [':', ': ', ':\r', ':\n'])):
                        space = self.data[self.index] not in ' \t'
                        self.index += 1
                        self.column += 1
                        self.allow_block_collection = False
                    if not (self.eat_ignored_newline() and self.eat_indent(indent)):
                        break
                    space = True
                return True
        return False

    def no_simple_key(self):
        self.guess_simple_key = False
        self.guess_simple_key_token = None
        self.guess_simple_key_indent = None

    def guessing_simple_key(self):
        self.guess_simple_key = True
        self.guess_simple_key_token = len(self.tokens)
        self.guess_simple_key_indent = self.column

    def unwind_indents(self, level):
        while self.indent > level:
            if self.flow_level:
                self.error("Invalid indentation")
            self.tokens.append('BLOCK_END')
            self.indent = self.indents.pop()
            self.no_simple_key()

    def fetch_token(self):
        self.unwind_indents(self.column)
        if self.index < len(self.data):
            if self.column == 0:
                if self.data[self.index] == '%':
                    self.tokens.append('DIRECTIVE')
                    self.eat_line()
                    self.no_simple_key()
                    return True
                if self.data[self.index:self.index+3] == '---' and  \
                        (not self.data[self.index+3:self.index+4] or self.data[self.index+3:self.index+4] in ' \r\n'):
                    self.unwind_indents(-1)
                    self.tokens.append('DOCUMENT_START')
                    self.index += 3
                    self.column += 3
                    self.allow_block_collection = False
                    self.allow_flow_key = False
                    self.guess_flow_keys = []
                    self.no_simple_key()
                    return True
                if self.data[self.index:self.index+3] == '...' and   \
                        (not self.data[self.index+3:self.index+4] or self.data[self.index+3:self.index+4] in ' \r\n'):
                    self.unwind_indents(-1)
                    self.tokens.append('DOCUMENT_END')
                    self.index += 3
                    self.column += 3
                    self.allow_block_collection = False
                    self.allow_flow_key = False
                    self.guess_flow_keys = []
                    self.no_simple_key()
                    return True
            if self.data[self.index] in '[]{}':
                if self.data[self.index] == '[':
                    self.flow_level += 1
                    self.allow_flow_key = True
                    self.tokens.append('FLOW_SEQ_START')
                elif self.data[self.index] == '{':
                    self.flow_level += 1
                    self.allow_flow_key = True
                    self.tokens.append('FLOW_MAP_START')
                elif self.data[self.index] == ']':
                    if not self.flow_level:
                        self.error("Extra ]")
                    self.flow_level -= 1
                    self.allow_flow_key = False
                    self.tokens.append('FLOW_SEQ_END')
                else:
                    if not self.flow_level:
                        self.error("Extra }")
                    self.flow_level -= 1
                    self.allow_flow_key = False
                    self.tokens.append('FLOW_MAP_END')
                while self.guess_flow_key_levels and self.guess_flow_key_levels[-1] > self.flow_level:
                    self.guess_flow_key_levels.pop()
                    self.guess_flow_key_tokens.pop()
                self.index += 1
                self.column += 1
                self.allow_block_collection = False
                return True
            if self.data[self.index] in '!&*':
                if self.flow_level and self.allow_flow_key:
                    self.guess_flow_key_levels.append(self.flow_level)
                    self.guess_flow_key_tokens.append(len(self.tokens))
                if not self.flow_level and self.allow_block_collection:
                    self.guessing_simple_key()
                if self.data[self.index] == '!':
                    self.tokens.append('TAG')
                elif self.data[self.index] == '&':
                    self.tokens.append('ANCHOR')
                else:
                    self.tokens.append('ALIAS')
                self.eat_ns()
                self.allow_flow_key = False
                self.allow_block_collection = False
                return True
            if self.data[self.index] == '"':
                if self.flow_level and self.allow_flow_key:
                    self.guess_flow_key_levels.append(self.flow_level)
                    self.guess_flow_key_tokens.append(len(self.tokens))
                if not self.flow_level and self.allow_block_collection:
                    self.guessing_simple_key()
                self.tokens.append('SCALAR')
                self.eat_double_quoted()
                self.allow_flow_key = False
                self.allow_block_collection = False
                return True
            if self.data[self.index] == '\'':
                if self.flow_level and self.allow_flow_key:
                    self.guess_flow_key_levels.append(self.flow_level)
                    self.guess_flow_key_tokens.append(len(self.tokens))
                if not self.flow_level and self.allow_block_collection:
                    self.guessing_simple_key()
                self.tokens.append('SCALAR')
                self.eat_single_quoted()
                self.allow_flow_key = False
                self.allow_block_collection = False
                return True
            if not self.flow_level:
                if self.data[self.index] in '-?:' and \
                        (not self.data[self.index+1:self.index+2] or self.data[self.index+1:self.index+2] in ' \r\n'):
                    if self.guess_simple_key and self.data[self.index] == ':':
                        self.tokens.insert(self.guess_simple_key_token, 'KEY')
                        if self.guess_simple_key_indent > self.indent:
                            self.indents.append(self.indent)
                            self.indent = self.guess_simple_key_indent
                            self.tokens.insert(self.guess_simple_key_token, 'BLOCK_MAP_START')
                        self.tokens.append('VALUE')
                        self.no_simple_key()
                        self.index += 1
                        self.column += 1
                        self.allow_block_collection = False
                        return True
                    else:
                        if not self.allow_block_collection:
                            self.error("Block collection should start at the beginning of the line")
                        if self.column > self.indent:
                            self.indents.append(self.indent)
                            self.indent = self.column
                            if self.data[self.index] == '-':
                                self.tokens.append('BLOCK_SEQ_START')
                            else:
                                self.tokens.append('BLOCK_MAP_START')
                        if self.data[self.index] == '-':
                            self.tokens.append('ENTRY')
                        elif self.data[self.index] == '?':
                            self.tokens.append('KEY')
                        else:
                            self.tokens.append('VALUE')
                        self.index += 1
                        self.column += 1
                        #self.allow_block_collection = False
                        self.allow_block_collection = True
                        self.no_simple_key()
                        return True
                if self.data[self.index] == '>':
                    self.no_simple_key()
                    self.tokens.append('SCALAR')
                    self.eat_folded()
                    self.allow_block_collection = True
                    return True
                if self.data[self.index] == '|':
                    self.no_simple_key()
                    self.tokens.append('SCALAR')
                    self.eat_literal()
                    self.allow_block_collection = True
                    return True
                if self.eat_block_plain():
                    self.tokens.append('SCALAR')
                    return True
            else:
                if self.data[self.index] in ',?:':
                    if self.data[self.index] == ',':
                        self.tokens.append('ENTRY')
                        while self.guess_flow_key_levels and self.guess_flow_key_levels[-1] >= self.flow_level:
                            self.guess_flow_key_levels.pop()
                            self.guess_flow_key_tokens.pop()
                        self.allow_flow_key = True
                    elif self.data[self.index] == '?':
                        self.tokens.append('KEY')
                        while self.guess_flow_key_levels and self.guess_flow_key_levels[-1] >= self.flow_level:
                            self.guess_flow_key_levels.pop()
                            self.guess_flow_key_tokens.pop()
                        self.allow_flow_key = False
                    else:
                        self.tokens.append('VALUE')
                        if self.guess_flow_key_levels and self.guess_flow_key_levels[-1] == self.flow_level:
                            self.guess_flow_key_levels.pop()
                            index = self.guess_flow_key_tokens.pop()
                            self.tokens.insert(index, 'KEY')
                        self.allow_flow_key =False
                    self.index += 1
                    self.column += 1
                    return True
                if self.eat_flow_plain():
                    self.tokens.append('SCALAR')
                    return True
            self.error("Invalid token")
        else:
            self.unwind_indents(-1)

    def error(self, message):
        raise Error(message, Marker(self.source, self.data, self.index))

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

