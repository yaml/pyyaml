
import yaml
import re

def get_version_string():
    cdef const char *value
    value = fy_library_version()
    version = PyUnicode_FromString(value)
    return version + ".0"

def get_version():
    cdef int major, minor, patch
    m = re.match(r"(\d+)\.(\d+)", get_version_string())
    major = int(m.group(1))
    minor = int(m.group(2))
    # we ignore patch number for now (libfyaml uses tags so...
    patch = 0
    return (major, minor, patch)

YAMLError = yaml.error.YAMLError
ReaderError = yaml.reader.ReaderError
ScannerError = yaml.scanner.ScannerError
ParserError = yaml.parser.ParserError
ComposerError = yaml.composer.ComposerError
ConstructorError = yaml.constructor.ConstructorError
EmitterError = yaml.emitter.EmitterError
SerializerError = yaml.serializer.SerializerError
RepresenterError = yaml.representer.RepresenterError

StreamStartEvent = yaml.events.StreamStartEvent
StreamEndEvent = yaml.events.StreamEndEvent
DocumentStartEvent = yaml.events.DocumentStartEvent
DocumentEndEvent = yaml.events.DocumentEndEvent
AliasEvent = yaml.events.AliasEvent
ScalarEvent = yaml.events.ScalarEvent
SequenceStartEvent = yaml.events.SequenceStartEvent
SequenceEndEvent = yaml.events.SequenceEndEvent
MappingStartEvent = yaml.events.MappingStartEvent
MappingEndEvent = yaml.events.MappingEndEvent

ScalarNode = yaml.nodes.ScalarNode
SequenceNode = yaml.nodes.SequenceNode
MappingNode = yaml.nodes.MappingNode

StreamStartToken = yaml.tokens.StreamStartToken
StreamEndToken = yaml.tokens.StreamEndToken
DirectiveToken = yaml.tokens.DirectiveToken
DocumentStartToken = yaml.tokens.DocumentStartToken
DocumentEndToken = yaml.tokens.DocumentEndToken
BlockSequenceStartToken = yaml.tokens.BlockSequenceStartToken
BlockMappingStartToken = yaml.tokens.BlockMappingStartToken
BlockEndToken = yaml.tokens.BlockEndToken
FlowSequenceStartToken = yaml.tokens.FlowSequenceStartToken
FlowMappingStartToken = yaml.tokens.FlowMappingStartToken
FlowSequenceEndToken = yaml.tokens.FlowSequenceEndToken
FlowMappingEndToken = yaml.tokens.FlowMappingEndToken
KeyToken = yaml.tokens.KeyToken
ValueToken = yaml.tokens.ValueToken
BlockEntryToken = yaml.tokens.BlockEntryToken
FlowEntryToken = yaml.tokens.FlowEntryToken
AliasToken = yaml.tokens.AliasToken
AnchorToken = yaml.tokens.AnchorToken
TagToken = yaml.tokens.TagToken
ScalarToken = yaml.tokens.ScalarToken

cdef class Mark:
    cdef readonly object name
    cdef readonly size_t index
    cdef readonly size_t line
    cdef readonly size_t column
    cdef readonly buffer
    cdef readonly pointer

    def __init__(self, object name, size_t index, size_t line, size_t column,
            object buffer, object pointer):
        self.name = name
        self.index = index
        self.line = line
        self.column = column
        self.buffer = buffer
        self.pointer = pointer

    def get_snippet(self):
        return None

    def __str__(self):
        where = "  in \"%s\", line %d, column %d"   \
                % (self.name, self.line+1, self.column+1)
        return where

cdef class FParser:

    cdef fy_parser *parser
    # we keep two pointers
    # cython doesn't do anonymous unions so we have to workaround it
    cdef fy_event *parsed_event
    cdef _fy_event *_parsed_event

    cdef object stream
    cdef object stream_name
    cdef object current_token
    cdef object current_event
    cdef object anchors
    cdef object stream_cache
    cdef int stream_cache_len
    cdef int stream_cache_pos
    cdef int unicode_source
    cdef int ret

    def __init__(self, stream):
        cdef is_readable
        cdef fy_parse_cfg cfg

        memset(&cfg, 0, sizeof(cfg))
        cfg.search_path = ""
        cfg.flags = <fy_parse_cfg_flags>(FYPCF_QUIET | FYPCF_DEFAULT_VERSION_1_1 | FYPCF_SLOPPY_FLOW_INDENTATION)

        self.parser = fy_parser_create(&cfg)
        if self.parser == NULL:
            raise MemoryError

        self.parsed_event = NULL
        self._parsed_event = NULL

        # printf("%s: parser created\n", "__init__")
        is_readable = 1
        try:
            stream.read
        except AttributeError:
            is_readable = 0
        self.unicode_source = 0
        if is_readable:
            self.stream = stream
            try:
                self.stream_name = stream.name
            except AttributeError:
                self.stream_name = u'<file>'
            self.stream_cache = None
            self.stream_cache_len = 0
            self.stream_cache_pos = 0
            ret = fy_parser_set_input_callback(self.parser, <void *>self, input_handler)
            if ret != 0:
                raise MemoryError
        else:
            if PyUnicode_CheckExact(stream) != 0:
                stream = PyUnicode_AsUTF8String(stream)
                self.stream_name = u'<unicode string>'
                self.unicode_source = 1
            else:
                self.stream_name = u'<byte string>'
            if PyBytes_CheckExact(stream) == 0:
                raise TypeError(u"a string or stream input is required")
            self.stream = stream
            ret = fy_parser_set_string(self.parser, PyBytes_AS_STRING(stream), PyBytes_GET_SIZE(stream))
            if ret != 0:
                raise MemoryError

        self.current_token = None
        self.current_event = None
        self.anchors = {}

    def __dealloc__(self):
        fy_parser_event_free(self.parser, self.parsed_event)
        fy_parser_destroy(self.parser)

    def dispose(self):
        pass

    cdef object _parser_error(self):
        # if self.parser.error == YAML_MEMORY_ERROR:
            printf("_parser_error()\n")
            return MemoryError
        # elif self.parser.error == YAML_READER_ERROR:
        #     return ReaderError(self.stream_name, self.parser.problem_offset,
        #             self.parser.problem_value, u'?', PyUnicode_FromString(self.parser.problem))
        # elif self.parser.error == YAML_SCANNER_ERROR    \
        #         or self.parser.error == YAML_PARSER_ERROR:
        #     context_mark = None
        #     problem_mark = None
        #     if self.parser.context != NULL:
        #         context_mark = Mark(self.stream_name,
        #                 self.parser.context_mark.index,
        #                 self.parser.context_mark.line,
        #                 self.parser.context_mark.column, None, None)
        #     if self.parser.problem != NULL:
        #         problem_mark = Mark(self.stream_name,
        #                 self.parser.problem_mark.index,
        #                 self.parser.problem_mark.line,
        #                 self.parser.problem_mark.column, None, None)
        #     context = None
        #     if self.parser.context != NULL:
        #         context = PyUnicode_FromString(self.parser.context)
        #     problem = PyUnicode_FromString(self.parser.problem)
        #     if self.parser.error == YAML_SCANNER_ERROR:
        #         return ScannerError(context, context_mark, problem, problem_mark)
        #     else:
        #         return ParserError(context, context_mark, problem, problem_mark)
        # raise ValueError(u"no parser error")

    def raw_scan(self):
        cdef fy_token *token
        cdef int count
        cdef fy_token_type type

        count = 0
        while True:
            token = fy_scan(self.parser)

            if token == NULL:
                raise ReaderError(self.stream_name, 0, 0, u'?', PyUnicode_FromString("problem"))

            type = fy_token_get_type(token)
            # we don't use the token
            fy_scan_token_free(self.parser, token)

            if type == FYTT_NONE:
                break

            count = count+1

        return count

    cdef object _scan(self):
        cdef fy_token *token
        cdef const fy_mark *start_mark
        cdef const fy_mark *end_mark

        while True:
            token = fy_scan(self.parser)
            if token == NULL:
                return None
                # raise ReaderError(self.stream_name, 0, 0, u'?', PyUnicode_FromString("problem"))
            type = fy_token_get_type(token)
            if type != FYTT_VALUE:
                break
            start_mark = fy_token_start_mark(token)
            end_mark = fy_token_end_mark(token)
            # remove from the token stream the NULL value
            if start_mark[0].input_pos != end_mark[0].input_pos:
                break

        token_object = self._token_to_object(token)
        fy_scan_token_free(self.parser, token)

        return token_object

    cdef object _token_to_object(self, fy_token *token):
        cdef const fy_mark *start_mark
        cdef const fy_mark *end_mark
        cdef fy_token_type type
        cdef const char *text
        cdef size_t textlen
        cdef const fy_version *vers
        cdef const char *prefix
        cdef const char *handle
        cdef const char *suffix
        cdef fy_scalar_style style

        start_mark = fy_token_start_mark(token)
        end_mark = fy_token_end_mark(token)

        start_markp = Mark(self.stream_name, start_mark[0].input_pos, start_mark[0].line, start_mark[0].column, None, None)
        end_markp = Mark(self.stream_name, end_mark[0].input_pos, end_mark[0].line, end_mark[0].column, None, None)

        type = fy_token_get_type(token)

        if type == FYTT_NONE:
            return None

        if type == FYTT_STREAM_START:
            # libfyaml only does utf-8
            encoding = u"utf-8"
            return StreamStartToken(start_markp, end_markp, encoding)

        if type == FYTT_STREAM_END:
            return StreamEndToken(start_markp, end_markp)

        if type == FYTT_VERSION_DIRECTIVE:

            vers = fy_version_directive_token_version(token)
            if vers == NULL:
                raise MemoryError
            return DirectiveToken(u"YAML", (vers[0].major, vers[0].minor), start_markp, end_markp)

        if type == FYTT_TAG_DIRECTIVE:

            prefix = fy_tag_directive_token_prefix0(token)
            if prefix == NULL:
                raise MemoryError

            handle = fy_tag_directive_token_handle0(token)
            if handle == NULL:
                raise MemoryError

            prefixp = PyUnicode_FromString(prefix)
            handlep = PyUnicode_FromString(handle)

            return DirectiveToken(u"TAG", (handlep, prefixp), start_markp, end_markp)

        if type == FYTT_DOCUMENT_START:
            return DocumentStartToken(start_markp, end_markp)

        if type == FYTT_DOCUMENT_END:
            return DocumentEndToken(start_markp, end_markp)

        if type == FYTT_BLOCK_SEQUENCE_START:
            return BlockSequenceStartToken(start_markp, end_markp)

        if type == FYTT_BLOCK_MAPPING_START:
            return BlockMappingStartToken(start_markp, end_markp)

        if type == FYTT_BLOCK_END:
            return BlockEndToken(start_markp, end_markp)

        if type == FYTT_FLOW_SEQUENCE_START:
            return FlowSequenceStartToken(start_markp, end_markp)

        if type == FYTT_FLOW_SEQUENCE_END:
            return FlowSequenceEndToken(start_markp, end_markp)

        if type == FYTT_FLOW_MAPPING_START:
            return FlowMappingStartToken(start_markp, end_markp)

        if type == FYTT_FLOW_MAPPING_END:
            return FlowMappingEndToken(start_markp, end_markp)

        if type == FYTT_BLOCK_ENTRY:
            return BlockEntryToken(start_markp, end_markp)

        if type == FYTT_FLOW_ENTRY:
            return FlowEntryToken(start_markp, end_markp)

        if type == FYTT_KEY:
            return KeyToken(start_markp, end_markp)

        if type == FYTT_VALUE:
            return ValueToken(start_markp, end_markp)

        if type == FYTT_ALIAS:
            text = fy_token_get_text0(token)
            if text == NULL:
                raise MemoryError

            value = PyUnicode_FromString(text)
            return AliasToken(value, start_markp, end_markp)

        if type == FYTT_ANCHOR:

            text = fy_token_get_text0(token)
            if text == NULL:
                raise MemoryError

            valuep = PyUnicode_FromString(text)
            return AnchorToken(valuep, start_markp, end_markp)

        if type == FYTT_TAG:

            handle = fy_tag_token_handle0(token)
            if handle == NULL:
                raise MemoryError

            suffix = fy_tag_token_suffix0(token)
            if suffix == NULL:
                raise MemoryError

            handlep = PyUnicode_FromString(handle)
            suffixp = PyUnicode_FromString(suffix)

            if suffixp == u'' or suffixp == '':
                suffixp = handlep
                handlep = None

            if handlep == u'' or handlep == '':
                handlep = None

            return TagToken((handlep, suffixp), start_markp, end_markp)

        if type == FYTT_SCALAR:

            text = fy_token_get_text(token, &textlen)
            if text == NULL:
                raise MemoryError

            value = PyUnicode_DecodeUTF8(text, textlen, 'strict')
            plain = False
            stylep = None

            style = fy_scalar_token_get_style(token)

            if style == FYSS_PLAIN:
                plain = True
                # stylep = u'' , plain as None
            elif style == FYSS_SINGLE_QUOTED:
                stylep = u'\''
            elif style == FYSS_DOUBLE_QUOTED:
                stylep = u'"'
            elif style == FYSS_LITERAL:
                stylep = u'|'
            elif style == FYSS_FOLDED:
                stylep = u'>'

            return ScalarToken(value, plain, start_markp, end_markp, stylep)

        raise ValueError(u"unknown token type")

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

    def raw_parse(self):
        cdef fy_event *event
        cdef fy_event_type type
        cdef int count

        count = 0
        while True:
            event = fy_parser_parse(self.parser)
            if event == NULL:
                raise ParserError(u"unexpected NULL return from fy_parser_parse (raw_parse)")
            type = event.type
            fy_parser_event_free(self.parser, event)

            if type == FYET_NONE:
                break

            count = count+1

        return count

    cdef object _parse(self):
        cdef fy_event *event

        event = fy_parser_parse(self.parser)
        if event == NULL:
            return None
            # raise ParserError(u"unexpected NULL return from fy_parser_parse")
        event_object = self._event_to_object(event)
        fy_parser_event_free(self.parser, event)
        return event_object

    cdef object _event_to_object(self, fy_event *event):
        cdef _fy_event *_event
        cdef const fy_mark *start_mark
        cdef const fy_mark *end_mark
        cdef fy_document_state *fyds
        cdef const fy_version *vers
        cdef const fy_tag *tag
        cdef void *tagiter
        cdef const char *text
        cdef size_t textlen
        cdef fy_event_type type
        cdef fy_node_style nstyle

        _event = <_fy_event *>event

        start_mark = fy_event_start_mark(event)
        end_mark = fy_event_end_mark(event)

        if start_mark != NULL:
            start_markp = Mark(self.stream_name, start_mark[0].input_pos, start_mark[0].line, start_mark[0].column, None, None)
        else:
            start_markp = None

        if start_mark != NULL:
            end_markp = Mark(self.stream_name, end_mark[0].input_pos, end_mark[0].line, end_mark[0].column, None, None)
        else:
            end_markp = None

        type = event.type

        if type == FYET_NONE:
            return None

        if type == FYET_STREAM_START:
            # libfyaml is utf8 only...
            encoding = u"utf-8"
            return StreamStartEvent(start_markp, end_markp, encoding)

        if type == FYET_STREAM_END:
            return StreamEndEvent(start_markp, end_markp)

        if type == FYET_DOCUMENT_START:
            explicit = False
            if _event.data.document_start.implicit == 0:
                explicit = True
            fyds = _event.data.document_start.document_state

            version = None
            if fy_document_state_version_explicit(fyds) == True:
                vers = fy_document_state_version(fyds)
                version = (vers[0].major, vers[0].minor)

            tags = {}
            tagsnr = 0
            if fy_document_state_tags_explicit(fyds) == True:
                tagiter = NULL
                while True:
                    tag = fy_document_state_tag_directive_iterate(fyds, &tagiter)
                    if tag == NULL:
                        break
                    # skip over default tags
                    implicit = fy_document_state_tag_is_default(fyds, tag)
                    if implicit == True:
                        continue

                    handle = PyUnicode_FromString(tag[0].handle)
                    prefix = PyUnicode_FromString(tag[0].prefix)
                    tags[handle] = prefix
                    tagsnr = tagsnr+1

            # if no tags found, set tags to None
            if tagsnr == 0:
                tags = None

            return DocumentStartEvent(start_markp, end_markp, explicit, version, tags)

        if type == FYET_DOCUMENT_END:
            explicit = False
            if _event.data.document_end.implicit == 0:
                explicit = True
            return DocumentEndEvent(start_markp, end_markp, explicit)

        if type == FYET_ALIAS:
            text = fy_token_get_text0(_event.data.alias.anchor)
            if text == NULL:
                raise MemoryError
            anchor = PyUnicode_FromString(text)
            return AliasEvent(anchor, start_markp, end_markp)

        if type == FYET_SCALAR:

            anchor = None
            if _event.data.scalar.anchor != NULL:
                text = fy_token_get_text0(_event.data.scalar.anchor)
                if text == NULL:
                    raise MemoryError
                anchor = PyUnicode_FromString(text)

            tagp = None
            if _event.data.scalar.tag != NULL:
                text = fy_token_get_text0(_event.data.scalar.tag)
                if text == NULL:
                    raise MemoryError
                tagp = PyUnicode_FromString(text)

            text = fy_token_get_text(_event.data.scalar.value, &textlen)
            if text == NULL:
                raise MemoryError

            value = PyUnicode_DecodeUTF8(text, textlen, 'strict')

            stylep = None
            style = fy_token_scalar_style(_event.data.scalar.value)

            if style == FYSS_PLAIN:
                stylep = u''
            elif style == FYSS_SINGLE_QUOTED:
                stylep = u'\''
            elif style == FYSS_DOUBLE_QUOTED:
                stylep = u'"'
            elif style == FYSS_LITERAL:
                stylep = u'|'
            elif style == FYSS_FOLDED:
                stylep = u'>'

            if (style == FYSS_PLAIN and tagp is None) or tagp == '!':
                implicit = (True, False)
            elif tagp is None:
                implicit = (False, True)
            else:
                implicit = (False, False)

            return ScalarEvent(anchor, tagp, implicit, value, start_markp, end_markp, stylep)

        if type == FYET_SEQUENCE_START:
            anchor = None
            if _event.data.sequence_start.anchor != NULL:
                text = fy_token_get_text0(_event.data.sequence_start.anchor)
                if text == NULL:
                    raise MemoryError
                anchor = PyUnicode_FromString(text)

            tagp = None
            if _event.data.sequence_start.tag != NULL:
                text = fy_token_get_text0(_event.data.sequence_start.tag)
                if text == NULL:
                    raise MemoryError
                tagp = PyUnicode_FromString(text)

            implicit = (tagp is None or tagp == u'!')

            flow_style = None
            nstyle = fy_event_get_node_style(event)
            if nstyle == FYNS_FLOW:
                flow_style = True
            elif nstyle == FYNS_BLOCK:
                flow_style = False

            return SequenceStartEvent(anchor, tagp, implicit, start_markp, end_markp, flow_style)

        if type == FYET_MAPPING_START:
            anchor = None
            if _event.data.mapping_start.anchor != NULL:
                text = fy_token_get_text0(_event.data.mapping_start.anchor)
                if text == NULL:
                    raise MemoryError
                anchor = PyUnicode_FromString(text)

            tagp = None
            if _event.data.mapping_start.tag != NULL:
                text = fy_token_get_text0(_event.data.mapping_start.tag)
                if text == NULL:
                    raise MemoryError
                tagp = PyUnicode_FromString(text)

            implicit = (tagp is None or tagp == u'!')

            flow_style = None
            nstyle = fy_event_get_node_style(event)
            if nstyle == FYNS_FLOW:
                flow_style = True
            elif nstyle == FYNS_BLOCK:
                flow_style = False

            return MappingStartEvent(anchor, tagp, implicit, start_markp, end_markp, flow_style)

        if type == FYET_SEQUENCE_END:
            return SequenceEndEvent(start_markp, end_markp)

        if type == FYET_MAPPING_END:
            return MappingEndEvent(start_markp, end_markp)

        raise ValueError(u"unknown event type")

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

    def check_node(self):
        # printf("check_node:\n")
        self._parse_next_event()
        if self.parsed_event.type == FYET_STREAM_START:
            fy_parser_event_free(self.parser, self.parsed_event)
            self.parsed_event = NULL
            self._parsed_event = NULL
            self._parse_next_event()
        if self.parsed_event == NULL or self.parsed_event.type == FYET_STREAM_END:
            return False
        return True

    def get_node(self):
        # printf("get_node: _parse_next_event() 1\n")
        self._parse_next_event()
        if self.parsed_event.type == FYET_STREAM_END:
            return None

        # printf("get_node: _parse_next_event() 1\n")
        self._parse_next_event()
        if self.parsed_event.type == FYET_STREAM_END:
            return None

        self._parse_free_event()

        node = self._compose_node(None, None)
        self.anchors = {}

        self._parse_free_event()

        # printf("get_node: _parse_next_event() 3\n")
        self._parse_next_event()

        return None

    def get_single_node(self):
        cdef const fy_mark *start_mark

        # printf("get_single_node: _parse_next_event() 1\n")
        self._parse_next_event()
        if self.parsed_event.type != FYET_STREAM_START:
            raise ComposerError("Parser not starting with stream start")
        # print "got FYET_STREAM_START"
        self._parse_free_event()

        document = None
        # printf("get_single_node: _parse_next_event() 2\n")
        self._parse_next_event()

        if self.parsed_event.type != FYET_DOCUMENT_START:
            raise ComposerError("Parser not producing document start")
        # print "got FYET_DOCUMENT_START"
        self._parse_free_event()

        node = self._compose_node(None, None)
        self.anchors = {}

        # printf("get_single_node: _parse_next_event() 3\n")
        self._parse_next_event()
        if self.parsed_event.type != FYET_DOCUMENT_END:
            raise ComposerError("Parser not producing document end")
        # print "got FYET_DOCUMENT_END"
        self._parse_free_event()

        # printf("get_single_node: _parse_next_event() 4\n")
        self._parse_next_event()
        if self.parsed_event.type == FYET_STREAM_END:
            # print "got FYET_STREAM_END"
            self._parse_free_event()
            return node

        if self.parsed_event.type != FYET_DOCUMENT_START:
            raise ComposerError("Parser not producing document start (on error)")

        # multi document
        start_mark = fy_event_start_mark(self.parsed_event)
        if start_mark != NULL:
            mark = Mark(self.stream_name, start_mark[0].input_pos, start_mark[0].line, start_mark[0].column, None, None)
        else:
            mark = None

        raise ComposerError(u"expected a single document in the stream",
                document.start_mark, u"but found another document", mark)

    cdef object _compose_node(self, object parent, object index):
        # printf("_compose_node\n")
        cdef const char *anchor_str
        cdef const char *tagstr
        cdef const fy_mark *start_mark
        cdef fy_token *anchor_token

        # printf("_compose_node() 1\n")
        self._parse_next_event()
        # printf("_compose_node() 1 after\n")

        if self.parsed_event == NULL or self.parsed_event.type == FYET_STREAM_END:
            # printf("_compose_node() None\n")
            return None

        if self.parsed_event.type == FYET_ALIAS:

            anchor_str = fy_token_get_text0(self._parsed_event.data.alias.anchor)
            if anchor_str == NULL:
                raise MemoryError

            anchor = PyUnicode_FromString(anchor_str)

            if anchor in self.anchors:
                self._parse_free_event()
                return self.anchors[anchor]

            start_mark = fy_event_start_mark(self.parsed_event)

            mark = Mark(self.stream_name, start_mark[0].input_pos, start_mark[0].line, start_mark[0].column, None, None)
            raise ComposerError(None, None, u"found undefined alias", mark)

        # get the anchor (if any)
        anchor_token = NULL
        if self.parsed_event.type == FYET_SCALAR:
            anchor_token = self._parsed_event.data.scalar.anchor
        elif self.parsed_event.type == FYET_SEQUENCE_START:
            anchor_token = self._parsed_event.data.sequence_start.anchor
        elif self.parsed_event.type == FYET_MAPPING_START:
            anchor_token = self._parsed_event.data.mapping_start.anchor

        # check duplicate anchor
        if anchor_token != NULL:
            anchor_str = fy_token_get_text0(anchor_token)
            if anchor_str == NULL:
                raise MemoryError
            anchor = PyUnicode_FromString(anchor_str)
        else:
            anchor = None

        if anchor != None and anchor in self.anchors:

            start_mark = fy_event_start_mark(self.parsed_event)

            mark = Mark(self.stream_name,
                    start_mark[0].input_pos,
                    start_mark[0].line,
                    start_mark[0].column,
                    None, None)
            raise ComposerError(u"found duplicate anchor; first occurrence",
                    self.anchors[anchor].start_mark, u"second occurrence", mark)

        # printf("_compose_node(): descend_resolver\n")
        self.descend_resolver(parent, index)
        # printf("_compose_node(): descend_resolver out\n")

        if self.parsed_event == NULL:
            # printf("_compose_node(): self.parsed_event == NULL\n")
            node = None
        if self.parsed_event.type == FYET_STREAM_END:
            # printf("_compose_node(): FYET_STREAM_END\n")
            none = None
        if self.parsed_event.type == FYET_SCALAR:
            # printf("_compose_node(): FYET_SCALAR\n")
            node = self._compose_scalar_node(anchor)
        elif self.parsed_event.type == FYET_SEQUENCE_START:
            # printf("_compose_node(): FYET_SEQUENCE_START\n")
            node = self._compose_sequence_node(anchor)
        elif self.parsed_event.type == FYET_MAPPING_START:
            # printf("_compose_node(): FYET_MAPPING_START\n")
            node = self._compose_mapping_node(anchor)
        else:
            raise ComposerError(u"Unknown event type")

        # printf("_compose_node(): ascend_resolver\n")
        self.ascend_resolver()
        # printf("_compose_node(): ascend_resolver end\n")
        return node

    cdef _compose_scalar_node(self, object anchor):
        # printf("_compose_scalar_node\n")
        cdef const fy_mark *start_mark
        cdef const fy_mark *end_mark
        cdef fy_mark empty_mark
        cdef const char *str
        cdef size_t len
        cdef const char *tag_str
        cdef fy_scalar_style style

        # printf("_compose_scalar_node(): before fy_event_start_mark\n")
        start_mark = fy_event_start_mark(self.parsed_event)
        # printf("_compose_scalar_node(): after fy_event_start_mark\n")
        end_mark = fy_event_end_mark(self.parsed_event)

        # printf("_compose_scalar_node(): start_mark=%p end_mark=%p\n", start_mark, end_mark)

        if start_mark == NULL and end_mark == NULL:
           empty_mark.input_pos = 0
           empty_mark.line = 0
           empty_mark.column = 0
           start_mark = end_mark = &empty_mark

        start_markp = Mark(self.stream_name, start_mark[0].input_pos, start_mark[0].line, start_mark[0].column, None, None)
        end_markp = Mark(self.stream_name, end_mark[0].input_pos, end_mark[0].line, end_mark[0].column, None, None)

        # printf("_compose_scalar_node(): before fy_token_get_text\n")
        str = fy_token_get_text(self._parsed_event.data.scalar.value, &len)
        # printf("_compose_scalar_node(): after fy_token_get_text\n")
        if str == NULL:
             # printf("str == NULL\n")
             raise MemoryError

        # printf("_compose_scalar_node(): before PyUnicode_DecodeUTF8\n")
        value = PyUnicode_DecodeUTF8(str, len, 'strict')
        # printf("_compose_scalar_node(): after PyUnicode_DecodeUTF8\n")

        # wtf are those...
        plain_implicit = False
        quoted_implicit = False

        if self._parsed_event.data.scalar.tag == NULL:
            tag = self.resolve(ScalarNode, value, (plain_implicit, quoted_implicit))
        else:
            tag_str = fy_token_get_text0(self._parsed_event.data.scalar.tag)
            if tag_str == NULL:
                raise MemoryError

            if tag_str[0] == c'!' and tag_str[1] == c'\0':
                tag = self.resolve(ScalarNode, value, (plain_implicit, quoted_implicit))
            else:
                tag = PyUnicode_FromString(tag_str)

        stylep = None
        style = fy_token_scalar_style(self._parsed_event.data.scalar.value)
        if style == FYSS_PLAIN:
            stylep = u''
        elif style == FYSS_SINGLE_QUOTED:
            stylep = u'\''
        elif style == FYSS_DOUBLE_QUOTED:
            stylep = u'"'
        elif style == FYSS_LITERAL:
            stylep = u'|'
        elif style == FYSS_FOLDED:
            stylep = u'>'

        node = ScalarNode(tag, value, start_markp, end_markp, stylep)

        if anchor is not None:
            self.anchors[anchor] = node

        self._parse_free_event()
        return node

    cdef _compose_sequence_node(self, object anchor):
        # printf("_compose_sequence_node\n")
        cdef const fy_mark *start_mark
        cdef const fy_mark *end_mark
        cdef fy_node_style nstyle
        cdef const char *tag_str
        cdef int index

        start_mark = fy_event_start_mark(self.parsed_event)

        start_markp = Mark(self.stream_name, start_mark[0].input_pos, start_mark[0].line, start_mark[0].column, None, None)
        implicit = False
        if self._parsed_event.data.sequence_start.sequence_start == NULL:
            implicit = True

        if self._parsed_event.data.sequence_start.tag == NULL:
            tag = self.resolve(SequenceNode, None, implicit)
        else:
            tag_str = fy_token_get_text0(self._parsed_event.data.sequence_start.tag)
            if tag_str == NULL:
                raise MemoryError

            if tag_str[0] == c'!' and tag_str[1] == c'\0':
                tag = self.resolve(SequenceNode, None, implicit)
            else:
                tag = PyUnicode_FromString(tag_str)

        flow_style = None
        nstyle = fy_event_get_node_style(self.parsed_event)
        if nstyle == FYNS_FLOW:
            flow_style = True
        elif nstyle == FYNS_BLOCK:
            flow_style = False
        value = []
        node = SequenceNode(tag, value, start_markp, None, flow_style)
        if anchor is not None:
            self.anchors[anchor] = node

        self._parse_free_event()

        index = 0
        self._parse_next_event()
        while self.parsed_event.type != FYET_SEQUENCE_END:
            value.append(self._compose_node(node, index))
            index = index+1
            self._parse_next_event()

        end_mark = fy_event_end_mark(self.parsed_event)

        node.end_mark = Mark(self.stream_name, end_mark[0].input_pos, end_mark[0].line, end_mark[0].column, None, None)

        self._parse_free_event()
        return node

    cdef _compose_mapping_node(self, object anchor):
        # print "_compose_mapping_node"
        cdef const fy_mark *start_mark
        cdef const fy_mark *end_mark
        cdef fy_node_style nstyle
        cdef const char *tag_str
        cdef int index

        start_mark = fy_event_start_mark(self.parsed_event)

        start_markp = Mark(self.stream_name, start_mark[0].input_pos, start_mark[0].line, start_mark[0].column, None, None)
        implicit = False
        if self._parsed_event.data.mapping_start.mapping_start == NULL:
            implicit = True

        if self._parsed_event.data.mapping_start.tag == NULL:
            tag = self.resolve(MappingNode, None, implicit)
        else:
            tag_str = fy_token_get_text0(self._parsed_event.data.mapping_start.tag)
            if tag_str == NULL:
                raise MemoryError

            if tag_str[0] == c'!' and tag_str[1] == c'\0':
                tag = self.resolve(MappingNode, None, implicit)
            else:
                tag = PyUnicode_FromString(tag_str)

        flow_style = None
        nstyle = fy_event_get_node_style(self.parsed_event)
        if nstyle == FYNS_FLOW:
            flow_style = True
        elif nstyle == FYNS_BLOCK:
            flow_style = False
        value = []
        node = MappingNode(tag, value, start_markp, None, flow_style)
        if anchor is not None:
            self.anchors[anchor] = node

        self._parse_free_event()

        index = 0
        self._parse_next_event()
        while self.parsed_event.type != FYET_MAPPING_END:
            item_key = self._compose_node(node, None)
            item_value = self._compose_node(node, item_key)
            value.append((item_key, item_value))
            self._parse_next_event()

        end_mark = fy_event_end_mark(self.parsed_event)

        node.end_mark = Mark(self.stream_name, end_mark[0].input_pos, end_mark[0].line, end_mark[0].column, None, None)

        self._parse_free_event()
        return node

    cdef char *_parsed_event_str(self):
        if self.parsed_event == NULL:
            return "NULL"
        elif self.parsed_event.type == FYET_NONE:
            return "NONE"
        elif self.parsed_event.type == FYET_STREAM_START:
            return "STREAM_START"
        elif self.parsed_event.type == FYET_STREAM_END:
            return "STREAM_END"
        elif self.parsed_event.type == FYET_DOCUMENT_START:
            return "DOCUMENT_START"
        elif self.parsed_event.type == FYET_DOCUMENT_END:
            return "DOCUMENT_END"
        elif self.parsed_event.type == FYET_MAPPING_START:
            return "MAPPING_START"
        elif self.parsed_event.type == FYET_MAPPING_END:
            return "MAPPING_END"
        elif self.parsed_event.type == FYET_SEQUENCE_START:
            return "SEQUENCE_START"
        elif self.parsed_event.type == FYET_SEQUENCE_END:
            return "SEQUENCE_END"
        elif self.parsed_event.type == FYET_SCALAR:
            return "SCALAR"
        elif self.parsed_event.type == FYET_ALIAS:
            return "ALIAS"

        return "UNKONWN"

    cdef void _parse_free_event(self):
        fy_parser_event_free(self.parser, self.parsed_event)
        self.parsed_event = NULL
        self._parsed_event = NULL

    cdef int _parse_next_event(self) except 0:

        if self.parsed_event != NULL:
            return 1

        self.parsed_event = fy_parser_parse(self.parser)

        if self.parsed_event != NULL:
            self._parsed_event = <_fy_event *>self.parsed_event
            # if self.parsed_event.type == FYET_STREAM_END:
            #    printf("_parse_next_event: STREAM_END\n")
            return 1

        raise ComposerError(u"unexpected NULL return from fy_parser_parse (_parse_next_event)")

cdef ssize_t input_handler(void *user, void *buf, size_t size):
    cdef FParser parser
    parser = <FParser>user

    if parser.stream_cache is None:
        value = parser.stream.read(size)
        if PyUnicode_CheckExact(value) != 0:
            value = PyUnicode_AsUTF8String(value)
            parser.unicode_source = 1
        if PyBytes_CheckExact(value) == 0:
            raise TypeError(u"a string value is expected")
        parser.stream_cache = value
        parser.stream_cache_pos = 0
        parser.stream_cache_len = PyBytes_GET_SIZE(value)

    if (parser.stream_cache_len - parser.stream_cache_pos) < <int>size:
        size = parser.stream_cache_len - parser.stream_cache_pos

    if size > 0:
        memcpy(buf, PyBytes_AS_STRING(parser.stream_cache) + parser.stream_cache_pos, size)
    parser.stream_cache_pos += size
    if parser.stream_cache_pos == parser.stream_cache_len:
        parser.stream_cache = None

    return size

cdef class FEmitter:

    cdef fy_emitter *emitter

    cdef object stream

    cdef int document_start_implicit
    cdef int document_end_implicit
    cdef object use_version
    cdef object use_tags

    cdef object serialized_nodes
    cdef object anchors
    cdef int last_alias_id
    cdef int closed
    cdef int dump_unicode
    cdef object use_encoding

    def __init__(self, stream, canonical=None, indent=None, width=None, allow_unicode=None, line_break=None, encoding=None, explicit_start=None, explicit_end=None, version=None, tags=None):
        cdef fy_emitter_cfg cfg
        cdef unsigned int flags

        flags = 0

        memset(&cfg, 0, sizeof(cfg))
        cfg.flags = FYECF_MODE_ORIGINAL
        cfg.output = output_handler
        cfg.userdata = <void *>self

        self.stream = stream
        self.dump_unicode = 0
        if hasattr(stream, u'encoding'):
            self.dump_unicode = 1
        if encoding != None:
            self.use_encoding = encoding
        else:
            self.use_encoding = u'utf-8'
        # if canonical:
        #     yaml_emitter_set_canonical(&self.emitter, 1)
        if indent is not None:
            if indent > 9 or indent < 1:
                raise TypeError(u"Indent is out of range")
            flags = flags | ((indent & FYECF_INDENT_MASK) << FYECF_INDENT_SHIFT)
        else:
            flags = flags | FYECF_INDENT_DEFAULT
            
        if width is not None:
            if width > 255 or width < 1:
                raise TypeError(u"Width is out of range")
            flags = flags | ((width & FYECF_WIDTH_MASK) << FYECF_WIDTH_SHIFT)
        else:
            flags = flags | FYECF_WIDTH_DEFAULT

        # if allow_unicode:
        #     yaml_emitter_set_unicode(&self.emitter, 1)
        # if line_break is not None:
        #     if line_break == '\r':
        #         yaml_emitter_set_break(&self.emitter, YAML_CR_BREAK)
        #     elif line_break == '\n':
        #         yaml_emitter_set_break(&self.emitter, YAML_LN_BREAK)
        #     elif line_break == '\r\n':
        #         yaml_emitter_set_break(&self.emitter, YAML_CRLN_BREAK)
        if explicit_start:
            self.document_start_implicit = 0
        else:
            self.document_start_implicit = 1
        if explicit_end:
            self.document_end_implicit = 0
        else:
            self.document_end_implicit = 1
        self.use_version = version
        self.use_tags = tags

        cfg.flags = <fy_emitter_cfg_flags>(FYECF_MODE_ORIGINAL | flags)
        self.emitter = fy_emitter_create(&cfg)
        if self.emitter == NULL:
             # printf("emitter: __init(): failed to create emitter()\n")
             raise MemoryError

        # printf("emitter __init__()\n")

        self.serialized_nodes = {}
        self.anchors = {}
        self.last_alias_id = 0
        self.closed = -1

    def __dealloc__(self):
        fy_emitter_destroy(self.emitter)

    def dispose(self):
        pass

    cdef object _emitter_error(self):
        # if self.emitter.error == YAML_MEMORY_ERROR:
            # printf("_emitter_error()\n")
            return MemoryError
        # elif self.emitter.error == YAML_EMITTER_ERROR:
        #     problem = PyUnicode_FromString(self.emitter.problem)
        #     return EmitterError(problem)
        # raise ValueError(u"no emitter error")
        # return None

    def emit(self, event_object):
        # printf("emit()\n")
        cdef fy_event *event = NULL

        # cdef yaml_encoding_t encoding
        # cdef yaml_version_directive_t version_directive_value
        # cdef yaml_version_directive_t *version_directive
        # cdef yaml_tag_directive_t tag_directives_value[128]
        # cdef yaml_tag_directive_t *tag_directives_start
        # cdef yaml_tag_directive_t *tag_directives_end
        cdef int implicit
        cdef int plain_implicit
        cdef int quoted_implicit
        cdef char *anchor
        cdef char *tag
        cdef char *value
        cdef int length
        cdef fy_scalar_style scalar_style
        cdef fy_version vers_tmp
        cdef fy_node_style node_style
        cdef fy_version *vers
        cdef fy_tag **tags
        cdef fy_tag *tags_arr
        cdef char *tag_handle
        cdef char *tag_prefix
        cdef int idx
        cdef int tag_count

        event_class = event_object.__class__
        if event_class is StreamStartEvent:
            if event_object.encoding != u'utf-8':
                raise ValueError(u"serializer only supports utf-8 (was " + event_object.encoding + u")")

            event = fy_emit_event_create(self.emitter, FYET_STREAM_START)
            if event == NULL:
                raise MemoryError

        elif event_class is StreamEndEvent:

            event = fy_emit_event_create(self.emitter, FYET_STREAM_END)
            if event == NULL:
                raise MemoryError

        elif event_class is DocumentStartEvent:

            vers = NULL
            if event_object.version:
                vers = &vers_tmp
                vers[0].major = event_object.version[0]
                vers[0].minor = event_object.version[1]

            tags = NULL
            tags_arr = NULL
            if event_object.tags:
                if len(event_object.tags) > 128:
                    raise ValueError(u"too many tags")

                tag_count = len(event_object.tags)
                tags = <fy_tag **>malloc(sizeof(fy_tag *) * (tag_count + 1))
                if tags == NULL:
                    raise MemoryError

                tags_arr = <fy_tag *>malloc(sizeof(fy_tag) * tag_count)
                if tags_arr == NULL:
                    raise MemoryError

                cache = []

                idx = 0
                for handle in event_object.tags:
                    prefix = event_object.tags[handle]
                    if PyUnicode_CheckExact(handle):
                        handle = PyUnicode_AsUTF8String(handle)
                        cache.append(handle)
                    if not PyBytes_CheckExact(handle):
                        raise TypeError(u"tag handle must be a string")
                    tag_handle = PyBytes_AS_STRING(handle)

                    if PyUnicode_CheckExact(prefix):
                        prefix = PyUnicode_AsUTF8String(prefix)
                        cache.append(prefix)
                    if not PyBytes_CheckExact(prefix):
                        raise TypeError(u"tag prefix must be a string")
                    tag_prefix = PyBytes_AS_STRING(prefix)

                    tags_arr[idx].handle = tag_handle
                    tags_arr[idx].prefix = tag_prefix
                    tags[idx] = &tags_arr[idx]
                    idx = idx + 1

                tags[idx] = NULL

            if event_object.explicit:
                implicit = 0
            else:
                implicit = 1

            event = fy_emit_event_create(self.emitter, FYET_DOCUMENT_START, implicit, vers, tags)

            if tags != NULL:
                free(tags)

            if tags_arr != NULL:
                free(tags_arr)

            if event == NULL:
                raise MemoryError

        elif event_class is DocumentEndEvent:
            if event_object.explicit:
                implicit = 0
            else:
                implicit = 1

            event = fy_emit_event_create(self.emitter, FYET_DOCUMENT_END, implicit)
            if event == NULL:
                raise MemoryError

        elif event_class is AliasEvent:
            anchor = NULL
            anchor_object = event_object.anchor
            if PyUnicode_CheckExact(anchor_object):
                anchor_object = PyUnicode_AsUTF8String(anchor_object)
            if not PyBytes_CheckExact(anchor_object):
                raise TypeError(u"anchor must be a string")
            anchor = PyBytes_AS_STRING(anchor_object)

            event = fy_emit_event_create(self.emitter, FYET_ALIAS, anchor)
            if event == NULL:
                raise MemoryError

        elif event_class is ScalarEvent:

            anchor = NULL
            anchor_object = event_object.anchor
            if anchor_object is not None:
                if PyUnicode_CheckExact(anchor_object):
                    anchor_object = PyUnicode_AsUTF8String(anchor_object)
                if not PyBytes_CheckExact(anchor_object):
                    raise TypeError(u"anchor must be a string")
                anchor = PyBytes_AS_STRING(anchor_object)

            tag = NULL
            tag_object = event_object.tag
            if tag_object is not None:
                if PyUnicode_CheckExact(tag_object):
                    tag_object = PyUnicode_AsUTF8String(tag_object)
                if not PyBytes_CheckExact(tag_object):
                    raise TypeError(u"tag must be a string")
                tag = PyBytes_AS_STRING(tag_object)
            value_object = event_object.value
            if PyUnicode_CheckExact(value_object):
                value_object = PyUnicode_AsUTF8String(value_object)
            if not PyBytes_CheckExact(value_object):
                raise TypeError(u"value must be a string")
            value = PyBytes_AS_STRING(value_object)
            length = PyBytes_GET_SIZE(value_object)

            plain_implicit = 0
            quoted_implicit = 0
            if event_object.implicit is not None:
                plain_implicit = event_object.implicit[0]
                quoted_implicit = event_object.implicit[1]

            style_object = event_object.style
            scalar_style = FYSS_PLAIN
            if style_object == "'" or style_object == u"'":
                scalar_style = FYSS_SINGLE_QUOTED
            elif style_object == "\"" or style_object == u"\"":
                scalar_style = FYSS_DOUBLE_QUOTED
            elif style_object == "|" or style_object == u"|":
                scalar_style = FYSS_LITERAL
            elif style_object == ">" or style_object == u">":
                scalar_style = FYSS_FOLDED

            if plain_implicit != 0 or quoted_implicit != 0:
                tag = NULL

            event = fy_emit_event_create(self.emitter, FYET_SCALAR, scalar_style, value, length, anchor, tag)
            if event == NULL:
                raise MemoryError

        elif event_class is SequenceStartEvent:
            anchor = NULL
            anchor_object = event_object.anchor
            if anchor_object is not None:
                if PyUnicode_CheckExact(anchor_object):
                    anchor_object = PyUnicode_AsUTF8String(anchor_object)
                if not PyBytes_CheckExact(anchor_object):
                    raise TypeError(u"anchor must be a string")
                anchor = PyBytes_AS_STRING(anchor_object)
            tag = NULL
            tag_object = event_object.tag
            if tag_object is not None:
                if PyUnicode_CheckExact(tag_object):
                    tag_object = PyUnicode_AsUTF8String(tag_object)
                if not PyBytes_CheckExact(tag_object):
                    raise TypeError(u"tag must be a string")
                tag = PyBytes_AS_STRING(tag_object)

            if event_object.flow_style:
                node_style = FYNS_FLOW
            else:
                node_style = FYNS_BLOCK

            if event_object.implicit:
                implicit = 1
            else:
                implicit = 0

            if implicit != 0:
                tag = NULL

            event = fy_emit_event_create(self.emitter, FYET_SEQUENCE_START, node_style, NULL, tag)
            if event == NULL:
                raise MemoryError

        elif event_class is SequenceEndEvent:
            event = fy_emit_event_create(self.emitter, FYET_SEQUENCE_END)
            if event == NULL:
                raise MemoryError

        elif event_class is MappingStartEvent:
            anchor = NULL
            anchor_object = event_object.anchor
            if anchor_object is not None:
                if PyUnicode_CheckExact(anchor_object):
                    anchor_object = PyUnicode_AsUTF8String(anchor_object)
                if not PyBytes_CheckExact(anchor_object):
                    raise TypeError(u"anchor must be a string")
                anchor = PyBytes_AS_STRING(anchor_object)

            tag = NULL
            tag_object = event_object.tag
            if tag_object is not None:
                if PyUnicode_CheckExact(tag_object):
                    tag_object = PyUnicode_AsUTF8String(tag_object)
                if not PyBytes_CheckExact(tag_object):
                    raise TypeError(u"tag must be a string")
                tag = PyBytes_AS_STRING(tag_object)

            if event_object.flow_style:
                node_style = FYNS_FLOW
            else:
                node_style = FYNS_BLOCK

            if event_object.implicit:
                implicit = 1
            else:
                implicit = 0

            event = fy_emit_event_create(self.emitter, FYET_MAPPING_START, node_style, anchor, tag)
            if event == NULL:
                raise MemoryError

        elif event_class is MappingEndEvent:
            event = fy_emit_event_create(self.emitter, FYET_MAPPING_END)
            if event == NULL:
                raise MemoryError

        else:
            raise TypeError(u"invalid event %s" % event_object)

        ret = fy_emit_event(self.emitter, event)
        if ret != 0:
            # error = self._emitter_error()
            # raise error
            raise MemoryError

        return 1

    def open(self):
        # printf("open()\n")
        cdef fy_event *event

        if self.closed == -1:
            if self.use_encoding != u'utf-8':
                raise ValueError(u"serializer only supports utf-8 (was " + self.use_encoding + u")")

            event = fy_emit_event_create(self.emitter, FYET_STREAM_START)
            if event == NULL:
                raise MemoryError
            ret = fy_emit_event(self.emitter, event)
            if ret != 0:
                raise MemoryError
            self.closed = 0
        elif self.closed == 1:
            raise SerializerError(u"serializer is closed")
        else:
            raise SerializerError(u"serializer is already opened")
        return None

    def close(self):
        # printf("close()\n")
        cdef fy_event *event
        if self.closed == -1:
            raise SerializerError(u"serializer is not opened")
        elif self.closed == 0:
            event = fy_emit_event_create(self.emitter, FYET_STREAM_END)
            if event == NULL:
                raise MemoryError
            ret = fy_emit_event(self.emitter, event)
            if ret != 0:
                raise MemoryError
            self.closed = 1
        return None

    def serialize(self, node):
        # printf("serialize()\n")
        cdef fy_event *event
        cdef fy_version *vers
        cdef fy_tag **tags
        cdef fy_tag *tags_arr
        cdef fy_version vers_tmp
        cdef char *tag_handle
        cdef char *tag_prefix
        cdef int idx
        cdef int tag_count

        vers = NULL
        tags = NULL
        if self.closed == -1:
            raise SerializerError(u"serializer is not opened")
        elif self.closed == 1:
            raise SerializerError(u"serializer is closed")
        cache = []
        vers = NULL
        if self.use_version:
            vers = &vers_tmp
            vers[0].major = self.use_version[0]
            vers[0].minor = self.use_version[1]

        tags = NULL
        tags_arr = NULL
        if self.use_tags:
            if len(self.use_tags) > 128:
                raise ValueError(u"too many tags")

            tag_count = len(self.use_tags)
            tags = <fy_tag **>malloc(sizeof(fy_tag *) * (tag_count + 1))
            if tags == NULL:
                raise MemoryError

            tags_arr = <fy_tag *>malloc(sizeof(fy_tag) * tag_count)
            if tags_arr == NULL:
                raise MemoryError

            idx = 0
            for handle in self.use_tags:
                prefix = self.use_tags[handle]
                if PyUnicode_CheckExact(handle):
                    handle = PyUnicode_AsUTF8String(handle)
                    cache.append(handle)
                if not PyBytes_CheckExact(handle):
                    raise TypeError(u"tag handle must be a string")
                tag_handle = PyBytes_AS_STRING(handle)

                if PyUnicode_CheckExact(prefix):
                    prefix = PyUnicode_AsUTF8String(prefix)
                    cache.append(prefix)
                if not PyBytes_CheckExact(prefix):
                    raise TypeError(u"tag prefix must be a string")
                tag_prefix = PyBytes_AS_STRING(prefix)

                tags_arr[idx].handle = tag_handle
                tags_arr[idx].prefix = tag_prefix
                tags[idx] = &tags_arr[idx]
                idx = idx + 1

            tags[idx] = NULL

        event = fy_emit_event_create(self.emitter, FYET_DOCUMENT_START, self.document_start_implicit, vers, tags)

        if vers != NULL:
            free(vers)

        if tags != NULL:
            free(tags)

        if tags_arr != NULL:
            free(tags_arr)

        if event == NULL:
            raise MemoryError
        ret = fy_emit_event(self.emitter, event)
        if ret != 0:
            raise MemoryError

        self._anchor_node(node)
        self._serialize_node(node, None, None)

        event = fy_emit_event_create(self.emitter, FYET_DOCUMENT_END, self.document_end_implicit)
        if event == NULL:
            raise MemoryError
        ret = fy_emit_event(self.emitter, event)
        if ret != 0:
            raise MemoryError

        self.serialized_nodes = {}
        self.anchors = {}
        self.last_alias_id = 0

        return None

    cdef int _anchor_node(self, object node) except 0:
        # printf("_anchor_node()\n")
        if node in self.anchors:
            if self.anchors[node] is None:
                self.last_alias_id = self.last_alias_id+1
                self.anchors[node] = u"id%03d" % self.last_alias_id
        else:
            self.anchors[node] = None
            node_class = node.__class__
            if node_class is SequenceNode:
                for item in node.value:
                    self._anchor_node(item)
            elif node_class is MappingNode:
                for key, value in node.value:
                    self._anchor_node(key)
                    self._anchor_node(value)
        return 1

    cdef int _serialize_node(self, object node, object parent, object index) except 0:
        # printf("_serialize_node()\n")
        cdef fy_event *event
        cdef char *anchor
        # cdef yaml_event_t event
        # cdef int implicit
        # cdef int plain_implicit
        # cdef int quoted_implicit
        # cdef char *tag
        # cdef char *value
        # cdef int length
        # cdef int item_index
        cdef fy_scalar_style scalar_style
        cdef fy_node_style node_style
        # cdef yaml_sequence_style_t sequence_style
        # cdef yaml_mapping_style_t mapping_style

        anchor_object = self.anchors[node]
        anchor = NULL
        if anchor_object is not None:
            if PyUnicode_CheckExact(anchor_object):
                anchor_object = PyUnicode_AsUTF8String(anchor_object)
            if not PyBytes_CheckExact(anchor_object):
                raise TypeError(u"anchor must be a string")
            anchor = PyBytes_AS_STRING(anchor_object)

        if node in self.serialized_nodes:
            event = fy_emit_event_create(self.emitter, FYET_ALIAS, anchor)
            if event == NULL:
                raise MemoryError
            ret = fy_emit_event(self.emitter, event)
            if ret != 0:
                raise MemoryError

            return 1

        node_class = node.__class__
        self.serialized_nodes[node] = True
        self.descend_resolver(parent, index)

        if node_class is ScalarNode:
            plain_implicit = 0
            quoted_implicit = 0
            tag_object = node.tag
            if self.resolve(ScalarNode, node.value, (True, False)) == tag_object:
                plain_implicit = 1
            if self.resolve(ScalarNode, node.value, (False, True)) == tag_object:
                quoted_implicit = 1
            tag = NULL
            if tag_object is not None:
                if PyUnicode_CheckExact(tag_object):
                    tag_object = PyUnicode_AsUTF8String(tag_object)
                if not PyBytes_CheckExact(tag_object):
                    raise TypeError(u"tag must be a string")
                tag = PyBytes_AS_STRING(tag_object)
            value_object = node.value
            if PyUnicode_CheckExact(value_object):
                value_object = PyUnicode_AsUTF8String(value_object)
            if not PyBytes_CheckExact(value_object):
                raise TypeError(u"value must be a string")
            value = PyBytes_AS_STRING(value_object)
            length = PyBytes_GET_SIZE(value_object)
            style_object = node.style

            scalar_style = FYSS_PLAIN
            if style_object == "'" or style_object == u"'":
                scalar_style = FYSS_SINGLE_QUOTED
            elif style_object == "\"" or style_object == u"\"":
                scalar_style = FYSS_DOUBLE_QUOTED
            elif style_object == "|" or style_object == u"|":
                scalar_style = FYSS_LITERAL
            elif style_object == ">" or style_object == u">":
                scalar_style = FYSS_FOLDED

            # printf("_serialize_node() - tag=%s plain_implicit=%d quoted_implicit=%d\n", tag, plain_implicit, quoted_implicit)

            if plain_implicit != 0 or quoted_implicit != 0:
                tag = NULL

            event = fy_emit_event_create(self.emitter, FYET_SCALAR, scalar_style, value, length, anchor, tag)
            if event == NULL:
                raise MemoryError
            ret = fy_emit_event(self.emitter, event)
            if ret != 0:
                raise MemoryError

        elif node_class is SequenceNode:
            tag_object = node.tag
            if self.resolve(SequenceNode, node.value, True) == tag_object:
                implicit = 1
            else:
                implicit = 0
            tag = NULL
            if tag_object is not None:
                if PyUnicode_CheckExact(tag_object):
                    tag_object = PyUnicode_AsUTF8String(tag_object)
                if not PyBytes_CheckExact(tag_object):
                    raise TypeError(u"tag must be a string")
                tag = PyBytes_AS_STRING(tag_object)

            if node.flow_style:
                node_style = FYNS_FLOW
            else:
                node_style = FYNS_BLOCK

            if implicit != 0:
                tag = NULL

            event = fy_emit_event_create(self.emitter, FYET_SEQUENCE_START, node_style, anchor, tag)
            if event == NULL:
                raise MemoryError
            ret = fy_emit_event(self.emitter, event)
            if ret != 0:
                raise MemoryError

            item_index = 0
            for item in node.value:
                self._serialize_node(item, node, item_index)
                item_index = item_index+1

            event = fy_emit_event_create(self.emitter, FYET_SEQUENCE_END)
            if event == NULL:
                raise MemoryError
            ret = fy_emit_event(self.emitter, event)
            if ret != 0:
                raise MemoryError

        elif node_class is MappingNode:
            tag_object = node.tag
            if self.resolve(MappingNode, node.value, True) == tag_object:
                implicit = 1
            else:
                implicit = 0
            tag = NULL
            if tag_object is not None:
                if PyUnicode_CheckExact(tag_object):
                    tag_object = PyUnicode_AsUTF8String(tag_object)
                if not PyBytes_CheckExact(tag_object):
                    raise TypeError(u"tag must be a string")
                tag = PyBytes_AS_STRING(tag_object)

            if node.flow_style:
                node_style = FYNS_FLOW
            else:
                node_style = FYNS_BLOCK

            if implicit != 0:
                tag = NULL

            event = fy_emit_event_create(self.emitter, FYET_MAPPING_START, node_style, anchor, tag)
            if event == NULL:
                raise MemoryError
            ret = fy_emit_event(self.emitter, event)
            if ret != 0:
                raise MemoryError

            for item_key, item_value in node.value:
                self._serialize_node(item_key, node, None)
                self._serialize_node(item_value, node, item_key)

            event = fy_emit_event_create(self.emitter, FYET_MAPPING_END)
            if event == NULL:
                raise MemoryError
            ret = fy_emit_event(self.emitter, event)
            if ret != 0:
                raise MemoryError

        self.ascend_resolver()
        return 1

cdef int output_handler(fy_emitter *emit, fy_emitter_write_type type, const char *str, int len, void *data):
    cdef FEmitter emitter
    emitter = <FEmitter>data
    if emitter.dump_unicode == 0:
        value = PyBytes_FromStringAndSize(str, len)
    else:
        value = PyUnicode_DecodeUTF8(str, len, 'strict')
    emitter.stream.write(value)
    return len
