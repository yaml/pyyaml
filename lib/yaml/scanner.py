
# Tokens:
# YAML-DIRECTIVE(major_version, minor_version), TAG-DIRECTIVE(handle, prefix)
# RESERVED-DIRECTIVE(name)
# DOCUMENT-START, DOCUMENT-END
# BLOCK-SEQUENCE-START, BLOCK-MAPPING-START, BLOCK-END
# FLOW-SEQUENCE-START, FLOW-MAPPING-START, FLOW-SEQUENCE-END, FLOW-MAPPING-END
# ENTRY, KEY, VALUE
# ALIAS(name), ANCHOR(name), TAG(value), SCALAR(value, plain)

__all__ = ['Scanner', 'ScannerError']

from error import YAMLError
from tokens import *

class ScannerError(YAMLError):
    # TODO:
    # ScannerError: while reading a quoted string
    #         in '...', line 5, column 10:
    # key: "valu\?e"
    #      ^
    # got unknown quote character '?'
    #         in '...', line 5, column 15:
    # key: "valu\?e"
    #            ^
    def __init__(self, context=None, context_marker=None,
            problem=None, problem_marker=None):
        self.context = context
        self.context_marker = context_marker
        self.problem = problem
        self.problem_marker = problem_marker

    def __str__(self):
        lines = []
        for (place, marker) in [(self.context, self.context_marker),
                                (self.problem, self.problem_marker)]:
            if place is not None:
                lines.append(place)
                if marker is not None:
                    lines.append(str(marker))
        return '\n'.join(lines)

class SimpleKey:
    def __init__(self, token_number, required, index, line, column, marker):
        self.token_number = token_number
        self.required = required
        self.index = index
        self.line = line
        self.column = column
        self.marker = marker

class Scanner:


    def __init__(self, reader):
        """Initialize the scanner."""
        # The input stream. The Reader class do the dirty work of checking for
        # BOM and converting the input data to Unicode. It also adds NUL to
        # the end.
        #
        # Reader supports the following methods
        #   self.reader.peek(i=0)       # peek the next i-th character
        #   self.reader.prefix(l=1)     # peek the next l characters
        #   self.reader.forward(l=1)    # read the next l characters
                                        # and move the pointer
        self.reader = reader

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

        # Variables related to simple keys treatment.

        # A simple key is a key that is not denoted by the '?' indicator.
        # Example of simple keys:
        #   ---
        #   block simple key: value
        #   ? not a simple key:
        #   : { flow simple key: value }
        # We emit the KEY token before all keys, so when we find a potential
        # simple key, we try to locate the corresponding ':' indicator.
        # Simple keys should be limited to a single line and 1024 characters.

        # Can a simple key start at the current position? A simple key may
        # start:
        # - at the beginning of the line, not counting indentation spaces
        #       (in block context),
        # - after '{', '[', ',' (in the flow context),
        # - after '?', ':', '-' (in the block context).
        # In the block context, this flag also signify if a block collection
        # may start at the current position.
        self.allow_simple_key = True

        # Keep track of possible simple keys. This is a dictionary. The key
        # is `flow_level`; there can be no more that one possible simple key
        # for each level. The value is a SimpleKey record:
        #   (token_number, required, index, line, column, marker)
        # A simple key may start with ALIAS, ANCHOR, TAG, SCALAR(flow),
        # '[', or '{' tokens.
        self.possible_simple_keys = {}

    # Two public methods.

    def peek_token(self):
        """Get the current token."""
        while self.need_more_tokens():
            self.fetch_more_tokens()
        if self.tokens:
            return self.tokens[0]

    def get_token(self):
        "Get the current token and remove it from the list of pending tokens."""
        while self.need_more_tokens():
            self.fetch_more_tokens()
        if self.tokens:
            self.tokens_taken += 1
            return self.tokens.pop(0)

    # Private methods.

    def need_more_tokens(self):
        if self.done:
            return False
        if not self.tokens:
            return True
        # The current token may be a potential simple key, so we
        # need to look further.
        self.stale_possible_simple_keys()
        if self.next_possible_simple_key() == self.tokens_taken:
            return True

    def fetch_more_tokens(self):

        # Eat whitespaces and comments until we reach the next token.
        self.scan_to_next_token()

        # Remove obsolete possible simple keys.
        self.stale_possible_simple_keys()

        # Compare the current indentation and column. It may add some tokens
        # and decrease the current indentation level.
        self.unwind_indent(self.reader.column)

        # Peek the next character.
        ch = self.reader.peek()

        # Is it the end of stream?
        if ch == u'\0':
            return self.fetch_stream_end()

        # Is it the byte order mark?
        if ch == u'\uFEFF':
            return self.fetch_bom()

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

        # Is it the entry indicator?
        if ch in u'-,' and self.check_entry():
            return self.fetch_entry()

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

        # Is it a tag?
        if ch == u'!':
            return self.fetch_tag()

        # Is it a literal scalar?
        if ch == u'|' and not self.flow_level:
            return self.fetch_literal()

        # Is it a folded scalar?
        if ch == u'>' and not self.flow_level:
            return self.fetch_folded()

        # Is it a single quoted scalar?
        if ch == u'\'':
            return self.fetch_single()

        # Is it a double quoted scalar?
        if ch == u'\"':
            return self.fetch_double()

        # It must be a plain scalar then.
        if self.check_plain():
            return self.fetch_plain()

        # No? It's an error. Let's produce a nice error message.
        raise ScannerError("while scanning for the next token", None,
                "found character %r that cannot start any token"
                % ch.encode('utf-8'), self.reader.get_marker())

    # Simple keys treatment.

    def next_possible_simple_key(self):
        # Return the number of the nearest possible simple key. Actually we
        # don't need to loop through the whole dictionary. We may replace it
        # with the following code:
        #   if not self.possible_simple_keys:
        #       return None
        #   return self.possible_simple_keys[
        #           min(self.possible_simple_keys.keys())].token_number
        min_token_number = None
        for level in self.possible_simple_keys:
            key = self.possible_simple_keys[level]
            if min_token_number is None or key.token_number < min_token_number:
                min_token_number = key.token_number
        return min_token_number

    def stale_possible_simple_keys(self):
        # Remove entries that are no longer possible simple keys. According to
        # the YAML specification, simple keys
        # - should be limited to a single line,
        # - should be no longer than 1024 characters.
        # Disabling this procedure will allow simple keys of any length and
        # height (may cause problems if indentation is broken though).
        for level in self.possible_simple_keys.keys():
            key = self.possible_simple_keys[level]
            if key.line != self.reader.line  \
                    or self.reader.index-key.index > 1024:
                if key.required:
                    raise ScannerError("while scanning a simple key", key.marker,
                            "could not found expected ':'", self.reader.get_marker())
                del self.possible_simple_keys[level]

    def save_possible_simple_key(self):
        # The next token may start a simple key. We check if it's possible
        # and save its position. This function is called for
        #   ALIAS, ANCHOR, TAG, SCALAR(flow), '[', and '{'.

        # Check if a simple key is required at the current position.
        required = not self.flow_level and self.indent == self.reader.column

        # A simple key is required only if it is the first token in the current
        # line. Therefore it is always allowed.
        assert self.allow_simple_key or not required

        # The next token might be a simple key. Let's save it's number and
        # position.
        if self.allow_simple_key:
            self.remove_possible_simple_key()
            token_number = self.tokens_taken+len(self.tokens)
            index = self.reader.index
            line = self.reader.line
            column = self.reader.column
            marker = self.reader.get_marker()
            key = SimpleKey(token_number, required,
                    index, line, column, marker)
            self.possible_simple_keys[self.flow_level] = key

    def remove_possible_simple_key(self):
        # Remove the saved possible key position at the current flow level.
        if self.flow_level in self.possible_simple_keys:
            key = self.possible_simple_keys[self.flow_level]
            
            # I don't think it's possible, but I could be wrong.
            assert not key.required
            #if key.required:
            #    raise ScannerError("while scanning a simple key", key.marker,
            #            "could not found expected ':'", self.reader.get_marker())

    # Indentation functions.

    def unwind_indent(self, column):

        # In flow context, tokens should respect indentation.
        # Actually the condition should be `self.indent >= column` according to
        # the spec. But this condition will prohibit intuitively correct
        # constructions such as
        # key : {
        # }
        if self.flow_level and self.indent > column:
            raise ScannerError(None, None,
                    "invalid intendation or unclosed '[' or '{'",
                    self.reader.get_marker())

        # In block context, we may need to issue the BLOCK-END tokens.
        while self.indent > column:
            marker = self.reader.get_marker()
            self.indent = self.indents.pop()
            self.tokens.append(BlockEndToken(marker, marker))

    def add_indent(self, column):
        # Check if we need to increase indentation.
        if self.indent < column:
            self.indents.append(self.indent)
            self.indent = column
            return True
        return False

    # Fetchers.

    def fetch_stream_end(self):

        # Set the current intendation to -1.
        self.unwind_indent(-1)

        # Reset everything (not really needed).
        self.allow_simple_key = False
        self.possible_simple_keys = {}

        # Read the token.
        marker = self.reader.get_marker()
        
        # Add END.
        self.tokens.append(StreamEndToken(marker, marker))

        # The reader is ended.
        self.done = True

    def fetch_bom(self):
        # We consider the BOM marker as a DOCUMENT-END indicator unless it's
        # the first character in the stream. It's a reasonable approximation
        # of the specification requirements. We can follow the specification
        # literally, but it will require a new token class. Probably later.

        # We ignore BOM if it is the first character in the stream.
        if self.reader.index == 0:
            slef.reader.forward()

        # Otherwise we issue DOCUMENT-END.
        else:

            # Set the current intendation to -1.
            self.unwind_indent(-1)

            # Reset simple keys. Note that there could not be a block
            # collection after BOM.
            self.remove_possible_simple_key()
            self.allow_simple_key = False

            # Add DOCUMENT-END.
            start_marker = self.reader.get_marker()
            self.reader.forward()
            end_marker = self.reader.get_marker()
            self.tokens.append(DocumentEndToken(start_marker, end_marker))

    def fetch_directive(self):
        
        # Set the current intendation to -1.
        self.unwind_indent(-1)

        # Reset simple keys.
        self.remove_possible_simple_key()
        self.allow_simple_key = False

        # Scan and add DIRECTIVE.
        self.tokens.append(self.scan_directive())

    def fetch_document_start(self):
        self.fetch_document_indicator(DocumentStartToken)

    def fetch_document_end(self):
        self.fetch_document_indicator(DocumentEndToken)

    def fetch_document_indicator(self, TokenClass):

        # Set the current intendation to -1.
        self.unwind_indent(-1)

        # Reset simple keys. Note that there could not be a block collection
        # after '---'.
        self.remove_possible_simple_key()
        self.allow_simple_key = False

        # Add DOCUMENT-START or DOCUMENT-END.
        start_marker = self.reader.get_marker()
        self.reader.forward(3)
        end_marker = self.reader.get_marker()
        self.tokens.append(TokenClass(start_marker, end_marker))

    def fetch_flow_sequence_start(self):
        self.fetch_flow_collection_start(FlowSequenceStartToken)

    def fetch_flow_mapping_start(self):
        self.fetch_flow_collection_start(FlowMappingStartToken)

    def fetch_flow_collection_start(self, TokenClass):

        # '[' and '{' may start a simple key.
        self.save_possible_simple_key()

        # Increase the flow level.
        self.flow_level += 1

        # Simple keys are allowed after '[' and '{'.
        self.allow_simple_key = True

        # Add FLOW-SEQUENCE-START or FLOW-MAPPING-START.
        start_marker = self.reader.get_marker()
        self.reader.forward()
        end_marker = self.reader.get_marker()
        self.tokens.append(TokenClass(start_marker, end_marker))

    def fetch_flow_sequence_end(self):
        self.fetch_flow_collection_end(FlowSequenceEndToken)

    def fetch_flow_mapping_end(self):
        self.fetch_flow_collection_end(FlowMappingEndToken)

    def fetch_flow_collection_end(self, TokenClass):

        # Reset possible simple key on the current level.
        self.remove_possible_simple_key()

        # Decrease the flow level.
        self.flow_level -= 1

        # No simple keys after ']' or '}'.
        self.allow_simple_key = False

        # Add FLOW-SEQUENCE-END or FLOW-MAPPING-END.
        start_marker = self.reader.get_marker()
        self.reader.forward()
        end_marker = self.reader.get_marker()
        self.tokens.append(TokenClass(start_marker, end_marker))

    def fetch_entry(self):

        # Block context needs additional checks.
        if not self.flow_level:

            # Are we allowed to start a new entry?
            if not self.allow_simple_key:
                raise ScannerError(None, None,
                        "sequence entries are not allowed here",
                        self.reader.get_marker())

            # We may need to add BLOCK-SEQUENCE-START.
            if self.add_indent(self.reader.column):
                marker = self.reader.get_marker()
                self.tokens.append(BlockSequenceStartToken(marker, marker))

        # Simple keys are allowed after '-' and ','.
        self.allow_simple_key = True

        # Reset possible simple key on the current level.
        self.remove_possible_simple_key()

        # Add ENTRY.
        start_marker = self.reader.get_marker()
        self.reader.forward()
        end_marker = self.reader.get_marker()
        self.tokens.append(EntryToken(start_marker, end_marker))

    def fetch_key(self):
        
        # Block context needs additional checks.
        if not self.flow_level:

            # Are we allowed to start a key (not nessesary a simple)?
            if not self.allow_simple_key:
                raise ScannerError(None, None,
                        "mapping keys are not allowed here",
                        self.reader.get_marker())

            # We may need to add BLOCK-MAPPING-START.
            if self.add_indent(self.reader.column):
                marker = self.reader.get_marker()
                self.tokens.append(BlockMappingStartToken(marker, marker))

        # Simple keys are allowed after '?' in the block context.
        self.allow_simple_key = not self.flow_level

        # Reset possible simple key on the current level.
        self.remove_possible_simple_key()

        # Add KEY.
        start_marker = self.reader.get_marker()
        self.reader.forward()
        end_marker = self.reader.get_marker()
        self.tokens.append(KeyToken(start_marker, end_marker))

    def fetch_value(self):

        # Do we determine a simple key?
        if self.flow_level in self.possible_simple_keys:

            # Add KEY.
            key = self.possible_simple_keys[self.flow_level]
            del self.possible_simple_keys[self.flow_level]
            self.tokens.insert(key.token_number-self.tokens_taken,
                    KeyToken(key.marker, key.marker))

            # If this key starts a new block mapping, we need to add
            # BLOCK-MAPPING-START.
            if not self.flow_level:
                if self.add_indent(key.column):
                    self.tokens.insert(key.token_number-self.tokens_taken,
                            BlockMappingStartToken(key.marker, key.marker))

            # There cannot be two simple keys one after another.
            self.allow_simple_key = False

        # It must be a part of a complex key.
        else:
            
            # Block context needs additional checks.
            # (Do we really need them? They will be catched by the parser
            # anyway.)
            if not self.flow_level:

                # We are allowed to start a complex value if and only if
                # we can start a simple key.
                if not self.allow_simple_key:
                    raise ScannerError(None, None,
                            "mapping values are not allowed here",
                            self.reader.get_marker())

            # Simple keys are allowed after ':' in the block context.
            self.allow_simple_key = not self.flow_level

            # Reset possible simple key on the current level.
            self.remove_possible_simple_key()

        # Add VALUE.
        start_marker = self.reader.get_marker()
        self.reader.forward()
        end_marker = self.reader.get_marker()
        self.tokens.append(ValueToken(start_marker, end_marker))

    def fetch_alias(self):

        # ALIAS could be a simple key.
        self.save_possible_simple_key()

        # No simple keys after ALIAS.
        self.allow_simple_key = False

        # Scan and add ALIAS.
        self.tokens.append(self.scan_anchor(AliasToken))

    def fetch_anchor(self):

        # ANCHOR could start a simple key.
        self.save_possible_simple_key()

        # No simple keys after ANCHOR.
        self.allow_simple_key = False

        # Scan and add ANCHOR.
        self.tokens.append(self.scan_anchor(AnchorToken))

    def fetch_tag(self):

        # TAG could start a simple key.
        self.save_possible_simple_key()

        # No simple keys after TAG.
        self.allow_simple_key = False

        # Scan and add TAG.
        self.tokens.append(self.scan_tag())

    def fetch_literal(self):
        self.fetch_block_scalar(folded=False)

    def fetch_folded(self):
        self.fetch_block_scalar(folded=True)

    def fetch_block_scalar(self, folded):

        # A simple key may follow a block scalar.
        self.allow_simple_key = True

        # Reset possible simple key on the current level.
        self.remove_possible_simple_key()

        # Scan and add SCALAR.
        self.tokens.append(self.scan_block_scalar(folded))

    def fetch_single(self):
        self.fetch_flow_scalar(double=False)

    def fetch_double(self):
        self.fetch_flow_scalar(double=True)

    def fetch_flow_scalar(self, double):

        # A flow scalar could be a simple key.
        self.save_possible_simple_key()

        # No simple keys after flow scalars.
        self.allow_simple_key = False

        # Scan and add SCALAR.
        self.tokens.append(self.scan_flow_scalar(double))

    def fetch_plain(self):

        # A plain scalar could be a simple key.
        self.save_possible_simple_key()

        # No simple keys after plain scalars. But note that `scan_plain` will
        # change this flag if the scan is finished at the beginning of the
        # line.
        self.allow_simple_key = False

        # Scan and add SCALAR. May change `allow_simple_key`.
        self.tokens.append(self.scan_plain())

    # Checkers.

    def check_directive(self):

        # DIRECTIVE:        ^ '%' ...
        # The '%' indicator is already checked.
        if self.reader.column == 0:
            return True

    def check_document_start(self):

        # DOCUMENT-START:   ^ '---' (' '|'\n')
        if self.reader.column == 0:
            if self.reader.prefix(3) == u'---'  \
                    and self.reader.peek(3) in u'\0 \t\r\n\x85\u2028\u2029':
                return True

    def check_document_end(self):

        # DOCUMENT-END:     ^ '...' (' '|'\n')
        if self.reader.column == 0:
            prefix = self.reader.peek(4)
            if self.reader.prefix(3) == u'...'  \
                    and self.reader.peek(3) in u'\0 \t\r\n\x85\u2028\u2029':
                return True

    def check_entry(self):

        # ENTRY(flow context):      ','
        if self.flow_level:
            return self.reader.peek() == u','

        # ENTRY(block context):     '-' (' '|'\n')
        else:
            return self.reader.peek() == u'-'   \
                    and self.reader.peek(1) in u'\0 \t\r\n\x85\u2028\u2029'

    def check_key(self):

        # KEY(flow context):    '?'
        if self.flow_level:
            return True

        # KEY(block context):   '?' (' '|'\n')
        else:
            return self.reader.peek(1) in u'\0 \t\r\n\x85\u2028\u2029'

    def check_value(self):

        # VALUE(flow context):  ':'
        if self.flow_level:
            return True

        # VALUE(block context): ':' (' '|'\n')
        else:
            return self.reader.peek(1) in u'\0 \t\r\n\x85\u2028\u2029'

    def check_plain(self):

        # A plain scalar may start with any non-space character except:
        #   '-', '?', ':', ',', '[', ']', '{', '}',
        #   '#', '&', '*', '!', '|', '>', '\'', '\"',
        #   '%', '@', '`'.
        #
        # It may also start with
        #   '-', '?', ':'
        # if it is followed by a non-space character.
        #
        # Note that we limit the last rule to the block context (except the
        # '-' character) because we want the flow context to be space
        # independent.
        ch = self.reader.peek()
        return ch not in u'\0 \t\r\n\x85\u2028\u2029-?:,[]{}#&*!|>\'\"%@`'  \
                or (self.reader.peek(1) not in u'\0 \t\r\n\x85\u2028\u2029'
                        and (ch == '-' or (not self.flow_level and ch in u'?:')))

    # Scanners.

    def scan_to_next_token(self):
        # We ignore spaces, line breaks and comments.
        # If we find a line break in the block context, we set the flag
        # `allow_simple_key` on.
        found = False
        while not found:
            while self.reader.peek() == u' ':
                self.reader.forward()
            if self.reader.peek() == u'#':
                while self.reader.peek() not in u'\0\r\n\x85\u2028\u2029':
                    self.reader.forward()
            if self.scan_line_break():
                if not self.flow_level:
                    self.allow_simple_key = True
            else:
                found = True

    def scan_directive(self):
        # See the specification for details.
        start_marker = self.reader.get_marker()
        self.reader.forward()
        name = self.scan_directive_name(start_marker)
        value = None
        if name == u'YAML':
            value = self.scan_yaml_directive_value(start_marker)
            end_marker = self.reader.get_marker()
        elif name == u'TAG':
            value = self.scan_tag_directive_value(start_marker)
            end_marker = self.reader.get_marker()
        else:
            end_marker = self.reader.get_marker()
            while self.reader.peek() not in u'\0\r\n\x85\u2028\u2029':
                self.reader.forward()
        self.scan_directive_ignored_line(start_marker)
        return DirectiveToken(name, value, start_marker, end_marker)

    def scan_directive_name(self, start_marker):
        # See the specification for details.
        length = 0
        ch = self.reader.peek(length)
        while u'0' <= ch <= u'9' or u'A' <= ch <= 'Z' or u'a' <= ch <= 'z'  \
                or ch in u'-_':
            length += 1
            ch = self.reader.peek(length)
        if not length:
            raise ScannerError("while scanning a directive", start_marker,
                    "expected directive name, but found %r" % ch.encode('utf-8'),
                    self.reader.get_marker())
        value = self.reader.prefix(length)
        self.reader.forward(length)
        ch = self.reader.peek()
        if ch not in u'\0 \r\n\x85\u2028\u2029':
            raise ScannerError("while scanning a directive" % name, start_marker,
                    "expected alphabetic or numeric character, but found %r"
                    % ch.encode('utf-8'), self.reader.get_marker())
        return value

    def scan_yaml_directive_value(self, start_marker):
        # See the specification for details.
        while self.reader.peek() == u' ':
            self.reader.forward()
        major = self.scan_yaml_directive_number(start_marker)
        if self.reader.peek() != '.':
            raise ScannerError("while scanning a directive", start_marker,
                    "expected a digit or '.', but found %r" % ch.encode('utf-8'),
                    self.reader.get_marker())
        self.reader.forward()
        minor = self.scan_yaml_directive_number(start_marker)
        if self.reader.peek() not in u'\0 \r\n\x85\u2028\u2029':
            raise ScannerError("while scanning a directive", start_marker,
                    "expected a digit or ' ', but found %r" % ch.encode('utf-8'),
                    self.reader.get_marker())
        return (major, minor)

    def scan_yaml_directive_number(self, start_marker):
        # See the specification for details.
        ch = self.reader.peek()
        if not (u'0' <= ch <= '9'):
            raise ScannerError("while scanning a directive", start_marker,
                    "expected a digit, but found %r" % ch.encode('utf-8'),
                    self.reader.get_marker())
        length = 0
        while u'0' <= self.reader.peek(length) <= u'9':
            length += 1
        value = int(self.reader.prefix(length))
        self.reader.forward(length)
        return value

    def scan_tag_directive_value(self, start_marker):
        # See the specification for details.
        while self.reader.peek() == u' ':
            self.reader.forward()
        handle = self.scan_tag_directive_handle(start_marker)
        while self.reader.peek() == u' ':
            self.reader.forward()
        prefix = self.scan_tag_directive_prefix(start_marker)
        return (handle, prefix)

    def scan_tag_directive_handle(self, start_marker):
        # See the specification for details.
        value = self.scan_tag_handle('directive', start_marker)
        if self.reader.peek() != u' ':
            raise ScannerError("while scanning a directive", start_marker,
                    "expected ' ', but found %r" % ch.encode('utf-8'),
                    self.reader.get_marker())
        return value

    def scan_tag_directive_prefix(self, start_marker):
        # See the specification for details.
        value = self.scan_tag_uri('directive', start_marker)
        ch = self.reader.peek()
        if ch not in u'\0 \r\n\x85\u2028\u2029':
            raise ScannerError("while scanning a directive", start_marker,
                    "expected ' ', but found %r" % ch.encode('utf-8'),
                    self.reader.get_marker())
        return value

    def scan_directive_ignored_line(self, start_marker):
        # See the specification for details.
        while self.reader.peek() == u' ':
            self.reader.forward()
        if self.reader.peek() == u'#':
            while self.reader.peek() not in u'\0\r\n\x85\u2028\u2029':
                self.reader.forward()
        ch = self.reader.peek()
        if ch not in u'\0\r\n\x85\u2028\u2029':
            raise ScannerError("while scanning a directive", start_marker,
                    "expected a comment or a line break, but found %r"
                        % ch.encode('utf-8'), self.reader.get_marker())
        self.scan_line_break()

    def scan_anchor(self, TokenClass):
        # The specification does not restrict characters for anchors and
        # aliases. This may lead to problems, for instance, the document:
        #   [ *alias, value ]
        # can be interpteted in two ways, as
        #   [ "value" ]
        # and
        #   [ *alias , "value" ]
        # Therefore we restrict aliases to numbers and ASCII letters.
        start_marker = self.reader.get_marker()
        indicator = self.reader.peek()
        if indicator == '*':
            name = 'alias'
        else:
            name = 'anchor'
        self.reader.forward()
        length = 0
        ch = self.reader.peek(length)
        while u'0' <= ch <= u'9' or u'A' <= ch <= 'Z' or u'a' <= ch <= 'z'  \
                or ch in u'-_':
            length += 1
            ch = self.reader.peek(length)
        if not length:
            raise ScannerError("while scanning an %s" % name, start_marker,
                    "expected anchor name, but found %r" % ch.encode('utf-8'),
                    self.reader.get_marker())
        value = self.reader.prefix(length)
        self.reader.forward(length)
        ch = self.reader.peek()
        if ch not in u'\0 \t\r\n\x85\u2028\u2029?:,]}%@`':
            raise ScannerError("while scanning an %s" % name, start_marker,
                    "expected alphabetic or numeric character, but found %r"
                    % ch.encode('utf-8'), self.reader.get_marker())
        end_marker = self.reader.get_marker()
        return TokenClass(value, start_marker, end_marker)

    def scan_tag(self):
        # See the specification for details.
        start_marker = self.reader.get_marker()
        ch = self.reader.peek(1)
        if ch == u'<':
            handle = None
            self.reader.forward(2)
            suffix = self.scan_tag_uri('tag', start_marker)
            if self.reader.peek() != u'>':
                raise ScannerError("while parsing a tag", start_marking,
                        "expected '>', but got %r" % self.reader.peek().encode('utf-8'),
                        self.reader.get_marker())
            self.reader.forward()
        elif ch in u'\0 \t\r\n\x85\u2028\u2029':
            handle = None
            suffix = u'!'
            self.reader.forward()
        else:
            length = 1
            use_handle = False
            while ch not in u'\0 \r\n\x85\u2028\u2029':
                if ch == u'!':
                    use_handle = True
                    break
                length += 1
                ch = self.reader.peek(length)
            handle = u'!'
            if use_handle:
                handle = self.scan_tag_handle('tag', start_marker)
            else:
                handle = u'!'
                self.reader.forward()
            suffix = self.scan_tag_uri('tag', start_marker)
        ch = self.reader.peek()
        if ch not in u'\0 \r\n\x85\u2028\u2029':
            raise ScannerError("while scanning a tag", start_marker,
                    "expected ' ', but found %r" % ch.encode('utf-8'),
                    self.reader.get_marker())
        value = (handle, suffix)
        end_marker = self.reader.get_marker()
        return TagToken(value, start_marker, end_marker)

    def scan_block_scalar(self, folded):
        # See the specification for details.

        chunks = []
        start_marker = self.reader.get_marker()

        # Scan the header.
        self.reader.forward()
        chomping, increment = self.scan_block_scalar_indicators(start_marker)
        self.scan_block_scalar_ignored_line(start_marker)

        # Determine the indentation level and go to the first non-empty line.
        min_indent = self.indent+1
        if min_indent < 1:
            min_indent = 1
        if increment is None:
            breaks, max_indent, end_marker = self.scan_block_scalar_indentation()
            indent = max(min_indent, max_indent)
        else:
            indent = min_indent+increment-1
            breaks, end_marker = self.scan_block_scalar_breaks(indent)
        line_break = u''

        # Scan the inner part of the block scalar.
        while self.reader.column == indent and self.reader.peek() != u'\0':
            chunks.extend(breaks)
            leading_non_space = self.reader.peek() not in u' \t'
            length = 0
            while self.reader.peek(length) not in u'\0\r\n\x85\u2028\u2029':
                length += 1
            chunks.append(self.reader.prefix(length))
            self.reader.forward(length)
            line_break = self.scan_line_break()
            breaks, end_marker = self.scan_block_scalar_breaks(indent)
            if self.reader.column == indent and self.reader.peek() != u'\0':
                # Unfortunately, folding rules are ambiguous.
                #
                # This is the folding according to the specification:
                #
                #if folded and line_break == u'\n'   \
                #        and leading_non_space and self.reader.peek() not in u' \t':
                #    if not breaks:
                #        chunks.append(u' ')
                #else:
                #    chunks.append(line_break)
                #
                # This is Clark Evans's interpretation (also in the spec
                # examples):
                #
                if folded and line_break == u'\n':
                    if not breaks:
                        if self.reader.peek() not in ' \t':
                            chunks.append(u' ')
                        else:
                            chunks.append(line_break)
                else:
                    chunks.append(line_break)
            else:
                break

        # Chomp the tail.
        if chomping is not False:
            chunks.append(line_break)
        if chomping is True:
            chunks.extend(breaks)

        # We are done.
        return ScalarToken(u''.join(chunks), False, start_marker, end_marker)

    def scan_block_scalar_indicators(self, start_marker):
        # See the specification for details.
        chomping = None
        increment = None
        ch = self.reader.peek()
        if ch in u'+-':
            if ch == '+':
                chomping = True
            else:
                chomping = False
            self.reader.forward()
            ch = self.reader.peek()
            if ch in u'0123456789':
                increment = int(ch)
                if increment == 0:
                    raise ScannerError("while scanning a block scalar", start_marker,
                            "expected indentation indicator in the range 1-9, but found 0",
                            self.reader.get_marker())
                self.reader.forward()
        elif ch in u'0123456789':
            increment = int(ch)
            if increment == 0:
                raise ScannerError("while scanning a block scalar", start_marker,
                        "expected indentation indicator in the range 1-9, but found 0",
                        self.reader.get_marker())
            self.reader.forward()
            ch = self.reader.peek()
            if ch in u'+-':
                if ch == '+':
                    chomping = True
                else:
                    chomping = False
                self.reader.forward()
        ch = self.reader.peek()
        if ch not in u'\0 \r\n\x85\u2028\u2029':
            raise ScannerError("while scanning a block scalar", start_marker,
                    "expected chomping or indentation indicators, but found %r"
                        % ch.encode('utf-8'), self.reader.get_marker())
        return chomping, increment

    def scan_block_scalar_ignored_line(self, start_marker):
        # See the specification for details.
        while self.reader.peek() == u' ':
            self.reader.forward()
        if self.reader.peek() == u'#':
            while self.reader.peek() not in u'\0\r\n\x85\u2028\u2029':
                self.reader.forward()
        ch = self.reader.peek()
        if ch not in u'\0\r\n\x85\u2028\u2029':
            raise ScannerError("while scanning a block scalar", start_marker,
                    "expected a comment or a line break, but found %r"
                        % ch.encode('utf-8'), self.reader.get_marker())
        self.scan_line_break()

    def scan_block_scalar_indentation(self):
        # See the specification for details.
        chunks = []
        max_indent = 0
        end_marker = self.reader.get_marker()
        while self.reader.peek() in u' \r\n\x85\u2028\u2029':
            if self.reader.peek() != u' ':
                chunks.append(self.scan_line_break())
                end_marker = self.reader.get_marker()
            else:
                self.reader.forward()
                if self.reader.column > max_indent:
                    max_indent = self.reader.column
        return chunks, max_indent, end_marker

    def scan_block_scalar_breaks(self, indent):
        # See the specification for details.
        chunks = []
        end_marker = self.reader.get_marker()
        while self.reader.column < indent and self.reader.peek() == u' ':
            self.reader.forward()
        while self.reader.peek() in u'\r\n\x85\u2028\u2029':
            chunks.append(self.scan_line_break())
            end_marker = self.reader.get_marker()
            while self.reader.column < indent and self.reader.peek() == u' ':
                self.reader.forward()
        return chunks, end_marker

    def scan_flow_scalar(self, double):
        # See the specification for details.
        chunks = []
        start_marker = self.reader.get_marker()
        indent = self.indent+1
        if indent == 0:
            indent = 1
        quote = self.reader.peek()
        self.reader.forward()
        chunks.extend(self.scan_flow_scalar_non_spaces(double, indent, start_marker))
        while self.reader.peek() != quote:
            chunks.extend(self.scan_flow_scalar_spaces(double, indent, start_marker))
            chunks.extend(self.scan_flow_scalar_non_spaces(double, indent, start_marker))
        self.reader.forward()
        end_marker = self.reader.get_marker()
        return ScalarToken(u''.join(chunks), False, start_marker, end_marker)

    ESCAPE_REPLACEMENTS = {
        u'0':   u'\0',
        u'a':   u'\x07',
        u'b':   u'\x08',
        u't':   u'\x09',
        u'\t':  u'\x09',
        u'n':   u'\x0A',
        u'v':   u'\x0B',
        u'f':   u'\x0C',
        u'r':   u'\x0D',
        u'e':   u'\x1B',
        u' ':   u'\x20',
        u'\"':  u'\"',
        u'\\':  u'\\',
        u'N':   u'\x85',
        u'_':   u'\xA0',
        u'L':   u'\u2028',
        u'P':   u'\u2029',
    }

    ESCAPE_CODES = {
        u'x':   2,
        u'u':   4,
        u'U':   8,
    }

    def scan_flow_scalar_non_spaces(self, double, indent, start_marker):
        # See the specification for details.
        chunks = []
        while True:
            length = 0
            while self.reader.peek(length) not in u'\'\"\\\0 \t\r\n\x85\u2028\u2029':
                length += 1
            if length:
                chunks.append(self.reader.prefix(length))
                self.reader.forward(length)
            ch = self.reader.peek()
            if not double and ch == u'\'' and self.reader.peek(1) == u'\'':
                chunks.append(u'\'')
                self.reader.forward(2)
            elif (double and ch == u'\'') or (not double and ch in u'\"\\'):
                chunks.append(ch)
                self.reader.forward()
            elif double and ch == u'\\':
                self.reader.forward()
                ch = self.reader.peek()
                if ch in self.ESCAPE_REPLACEMENTS:
                    chunks.append(self.ESCAPE_REPLACEMENTS[ch])
                    self.reader.forward()
                elif ch in self.ESCAPE_CODES:
                    length = self.ESCAPE_CODES[ch]
                    self.reader.forward()
                    for k in range(length):
                        if self.reader.peek(k) not in u'0123456789ABCDEFabcdef':
                            raise ScannerError("while scanning a double-quoted scalar", start_marker,
                                    "expected escape sequence of %d hexdecimal numbers, but found %r" %
                                        (length, self.reader.peek(k).encode('utf-8')), self.reader.get_marker())
                    code = int(self.reader.prefix(length), 16)
                    chunks.append(unichr(code))
                    self.reader.forward(length)
                elif ch in u'\r\n\x85\u2028\u2029':
                    self.scan_line_break()
                    chunks.extend(self.scan_flow_scalar_breaks(double, indent, start_marker))
                else:
                    raise ScannerError("while scanning a double-quoted scalar", start_marker,
                            "found unknown escape character %r" % ch.encode('utf-8'), self.reader.get_marker())
            else:
                return chunks

    def scan_flow_scalar_spaces(self, double, indent, start_marker):
        # See the specification for details.
        chunks = []
        length = 0
        while self.reader.peek(length) in u' \t':
            length += 1
        whitespaces = self.reader.prefix(length)
        self.reader.forward(length)
        ch = self.reader.peek()
        if ch == u'\0':
            raise ScannerError("while scanning a quoted scalar", start_marker,
                    "found unexpected end of stream", self.reader.get_marker())
        elif ch in u'\r\n\x85\u2028\u2029':
            line_break = self.scan_line_break()
            breaks = self.scan_flow_scalar_breaks(double, indent, start_marker)
            if line_break != u'\n':
                chunks.append(line_break)
            elif not breaks:
                chunks.append(u' ')
            chunks.extend(breaks)
        else:
            chunks.append(whitespaces)
        return chunks

    def scan_flow_scalar_breaks(self, double, indent, start_marker):
        # See the specification for details.
        chunks = []
        while True:
            while self.reader.column < indent and self.reader.peek() == u' ':
                self.reader.forward()
            if self.reader.column < indent  \
                    and self.reader.peek() not in u'\0\r\n\x85\u2028\u2029':
                s = 's'
                if indent == 1:
                    s = ''
                raise ScannerError("while scanning a quoted scalar", start_marker,
                        "expected %d space%s indentation, but found %r"
                        % (indent, s, self.reader.peek().encode('utf-8')),
                        self.reader.get_marker())
            while self.reader.peek() in u' \t':
                self.reader.forward()
            if self.reader.peek() in u'\r\n\x85\u2028\u2029':
                chunks.append(self.scan_line_break())
            else:
                return chunks

    def scan_plain(self):
        # See the specification for details.
        # We add an additional restriction for the flow context:
        #   plain scalars in the flow context cannot contain ':' and '?'.
        # We also keep track of the `allow_simple_key` flag here.
        chunks = []
        start_marker = self.reader.get_marker()
        end_marker = start_marker
        indent = self.indent+1
        if indent == 0:
            indent = 1
        spaces = []
        while True:
            length = 0
            if self.reader.peek() == u'#':
                break
            while True:
                ch = self.reader.peek(length)
                if ch in u'\0 \t\r\n\x85\u2028\u2029'   \
                        or (not self.flow_level and ch == u':' and
                                self.reader.peek(length+1) in u'\0 \t\r\n\x28\u2028\u2029') \
                        or (self.flow_level and ch in u',:?[]{}'):
                    break
                length += 1
            if length == 0:
                break
            self.allow_simple_key = False
            chunks.extend(spaces)
            chunks.append(self.reader.prefix(length))
            self.reader.forward(length)
            end_marker = self.reader.get_marker()
            spaces = self.scan_plain_spaces(indent)
            if not spaces or self.reader.peek() == u'#' \
                    or self.reader.column < indent:
                break
        return ScalarToken(u''.join(chunks), True, start_marker, end_marker)

    def scan_plain_spaces(self, indent):
        # See the specification for details.
        # The specification is really confusing about tabs in plain scalars.
        # We just forbid them completely. Do not use tabs in YAML!
        chunks = []
        length = 0
        while self.reader.peek(length) in u' ':
            length += 1
        whitespaces = self.reader.prefix(length)
        self.reader.forward(length)
        ch = self.reader.peek()
        if ch in u'\r\n\x85\u2028\u2029':
            line_break = self.scan_line_break()
            self.allow_simple_key = True
            breaks = []
            while self.reader.peek() in u' \r\n\x85\u2028\u2029':
                if self.reader.peek() == ' ':
                    self.reader.forward()
                else:
                    breaks.append(self.scan_line_break())
            if line_break != u'\n':
                chunks.append(line_break)
            elif not breaks:
                chunks.append(u' ')
            chunks.extend(breaks)
        elif whitespaces:
            chunks.append(whitespaces)
        return chunks

    def scan_tag_handle(self, name, start_marker):
        # See the specification for details.
        # For some strange reasons, the specification does not allow '_' in
        # tag handles. I have allowed it anyway.
        if self.reader.peek() != u'!':
            raise ScannerError("while scanning a %s" % name, start_marker,
                    "expected '!', but found %r" % ch.encode('utf-8'),
                    self.reader.get_marker())
        length = 1
        ch = self.reader.peek(length)
        if ch != u' ':
            while u'0' <= ch <= u'9' or u'A' <= ch <= 'Z' or u'a' <= ch <= 'z'  \
                    or ch in u'-_':
                length += 1
                ch = self.reader.peek(length)
            if ch != u'!':
                self.reader.forward(length)
                raise ScannerError("while scanning a %s" % name, start_marker,
                        "expected '!', but found %r" % ch.encode('utf-8'),
                        self.reader.get_marker())
            length += 1
        value = self.reader.prefix(length)
        self.reader.forward(length)
        return value

    def scan_tag_uri(self, name, start_marker):
        # See the specification for details.
        # Note: we do not check if URI is well-formed.
        chunks = []
        length = 0
        ch = self.reader.peek(length)
        while u'0' <= ch <= u'9' or u'A' <= ch <= 'Z' or u'a' <= ch <= 'z'  \
                or ch in u'-;/?:@&=+$,_.!~*\'()[]%':
            if ch == u'%':
                chunks.append(self.reader.prefix(length))
                self.reader.forward(length)
                length = 0
                chunks.append(self.scan_uri_escapes(name, start_marker))
            else:
                length += 1
            ch = self.reader.peek(length)
        if length:
            chunks.append(self.reader.prefix(length))
            self.reader.forward(length)
            length = 0
        if not chunks:
            raise ScannerError("while parsing a %s" % name, start_marker,
                    "expected URI, but found %r" % ch.encode('utf-8'),
                    self.reader.get_marker())
        return u''.join(chunks)

    def scan_uri_escapes(self, name, start_marker):
        # See the specification for details.
        bytes = []
        marker = self.reader.get_marker()
        while self.reader.peek() == u'%':
            self.reader.forward()
            for k in range(2):
                if self.reader.peek(k) not in u'0123456789ABCDEFabcdef':
                    raise ScannerError("while scanning a %s" % name, start_marker,
                            "expected URI escape sequence of 2 hexdecimal numbers, but found %r" %
                                (self.reader.peek(k).encode('utf-8')), self.reader.get_marker())
            bytes.append(chr(int(self.reader.prefix(2), 16)))
            self.reader.forward(2)
        try:
            value = unicode(''.join(bytes), 'utf-8')
        except UnicodeDecodeError, exc:
            raise ScannerError("while scanning a %s" % name, start_marker, str(exc), marker)
        return value

    def scan_line_break(self):
        # Transforms:
        #   '\r\n'      :   '\n'
        #   '\r'        :   '\n'
        #   '\n'        :   '\n'
        #   '\x85'      :   '\n'
        #   '\u2028'    :   '\u2028'
        #   '\u2029     :   '\u2029'
        #   default     :   ''
        ch = self.reader.peek()
        if ch in u'\r\n\x85':
            if self.reader.prefix(2) == u'\r\n':
                self.forward(2)
            else:
                self.reader.forward()
            return u'\n'
        elif ch in u'\u2028\u2029':
            self.reader.forward()
            return ch
        return u''

#try:
#    import psyco
#    psyco.bind(Scanner)
#except ImportError:
#    pass

