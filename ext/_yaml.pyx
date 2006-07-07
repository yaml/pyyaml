
import yaml

def get_version_string():
    return yaml_get_version_string()

def get_version():
    cdef int major, minor, patch
    yaml_get_version(&major, &minor, &patch)
    return (major, minor, patch)

def test_scanner(data):
    cdef yaml_parser_t *parser
    cdef yaml_token_t *token
    cdef int done
    if PyString_CheckExact(data) == 0:
        raise TypeError("string input required")
    parser = yaml_parser_new()
    if parser == NULL:
        raise MemoryError
    yaml_parser_set_input_string(parser, PyString_AS_STRING(data), PyString_GET_SIZE(data))
    done = 0
    while done == 0:
        token = yaml_parser_get_token(parser)
        if token == NULL:
            raise MemoryError
        if token.type == YAML_STREAM_END_TOKEN:
            done = 1
        yaml_token_delete(token)
    yaml_parser_delete(parser)

def test_parser(data):
    cdef yaml_parser_t *parser
    cdef yaml_event_t *event
    cdef int done
    if PyString_CheckExact(data) == 0:
        raise TypeError("string input required")
    parser = yaml_parser_new()
    if parser == NULL:
        raise MemoryError
    yaml_parser_set_input_string(parser, PyString_AS_STRING(data), PyString_GET_SIZE(data))
    done = 0
    while done == 0:
        event = yaml_parser_get_event(parser)
        if event == NULL:
            raise MemoryError
        if event.type == YAML_STREAM_END_EVENT:
            done = 1
        yaml_event_delete(event)
    yaml_parser_delete(parser)

cdef class ScannerAndParser:

    cdef yaml_parser_t *parser
    cdef int eof
    cdef object stream
    cdef yaml_token_t *cached_token
    cdef yaml_event_t *cached_event
    cdef object cached_obj

    def __init__(self, stream):
        if hasattr(stream, 'read'):
            stream = stream.read()
        if PyUnicode_CheckExact(stream) != 0:
            stream = stream.encode('utf-8')
        if PyString_CheckExact(stream) == 0:
            raise TypeError("a string or stream input is required")
        self.parser = yaml_parser_new()
        if self.parser == NULL:
            raise MemoryError
        yaml_parser_set_input_string(self.parser, PyString_AS_STRING(stream), PyString_GET_SIZE(stream))
        self.eof = 0
        self.stream = stream
        self.cached_token = NULL
        self.cached_obj = None

    def __dealloc__(self):
        if self.parser != NULL:
            yaml_parser_delete(self.parser)
            self.parser = NULL

    cdef object _convert_token(self, yaml_token_t *token):
        if token == NULL:
            if self.parser.error == YAML_MEMORY_ERROR:
                raise MemoryError
            elif self.parser.error == YAML_READER_ERROR:
                raise yaml.reader.ReaderError("<input>",
                        self.parser.problem_offset,
                        self.parser.problem_value,
                        '?', self.parser.problem)
            elif self.parser.error == YAML_SCANNER_ERROR:
                if self.parser.context != NULL:
                    raise yaml.scanner.ScannerError(
                            self.parser.context,
                            yaml.Mark("<input>",
                                self.parser.context_mark.index,
                                self.parser.context_mark.line,
                                self.parser.context_mark.column,
                                None, None),
                            self.parser.problem,
                            yaml.Mark("<input>",
                                self.parser.problem_mark.index,
                                self.parser.problem_mark.line,
                                self.parser.problem_mark.column,
                                None, None))
                else:
                    raise yaml.scanner.ScannerError(None, None,
                            self.parser.problem,
                            yaml.Mark("<input>",
                                self.parser.problem_mark.index,
                                self.parser.problem_mark.line,
                                self.parser.problem_mark.column,
                                None, None))
            else:
                raise RuntimeError("neither error nor token produced")
        start_mark = yaml.Mark("<input>",
                token.start_mark.index,
                token.start_mark.line,
                token.start_mark.column,
                None, None)
        end_mark = yaml.Mark("<input>",
                token.end_mark.index,
                token.end_mark.line,
                token.end_mark.column,
                None, None)
        if token.type == YAML_STREAM_START_TOKEN:
            return yaml.StreamStartToken(start_mark, end_mark)
        elif token.type == YAML_STREAM_END_TOKEN:
            return yaml.StreamEndToken(start_mark, end_mark)
        elif token.type == YAML_VERSION_DIRECTIVE_TOKEN:
            return yaml.DirectiveToken('YAML',
                    (token.data.version_directive.major,
                        token.data.version_directive.minor),
                    start_mark, end_mark)
        elif token.type == YAML_TAG_DIRECTIVE_TOKEN:
            return yaml.DirectiveToken('TAG',
                    (token.data.tag_directive.handle,
                        token.data.tag_directive.prefix),
                    start_mark, end_mark)
        elif token.type == YAML_DOCUMENT_START_TOKEN:
            return yaml.DocumentStartToken(start_mark, end_mark)
        elif token.type == YAML_DOCUMENT_END_TOKEN:
            return yaml.DocumentEndToken(start_mark, end_mark)
        elif token.type == YAML_BLOCK_SEQUENCE_START_TOKEN:
            return yaml.BlockSequenceStartToken(start_mark, end_mark)
        elif token.type == YAML_BLOCK_MAPPING_START_TOKEN:
            return yaml.BlockMappingStartToken(start_mark, end_mark)
        elif token.type == YAML_BLOCK_END_TOKEN:
            return yaml.BlockEndToken(start_mark, end_mark)
        elif token.type == YAML_FLOW_SEQUENCE_START_TOKEN:
            return yaml.FlowSequenceStartToken(start_mark, end_mark)
        elif token.type == YAML_FLOW_SEQUENCE_END_TOKEN:
            return yaml.FlowSequenceEndToken(start_mark, end_mark)
        elif token.type == YAML_FLOW_MAPPING_START_TOKEN:
            return yaml.FlowMappingStartToken(start_mark, end_mark)
        elif token.type == YAML_FLOW_MAPPING_END_TOKEN:
            return yaml.FlowMappingEndToken(start_mark, end_mark)
        elif token.type == YAML_BLOCK_ENTRY_TOKEN:
            return yaml.BlockEntryToken(start_mark, end_mark)
        elif token.type == YAML_FLOW_ENTRY_TOKEN:
            return yaml.FlowEntryToken(start_mark, end_mark)
        elif token.type == YAML_KEY_TOKEN:
            return yaml.KeyToken(start_mark, end_mark)
        elif token.type == YAML_VALUE_TOKEN:
            return yaml.ValueToken(start_mark, end_mark)
        elif token.type == YAML_ALIAS_TOKEN:
            return yaml.AliasToken(token.data.alias.value,
                    start_mark, end_mark)
        elif token.type == YAML_ANCHOR_TOKEN:
            return yaml.AnchorToken(token.data.anchor.value,
                    start_mark, end_mark)
        elif token.type == YAML_TAG_TOKEN:
            handle = token.data.tag.handle
            if handle == '':
                handle = None
            return yaml.TagToken((handle, token.data.tag.suffix),
                    start_mark, end_mark)
        elif token.type == YAML_SCALAR_TOKEN:
            value = PyString_FromStringAndSize(token.data.scalar.value, token.data.scalar.length)
            return yaml.ScalarToken(unicode(value, 'utf-8'),
                    bool(token.data.scalar.style == YAML_PLAIN_SCALAR_STYLE),
                    start_mark, end_mark)
        else:
            raise RuntimeError("unknown token type")

    cdef object _convert_event(self, yaml_event_t *event):
        if event == NULL:
            if self.parser.error == YAML_MEMORY_ERROR:
                raise MemoryError
            elif self.parser.error == YAML_READER_ERROR:
                raise yaml.reader.ReaderError("<input>",
                        self.parser.problem_offset,
                        self.parser.problem_value,
                        '?', self.parser.problem)
            elif self.parser.error == YAML_SCANNER_ERROR:
                if self.parser.context != NULL:
                    raise yaml.scanner.ScannerError(
                            self.parser.context,
                            yaml.Mark("<input>",
                                self.parser.context_mark.index,
                                self.parser.context_mark.line,
                                self.parser.context_mark.column,
                                None, None),
                            self.parser.problem,
                            yaml.Mark("<input>",
                                self.parser.problem_mark.index,
                                self.parser.problem_mark.line,
                                self.parser.problem_mark.column,
                                None, None))
                else:
                    raise yaml.scanner.ScannerError(None, None,
                            self.parser.problem,
                            yaml.Mark("<input>",
                                self.parser.problem_mark.index,
                                self.parser.problem_mark.line,
                                self.parser.problem_mark.column,
                                None, None))
            elif self.parser.error == YAML_PARSER_ERROR:
                if self.parser.context != NULL:
                    raise yaml.parser.ParserError(
                            self.parser.context,
                            yaml.Mark("<input>",
                                self.parser.context_mark.index,
                                self.parser.context_mark.line,
                                self.parser.context_mark.column,
                                None, None),
                            self.parser.problem,
                            yaml.Mark("<input>",
                                self.parser.problem_mark.index,
                                self.parser.problem_mark.line,
                                self.parser.problem_mark.column,
                                None, None))
                else:
                    raise yaml.parser.ParserError(None, None,
                            self.parser.problem,
                            yaml.Mark("<input>",
                                self.parser.problem_mark.index,
                                self.parser.problem_mark.line,
                                self.parser.problem_mark.column,
                                None, None))
            else:
                raise RuntimeError("neither error nor event produced")
        start_mark = yaml.Mark("<input>",
                event.start_mark.index,
                event.start_mark.line,
                event.start_mark.column,
                None, None)
        end_mark = yaml.Mark("<input>",
                event.end_mark.index,
                event.end_mark.line,
                event.end_mark.column,
                None, None)
        if event.type == YAML_STREAM_START_EVENT:
            return yaml.StreamStartEvent(start_mark, end_mark)
        elif event.type == YAML_STREAM_END_EVENT:
            return yaml.StreamEndEvent(start_mark, end_mark)
        elif event.type == YAML_DOCUMENT_START_EVENT:
            return yaml.DocumentStartEvent(start_mark, end_mark,
                    (event.data.document_start.implicit == 0))
        elif event.type == YAML_DOCUMENT_END_EVENT:
            return yaml.DocumentEndEvent(start_mark, end_mark,
                    (event.data.document_end.implicit == 0))
        elif event.type == YAML_SCALAR_EVENT:
            if event.data.scalar.anchor == NULL:
                anchor = None
            else:
                anchor = event.data.scalar.anchor
            if event.data.scalar.tag == NULL:
                tag = None
            else:
                tag = event.data.scalar.tag
            implicit = (event.data.scalar.plain_implicit == 1, event.data.scalar.quoted_implicit == 1)
            flow_style = (event.data.sequence_start.style == YAML_FLOW_SEQUENCE_STYLE)
            value = PyString_FromStringAndSize(event.data.scalar.value, event.data.scalar.length)
            return yaml.ScalarEvent(anchor, tag, implicit, unicode(value, 'utf-8'),
                    start_mark, end_mark)
        elif event.type == YAML_ALIAS_EVENT:
            if event.data.alias.anchor == NULL:
                anchor = None
            else:
                anchor = event.data.alias.anchor
            return yaml.AliasEvent(anchor, start_mark, end_mark)
        elif event.type == YAML_SEQUENCE_START_EVENT:
            if event.data.sequence_start.anchor == NULL:
                anchor = None
            else:
                anchor = event.data.sequence_start.anchor
            if event.data.sequence_start.tag == NULL:
                tag = None
            else:
                tag = event.data.sequence_start.tag
            implicit = (event.data.sequence_start.implicit == 1)
            flow_style = (event.data.sequence_start.style == YAML_FLOW_SEQUENCE_STYLE)
            return yaml.SequenceStartEvent(anchor, tag, implicit,
                    start_mark, end_mark, flow_style)
        elif event.type == YAML_MAPPING_START_EVENT:
            if event.data.mapping_start.anchor == NULL:
                anchor = None
            else:
                anchor = event.data.mapping_start.anchor
            if event.data.mapping_start.tag == NULL:
                tag = None
            else:
                tag = event.data.mapping_start.tag
            implicit = (event.data.mapping_start.implicit == 1)
            flow_style = (event.data.mapping_start.style == YAML_FLOW_MAPPING_STYLE)
            return yaml.MappingStartEvent(anchor, tag, implicit,
                    start_mark, end_mark, flow_style)
        elif event.type == YAML_SEQUENCE_END_EVENT:
            return yaml.SequenceEndEvent(start_mark, end_mark)
        elif event.type == YAML_MAPPING_END_EVENT:
            return yaml.MappingEndEvent(start_mark, end_mark)
        else:
            raise RuntimeError("unknown event type")

    def get_token(self):
        cdef yaml_token_t *token
        if self.cached_token != NULL:
            yaml_token_delete(yaml_parser_get_token(self.parser))
            obj = self.cached_obj
            self.cached_token = NULL
            self.cached_obj = None
            return obj
        if self.eof != 0:
            return None
        token = yaml_parser_get_token(self.parser)
        obj = self._convert_token(token)
        if token.type == YAML_STREAM_END_TOKEN:
            self.eof = 1
        yaml_token_delete(token)
        return obj

    def peek_token(self):
        cdef yaml_token_t *token
        if self.cached_token != NULL:
            return self.cached_obj
        if self.eof != 0:
            return None
        token = yaml_parser_peek_token(self.parser)
        obj = self._convert_token(token)
        if token.type == YAML_STREAM_END_TOKEN:
            self.eof = 1
        self.cached_token = token
        self.cached_obj = obj
        return obj

    def check_token(self, *choices):
        cdef yaml_token_t *token
        if self.cached_token != NULL:
            obj = self.cached_obj
        elif self.eof != 0:
            return False
        else:
            token = yaml_parser_peek_token(self.parser)
            obj = self._convert_token(token)
            if token.type == YAML_STREAM_END_TOKEN:
                self.eof = 1
            self.cached_token = token
            self.cached_obj = obj
        if not choices:
            return True
        for choice in choices:
            if isinstance(obj, choice):
                return True
        return False

    def get_event(self):
        cdef yaml_event_t *event
        if self.cached_event != NULL:
            yaml_event_delete(yaml_parser_get_event(self.parser))
            obj = self.cached_obj
            self.cached_event = NULL
            self.cached_obj = None
            return obj
        if self.eof != 0:
            return None
        event = yaml_parser_get_event(self.parser)
        obj = self._convert_event(event)
        if event.type == YAML_STREAM_END_EVENT:
            self.eof = 1
        yaml_event_delete(event)
        return obj

    def peek_event(self):
        cdef yaml_event_t *event
        if self.cached_event != NULL:
            return self.cached_obj
        if self.eof != 0:
            return None
        event = yaml_parser_peek_event(self.parser)
        obj = self._convert_event(event)
        if event.type == YAML_STREAM_END_EVENT:
            self.eof = 1
        self.cached_event = event
        self.cached_obj = obj
        return obj

    def check_event(self, *choices):
        cdef yaml_event_t *event
        if self.cached_event != NULL:
            obj = self.cached_obj
        elif self.eof != 0:
            return False
        else:
            event = yaml_parser_peek_event(self.parser)
            obj = self._convert_event(event)
            if event.type == YAML_STREAM_END_EVENT:
                self.eof = 1
            self.cached_event = event
            self.cached_obj = obj
        if not choices:
            return True
        for choice in choices:
            if isinstance(obj, choice):
                return True
        return False

class Loader(ScannerAndParser,
        yaml.composer.Composer,
        yaml.constructor.Constructor,
        yaml.resolver.Resolver):

    def __init__(self, stream):
        ScannerAndParser.__init__(self, stream)
        yaml.composer.Composer.__init__(self)
        yaml.constructor.Constructor.__init__(self)
        yaml.resolver.Resolver.__init__(self)

yaml.ExtLoader = Loader

