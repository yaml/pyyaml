
cdef extern from "_yaml.h":

    int PyString_CheckExact(object o)
    int PyUnicode_CheckExact(object o)
    char *PyString_AS_STRING(object o)
    int PyString_GET_SIZE(object o)
    object PyString_FromStringAndSize(char *v, int l)

    cdef enum yaml_encoding_t:
        YAML_ANY_ENCODING
        YAML_UTF8_ENCODING
        YAML_UTF16LE_ENCODING
        YAML_UTF16BE_ENCODING
    cdef enum yaml_error_type_t:
        YAML_NO_ERROR
        YAML_MEMORY_ERROR
        YAML_READER_ERROR
        YAML_SCANNER_ERROR
        YAML_PARSER_ERROR
        YAML_WRITER_ERROR
        YAML_EMITTER_ERROR
    cdef enum yaml_scalar_style_t:
        YAML_ANY_SCALAR_STYLE
        YAML_PLAIN_SCALAR_STYLE
        YAML_SINGLE_QUOTED_SCALAR_STYLE
        YAML_DOUBLE_QUOTED_SCALAR_STYLE
        YAML_LITERAL_SCALAR_STYLE
        YAML_FOLDED_SCALAR_STYLE
    cdef enum yaml_sequence_style_t:
        YAML_ANY_SEQUENCE_STYLE
        YAML_BLOCK_SEQUENCE_STYLE
        YAML_FLOW_SEQUENCE_STYLE
    cdef enum yaml_mapping_style_t:
        YAML_ANY_MAPPING_STYLE
        YAML_BLOCK_MAPPING_STYLE
        YAML_FLOW_MAPPING_STYLE
    cdef enum yaml_token_type_t:
        YAML_STREAM_START_TOKEN
        YAML_STREAM_END_TOKEN
        YAML_VERSION_DIRECTIVE_TOKEN
        YAML_TAG_DIRECTIVE_TOKEN
        YAML_DOCUMENT_START_TOKEN
        YAML_DOCUMENT_END_TOKEN
        YAML_BLOCK_SEQUENCE_START_TOKEN
        YAML_BLOCK_MAPPING_START_TOKEN
        YAML_BLOCK_END_TOKEN
        YAML_FLOW_SEQUENCE_START_TOKEN
        YAML_FLOW_SEQUENCE_END_TOKEN
        YAML_FLOW_MAPPING_START_TOKEN
        YAML_FLOW_MAPPING_END_TOKEN
        YAML_BLOCK_ENTRY_TOKEN
        YAML_FLOW_ENTRY_TOKEN
        YAML_KEY_TOKEN
        YAML_VALUE_TOKEN
        YAML_ALIAS_TOKEN
        YAML_ANCHOR_TOKEN
        YAML_TAG_TOKEN
        YAML_SCALAR_TOKEN

    ctypedef int yaml_read_handler_t(void *data, char *buffer,
            int size, int *size_read)

    ctypedef struct yaml_mark_t:
        int index
        int line
        int column
    ctypedef struct _yaml_token_tag_data_t:
        char *handle
        char *suffix
    ctypedef struct _yaml_token_scalar_data_t:
        char *value
        int length
        yaml_scalar_style_t style
    ctypedef struct _yaml_token_version_directive_data_t:
        int major
        int minor
    ctypedef struct _yaml_token_tag_directive_data_t:
        char *handle
        char *prefix
    ctypedef union _yaml_token_data_t:
        yaml_encoding_t encoding
        char *anchor
        _yaml_token_tag_data_t tag
        _yaml_token_scalar_data_t scalar
        _yaml_token_version_directive_data_t version_directive
        _yaml_token_tag_directive_data_t tag_directive
    ctypedef struct yaml_token_t:
        yaml_token_type_t type
        _yaml_token_data_t data
        yaml_mark_t start_mark
        yaml_mark_t end_mark
    ctypedef struct yaml_parser_t:
        yaml_error_type_t error
        char *problem
        int problem_offset
        int problem_value
        yaml_mark_t problem_mark
        char *context
        yaml_mark_t context_mark

    char *yaml_get_version_string()
    void yaml_get_version(int *major, int *minor, int *patch)
    void yaml_token_delete(yaml_token_t *token)
    yaml_parser_t *yaml_parser_new()
    void yaml_parser_delete(yaml_parser_t *parser)
    void yaml_parser_set_input_string(yaml_parser_t *parser,
            char *input, int size)
    void yaml_parser_set_input(yaml_parser_t *parser,
            yaml_read_handler_t *handler, void *data)
    void yaml_parser_set_encoding(yaml_parser_t *parser,
            yaml_encoding_t encoding)
    yaml_token_t *yaml_parser_get_token(yaml_parser_t *parser)
    yaml_token_t *yaml_parser_peek_token(yaml_parser_t *parser)

