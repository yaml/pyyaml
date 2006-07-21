
import yaml

def get_version_string():
    return yaml_get_version_string()

def get_version():
    cdef int major, minor, patch
    yaml_get_version(&major, &minor, &patch)
    return (major, minor, patch)

def test_scanner(stream):
    cdef yaml_parser_t parser
    cdef yaml_token_t token
    cdef int done
    cdef int count
    if hasattr(stream, 'read'):
        stream = stream.read()
    if PyUnicode_CheckExact(stream) != 0:
        stream = stream.encode('utf-8')
    if PyString_CheckExact(stream) == 0:
        raise TypeError("a string or stream input is required")
    if yaml_parser_initialize(&parser) == 0:
        raise RuntimeError("cannot initialize parser")
    yaml_parser_set_input_string(&parser, PyString_AS_STRING(stream), PyString_GET_SIZE(stream))
    done = 0
    count = 0
    while done == 0:
        if yaml_parser_scan(&parser, &token) == 0:
            raise RuntimeError("cannot get next token: #%s" % count)
        if token.type == YAML_NO_TOKEN:
            done = 1
        else:
            count = count+1
        yaml_token_delete(&token)
    yaml_parser_delete(&parser)
    dummy = len(stream)
    return count

def test_parser(stream):
    cdef yaml_parser_t parser
    cdef yaml_event_t event
    cdef int done
    cdef int count
    if hasattr(stream, 'read'):
        stream = stream.read()
    if PyUnicode_CheckExact(stream) != 0:
        stream = stream.encode('utf-8')
    if PyString_CheckExact(stream) == 0:
        raise TypeError("a string or stream input is required")
    if yaml_parser_initialize(&parser) == 0:
        raise RuntimeError("cannot initialize parser")
    yaml_parser_set_input_string(&parser, PyString_AS_STRING(stream), PyString_GET_SIZE(stream))
    done = 0
    count = 0
    while done == 0:
        if yaml_parser_parse(&parser, &event) == 0:
            raise RuntimeError("cannot get next event: #%s" % count)
        if event.type == YAML_NO_EVENT:
            done = 1
        else:
            count = count+1
        yaml_event_delete(&event)
    yaml_parser_delete(&parser)
    dummy = len(stream)
    return count

cdef class ScannerAndParser:

    cdef yaml_parser_t parser

    cdef object stream
    cdef object current_token
    cdef object current_event

    cdef object cached_input
    cdef object cached_YAML
    cdef object cached_TAG
    cdef object cached_question
    cdef object cached_Mark
    cdef object cached_ReaderError
    cdef object cached_ScannerError
    cdef object cached_ParserError
    cdef object cached_StreamStartToken
    cdef object cached_StreamEndToken
    cdef object cached_DirectiveToken
    cdef object cached_DocumentStartToken
    cdef object cached_DocumentEndToken
    cdef object cached_BlockSequenceStartToken
    cdef object cached_BlockMappingStartToken
    cdef object cached_BlockEndToken
    cdef object cached_FlowSequenceStartToken
    cdef object cached_FlowMappingStartToken
    cdef object cached_FlowSequenceEndToken
    cdef object cached_FlowMappingEndToken
    cdef object cached_BlockEntryToken
    cdef object cached_FlowEntryToken
    cdef object cached_KeyToken
    cdef object cached_ValueToken
    cdef object cached_AliasToken
    cdef object cached_AnchorToken
    cdef object cached_TagToken
    cdef object cached_ScalarToken
    cdef object cached_StreamStartEvent
    cdef object cached_StreamEndEvent
    cdef object cached_DocumentStartEvent
    cdef object cached_DocumentEndEvent
    cdef object cached_AliasEvent
    cdef object cached_SequenceStartEvent
    cdef object cached_SequenceEndEvent
    cdef object cached_MappingStartEvent
    cdef object cached_MappingEndEvent

    def __init__(self, stream):
        if yaml_parser_initialize(&self.parser) == 0:
            raise MemoryError
        if hasattr(stream, 'read'):
            self.stream = stream
            yaml_parser_set_input(&self.parser, input_handler, <void *>self)
        else:
            if PyUnicode_CheckExact(stream) != 0:
                stream = PyUnicode_AsUTF8String(stream)
            if PyString_CheckExact(stream) == 0:
                raise TypeError("a string or stream input is required")
            self.stream = stream
            yaml_parser_set_input_string(&self.parser, PyString_AS_STRING(stream), PyString_GET_SIZE(stream))
        self.current_token = None
        self._cache_names()

    def get_token(self):
        if self.current_token is not None:
            value = self.current_token
            self.current_token = None
        else:
            value = self._scan()
        return value

    def peek_token(self):
        if self.current_token is None:
            self.current_token = self._scan()
        return self.current_token

    def check_token(self, *choices):
        if self.current_token is None:
            self.current_token = self._scan()
        if self.current_token is None:
            return False
        if not choices:
            return True
        token_class = self.current_token.__class__
        for choice in choices:
            if token_class is choice:
                return True
        return False

    def get_event(self):
        if self.current_event is not None:
            value = self.current_event
            self.current_event = None
        else:
            value = self._parse()
        return value

    def peek_event(self):
        if self.current_event is None:
            self.current_event = self._parse()
        return self.current_event

    def check_event(self, *choices):
        if self.current_event is None:
            self.current_event = self._parse()
        if self.current_event is None:
            return False
        if not choices:
            return True
        event_class = self.current_event.__class__
        for choice in choices:
            if event_class is choice:
                return True
        return False

    def __dealloc__(self):
        yaml_parser_delete(&self.parser)

    cdef object _cache_names(self):
        self.cached_input = '<input>'
        self.cached_YAML = 'YAML'
        self.cached_TAG = 'TAG'
        self.cached_question = '?'
        self.cached_Mark = yaml.Mark
        self.cached_ReaderError = yaml.reader.ReaderError
        self.cached_ScannerError = yaml.scanner.ScannerError
        self.cached_ParserError = yaml.parser.ParserError
        self.cached_StreamStartToken = yaml.StreamStartToken
        self.cached_StreamEndToken = yaml.StreamEndToken
        self.cached_DirectiveToken = yaml.DirectiveToken
        self.cached_DocumentStartToken = yaml.DocumentStartToken
        self.cached_DocumentEndToken = yaml.DocumentEndToken
        self.cached_BlockSequenceStartToken = yaml.BlockSequenceStartToken
        self.cached_BlockMappingStartToken = yaml.BlockMappingStartToken
        self.cached_BlockEndToken = yaml.BlockEndToken
        self.cached_FlowSequenceStartToken = yaml.FlowSequenceStartToken
        self.cached_FlowMappingStartToken = yaml.FlowMappingStartToken
        self.cached_FlowSequenceEndToken = yaml.FlowSequenceEndToken
        self.cached_FlowMappingEndToken = yaml.FlowMappingEndToken
        self.cached_BlockEntryToken = yaml.BlockEntryToken
        self.cached_FlowEntryToken = yaml.FlowEntryToken
        self.cached_KeyToken = yaml.KeyToken
        self.cached_ValueToken = yaml.ValueToken
        self.cached_AliasToken = yaml.AliasToken
        self.cached_AnchorToken = yaml.AnchorToken
        self.cached_TagToken = yaml.TagToken
        self.cached_ScalarToken = yaml.ScalarToken
        self.cached_StreamStartEvent = yaml.StreamStartEvent
        self.cached_StreamEndEvent = yaml.StreamEndEvent
        self.cached_DocumentStartEvent = yaml.DocumentStartEvent
        self.cached_DocumentEndEvent = yaml.DocumentEndEvent
        self.cached_AliasEvent = yaml.AliasEvent
        self.cached_ScalarEvent = yaml.ScalarEvent
        self.cached_SequenceStartEvent = yaml.SequenceStartEvent
        self.cached_SequenceEndEvent = yaml.SequenceEndEvent
        self.cached_MappingStartEvent = yaml.MappingStartEvent
        self.cached_MappingEndEvent = yaml.MappingEndEvent

    cdef object _scan(self):
        cdef yaml_token_t token
        if yaml_parser_scan(&self.parser, &token) == 0:
            if self.parser.error == YAML_MEMORY_ERROR:
                raise MemoryError
            elif self.parser.error == YAML_READER_ERROR:
                raise self.cached_ReaderError(self.cached_input,
                        self.parser.problem_offset,
                        self.parser.problem_value,
                        self.cached_question, self.parser.problem)
            elif self.parser.error == YAML_SCANNER_ERROR:
                context_mark = None
                problem_mark = None
                if self.parser.context != NULL:
                    context_mark = self.cached_Mark(self.cached_input,
                            self.parser.context_mark.index,
                            self.parser.context_mark.line,
                            self.parser.context_mark.column,
                            None, None)
                if self.parser.problem != NULL:
                    problem_mark = self.cached_Mark(self.cached_input,
                            self.parser.problem_mark.index,
                            self.parser.problem_mark.line,
                            self.parser.problem_mark.column,
                            None, None)
                if self.parser.context != NULL:
                    raise self.cached_ScannerError(
                            self.parser.context, context_mark,
                            self.parser.problem, problem_mark)
                else:
                    raise yaml.scanner.ScannerError(None, None,
                            self.parser.problem, problem_mark)
        start_mark = yaml.Mark(self.cached_input,
                token.start_mark.index,
                token.start_mark.line,
                token.start_mark.column,
                None, None)
        end_mark = yaml.Mark(self.cached_input,
                token.end_mark.index,
                token.end_mark.line,
                token.end_mark.column,
                None, None)
        if token.type == YAML_NO_TOKEN:
            return None
        elif token.type == YAML_STREAM_START_TOKEN:
            return self.cached_StreamStartToken(start_mark, end_mark)
        elif token.type == YAML_STREAM_END_TOKEN:
            return self.cached_StreamEndToken(start_mark, end_mark)
        elif token.type == YAML_VERSION_DIRECTIVE_TOKEN:
            return self.cached_DirectiveToken(self.cached_YAML,
                    (token.data.version_directive.major,
                        token.data.version_directive.minor),
                    start_mark, end_mark)
        elif token.type == YAML_TAG_DIRECTIVE_TOKEN:
            return self.cached_DirectiveToken(self.cached_TAG,
                    (token.data.tag_directive.handle,
                        token.data.tag_directive.prefix),
                    start_mark, end_mark)
        elif token.type == YAML_DOCUMENT_START_TOKEN:
            return self.cached_DocumentStartToken(start_mark, end_mark)
        elif token.type == YAML_DOCUMENT_END_TOKEN:
            return self.cached_DocumentEndToken(start_mark, end_mark)
        elif token.type == YAML_BLOCK_SEQUENCE_START_TOKEN:
            return self.cached_BlockSequenceStartToken(start_mark, end_mark)
        elif token.type == YAML_BLOCK_MAPPING_START_TOKEN:
            return self.cached_BlockMappingStartToken(start_mark, end_mark)
        elif token.type == YAML_BLOCK_END_TOKEN:
            return self.cached_BlockEndToken(start_mark, end_mark)
        elif token.type == YAML_FLOW_SEQUENCE_START_TOKEN:
            return self.cached_FlowSequenceStartToken(start_mark, end_mark)
        elif token.type == YAML_FLOW_SEQUENCE_END_TOKEN:
            return self.cached_FlowSequenceEndToken(start_mark, end_mark)
        elif token.type == YAML_FLOW_MAPPING_START_TOKEN:
            return self.cached_FlowMappingStartToken(start_mark, end_mark)
        elif token.type == YAML_FLOW_MAPPING_END_TOKEN:
            return self.cached_FlowMappingEndToken(start_mark, end_mark)
        elif token.type == YAML_BLOCK_ENTRY_TOKEN:
            return self.cached_BlockEntryToken(start_mark, end_mark)
        elif token.type == YAML_FLOW_ENTRY_TOKEN:
            return self.cached_FlowEntryToken(start_mark, end_mark)
        elif token.type == YAML_KEY_TOKEN:
            return self.cached_KeyToken(start_mark, end_mark)
        elif token.type == YAML_VALUE_TOKEN:
            return self.cached_ValueToken(start_mark, end_mark)
        elif token.type == YAML_ALIAS_TOKEN:
            value = PyUnicode_DecodeUTF8(token.data.alias.value,
                    strlen(token.data.alias.value), 'strict')
            return self.cached_AliasToken(value, start_mark, end_mark)
        elif token.type == YAML_ANCHOR_TOKEN:
            value = PyUnicode_DecodeUTF8(token.data.anchor.value,
                    strlen(token.data.anchor.value), 'strict')
            return self.cached_AnchorToken(value, start_mark, end_mark)
        elif token.type == YAML_TAG_TOKEN:
            handle = PyUnicode_DecodeUTF8(token.data.tag.handle,
                    strlen(token.data.tag.handle), 'strict')
            suffix = PyUnicode_DecodeUTF8(token.data.tag.suffix,
                    strlen(token.data.tag.suffix), 'strict')
            if not handle:
                handle = None
            return self.cached_TagToken((handle, suffix), start_mark, end_mark)
        elif token.type == YAML_SCALAR_TOKEN:
            value = PyUnicode_DecodeUTF8(token.data.scalar.value,
                    token.data.scalar.length, 'strict')
            plain = False
            style = None
            if token.data.scalar.style == YAML_PLAIN_SCALAR_STYLE:
                plain = True
                style = ''
            elif token.data.scalar.style == YAML_SINGLE_QUOTED_SCALAR_STYLE:
                style = '\''
            elif token.data.scalar.style == YAML_DOUBLE_QUOTED_SCALAR_STYLE:
                style = '"'
            elif token.data.scalar.style == YAML_LITERAL_SCALAR_STYLE:
                style = '|'
            elif token.data.scalar.style == YAML_FOLDED_SCALAR_STYLE:
                style = '>'
            return self.cached_ScalarToken(value, plain,
                    start_mark, end_mark, style)
        else:
            raise RuntimeError("unknown token type")

    cdef object _parse(self):
        cdef yaml_event_t event
        if yaml_parser_parse(&self.parser, &event) == 0:
            if self.parser.error == YAML_MEMORY_ERROR:
                raise MemoryError
            elif self.parser.error == YAML_READER_ERROR:
                raise self.cached_ReaderError(self.cached_input,
                        self.parser.problem_offset,
                        self.parser.problem_value,
                        self.cached_question, self.parser.problem)
            elif self.parser.error == YAML_SCANNER_ERROR    \
                    or self.parser.error == YAML_PARSER_ERROR:
                context_mark = None
                problem_mark = None
                if self.parser.context != NULL:
                    context_mark = self.cached_Mark(self.cached_input,
                            self.parser.context_mark.index,
                            self.parser.context_mark.line,
                            self.parser.context_mark.column,
                            None, None)
                if self.parser.problem != NULL:
                    problem_mark = self.cached_Mark(self.cached_input,
                            self.parser.problem_mark.index,
                            self.parser.problem_mark.line,
                            self.parser.problem_mark.column,
                            None, None)
                if self.parser.error == YAML_SCANNER_ERROR:
                    if self.parser.context != NULL:
                        raise self.cached_ScannerError(
                                self.parser.context, context_mark,
                                self.parser.problem, problem_mark)
                    else:
                        raise self.cached_ScannerError(None, None,
                                self.parser.problem, problem_mark)
                else:
                    if self.parser.context != NULL:
                        raise self.cached_ParserError(
                                self.parser.context, context_mark,
                                self.parser.problem, problem_mark)
                    else:
                        raise self.cached_ParserError(None, None,
                                self.parser.problem, problem_mark)
        start_mark = yaml.Mark(self.cached_input,
                event.start_mark.index,
                event.start_mark.line,
                event.start_mark.column,
                None, None)
        end_mark = yaml.Mark(self.cached_input,
                event.end_mark.index,
                event.end_mark.line,
                event.end_mark.column,
                None, None)
        if event.type == YAML_NO_EVENT:
            return None
        elif event.type == YAML_STREAM_START_EVENT:
            return self.cached_StreamStartEvent(start_mark, end_mark)
        elif event.type == YAML_STREAM_END_EVENT:
            return self.cached_StreamEndEvent(start_mark, end_mark)
        elif event.type == YAML_DOCUMENT_START_EVENT:
            return self.cached_DocumentStartEvent(start_mark, end_mark)
        elif event.type == YAML_DOCUMENT_END_EVENT:
            return self.cached_DocumentEndEvent(start_mark, end_mark)
        elif event.type == YAML_ALIAS_EVENT:
            anchor = PyUnicode_DecodeUTF8(event.data.alias.anchor,
                    strlen(event.data.alias.anchor), 'strict')
            return self.cached_AliasEvent(anchor, start_mark, end_mark)
        elif event.type == YAML_SCALAR_EVENT:
            anchor = None
            if event.data.scalar.anchor != NULL:
                anchor = PyUnicode_DecodeUTF8(event.data.scalar.anchor,
                        strlen(event.data.scalar.anchor), 'strict')
            tag = None
            if event.data.scalar.tag != NULL:
                tag = PyUnicode_DecodeUTF8(event.data.scalar.tag,
                        strlen(event.data.scalar.tag), 'strict')
            value = PyUnicode_DecodeUTF8(event.data.scalar.value,
                    event.data.scalar.length, 'strict')
            plain_implicit = (event.data.scalar.plain_implicit == 1)
            quoted_implicit = (event.data.scalar.quoted_implicit == 1)
            style = None
            if event.data.scalar.style == YAML_PLAIN_SCALAR_STYLE:
                style = ''
            elif event.data.scalar.style == YAML_SINGLE_QUOTED_SCALAR_STYLE:
                style = '\''
            elif event.data.scalar.style == YAML_DOUBLE_QUOTED_SCALAR_STYLE:
                style = '"'
            elif event.data.scalar.style == YAML_LITERAL_SCALAR_STYLE:
                style = '|'
            elif event.data.scalar.style == YAML_FOLDED_SCALAR_STYLE:
                style = '>'
            return self.cached_ScalarEvent(anchor, tag,
                    (plain_implicit, quoted_implicit),
                    value, start_mark, end_mark, style)
        elif event.type == YAML_SEQUENCE_START_EVENT:
            anchor = None
            if event.data.sequence_start.anchor != NULL:
                anchor = PyUnicode_DecodeUTF8(event.data.sequence_start.anchor,
                        strlen(event.data.sequence_start.anchor), 'strict')
            tag = None
            if event.data.sequence_start.tag != NULL:
                tag = PyUnicode_DecodeUTF8(event.data.sequence_start.tag,
                        strlen(event.data.sequence_start.tag), 'strict')
            implicit = (event.data.sequence_start.implicit == 1)
            flow_style = None
            if event.data.sequence_start.style == YAML_FLOW_SEQUENCE_STYLE:
                flow_style = True
            elif event.data.sequence_start.style == YAML_BLOCK_SEQUENCE_STYLE:
                flow_style = False
            return self.cached_SequenceStartEvent(anchor, tag, implicit,
                    start_mark, end_mark, flow_style)
        elif event.type == YAML_MAPPING_START_EVENT:
            anchor = None
            if event.data.mapping_start.anchor != NULL:
                anchor = PyUnicode_DecodeUTF8(event.data.mapping_start.anchor,
                        strlen(event.data.mapping_start.anchor), 'strict')
            tag = None
            if event.data.mapping_start.tag != NULL:
                tag = PyUnicode_DecodeUTF8(event.data.mapping_start.tag,
                        strlen(event.data.mapping_start.tag), 'strict')
            implicit = (event.data.mapping_start.implicit == 1)
            flow_style = None
            if event.data.mapping_start.style == YAML_FLOW_SEQUENCE_STYLE:
                flow_style = True
            elif event.data.mapping_start.style == YAML_BLOCK_SEQUENCE_STYLE:
                flow_style = False
            return self.cached_MappingStartEvent(anchor, tag, implicit,
                    start_mark, end_mark, flow_style)
        elif event.type == YAML_SEQUENCE_END_EVENT:
            return self.cached_SequenceEndEvent(start_mark, end_mark)
        elif event.type == YAML_MAPPING_END_EVENT:
            return self.cached_MappingEndEvent(start_mark, end_mark)
        else:
            raise RuntimeError("unknown event type")

cdef int input_handler(void *data, char *buffer, int size, int *read) except 0:
    cdef ScannerAndParser parser
    parser = <ScannerAndParser>data
    value = parser.stream.read(size)
    if PyString_CheckExact(value) == 0:
        raise TypeError("a string value is expected")
    if PyString_GET_SIZE(value) > size:
        raise ValueError("a string value it too long")
    memcpy(buffer, PyString_AS_STRING(value), PyString_GET_SIZE(value))
    read[0] = PyString_GET_SIZE(value)
    return 1

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

