# This module contains abstractions for the input stream. You don't have to
# looks further, there are no pretty code.
#
# We define two classes here.
#
#   Marker(source, line, column)
# It's just a record and its only use is producing nice error messages.
# Parser does not use it for any other purposes.
#
#   Stream(source, data)
# Stream determines the encoding of `data` and converts it to unicode.
# Stream provides the following methods and attributes:
#   stream.peek(length=1) - return the next `length` characters
#   stream.forward(length=1) - move the current position to `length` characters.
#   stream.index - the number of the current character.
#   stream.line, stream.column - the line and the column of the current character.


from error import YAMLError

import codecs, re

# Unfortunately, codec functions in Python 2.3 does not support the `finish`
# arguments, so we have to write our own wrappers.

try:
    codecs.utf_8_decode('', 'strict', False)
    from codecs import utf_8_decode, utf_16_le_decode, utf_16_be_decode

except TypeError:

    def utf_16_le_decode(data, errors, finish=False):
        if not finish and len(data) % 2 == 1:
            data = data[:-1]
        return codecs.utf_16_le_decode(data, errors)

    def utf_16_be_decode(data, errors, finish=False):
        if not finish and len(data) % 2 == 1:
            data = data[:-1]
        return codecs.utf_16_be_decode(data, errors)

    def utf_8_decode(data, errors, finish=False):
        if not finish:
            # We are trying to remove a possible incomplete multibyte character
            # from the suffix of the data.
            # The first byte of a multi-byte sequence is in the range 0xc0 to 0xfd.
            # All further bytes are in the range 0x80 to 0xbf.
            # UTF-8 encoded UCS characters may be up to six bytes long.
            count = 0
            while count < 5 and count < len(data)   \
                    and '\x80' <= data[-count-1] <= '\xBF':
                count -= 1
            if count < 5 and count < len(data)  \
                    and '\xC0' <= data[-count-1] <= '\xFD':
                data = data[:-count-1]
        return codecs.utf_8_decode(data, errors)

class Marker:

    def __init__(self, source, line, column, buffer, pointer):
        self.source = source
        self.line = line
        self.column = column
        self.buffer = buffer
        self.pointer = pointer

    def get_snippet(self, max_length=79):
        if self.buffer is None:
            return None
        head = ''
        start = self.pointer
        while start > 0 and self.buffer[start-1] not in u'\0\r\n\x85\u2028\u2029':
            start -= 1
            if self.pointer-start > max_length/2-1:
                head = ' ... '
                start += 5
                break
        tail = ''
        end = self.pointer
        while end < len(self.buffer) and self.buffer[end] not in u'\0\r\n\x85\u2028\u2029':
            end += 1
            if end-self.pointer > max_length/2-1:
                tail = ' ... '
                end -= 5
                break
        snippet = self.buffer[start:end].encode('utf-8')
        return head + snippet + tail + '\n'  \
                + ' '*(self.pointer-start+len(head)) + '^' + '\n'

class StreamError(YAMLError):

    def __init__(self, source, encoding, character, position, reason):
        self.source = source
        self.encoding = encoding
        self.character = character
        self.position = position
        self.reason = reason

    def __str__(self):
        if isinstance(self.character, str):
            return "'%s' codec can't decode byte #x%02x: %s\n"  \
                    "\tin file '%s', position %d."   \
                    % (self.encoding, ord(self.character), self.reason,
                            self.source, self.position)
        else:
            return "unacceptable character #x%04x: %s\n"    \
                    "\tin file '%s', position %d."   \
                    % (ord(self.character), self.reason,
                            self.source, self.position)

class Stream:
    # Stream:
    # - determines the data encoding and converts it to unicode,
    # - checks if characters are in allowed range,
    # - adds '\0' to the end.

    # Yeah, it's ugly and slow.

    def __init__(self, source, data):
        self.source = source
        self.stream = None
        self.stream_pointer = 0
        self.eof = True
        self.buffer = u''
        self.pointer = 0
        self.raw_buffer = None
        self.raw_decoder = None
        self.index = 0
        self.line = 0
        self.column = 0
        if isinstance(data, unicode):
            self.check_printable(data)
            self.buffer = data+u'\0'
        elif isinstance(data, str):
            self.raw_buffer = data
            self.determine_encoding()
        else:
            self.stream = data
            self.eof = False
            self.raw_buffer = ''
            self.determine_encoding()

    def peek(self, length=1):
        if self.pointer+length >= len(self.buffer):
            self.update(length)
        return self.buffer[self.pointer:self.pointer+length]

    def forward(self, length=1):
        if self.pointer+length+1 >= len(self.buffer):
            self.update(length+1)
        for k in range(length):
            ch = self.buffer[self.pointer]
            self.pointer += 1
            self.index += 1
            if ch in u'\n\x85\u2028\u2029'  \
                    or (ch == u'\r' and self.buffer[self.pointer+1] != u'\n'):
                self.line += 1
                self.column = 0
            elif ch != u'\uFEFF':
                self.column += 1

    def get_marker(self):
        if self.stream is None:
            return Marker(self.source, self.line, self.column,
                    self.buffer, self.pointer)
        else:
            return Marker(self.source, self.line, self.column, None, None)

    def determine_encoding(self):
        while not self.eof and len(self.raw_buffer) < 2:
            self.update_raw()
        if self.raw_buffer.startswith(codecs.BOM_UTF16_LE):
            self.raw_decode = utf_16_le_decode
        elif self.raw_buffer.startswith(codecs.BOM_UTF16_BE):
            self.raw_decode = utf_16_be_decode
        else:
            self.raw_decode = utf_8_decode
        self.update(1)

    NON_PRINTABLE = re.compile(u'[^\x09\x0A\x0D\x20-\x7E\x85\xA0-\uD7FF\uE000-\uFFFD]')
    def check_printable(self, data):
        match = self.NON_PRINTABLE.search(data)
        if match:
            character = match.group()
            position = self.index+(len(self.buffer)-self.pointer)+match.start()
            raise StreamError(self.source, 'unicode', character, position,
                    "control characters are not allowed")

    def update(self, length):
        if self.raw_buffer is None:
            return
        self.buffer = self.buffer[self.pointer:]
        self.pointer = 0
        while len(self.buffer) < length:
            if not self.eof:
                self.update_raw()
            try:
                data, converted = self.raw_decode(self.raw_buffer,
                        'strict', self.eof)
            except UnicodeDecodeError, exc:
                character = exc.object[exc.start]
                if self.stream is not None:
                    position = self.stream_pointer-len(self.raw_buffer)+exc.start
                else:
                    position = exc.start
                raise StreamError(self.source, exc.encoding,
                        character, position, exc.reason)
            self.check_printable(data)
            self.buffer += data
            self.raw_buffer = self.raw_buffer[converted:]
            if self.eof:
                self.buffer += u'\0'
                self.raw_buffer = None
                break

    def update_raw(self, size=1024):
        data = self.stream.read(size)
        if data:
            self.raw_buffer += data
            self.stream_pointer += len(data)
        else:
            self.eof = True

#try:
#    import psyco
#    psyco.bind(Stream)
#except ImportError:
#    pass

