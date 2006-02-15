
# Tokens:
# YAML-DIRECTIVE(major_version, minor_version), TAG-DIRECTIVE(handle, prefix)
# RESERVED-DIRECTIVE(name)
# DOCUMENT-START, DOCUMENT-END
# BLOCK-SEQUENCE-START, BLOCK-MAPPING-START, BLOCK-END
# FLOW-SEQUENCE-START, FLOW-MAPPING-START, FLOW-SEQUENCE-END, FLOW-MAPPING-END
# ENTRY, KEY, VALUE
# ALIAS(name), ANCHOR(name), TAG(value), SCALAR(value, plain)


from marker import Marker
#from error import YAMLError
from stream import Stream

#class ScannerError(YAMLError):
class ScannerError(Exception):
    pass

class Token:
    def __init__(self, start_marker, end_marker):
        self.start_marker = start_marker
        self.end_marker = end_marker

class DirectiveToken(Token):
    pass

class YAMLDirectiveToken(DirectiveToken):
    def __init__(self, major_version, minor_version, start_marker, end_marker):
        self.major_version = major_version
        self.minor_version = minor_version
        self.start_marker = start_marker
        self.end_marker = end_marker

class TagDirectiveToken(DirectiveToken):
    pass

class ReservedDirectiveToken(DirectiveToken):
    def __init__(self, name, start_marker, end_marker):
        self.name = name
        self.start_marker = start_marker
        self.end_marker = end_marker

class DocumentStartToken(Token):
    pass

class DocumentEndToken(Token):
    pass

class EndToken(Token):
    pass

class BlockSequenceStartToken(Token):
    pass

class BlockMappingStartToken(Token):
    pass

class BlockEndToken(Token):
    pass

class FlowSequenceStartToken(Token):
    pass

class FlowMappingStartToken(Token):
    pass

class FlowSequenceEndToken(Token):
    pass

class FlowMappingEndToken(Token):
    pass

class KeyToken(Token):
    pass

class ValueToken(Token):
    pass

class EntryToken(Token):
    pass

class AliasToken(Token):
    def __init__(self, value, start_marker, end_marker):
        self.value = value
        self.start_marker = start_marker
        self.end_marker = end_marker

class AnchorToken(Token):
    def __init__(self, value, start_marker, end_marker):
        self.value = value
        self.start_marker = start_marker
        self.end_marker = end_marker

class TagToken(Token):
    def __init__(self, value, start_marker, end_marker):
        self.value = value
        self.start_marker = start_marker
        self.end_marker = end_marker

class ScalarToken(Token):
    def __init__(self, value, plain, start_marker, end_marker):
        self.value = value
        self.plain = plain
        self.start_marker = start_marker
        self.end_marker = end_marker

class SimpleKey:
    def __init__(self, token_number, required, index, line, column, marker):
        self.token_number = token_number
        self.required = required
        self.index = index
        self.line = line
        self.column = column
        self.marker = marker

class Scanner:

    def __init__(self, source, data):
        """Initialize the scanner."""
        # The input stream. The Stream class do the dirty work of checking for
        # BOM and converting the input data to Unicode. It also adds NUL to
        # the end.
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
        self.unwind_indent(self.stream.column)

        #print
        #print self.stream.get_marker().get_snippet()

        # Peek the next character.
        ch = self.stream.peek()

        # Is it the end of stream?
        if ch == u'\0':
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
        self.invalid_token()

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
            if key.line != self.stream.line  \
                    or self.stream.index-key.index > 1024:
                if key.required:
                    self.fail("simple key is required")
                del self.possible_simple_keys[level]

    def save_possible_simple_key(self):
        # The next token may start a simple key. We check if it's possible
        # and save its position. This function is called for
        #   ALIAS, ANCHOR, TAG, SCALAR(flow), '[', and '{'.

        # Check if a simple key is required at the current position.
        required = not self.flow_level and self.indent == self.stream.column

        # The next token might be a simple key. Let's save it's number and
        # position.
        if self.allow_simple_key:
            self.remove_possible_simple_key()
            token_number = self.tokens_taken+len(self.tokens)
            index = self.stream.index
            line = self.stream.line
            column = self.stream.column
            marker = self.stream.get_marker()
            key = SimpleKey(token_number, required,
                    index, line, column, marker)
            self.possible_simple_keys[self.flow_level] = key

        # A simple key is required at the current position.
        elif required:
            self.fail("simple key is required")

    def remove_possible_simple_key(self):
        # Remove the saved possible key position at the current flow level.
        if self.flow_level in self.possible_simple_keys:
            key = self.possible_simple_keys[self.flow_level]
            if key.required:
                self.fail("simple key is required")

    # Indentation functions.

    def unwind_indent(self, column):

        # In flow context, tokens should respect indentation.
        if self.flow_level and self.indent > column:
            self.fail("invalid intendation in the flow context")

        # In block context, we may need to issue the BLOCK-END tokens.
        while self.indent > column:
            marker = self.stream.get_marker()
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

    def fetch_end(self):

        # Set the current intendation to -1.
        self.unwind_indent(-1)

        # Reset everything (not really needed).
        self.allow_simple_key = False
        self.possible_simple_keys = {}

        # Read the token.
        marker = self.stream.get_marker()
        
        # Add END.
        self.tokens.append(EndToken(marker, marker))

        # The stream is ended.
        self.done = True

    def fetch_directive(self):
        
        # Set the current intendation to -1.
        self.unwind_indent(-1)

        # Reset simple keys.
        self.remove_possible_simple_key()
        self.allow_simple_key = False

        # Scan and add DIRECTIVE.
        self.scan_directive()

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
        start_marker = self.stream.get_marker()
        self.stream.read(3)
        end_marker = self.stream.get_marker()
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
        start_marker = self.stream.get_marker()
        self.stream.read()
        end_marker = self.stream.get_marker()
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
        start_marker = self.stream.get_marker()
        self.stream.read()
        end_marker = self.stream.get_marker()
        self.tokens.append(TokenClass(start_marker, end_marker))

    def fetch_entry(self):

        # Block context needs additional checks.
        if not self.flow_level:

            # Are we allowed to start a new entry?
            if not self.allow_simple_key:
                self.fail("Cannot start a new entry here")

            # We may need to add BLOCK-SEQUENCE-START.
            if self.add_indent(self.stream.column):
                marker = self.stream.get_marker()
                self.tokens.append(BlockSequenceStartToken(marker, marker))

        # Simple keys are allowed after '-' and ','.
        self.allow_simple_key = True

        # Reset possible simple key on the current level.
        self.remove_possible_simple_key()

        # Add ENTRY.
        start_marker = self.stream.get_marker()
        self.stream.read()
        end_marker = self.stream.get_marker()
        self.tokens.append(EntryToken(start_marker, end_marker))

    def fetch_key(self):
        
        # Block context needs additional checks.
        if not self.flow_level:

            # Are we allowed to start a key (not nessesary a simple)?
            if not self.allow_simple_key:
                self.fail("Cannot start a new key here")

            # We may need to add BLOCK-MAPPING-START.
            if self.add_indent(self.stream.column):
                marker = self.stream.get_marker()
                self.tokens.append(BlockMappingStartToken(marker, marker))

        # Simple keys are allowed after '?' in the block context.
        self.allow_simple_key = not self.flow_level

        # Reset possible simple key on the current level.
        self.remove_possible_simple_key()

        # Add KEY.
        start_marker = self.stream.get_marker()
        self.stream.read()
        end_marker = self.stream.get_marker()
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
            
            # Simple keys are allowed after ':' in the block context.
            self.allow_simple_key = not self.flow_level

            # Reset possible simple key on the current level.
            self.remove_possible_simple_key()

        # Add VALUE.
        start_marker = self.stream.get_marker()
        self.stream.read()
        end_marker = self.stream.get_marker()
        self.tokens.append(ValueToken(start_marker, end_marker))

    def fetch_alias(self):

        # ALIAS could be a simple key.
        self.save_possible_simple_key()

        # No simple keys after ALIAS.
        self.allow_simple_key = False

        # Scan and add ALIAS.
        self.scan_anchor(AliasToken)

    def fetch_anchor(self):

        # ANCHOR could start a simple key.
        self.save_possible_simple_key()

        # No simple keys after ANCHOR.
        self.allow_simple_key = False

        # Scan and add ANCHOR.
        self.scan_anchor(AnchorToken)

    def fetch_tag(self):

        # TAG could start a simple key.
        self.save_possible_simple_key()

        # No simple keys after TAG.
        self.allow_simple_key = False

        # Scan and add TAG.
        self.scan_tag()

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
        self.scan_block_scalar(folded)

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
        self.scan_flow_scalar(double)

    def fetch_plain(self):

        # A plain scalar could be a simple key.
        self.save_possible_simple_key()

        # No simple keys after plain scalars. But note that `scan_plain` will
        # change this flag if the scan is finished at the beginning of the
        # line.
        self.allow_simple_key = False

        # Scan and add SCALAR. May change `allow_simple_key`.
        self.scan_plain()

    # Checkers.

    def check_directive(self):

        # DIRECTIVE:        ^ '%' ...
        # The '%' indicator is already checked.
        if self.stream.column == 0:
            return True

    def check_document_start(self):

        # DOCUMENT-START:   ^ '---' (' '|'\n')
        if self.stream.column == 0:
            prefix = self.stream.peek(4)
            if prefix[:3] == u'---' and prefix[3] in u'\0 \t\r\n\x85\u2028\u2029':
                return True

    def check_document_end(self):

        # DOCUMENT-END:     ^ '...' (' '|'\n')
        if self.stream.column == 0:
            prefix = self.stream.peek(4)
            if prefix[:3] == u'...' and prefix[3] in u'\0 \t\r\n\x85\u2028\u2029':
                return True

    def check_entry(self):

        # ENTRY(flow context):      ','
        if self.flow_level:
            return self.stream.peek() == u','

        # ENTRY(block context):     '-' (' '|'\n')
        else:
            prefix = self.stream.peek(2)
            return prefix[0] == u'-' and prefix[1] in u'\0 \t\r\n\x85\u2028\u2029'

    def check_key(self):

        # KEY(flow context):    '?'
        if self.flow_level:
            return True

        # KEY(block context):   '?' (' '|'\n')
        else:
            prefix = self.stream.peek(2)
            return prefix[1] in u'\0 \t\r\n\x85\u2028\u2029'

    def check_value(self):

        # VALUE(flow context):  ':'
        if self.flow_level:
            return True

        # VALUE(block context): ':' (' '|'\n')
        else:
            prefix = self.stream.peek(2)
            return prefix[1] in u'\0 \t\r\n\x85\u2028\u2029'

    def check_plain(self):
        return True

    # Scanners.

    def scan_to_next_token(self):
        found = False
        while not found:
            while self.stream.peek() == u' ':
                self.stream.read()
            if self.stream.peek() == u'#':
                while self.stream.peek() not in u'\r\n':
                    self.stream.read()
            if self.stream.peek() in u'\r\n':
                self.stream.read()
                if not self.flow_level:
                    self.allow_simple_key = True
            else:
                found = True

    def scan_directive(self):
        marker = self.stream.get_marker()
        if self.stream.peek(5) == u'%YAML ':
            self.tokens.append(YAMLDirectiveToken(1, 1, marker, marker))
        elif self.stream.peek(4) == u'%TAG ':
            self.tokens.append(TagDirectiveToken(marker, marker))
        else:
            self.tokens.append(ReservedDirectiveToken('', marker, marker))
        while self.stream.peek() not in u'\0\r\n':
            self.stream.read()
        self.stream.read()

    def scan_anchor(self, TokenClass):
        start_marker = self.stream.get_marker()
        while self.stream.peek() not in u'\0 \t\r\n,:':
            self.stream.read()
        end_marker = self.stream.get_marker()
        self.tokens.append(TokenClass('', start_marker, end_marker))

    def scan_tag(self):
        start_marker = self.stream.get_marker()
        while self.stream.peek() not in u'\0 \t\r\n':
            self.stream.read()
        end_marker = self.stream.get_marker()
        self.tokens.append(TagToken('', start_marker, end_marker))

    def scan_block_scalar(self, folded):
        start_marker = self.stream.get_marker()
        indent = self.indent+1
        if indent < 1:
            indent = 1
        while True:
            while self.stream.peek() and self.stream.peek() and self.stream.peek() not in u'\0\r\n\x85\u2028\u2029':
                self.stream.read()
            if self.stream.peek() != u'\0':
                self.stream.read()
            count = 0
            while count < indent and self.stream.peek() == u' ':
                self.stream.read()
                count += 1
            if count < indent and self.stream.peek() not in u'#\r\n\x85\u2028\u2029':
                break
        self.tokens.append(ScalarToken('', False, start_marker, start_marker))

    def scan_flow_scalar(self, double):
        marker = self.stream.get_marker()
        quote = self.stream.read()
        while self.stream.peek() != quote:
            if double and self.stream.peek() == u'\\':
                self.stream.read(2)
            elif not double and self.stream.peek(3)[1:] == u'\'\'':
                self.stream.read(3)
            else:
                self.stream.read(1)
        self.stream.read(1)
        self.tokens.append(ScalarToken('', False, marker, marker))

    def scan_plain(self):
        indent = self.indent+1
        if indent < 1:
            indent = 1
        space = False
        marker = self.stream.get_marker()
        while True:
            while self.stream.peek() == u' ':
                self.stream.read()
                space = True
            while self.stream.peek() not in u'\0\r\n?:,[]{}#'   \
                    or (not space and self.stream.peek() == '#')    \
                    or (not self.flow_level and self.stream.peek() in '?,[]{}') \
                    or (not self.flow_level and self.stream.peek() == ':' and self.stream.peek(2)[1] not in u' \0\r\n'):
                space = self.stream.peek() not in u' \t'
                self.stream.read()
                self.allow_simple_key = False
            if self.stream.peek() not in u'\r\n':
                break
            while self.stream.peek() in u'\r\n':
                self.stream.read()
                if not self.flow_level:
                    self.allow_simple_key = True
            count = 0
            while self.stream.peek() == u' ' and count < indent:
                self.stream.read()
                count += 1
            if count < indent:
                break
            space = True
        self.tokens.append(ScalarToken('', True, marker, marker))

    def invalid_token(self):
        self.fail("invalid token")

    def fail(self, message):
        raise ScannerError(message)

